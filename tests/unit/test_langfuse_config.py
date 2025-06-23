"""
Unit tests for Langfuse configuration via centralized configuration.
"""

import os
from unittest.mock import patch

from src.config import ConfigManager, configs


class TestLangfuseConfigs:
    """Test Langfuse configuration via centralized configs."""

    def test_langfuse_config_from_configs(self, mock_api_keys):
        """Test that Langfuse configuration is accessible via configs."""
        config = configs.observability.langfuse

        # Test basic structure
        assert hasattr(config, "enabled")
        assert hasattr(config, "host")
        assert hasattr(config, "public_key")
        assert hasattr(config, "secret_key")
        assert hasattr(config, "is_valid")

    def test_langfuse_validation_method(self, mock_api_keys):
        """Test the is_valid method works correctly."""
        config = configs.observability.langfuse

        # With mocked keys, should be valid if enabled
        if config.enabled and config.public_key and config.secret_key:
            assert config.is_valid() is True
        else:
            # If disabled or missing keys, should be invalid
            assert config.is_valid() is False

    def test_langfuse_default_host(self):
        """Test that default host is set correctly."""
        config = configs.observability.langfuse
        assert config.host == "https://us.cloud.langfuse.com"

    def test_langfuse_environment_loading(self):
        """Test that Langfuse config loads from environment variables."""
        with patch.dict(
            os.environ,
            {
                "APP_ENV": "dev",
                "LANGFUSE_PUBLIC_KEY": "test_public_key",
                "LANGFUSE_SECRET_KEY": "test_secret_key",
            },
        ):
            # Reload configs to pick up new environment variables
            test_configs = configs.reload()

            config = test_configs.observability.langfuse
            assert config.public_key == "test_public_key"
            assert config.secret_key == "test_secret_key"

    def test_langfuse_enabled_in_dev_environment(self):
        """Test that Langfuse is enabled in development environment."""
        with patch.dict(os.environ, {"APP_ENV": "dev"}):
            test_configs = configs.reload()

            config = test_configs.observability.langfuse
            # In dev.toml, langfuse is enabled
            assert config.enabled is True

    def test_langfuse_disabled_in_test_environment(self):
        """Test that Langfuse is disabled in test environment."""
        with patch.dict(os.environ, {"APP_ENV": "test"}):
            test_configs = configs.reload()

            config = test_configs.observability.langfuse
            # In test.toml, langfuse is disabled
            assert config.enabled is False

    def test_langfuse_disabled_in_prod_environment(self):
        """Test that Langfuse is disabled by default in production environment."""
        with patch.dict(os.environ, {"APP_ENV": "prod"}):
            test_configs = configs.reload()

            config = test_configs.observability.langfuse
            # In prod.toml, langfuse is disabled by default
            assert config.enabled is False
