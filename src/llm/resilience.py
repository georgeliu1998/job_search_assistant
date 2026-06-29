"""
LLM call-resilience building block.

This is the first, reusable instance of the call-resilience pattern: it answers
"did we get a valid response object at all?" (timeouts, rate limits, 5xx,
connection drops, and structured-output parse failures), separate from the
quality layer (the workflow's critic gates).

Mechanism: LangChain-native, Tenacity-backed. Each provider model is bound to
its structured-output schema *before* being composed, then wrapped with a
same-provider transient retry (``with_retry``) and finally placed under a
cross-provider fallback (``with_fallbacks``). A provider-agnostic classifier
decides what counts as transient (retry + fall back) versus fail-fast (auth /
malformed / unknown -> surface immediately so real bugs aren't masked).
"""

import os
from typing import Any, Optional, Tuple, Type

from langchain_core.exceptions import OutputParserException
from langchain_core.language_models import BaseChatModel
from langchain_core.runnables import Runnable, RunnableConfig, RunnableLambda
from pydantic import BaseModel, ValidationError

from src.config.models import LLMConfig
from src.exceptions.llm import LLMError
from src.llm.factory import get_chat_model
from src.utils.logging import get_logger

logger = get_logger(__name__)

# Default same-provider attempts before falling back. T2 wires this from the
# global ``[llm.resilience]`` config; kept as a plain argument here so this
# building block has no dependency on the (later) config additions.
DEFAULT_MAX_ATTEMPTS_PER_PROVIDER = 3

# HTTP status codes that represent a transient, retryable condition when a
# provider lumps several failure modes under one exception type (the Google
# ``genai`` SDK in particular raises a single ``ClientError`` for all 4xx).
_TRANSIENT_STATUS_CODES = frozenset({408, 409, 425, 429})

_PROVIDER_ENV_VARS = {
    "anthropic": "ANTHROPIC_API_KEY",
    "google": "GOOGLE_API_KEY",
}


class TransientLLMError(LLMError):
    """Internal marker wrapping an underlying transient failure.

    The classifier converts any provider/framework exception it deems transient
    into this single type, so the native ``with_retry`` / ``with_fallbacks``
    type filters can act on one unambiguous class while non-transient errors
    keep their original type and fail fast.
    """


def _build_transient_type_tuple() -> Tuple[Type[BaseException], ...]:
    """Collect always-transient exception types from whatever SDKs are present.

    Imports are best-effort so a single-provider install (or a missing optional
    dependency) never breaks the classifier.
    """
    types: list[Type[BaseException]] = [OutputParserException, ValidationError]

    try:
        import httpx

        types += [
            httpx.TimeoutException,
            httpx.ConnectError,
            httpx.ReadError,
            httpx.RemoteProtocolError,
            httpx.PoolTimeout,
        ]
    except ImportError:  # pragma: no cover - httpx is a hard dependency
        pass

    try:
        import anthropic

        types += [
            anthropic.APITimeoutError,
            anthropic.APIConnectionError,
            anthropic.RateLimitError,
            anthropic.InternalServerError,
        ]
    except ImportError:  # pragma: no cover - provider package optional
        pass

    return tuple(types)


_TRANSIENT_EXCEPTION_TYPES: Tuple[Type[BaseException], ...] = _build_transient_type_tuple()


def is_transient_error(exc: BaseException) -> bool:
    """Classify an exception as transient (retry + fall back) or fail-fast.

    Transient: timeouts, connection drops, rate limits, 5xx/service-unavailable,
    and structured-output parse/validation failures. Everything else - auth
    errors (a config bug), clearly-malformed 4xx, and unknown exceptions - is
    fail-fast so genuine errors surface instead of being silently retried away.
    """
    if isinstance(exc, _TRANSIENT_EXCEPTION_TYPES):
        return True

    # Google's ``genai`` SDK raises a single ``ServerError`` for 5xx and a
    # single ``ClientError`` for all 4xx, so transient 429s must be told apart
    # from fail-fast 400/401/403 by inspecting the HTTP status code.
    try:
        from google.genai import errors as genai_errors
    except ImportError:  # pragma: no cover - provider package optional
        return False

    if isinstance(exc, genai_errors.ServerError):
        return True
    if isinstance(exc, genai_errors.APIError):
        return getattr(exc, "code", None) in _TRANSIENT_STATUS_CODES

    return False


def _has_api_key(config: LLMConfig) -> bool:
    """Return whether an API key is resolvable for the config's provider."""
    if getattr(config, "api_key", None):
        return True
    env_var = _PROVIDER_ENV_VARS.get(config.provider.lower())
    return bool(env_var and os.getenv(env_var))


