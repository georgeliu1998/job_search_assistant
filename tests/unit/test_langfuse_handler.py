"""
Unit tests for Langfuse handler functionality.
"""

import os
from unittest.mock import MagicMock, patch

from src.llm.langfuse_handler import (
    get_langfuse_handler,
    is_langfuse_enabled,
    reset_langfuse_handler,
)


class TestGetLangfuseHandler:
    """Test get_langfuse_handler function."""

    def setup_method(self):
        """Reset handler before each test."""
        reset_langfuse_handler()

    def test_disabled_tracing(self):
        """Test that disabled tracing returns None."""
        # Use direct parameter to disable
        handler = get_langfuse_handler(enabled=False)
        assert handler is None

    def test_missing_credentials(self):
        """Test that missing credentials returns None."""
        # Use direct parameters with missing credentials (empty strings)
        handler = get_langfuse_handler(
            enabled=True,
            public_key="",
            secret_key=""
        )
        assert handler is None

    @patch("src.llm.langfuse_handler.CallbackHandler")
    def test_successful_initialization(self, mock_callback_handler):
        """Test successful handler initialization."""
        mock_handler = MagicMock()
        mock_callback_handler.return_value = mock_handler

        # Use direct parameters to ensure valid configuration
        handler = get_langfuse_handler(
            enabled=True,
            public_key="test_public",
            secret_key="test_secret",
            host="https://test.langfuse.com"
        )
        assert handler is mock_handler
        mock_callback_handler.assert_called_once_with(
            public_key="test_public",
            secret_key="test_secret",
            host="https://test.langfuse.com",
        )

    @patch("src.llm.langfuse_handler.CallbackHandler")
    def test_initialization_failure(self, mock_callback_handler):
        """Test handling of initialization failures."""
        mock_callback_handler.side_effect = Exception("Connection failed")

        handler = get_langfuse_handler(
            enabled=True,
            public_key="test_public",
            secret_key="test_secret"
        )
        assert handler is None

    def test_direct_parameter_override(self):
        """Test that direct parameters override settings."""
        # Disable via direct parameter even if settings might enable it
        handler = get_langfuse_handler(enabled=False)
        assert handler is None

    @patch("src.llm.langfuse_handler.CallbackHandler")
    def test_singleton_behavior(self, mock_callback_handler):
        """Test that handler is only initialized once and reused."""
        mock_handler = MagicMock()
        mock_callback_handler.return_value = mock_handler

        # First call should initialize
        handler1 = get_langfuse_handler(
            enabled=True,
            public_key="test_public",
            secret_key="test_secret"
        )
        assert handler1 is mock_handler
        assert mock_callback_handler.call_count == 1

        # Second call should reuse the same instance
        handler2 = get_langfuse_handler()
        assert handler2 is handler1
        assert handler2 is mock_handler
        # Should not have called CallbackHandler again
        assert mock_callback_handler.call_count == 1

        # Third call with different parameters should still reuse
        handler3 = get_langfuse_handler(
            public_key="different_key", secret_key="different_secret"
        )
        assert handler3 is handler1
        assert handler3 is mock_handler
        # Should not have called CallbackHandler again
        assert mock_callback_handler.call_count == 1

    @patch("src.llm.langfuse_handler.CallbackHandler")
    def test_singleton_behavior_disabled(self, mock_callback_handler):
        """Test singleton behavior when handler is disabled."""
        # First call should return None
        handler1 = get_langfuse_handler(enabled=False)
        assert handler1 is None
        assert mock_callback_handler.call_count == 0

        # Second call should also return None without initializing
        handler2 = get_langfuse_handler()
        assert handler2 is None
        assert mock_callback_handler.call_count == 0


class TestResetLangfuseHandler:
    """Test reset_langfuse_handler function."""

    def setup_method(self):
        """Reset handler before each test."""
        reset_langfuse_handler()

    @patch("src.llm.langfuse_handler.CallbackHandler")
    def test_reset_allows_reinitialization(self, mock_callback_handler):
        """Test that reset allows handler to be reinitialized."""
        mock_handler1 = MagicMock()
        mock_handler2 = MagicMock()
        mock_callback_handler.side_effect = [mock_handler1, mock_handler2]

        # First initialization
        handler1 = get_langfuse_handler(
            enabled=True,
            public_key="test_public",
            secret_key="test_secret"
        )
        assert handler1 is mock_handler1
        assert mock_callback_handler.call_count == 1

        # Reset the handler
        reset_langfuse_handler()

        # Second initialization should create a new instance
        handler2 = get_langfuse_handler(
            enabled=True,
            public_key="test_public2",
            secret_key="test_secret2"
        )
        assert handler2 is mock_handler2
        assert handler2 is not handler1
        assert mock_callback_handler.call_count == 2


class TestHelperFunctions:
    """Test helper functions."""

    def setup_method(self):
        """Reset handler before each test."""
        reset_langfuse_handler()

    def test_is_langfuse_enabled(self, mock_api_keys):
        """Test is_langfuse_enabled function with centralized settings."""
        # This will test the actual settings configuration
        # In test environment, langfuse should be disabled by default
        enabled = is_langfuse_enabled()
        # Since we're in test environment, it should be False
        assert enabled is False

    def test_is_langfuse_enabled_with_environment_override(self):
        """Test is_langfuse_enabled with environment variable override."""
        with patch.dict(
            os.environ,
            {
                "APP_ENV": "dev",
                "LANGFUSE_PUBLIC_KEY": "test_public",
                "LANGFUSE_SECRET_KEY": "test_secret",
            },
        ):
            # Reload settings to pick up environment changes
            from src.config.settings import reload_settings
            reload_settings()
            
            # In dev environment with valid keys, should be enabled
            enabled = is_langfuse_enabled()
            assert enabled is True
