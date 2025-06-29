"""
Unit tests for Langfuse configuration via centralized configuration.
"""

import os
from unittest.mock import patch

from src.config import ConfigManager, config


class TestLangfuseConfig:
    """Test Langfuse configuration via centralized config."""

    def test_langfuse_config_from_config(self, mock_api_keys):
        """Test that Langfuse configuration is accessible via config."""
        langfuse_config = config.observability.langfuse

        # Test basic structure
        assert hasattr(langfuse_config, "enabled")
        assert hasattr(langfuse_config, "host")
        assert hasattr(langfuse_config, "public_key")
        assert hasattr(langfuse_config, "secret_key")
        assert hasattr(langfuse_config, "is_valid")

    def test_langfuse_validation_method(self, mock_api_keys):
        """Test the is_valid method works correctly."""
        langfuse_config = config.observability.langfuse

        # With mocked keys, should be valid if enabled
        if (
            langfuse_config.enabled
            and langfuse_config.public_key
            and langfuse_config.secret_key
        ):
            assert langfuse_config.is_valid() is True
        else:
            # If disabled or missing keys, should be invalid
            assert langfuse_config.is_valid() is False

    def test_langfuse_default_host(self):
        """Test that default host is set correctly."""
        langfuse_config = config.observability.langfuse
        assert langfuse_config.host == "https://us.cloud.langfuse.com"

    def test_langfuse_environment_loading(self):
        """Test that Langfuse config loads from environment variables."""
        with patch.dict(
            os.environ,
            {
                "APP_ENV": "dev",
                "ANTHROPIC_API_KEY": "test-anthropic-key",  # Required for dev environment
                "LANGFUSE_PUBLIC_KEY": "test_public_key",
                "LANGFUSE_SECRET_KEY": "test_secret_key",
            },
        ):
            # Reload config to pick up new environment variables
            test_config = config.reload()

            langfuse_config = test_config.observability.langfuse
            assert langfuse_config.public_key == "test_public_key"
            assert langfuse_config.secret_key == "test_secret_key"

    def test_langfuse_enabled_in_dev_environment(self):
        """Test that Langfuse is enabled in development environment."""
        with patch.dict(
            os.environ,
            {
                "APP_ENV": "dev",
                "ANTHROPIC_API_KEY": "test-anthropic-key",  # Required for dev environment
            },
        ):
            test_config = config.reload()

            langfuse_config = test_config.observability.langfuse
            # In dev.toml, langfuse is enabled
            assert langfuse_config.enabled is True

    def test_langfuse_disabled_in_stage_environment(self):
        """Test that Langfuse is disabled in stage environment."""
        with patch.dict(os.environ, {"APP_ENV": "stage"}):
            test_config = config.reload()

            langfuse_config = test_config.observability.langfuse
            # In stage.toml, langfuse is disabled
            assert langfuse_config.enabled is False

    def test_langfuse_enabled_in_prod_environment(self):
        """Test that Langfuse is enabled in production environment."""
        with patch.dict(
            os.environ,
            {
                "APP_ENV": "prod",
                "ANTHROPIC_API_KEY": "test-anthropic-key",  # Required for prod environment
            },
        ):
            test_config = config.reload()

            langfuse_config = test_config.observability.langfuse
            # In prod.toml, langfuse is enabled
            assert langfuse_config.enabled is True
