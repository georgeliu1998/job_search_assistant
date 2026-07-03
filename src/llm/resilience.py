"""
LLM call-resilience building block.

A reusable call-resilience helper: it answers "did we get a valid response
object at all?" (timeouts, rate limits, 5xx, connection drops, and
structured-output parse failures), separate from any content-quality checks.

Mechanism: LangChain-native, Tenacity-backed. Each provider model is bound to
its structured-output schema *before* being composed, then wrapped with a
same-provider transient retry (``with_retry``) and finally placed under a
cross-provider fallback (``with_fallbacks``). A provider-agnostic classifier
decides what counts as transient (retry + fall back) versus fail-fast (auth /
malformed / unknown -> surface immediately so real bugs aren't masked).
"""

import os
from typing import Any, Dict, List, Mapping, Optional, Tuple, Type

from langchain_core.exceptions import OutputParserException
from langchain_core.language_models import BaseChatModel
from langchain_core.runnables import Runnable, RunnableConfig, RunnableLambda
from pydantic import BaseModel, ValidationError

from src.config.models import LLMConfig
from src.exceptions.llm import LLMError
from src.llm.factory import PROVIDER_ENV_VARS, get_chat_model
from src.utils.logging import get_logger

logger = get_logger(__name__)

# Default number of same-provider attempts before falling back; overridable
# per call so this building block stays independent of any external config.
DEFAULT_MAX_ATTEMPTS_PER_PROVIDER = 3

# HTTP status codes that represent a transient, retryable condition when a
# provider lumps several failure modes under one exception type (the Google
# ``genai`` SDK in particular raises a single ``ClientError`` for all 4xx).
_TRANSIENT_STATUS_CODES = frozenset({408, 409, 425, 429})


class TransientLLMError(LLMError):
    """Raised when a transient LLM failure exhausts all retries and fallbacks.

    Internally, the classifier wraps each transient provider/framework failure
    into this single type so the native ``with_retry`` / ``with_fallbacks``
    type filters can act on one unambiguous class while non-transient errors
    keep their original type and fail fast. This is also what callers of a
    runnable built by :func:`build_resilient_llm` will see raised if the
    primary's retries *and* the fallback's retries are all exhausted; the
    original provider exception is preserved via ``__cause__``.
    """


def _build_transient_type_tuple() -> Tuple[Type[BaseException], ...]:
    """Collect always-transient exception types from whatever SDKs are present.

    Imports are best-effort so a single-provider install (or a missing optional
    dependency) never breaks the classifier.
    """
    # Trade-off: at temperature=0.0 a parse failure is close to deterministic,
    # so same-provider retries here are likely to re-fail before the
    # cross-provider fallback (which is what actually helps) kicks in. Still
    # worth retrying since not every task runs at temperature=0.0, and a
    # transient upstream glitch can also produce a one-off malformed response.
    # Cost asymmetry to be aware of: a persistent output_model/schema bug (not
    # a flake) burns the full budget on every request - up to
    # 2 x max_attempts_per_provider billed calls when a fallback is configured
    # - since every attempt on both providers repeats the same failure. Lower
    # max_attempts_per_provider for a task if this becomes a concern.
    types: List[Type[BaseException]] = [OutputParserException, ValidationError]

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

        # APITimeoutError subclasses APIConnectionError; status-carrying errors
        # (rate limits, 5xx/overloaded) are handled separately below via
        # status_code inspection, since APIStatusError covers many status codes.
        types += [anthropic.APIConnectionError]
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

    # Anthropic's SDK carries the HTTP status on every APIStatusError subclass
    # (RateLimitError=429, ServiceUnavailableError=503, OverloadedError=529,
    # DeadlineExceededError=504, InternalServerError=5xx, ...), so inspecting
    # status_code covers all of them without enumerating each subclass and
    # tells them apart from fail-fast 400/401/403/404.
    try:
        import anthropic

        if isinstance(exc, anthropic.APIStatusError):
            status_code = getattr(exc, "status_code", None)
            return status_code is not None and (
                status_code >= 500 or status_code in _TRANSIENT_STATUS_CODES
            )
    except ImportError:  # pragma: no cover - provider package optional
        pass

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
    env_var = PROVIDER_ENV_VARS.get(config.provider.lower())
    return bool(env_var and os.getenv(env_var))


