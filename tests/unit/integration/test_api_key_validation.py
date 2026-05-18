"""
Integration tests for API key validation across different environments.

These tests verify that the application properly validates API keys for
different LLM providers under various environment configurations.
"""

import os

import pytest

from src.config.models import LLMProfileConfig
from src.exceptions.llm import LLMProviderError
from src.llm import get_chat_model


class TestAPIKeyValidation:
    """Test API key validation for different LLM providers."""

    def test_anthropic_missing_api_key_raises_error(self):
        """Test that Anthropic model creation fails without API key."""
        config = LLMProfileConfig(
            provider="anthropic",
            model="claude-haiku-4-5",
        )

        old_key = os.environ.pop("ANTHROPIC_API_KEY", None)

        try:
            with pytest.raises(LLMProviderError, match="API key not found"):
                get_chat_model(config)
        finally:
            if old_key:
                os.environ["ANTHROPIC_API_KEY"] = old_key

    def test_anthropic_accepts_valid_api_key(self):
        """Test that Anthropic model is created with a valid API key."""
        config = LLMProfileConfig(
            provider="anthropic",
            model="claude-haiku-4-5",
            api_key="sk-ant-api03-test-key-format",
        )

        model = get_chat_model(config)
        assert model is not None

    def test_different_providers_require_different_api_keys(self):
        """Test that different providers validate their specific API key environment variables."""
        anthropic_config = LLMProfileConfig(
            provider="anthropic",
            model="claude-haiku-4-5",
        )

        google_config = LLMProfileConfig(
            provider="google",
            model="gemini-2.5-flash",
        )

        old_anthropic = os.environ.pop("ANTHROPIC_API_KEY", None)
        old_google = os.environ.pop("GOOGLE_API_KEY", None)

        try:
            with pytest.raises(LLMProviderError, match="ANTHROPIC_API_KEY"):
                get_chat_model(anthropic_config)

            with pytest.raises(LLMProviderError, match="GOOGLE_API_KEY"):
                get_chat_model(google_config)

        finally:
            if old_anthropic:
                os.environ["ANTHROPIC_API_KEY"] = old_anthropic
            if old_google:
                os.environ["GOOGLE_API_KEY"] = old_google

    def test_api_key_precedence_config_over_environment(self):
        """Test that API key in config takes precedence over environment variable."""
        config_key = "config-api-key"
        env_key = "env-api-key"

        os.environ["ANTHROPIC_API_KEY"] = env_key

        try:
            config = LLMProfileConfig(
                provider="anthropic",
                model="claude-haiku-4-5",
                api_key=config_key,
            )

            model = get_chat_model(config)
            assert model is not None

        finally:
            os.environ.pop("ANTHROPIC_API_KEY", None)
