"""
Integration tests for API key validation across different environments.

These tests verify that the application properly validates API keys for
different LLM providers under various environment configurations.
"""

import os

import pytest

from src.config.models import LLMProfileConfig
from src.exceptions.llm import LLMProviderError
from src.llm import get_llm_client


class TestAPIKeyValidation:
    """Test API key validation for different LLM providers."""

    def test_anthropic_client_validates_api_key_presence(self):
        """Test that Anthropic client validates API key is present."""
        # Create config without API key in environment
        config = LLMProfileConfig(
            provider="anthropic",
            model="claude-3-5-haiku-20241022",
            # No api_key provided
        )

        # Clear any existing environment variable
        old_key = os.environ.pop("ANTHROPIC_API_KEY", None)

        try:
            # This should raise an error due to missing API key
            with pytest.raises(LLMProviderError, match="API key not found"):
                client = get_llm_client(config)
                # Try to access the underlying client which triggers API key validation
                client._get_client()
        finally:
            # Restore original environment
            if old_key:
                os.environ["ANTHROPIC_API_KEY"] = old_key

    def test_anthropic_client_accepts_valid_api_key(self):
        """Test that Anthropic client accepts a valid API key format."""
        config_with_key = LLMProfileConfig(
            provider="anthropic",
            model="claude-3-5-haiku-20241022",
            api_key="sk-ant-api03-test-key-format",
        )

        # This should not raise an error
        client = get_llm_client(config_with_key)
        assert client is not None
        assert client.get_model_name() == "claude-3-5-haiku-20241022"

    def test_different_providers_require_different_api_keys(self):
        """Test that different providers validate their specific API key environment variables."""
        # Test Anthropic
        anthropic_config = LLMProfileConfig(
            provider="anthropic",
            model="claude-3-5-haiku-20241022",
        )

        # Test Google
        google_config = LLMProfileConfig(
            provider="google",
            model="gemini-2.5-flash",
        )

        # Clear environment variables
        old_anthropic = os.environ.pop("ANTHROPIC_API_KEY", None)
        old_google = os.environ.pop("GOOGLE_API_KEY", None)

        try:
            # Both should fail with missing API key errors
            with pytest.raises(LLMProviderError, match="ANTHROPIC_API_KEY"):
                client = get_llm_client(anthropic_config)
                client._get_client()

            with pytest.raises(LLMProviderError, match="GOOGLE_API_KEY"):
                client = get_llm_client(google_config)
                client._get_client()

        finally:
            # Restore environment
            if old_anthropic:
                os.environ["ANTHROPIC_API_KEY"] = old_anthropic
            if old_google:
                os.environ["GOOGLE_API_KEY"] = old_google

    def test_api_key_precedence_config_over_environment(self):
        """Test that API key in config takes precedence over environment variable."""
        config_key = "config-api-key"
        env_key = "env-api-key"

        # Set environment variable
        os.environ["ANTHROPIC_API_KEY"] = env_key

        try:
            # Create config with explicit API key
            config = LLMProfileConfig(
                provider="anthropic",
                model="claude-3-5-haiku-20241022",
                api_key=config_key,
            )

            client = get_llm_client(config)

            # The config should use the explicit API key, not the environment one
            assert client.config.api_key == config_key

        finally:
            # Clean up environment
            os.environ.pop("ANTHROPIC_API_KEY", None)
