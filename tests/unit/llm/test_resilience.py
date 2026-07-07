"""
Unit tests for the LLM call-resilience building block.

Covers the exception classifier (transient vs. fail-fast), the resilient
runnable builder (retry + cross-provider fallback), graceful skipping of a
fallback whose API key is missing, and structured-output binding with
``include_raw=False``.
"""

from typing import Any, Dict, List, Optional
from unittest.mock import MagicMock, patch
from uuid import UUID

import httpx
import pytest
from langchain_core.callbacks.base import BaseCallbackHandler
from langchain_core.exceptions import OutputParserException
from langchain_core.runnables import RunnableLambda
from langchain_core.runnables.fallbacks import RunnableWithFallbacks
from pydantic import BaseModel, ValidationError

from src.config.models import LLMConfig
from src.exceptions.llm import LLMProviderError
from src.llm.resilience import (
    TransientLLMError,
    _has_api_key,
    build_resilient_llm,
    is_transient_error,
)


class _Schema(BaseModel):
    value: int


def _make_validation_error() -> ValidationError:
    try:
        _Schema(value="not-an-int")
    except ValidationError as exc:
        return exc
    raise AssertionError("expected ValidationError")


def _anthropic_error(status_code: int, cls: Optional[type] = None) -> BaseException:
    """Build a real Anthropic APIStatusError (subclass) with a given status code."""
    import anthropic

    request = httpx.Request("POST", "https://api.anthropic.com/v1/messages")
    body = {"error": {"type": "x", "message": "boom"}}
    response = httpx.Response(status_code, request=request, json=body)
    error_cls = cls or anthropic.APIStatusError
    return error_cls("boom", response=response, body=body)


class _RecordingHandler(BaseCallbackHandler):
    """Records the `name` of every chain that reports on_chain_start.

    Used to lock in that callbacks registered via config={"callbacks": [...]}
    reach the resilient_* leaf runnables, not just the outermost chain. Note:
    this currently happens via LangChain's config contextvar and would still
    pass even if _guard_leaf's explicit config forwarding were broken (e.g.
    misnamed) - see _guard_leaf's docstring for that distinction.
    """

    def __init__(self) -> None:
        self.chain_start_names: List[Optional[str]] = []

    def on_chain_start(
        self,
        serialized: Dict[str, Any],
        inputs: Dict[str, Any],
        *,
        run_id: UUID,
        parent_run_id: Optional[UUID] = None,
        tags: Optional[List[str]] = None,
        metadata: Optional[Dict[str, Any]] = None,
        **kwargs: Any,
    ) -> None:
        self.chain_start_names.append(kwargs.get("name"))


def _google_error(code: int) -> BaseException:
    from google.genai import errors as genai_errors

    payload = {"error": {"message": "boom"}}
    if code >= 500:
        return genai_errors.ServerError(code, payload)
    return genai_errors.ClientError(code, payload)


class TestIsTransientError:
    """The classifier maps exceptions to transient vs. fail-fast."""

    @pytest.mark.parametrize(
        "exc",
        [
            httpx.TimeoutException("slow"),
            httpx.ConnectError("no route"),
            OutputParserException("bad json"),
            _make_validation_error(),
        ],
    )
    def test_transient_exceptions(self, exc):
        assert is_transient_error(exc) is True

    @pytest.mark.parametrize("status_code", [408, 409, 425, 429])
    def test_google_client_error_transient_status_codes(self, status_code):
        assert is_transient_error(_google_error(status_code)) is True

    def test_google_server_error_is_transient(self):
        assert is_transient_error(_google_error(503)) is True

    def test_google_bad_request_is_fail_fast(self):
        assert is_transient_error(_google_error(400)) is False

    def test_google_auth_error_is_fail_fast(self):
        assert is_transient_error(_google_error(401)) is False

    @pytest.mark.parametrize("status_code", [429, 500, 503, 504, 529])
    def test_anthropic_status_codes_are_transient(self, status_code):
        assert is_transient_error(_anthropic_error(status_code)) is True

    def test_anthropic_connection_error_is_transient(self):
        import anthropic

        request = httpx.Request("POST", "https://api.anthropic.com/v1/messages")
        exc = anthropic.APIConnectionError(request=request)
        assert is_transient_error(exc) is True

    @pytest.mark.parametrize("status_code", [400, 401, 403, 404, 422])
    def test_anthropic_status_codes_are_fail_fast(self, status_code):
        assert is_transient_error(_anthropic_error(status_code)) is False

    @pytest.mark.parametrize(
        "exc",
        [
            ValueError("nope"),
            KeyError("missing"),
            LLMProviderError("API key not found"),
            RuntimeError("unknown"),
        ],
    )
    def test_fail_fast_exceptions(self, exc):
        assert is_transient_error(exc) is False