def _guard_leaf(runnable: Runnable, config: LLMConfig, role: str) -> Runnable:
    """Wrap a model/structured runnable to normalize errors and log who served.

    The outer ``config: LLMConfig`` identifies this leaf's provider/model for
    logging only. The inner callback's ``config: Optional[RunnableConfig]``
    parameter must be named exactly ``config`` - LangChain's
    ``accepts_config()`` only injects the caller's ``RunnableConfig`` (with
    Langfuse callbacks/tags) into a wrapped callable when the parameter is
    literally named ``config``; any other name (e.g. ``run_config``) is never
    populated. We forward it explicitly to ``runnable.invoke()`` as
    belt-and-braces; today, callbacks also propagate independently via
    LangChain's config contextvar regardless of this parameter's name, but the
    explicit forwarding is what the parameter name must match to actually
    fire, and is what protects us if that contextvar behavior ever changes.

    Transient failures are re-raised as ``TransientLLMError`` (the single type
    the retry/fallback filters watch); non-transient failures propagate
    unchanged (fail fast). On success it logs which provider+model actually
    served the response, making primary-provider degradation observable.
    """
    provider, model = config.provider, config.model

    def _invoke(value: Any, config: Optional[RunnableConfig] = None) -> Any:
        try:
            result = runnable.invoke(value, config=config)
        except TransientLLMError:
            raise
        except Exception as exc:
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
        # Routine primary success is expected on every call and would be pure
        # noise at INFO; the fallback actually serving is the degradation
        # signal worth surfacing by default.
        log = logger.info if role == "fallback" else logger.debug
        log("LLM response served by provider=%s model=%s (role=%s)", provider, model, role)
        return result

    return RunnableLambda(_invoke, name=f"resilient_{role}_{provider}")


def _build_leaf(
    config: LLMConfig,
    output_model: Optional[Type[BaseModel]],
    role: str,
    max_attempts_per_provider: int,
    wait_exponential_jitter: bool,
    exponential_jitter_params: Optional[Mapping[str, Any]],
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

    retry_kwargs: Dict[str, Any] = {
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
    exponential_jitter_params: Optional[Mapping[str, Any]] = None,
) -> Runnable:
    """Build a resilient runnable: same-provider retry under cross-provider fallback.

    Args:
        primary_config: LLM config for the primary provider/model. Unlike the
            fallback, a missing primary API key is *not* handled gracefully:
            it raises ``LLMProviderError`` eagerly (via ``get_chat_model``)
            since a misconfigured primary is a config bug, not a runtime
            condition to degrade around.
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

        Note: there is no aggregate deadline across retries + fallback. Worst
        case latency is roughly ``max_attempts_per_provider`` x number of
        providers, plus exponential backoff between attempts. Fine for
        best-effort batch jobs; revisit with an overall timeout if this is
        ever wired into a latency-sensitive (e.g. interactive) path.

    Raises:
        ValueError: If ``max_attempts_per_provider`` is not a positive integer.
            Notably, Tenacity's ``stop_after_attempt`` treats 0 or a negative
            value as "never stop", which would otherwise retry forever instead
            of failing fast.
        TransientLLMError: If the primary's retries and the fallback's retries
            (when a fallback is configured) are all exhausted. The original
            provider exception is available via ``__cause__``. Non-transient
            errors (auth, malformed input, unknown) propagate with their
            original type instead.
    """
    if max_attempts_per_provider < 1:
        raise ValueError(
            f"max_attempts_per_provider must be >= 1, got {max_attempts_per_provider} "
            "(0 or negative would retry forever under Tenacity's stop_after_attempt)."
        )

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
