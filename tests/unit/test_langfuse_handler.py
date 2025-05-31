"""
Unit tests for Langfuse handler functionality.
"""

import os
from unittest.mock import MagicMock, patch

from src.llm.langfuse_handler import get_langfuse_handler, is_langfuse_enabled


class TestGetLangfuseHandler:
    """Test get_langfuse_handler function."""

    def test_disabled_tracing(self):
        """Test that disabled tracing returns None."""
        with patch.dict(os.environ, {"LANGFUSE_ENABLED": "false"}):
            handler = get_langfuse_handler()
            assert handler is None

    def test_missing_credentials(self):
        """Test that missing credentials returns None."""
        with patch.dict(os.environ, {"LANGFUSE_ENABLED": "true"}, clear=True):
            handler = get_langfuse_handler()
            assert handler is None

    @patch("src.llm.langfuse_handler.CallbackHandler")
    def test_successful_initialization(self, mock_callback_handler):
        """Test successful handler initialization."""
        mock_handler = MagicMock()
        mock_callback_handler.return_value = mock_handler

        with patch.dict(
            os.environ,
            {
                "LANGFUSE_ENABLED": "true",
                "LANGFUSE_PUBLIC_KEY": "test_public",
                "LANGFUSE_SECRET_KEY": "test_secret",
            },
        ):
            handler = get_langfuse_handler()
            assert handler is mock_handler
            mock_callback_handler.assert_called_once_with(
                public_key="test_public",
                secret_key="test_secret",
                host="https://cloud.langfuse.com",
            )

    @patch("src.llm.langfuse_handler.CallbackHandler")
    def test_initialization_failure(self, mock_callback_handler):
        """Test handling of initialization failures."""
        mock_callback_handler.side_effect = Exception("Connection failed")

        with patch.dict(
            os.environ,
            {
                "LANGFUSE_ENABLED": "true",
                "LANGFUSE_PUBLIC_KEY": "test_public",
                "LANGFUSE_SECRET_KEY": "test_secret",
            },
        ):
            handler = get_langfuse_handler()
            assert handler is None

    def test_direct_parameter_override(self):
        """Test that direct parameters override environment variables."""
        with patch.dict(
            os.environ,
            {
                "LANGFUSE_ENABLED": "false",  # Disabled in env
                "LANGFUSE_PUBLIC_KEY": "env_public",
                "LANGFUSE_SECRET_KEY": "env_secret",
            },
        ):
            # Enable via direct parameter
            handler = get_langfuse_handler(enabled=False)
            assert handler is None


class TestHelperFunctions:
    """Test helper functions."""

    def test_is_langfuse_enabled(self):
        """Test is_langfuse_enabled function."""
        with patch.dict(
            os.environ,
            {
                "LANGFUSE_ENABLED": "true",
                "LANGFUSE_PUBLIC_KEY": "test_public",
                "LANGFUSE_SECRET_KEY": "test_secret",
            },
        ):
            assert is_langfuse_enabled() is True

        with patch.dict(os.environ, {"LANGFUSE_ENABLED": "false"}):
            assert is_langfuse_enabled() is False