def _guard_leaf(runnable: Runnable, config: LLMConfig, role: str) -> Runnable:
    """Wrap a model/structured runnable to normalize errors and log who served.

    Transient failures are re-raised as ``TransientLLMError`` (the single type
    the retry/fallback filters watch); non-transient failures propagate
    unchanged (fail fast). On success it logs which provider+model actually
    served the response, making primary-provider degradation observable. The
    incoming ``config`` (carrying the Langfuse callbacks) is forwarded so
    tracing propagates to the fallback runnable too.
    """
    provider, model = config.provider, config.model

    def _invoke(value: Any, run_config: Optional[RunnableConfig] = None) -> Any:
        try:
            result = runnable.invoke(value, config=run_config)
        except TransientLLMError:
            raise
        except BaseException as exc:
            if is_transient_error(exc):
                logger.warning(
                    "Transient LLM error from provider=%s model=%s (role=%s): %s",
                    provider,
                    model,
                    role,
                    exc,
                )
                raise TransientLLMError(
                    f"Transient error from {provider}/{model}: {exc}",
                    details={"provider": provider, "model": model, "role": role},
                ) from exc
            raise
        logger.info(
            "LLM response served by provider=%s model=%s (role=%s)",
            provider,
            model,
            role,
        )
        return result

    return RunnableLambda(_invoke, name=f"resilient_{role}_{provider}")


def _build_leaf(
    config: LLMConfig,
    output_model: Optional[Type[BaseModel]],
    role: str,
    max_attempts_per_provider: int,
    wait_exponential_jitter: bool,
    exponential_jitter_params: Optional[dict],
) -> Runnable:
    """Build a single resilient provider leaf: structured-output + retry."""
    model: BaseChatModel = get_chat_model(config)
    if output_model is not None:
        # include_raw=False is REQUIRED: with include_raw=True a schema-validation
        # failure is swallowed into a ``parsing_error`` key and never raises, so
        # neither the retry nor the fallback would ever trigger. Binding the
        # schema per model here (before any fallback composition) also avoids the
        # introspection bug from calling with_structured_output on a
        # RunnableWithFallbacks.
        bound: Runnable = model.with_structured_output(output_model, include_raw=False)
    else:
        bound = model

    guarded = _guard_leaf(bound, config, role)

    retry_kwargs: dict[str, Any] = {
        "retry_if_exception_type": (TransientLLMError,),
        "wait_exponential_jitter": wait_exponential_jitter,
        "stop_after_attempt": max_attempts_per_provider,
    }
    if exponential_jitter_params is not None:
        retry_kwargs["exponential_jitter_params"] = exponential_jitter_params

    return guarded.with_retry(**retry_kwargs)


def build_resilient_llm(
    primary_config: LLMConfig,
    fallback_config: Optional[LLMConfig] = None,
    *,
    output_model: Optional[Type[BaseModel]] = None,
    max_attempts_per_provider: int = DEFAULT_MAX_ATTEMPTS_PER_PROVIDER,
    wait_exponential_jitter: bool = True,
    exponential_jitter_params: Optional[dict] = None,
) -> Runnable:
    """Build a resilient runnable: same-provider retry under cross-provider fallback.

    Args:
        primary_config: LLM config for the primary provider/model.
        fallback_config: Optional tier-matched fallback on a different provider.
            If omitted, or if its API key is not configured, the fallback is
            skipped gracefully and only the primary (with retries) is used - so
            single-key environments don't crash.
        output_model: Optional Pydantic schema; when given, each provider is
            bound via ``with_structured_output(include_raw=False)`` so parse
            failures raise and trigger retry/fallback.
        max_attempts_per_provider: Same-provider transient attempts before
            either falling back (if a fallback exists) or failing.
        wait_exponential_jitter: Use exponential backoff with jitter between
            same-provider attempts.
        exponential_jitter_params: Optional fine-grained backoff parameters
            forwarded to LangChain's ``with_retry`` (e.g. initial/max/exp_base).

    Returns:
        A LangChain ``Runnable`` to ``.invoke(messages, config=...)``. Pass the
        Langfuse config so tracing propagates across the fallback boundary.
    """
    primary_leaf = _build_leaf(
        primary_config,
        output_model,
        "primary",
        max_attempts_per_provider,
        wait_exponential_jitter,
        exponential_jitter_params,
    )

    if fallback_config is None:
        logger.debug(
            "No fallback configured for provider=%s model=%s; using primary retries only.",
            primary_config.provider,
            primary_config.model,
        )
        return primary_leaf

    if not _has_api_key(fallback_config):
        logger.warning(
            "Fallback provider '%s' API key not configured; skipping fallback and "
            "relying on primary (%s) retries only.",
            fallback_config.provider,
            primary_config.provider,
        )
        return primary_leaf

    fallback_leaf = _build_leaf(
        fallback_config,
        output_model,
        "fallback",
        max_attempts_per_provider,
        wait_exponential_jitter,
        exponential_jitter_params,
    )

    return primary_leaf.with_fallbacks(
        [fallback_leaf],
        exceptions_to_handle=(TransientLLMError,),
    )
