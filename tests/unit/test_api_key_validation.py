"""
Tests for API key validation functionality
"""

import os
from unittest.mock import MagicMock, patch

import pytest
from pydantic import ValidationError

from src.config.models import LLMProfileConfig
from src.exceptions.llm import LLMProviderError
from src.llm.clients.anthropic import AnthropicClient


class TestAPIKeyValidation:
    """Test API key validation in different environments"""

    def test_api_key_required_in_production_environment(self):
        """Test that API key is required in production environment"""
        with patch("src.config.models.os.getenv") as mock_getenv:
            mock_getenv.return_value = "prod"  # Production environment

            with pytest.raises(ValidationError) as exc_info:
                LLMProfileConfig(
                    provider="anthropic",
                    model="claude-3-5-haiku-20241022",
                    api_key=None,
                )

            error_msg = str(exc_info.value)
            assert "API key is required for anthropic provider" in error_msg

    def test_api_key_required_in_dev_environment(self):
        """Test that API key is required in development environment"""
        with patch("src.config.models.os.getenv") as mock_getenv:
            mock_getenv.return_value = "dev"  # Development environment

            with pytest.raises(ValidationError) as exc_info:
                LLMProfileConfig(
                    provider="anthropic",
                    model="claude-3-5-haiku-20241022",
                    api_key=None,
                )

            error_msg = str(exc_info.value)
            assert "API key is required for anthropic provider" in error_msg

    def test_api_key_optional_in_stage_environment(self):
        """Test that API key is optional in stage environment"""
        with patch.dict(os.environ, {"APP_ENV": "stage"}, clear=False):
            # Should not raise an error
            config = LLMProfileConfig(
                provider="anthropic", model="stage-test-model", api_key=None
            )
            assert config.api_key is None

    def test_api_key_optional_in_test_environment(self):
        """Test that API key is optional when running in pytest (stage environment)"""
        # This test runs in actual pytest environment with APP_ENV=stage, so validation should be skipped
        config = LLMProfileConfig(
            provider="anthropic", model="claude-3-5-haiku-20241022", api_key=None
        )
        assert config.api_key is None

    def test_api_key_provided_passes_validation(self):
        """Test that providing an API key passes validation"""
        config = LLMProfileConfig(
            provider="anthropic", model="claude-3-5-haiku-20241022", api_key="test-key"
        )
        assert config.api_key == "test-key"

    def test_llm_client_error_message_improvement(self):
        """Test that LLM client provides helpful error messages"""
        # Create config with no API key (this should pass in test environment)
        config = LLMProfileConfig(
            provider="anthropic", model="claude-3-5-haiku-20241022", api_key=None
        )

        # We need to test the _ensure_api_key method directly since the client constructor
        # will call it during initialization. Let's create a client with a valid API key first,
        # then test the method with a missing key.
        config_with_key = LLMProfileConfig(
            provider="anthropic", model="claude-3-5-haiku-20241022", api_key="dummy-key"
        )
        client = AnthropicClient(config_with_key)

        # Mock os.getenv to return empty string for API key
        with patch("src.llm.clients.base.os.getenv", return_value=""):
            # Override the config to have no API key
            client.config.api_key = None

            with pytest.raises(LLMProviderError) as exc_info:
                client._ensure_api_key("ANTHROPIC_API_KEY")

            error_msg = str(exc_info.value)
            assert "API key not found" in error_msg
            assert "ANTHROPIC_API_KEY" in error_msg
            assert "environment or .env file" in error_msg
            assert "README.md" in error_msg