class TestHasApiKey:
    """Direct unit coverage for _has_api_key's two resolution paths."""

    def test_true_when_api_key_set_directly_on_config(self, monkeypatch):
        monkeypatch.delenv("GOOGLE_API_KEY", raising=False)
        config = LLMConfig(provider="google", model="gemini-2.5-flash-lite", api_key="k")

        assert _has_api_key(config) is True

    def test_true_when_env_var_set_and_config_key_absent(self, monkeypatch):
        monkeypatch.setenv("GOOGLE_API_KEY", "env-key")
        config = LLMConfig(provider="google", model="gemini-2.5-flash-lite", api_key=None)

        assert _has_api_key(config) is True

    def test_false_when_neither_config_key_nor_env_var_set(self, monkeypatch):
        monkeypatch.delenv("GOOGLE_API_KEY", raising=False)
        config = LLMConfig(provider="google", model="gemini-2.5-flash-lite", api_key=None)

        assert _has_api_key(config) is False


class TestBuildResilientLLM:
    """The builder composes retry + fallback and degrades gracefully."""

    def _config(self, provider="anthropic", model="claude-haiku-4-5", api_key="k"):
        return LLMConfig(provider=provider, model=model, api_key=api_key)

    @pytest.mark.parametrize("bad_value", [0, -1])
    def test_rejects_non_positive_max_attempts_per_provider(self, bad_value):
        with pytest.raises(ValueError, match="max_attempts_per_provider"):
            build_resilient_llm(self._config(), max_attempts_per_provider=bad_value)

    @patch("src.llm.resilience.get_chat_model")
    def test_no_fallback_returns_primary_only(self, mock_get):
        mock_get.return_value = RunnableLambda(lambda x: "ok")

        result = build_resilient_llm(self._config())

        assert not isinstance(result, RunnableWithFallbacks)
        assert mock_get.call_count == 1

    @patch("src.llm.resilience.get_chat_model")
    def test_both_keys_present_composes_fallback(self, mock_get):
        mock_get.side_effect = [RunnableLambda(lambda x: "p"), RunnableLambda(lambda x: "f")]

        result = build_resilient_llm(
            self._config(),
            self._config(provider="google", model="gemini-2.5-flash-lite", api_key="k2"),
        )

        assert isinstance(result, RunnableWithFallbacks)
        assert mock_get.call_count == 2

    @patch("src.llm.resilience.get_chat_model")
    def test_missing_fallback_key_skips_fallback(self, mock_get, monkeypatch, caplog):
        monkeypatch.delenv("GOOGLE_API_KEY", raising=False)
        monkeypatch.delenv("ANTHROPIC_API_KEY", raising=False)
        mock_get.return_value = RunnableLambda(lambda x: "p")
        fallback = self._config(provider="google", model="gemini-2.5-flash-lite", api_key=None)

        with caplog.at_level("WARNING"):
            result = build_resilient_llm(self._config(), fallback)

        assert not isinstance(result, RunnableWithFallbacks)
        assert mock_get.call_count == 1
        assert "skipping fallback" in caplog.text.lower()

    @patch("src.llm.resilience.get_chat_model")
    def test_structured_output_binds_include_raw_false(self, mock_get):
        model = MagicMock()
        mock_get.return_value = model

        build_resilient_llm(self._config(), output_model=_Schema)

        model.with_structured_output.assert_called_once_with(_Schema, include_raw=False)

    @patch("src.llm.resilience.get_chat_model")
    def test_structured_output_parse_failure_falls_back(self, mock_get):
        def raise_parse_error(_):
            raise OutputParserException("bad json")

        primary_model = MagicMock()
        primary_model.with_structured_output.return_value = RunnableLambda(raise_parse_error)

        fallback_model = MagicMock()
        fallback_model.with_structured_output.return_value = RunnableLambda(
            lambda _: _Schema(value=1)
        )

        mock_get.side_effect = [primary_model, fallback_model]

        result = build_resilient_llm(
            self._config(),
            self._config(provider="google", model="gemini-2.5-flash-lite", api_key="k2"),
            output_model=_Schema,
            max_attempts_per_provider=1,
        )

        assert result.invoke("hi") == _Schema(value=1)
        primary_model.with_structured_output.assert_called_once_with(_Schema, include_raw=False)
        fallback_model.with_structured_output.assert_called_once_with(_Schema, include_raw=False)

    @patch("src.llm.resilience.get_chat_model")
    def test_callbacks_propagate_to_primary_leaf(self, mock_get):
        mock_get.return_value = RunnableLambda(lambda x: "ok")
        chain = build_resilient_llm(self._config())
        handler = _RecordingHandler()

        result = chain.invoke("hi", config={"callbacks": [handler]})

        assert result == "ok"
        assert any(
            name is not None and name.startswith("resilient_primary_")
            for name in handler.chain_start_names
        )

    @patch("src.llm.resilience.get_chat_model")
    def test_callbacks_propagate_to_fallback_leaf(self, mock_get):
        def primary(_):
            raise httpx.ConnectError("down")

        mock_get.side_effect = [RunnableLambda(primary), RunnableLambda(lambda x: "FALLBACK")]
        chain = build_resilient_llm(
            self._config(),
            self._config(provider="google", model="gemini-2.5-flash-lite", api_key="k2"),
            max_attempts_per_provider=1,
        )
        handler = _RecordingHandler()

        result = chain.invoke("hi", config={"callbacks": [handler]})

        assert result == "FALLBACK"
        assert any(
            name is not None and name.startswith("resilient_fallback_")
            for name in handler.chain_start_names
        )

    @patch("src.llm.resilience.get_chat_model")
    def test_transient_primary_failure_falls_back(self, mock_get):
        attempts = {"primary": 0, "fallback": 0}

        def primary(_):
            attempts["primary"] += 1
            raise httpx.ConnectError("down")

        def fallback(_):
            attempts["fallback"] += 1
            return "FALLBACK"

        mock_get.side_effect = [RunnableLambda(primary), RunnableLambda(fallback)]

        result = build_resilient_llm(
            self._config(),
            self._config(provider="google", model="gemini-2.5-flash-lite", api_key="k2"),
            max_attempts_per_provider=2,
            wait_exponential_jitter=False,
        )

        assert result.invoke("hi") == "FALLBACK"
        assert attempts["primary"] == 2
        assert attempts["fallback"] == 1

    @patch("src.llm.resilience.get_chat_model")
    def test_fail_fast_error_is_not_retried_or_fallen_back(self, mock_get):
        attempts = {"primary": 0, "fallback": 0}

        def primary(_):
            attempts["primary"] += 1
            raise ValueError("config bug")

        def fallback(_):
            attempts["fallback"] += 1
            return "FALLBACK"

        mock_get.side_effect = [RunnableLambda(primary), RunnableLambda(fallback)]

        result = build_resilient_llm(
            self._config(),
            self._config(provider="google", model="gemini-2.5-flash-lite", api_key="k2"),
            max_attempts_per_provider=3,
        )

        with pytest.raises(ValueError, match="config bug"):
            result.invoke("hi")
        assert attempts["primary"] == 1
        assert attempts["fallback"] == 0

    @patch("src.llm.resilience.get_chat_model")
    def test_exhausted_retries_and_fallback_raise_transient_llm_error(self, mock_get):
        def always_fails(_):
            raise httpx.ConnectError("down")

        mock_get.side_effect = [RunnableLambda(always_fails), RunnableLambda(always_fails)]

        result = build_resilient_llm(
            self._config(),
            self._config(provider="google", model="gemini-2.5-flash-lite", api_key="k2"),
            max_attempts_per_provider=2,
            wait_exponential_jitter=False,
        )

        with pytest.raises(TransientLLMError) as exc_info:
            result.invoke("hi")
        assert isinstance(exc_info.value.__cause__, httpx.ConnectError)

    @patch("src.llm.resilience.get_chat_model")
    def test_primary_success_logs_served_provider_at_debug_not_info(self, mock_get, caplog):
        state = {"n": 0}

        def primary(_):
            state["n"] += 1
            if state["n"] == 1:
                raise httpx.ConnectError("down")
            return "RECOVERED"

        mock_get.return_value = RunnableLambda(primary)

        result = build_resilient_llm(
            self._config(), max_attempts_per_provider=3, wait_exponential_jitter=False
        )

        with caplog.at_level("DEBUG"):
            assert result.invoke("hi") == "RECOVERED"

        served_records = [r for r in caplog.records if "served by provider=anthropic" in r.message]
        assert len(served_records) == 1
        assert served_records[0].levelname == "DEBUG"

    @patch("src.llm.resilience.get_chat_model")
    def test_fallback_success_logs_served_provider_at_info(self, mock_get, caplog):
        def primary(_):
            raise httpx.ConnectError("down")

        def fallback(_):
            return "FALLBACK"

        mock_get.side_effect = [RunnableLambda(primary), RunnableLambda(fallback)]

        result = build_resilient_llm(
            self._config(),
            self._config(provider="google", model="gemini-2.5-flash-lite", api_key="k2"),
            max_attempts_per_provider=1,
        )

        with caplog.at_level("DEBUG"):
            assert result.invoke("hi") == "FALLBACK"

        served_records = [r for r in caplog.records if "served by provider=google" in r.message]
        assert len(served_records) == 1
        assert served_records[0].levelname == "INFO"
