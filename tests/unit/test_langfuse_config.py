"""
Unit tests for Langfuse configuration.
"""

import os
from unittest.mock import patch

from src.config.langfuse import LangfuseConfig, get_langfuse_config


class TestLangfuseConfig:
    """Test LangfuseConfig class."""

    def test_config_from_env_vars(self):
        """Test configuration loading from environment variables."""
        with patch.dict(
            os.environ,
            {
                "LANGFUSE_PUBLIC_KEY": "test_public",
                "LANGFUSE_SECRET_KEY": "test_secret",
                "LANGFUSE_HOST": "https://test.langfuse.com",
                "LANGFUSE_ENABLED": "true",
            },
        ):
            config = LangfuseConfig()
            assert config.public_key == "test_public"
            assert config.secret_key == "test_secret"
            assert config.host == "https://test.langfuse.com"
            assert config.enabled is True

    def test_config_disabled_by_default(self):
        """Test that configuration is disabled by default."""
        with patch.dict(os.environ, {}, clear=True):
            config = LangfuseConfig()
            assert config.enabled is False

    def test_config_enabled_variations(self):
        """Test different ways to enable configuration."""
        enabled_values = ["true", "True", "1", "yes", "on"]

        for value in enabled_values:
            with patch.dict(os.environ, {"LANGFUSE_ENABLED": value}):
                config = LangfuseConfig()
                assert config.enabled is True, f"Failed for value: {value}"

    def test_config_validation(self):
        """Test configuration validation."""
        # Valid config
        config = LangfuseConfig(
            public_key="test_public", secret_key="test_secret", enabled=True
        )
        assert config.is_valid() is True

        # Missing keys - clear environment variables to ensure clean test
        with patch.dict(os.environ, {}, clear=True):
            config = LangfuseConfig(enabled=True)
            assert config.is_valid() is False

        # Disabled
        config = LangfuseConfig(
            public_key="test_public", secret_key="test_secret", enabled=False
        )
        assert config.is_valid() is False

    def test_host_validation(self):
        """Test host URL validation."""
        config = LangfuseConfig(host="https://valid.example.com")
        assert config.validate_host() is True

        config = LangfuseConfig(host="invalid-url")
        assert config.validate_host() is False


class TestGetLangfuseConfig:
    """Test get_langfuse_config function."""

    def test_get_config_function(self):
        """Test that get_langfuse_config returns proper config."""
        config = get_langfuse_config(
            public_key="test_public",
            secret_key="test_secret",
            host="https://test.example.com",
            enabled=True,
        )

        assert isinstance(config, LangfuseConfig)
        assert config.public_key == "test_public"
        assert config.secret_key == "test_secret"
        assert config.host == "https://test.example.com"
        assert config.enabled is True

    def test_get_config_with_env_fallback(self):
        """Test that get_langfuse_config falls back to environment variables."""
        with patch.dict(
            os.environ,
            {
                "LANGFUSE_PUBLIC_KEY": "env_public",
                "LANGFUSE_SECRET_KEY": "env_secret",
                "LANGFUSE_ENABLED": "true",
            },
        ):
            config = get_langfuse_config()
            assert config.public_key == "env_public"
            assert config.secret_key == "env_secret"
            assert config.enabled is True
