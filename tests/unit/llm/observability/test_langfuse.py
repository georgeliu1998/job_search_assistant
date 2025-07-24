"""
Unit tests for Langfuse manager functionality.
"""

import os
from unittest.mock import MagicMock, patch

import pytest

from src.llm.observability import LangfuseManager, langfuse_manager


class TestLangfuseManager:
    """Test the LangfuseManager class."""

    def setup_method(self):
        """Setup for each test."""
        # Create a fresh manager instance for testing
        self.manager = LangfuseManager()
        self.manager.reset()

    @patch("src.llm.observability.langfuse.CallbackHandler")
    def test_get_handler_when_enabled(self, mock_callback_handler):
        """Test get_handler when Langfuse is enabled and configured."""
        mock_handler = MagicMock()
        mock_callback_handler.return_value = mock_handler

        # Mock the config to be enabled and valid
        with patch.object(self.manager, "is_enabled", return_value=True):
            handler = self.manager.get_handler()

            assert handler is mock_handler
            mock_callback_handler.assert_called_once_with()

    def test_get_handler_when_disabled(self):
        """Test get_handler when Langfuse is disabled."""
        # Mock the config to be disabled
        with patch.object(self.manager, "is_enabled", return_value=False):
            handler = self.manager.get_handler()

            assert handler is None

    @patch("src.llm.observability.langfuse.CallbackHandler")
    def test_get_handler_initialization_failure(self, mock_callback_handler):
        """Test get_handler when CallbackHandler initialization fails."""
        mock_callback_handler.side_effect = Exception("Connection failed")

        with patch.object(self.manager, "is_enabled", return_value=True):
            handler = self.manager.get_handler()

            assert handler is None

    @patch("src.llm.observability.langfuse.CallbackHandler")
    def test_get_handler_caching(self, mock_callback_handler):
        """Test that handler is cached and reused."""
        mock_handler = MagicMock()
        mock_callback_handler.return_value = mock_handler

        with patch.object(self.manager, "is_enabled", return_value=True):
            # First call should initialize
            handler1 = self.manager.get_handler()
            assert handler1 is mock_handler
            assert mock_callback_handler.call_count == 1

            # Second call should reuse cached handler
            handler2 = self.manager.get_handler()
            assert handler2 is handler1
            assert mock_callback_handler.call_count == 1

    def test_get_config_with_handler(self):
        """Test get_config when handler is available."""
        mock_handler = MagicMock()

        with patch.object(self.manager, "get_handler", return_value=mock_handler):
            config = self.manager.get_config()

            expected = {"callbacks": [mock_handler]}
            assert config == expected

    def test_get_config_without_handler(self):
        """Test get_config when handler is not available."""
        with patch.object(self.manager, "get_handler", return_value=None):
            config = self.manager.get_config()

            assert config == {}

    def test_get_config_with_additional_config(self):
        """Test get_config with additional configuration."""
        mock_handler = MagicMock()
        additional_config = {"temperature": 0.5, "max_tokens": 100}

        with patch.object(self.manager, "get_handler", return_value=mock_handler):
            config = self.manager.get_config(additional_config)

            expected = {
                "callbacks": [mock_handler],
                "temperature": 0.5,
                "max_tokens": 100,
            }
            assert config == expected

    @patch("src.llm.observability.langfuse._workflow_context")
    def test_get_config_in_workflow_context(self, mock_context):
        """Test get_config skips tracing when in workflow context."""
        mock_context.get.return_value = True

        with patch.object(self.manager, "get_handler") as mock_get_handler:
            config = self.manager.get_config()

            # Should return empty config and not call get_handler
            assert config == {}
            mock_get_handler.assert_not_called()

    @patch("src.llm.observability.langfuse._workflow_context")
    def test_get_config_force_tracing_in_workflow_context(self, mock_context):
        """Test get_config with force_tracing=True includes tracing even in workflow context."""
        mock_context.get.return_value = True
        mock_handler = MagicMock()

        with patch.object(self.manager, "get_handler", return_value=mock_handler):
            config = self.manager.get_config(force_tracing=True)

            expected = {"callbacks": [mock_handler]}
            assert config == expected

    @patch("src.llm.observability.langfuse._workflow_context")
    def test_get_workflow_config(self, mock_context):
        """Test get_workflow_config sets context and includes tracing."""
        mock_handler = MagicMock()

        with patch.object(self.manager, "get_handler", return_value=mock_handler):
            config = self.manager.get_workflow_config()

            # Should set workflow context
            mock_context.set.assert_called_with(True)

            # Should include handler
            expected = {"callbacks": [mock_handler]}
            assert config == expected

    @patch("src.llm.observability.langfuse._workflow_context")
    def test_get_workflow_config_with_additional_config(self, mock_context):
        """Test get_workflow_config with additional configuration."""
        mock_handler = MagicMock()
        additional_config = {"temperature": 0.7}

        with patch.object(self.manager, "get_handler", return_value=mock_handler):
            config = self.manager.get_workflow_config(additional_config)

            expected = {
                "callbacks": [mock_handler],
                "temperature": 0.7,
            }
            assert config == expected

    @patch("src.llm.observability.langfuse._workflow_context")
    def test_reset(self, mock_context):
        """Test reset functionality."""
        # Set up a handler first
        with patch(
            "src.llm.observability.langfuse.CallbackHandler"
        ) as mock_callback_handler:
            mock_handler = MagicMock()
            mock_callback_handler.return_value = mock_handler

            with patch.object(self.manager, "is_enabled", return_value=True):
                # Get handler to initialize it
                handler1 = self.manager.get_handler()
                assert handler1 is mock_handler

                # Reset should clear the cached handler and context
                self.manager.reset()
                mock_context.set.assert_called_with(False)

                # Next call should create a new handler
                handler2 = self.manager.get_handler()
                assert handler2 is mock_handler
                # Should have been called twice now
                assert mock_callback_handler.call_count == 2

    def test_is_enabled_integration(self, mock_api_keys):
        """Test is_enabled with real config integration."""
        # In stage environment with mocked keys, should be disabled by default
        enabled = self.manager.is_enabled()
        assert enabled is False


class TestGlobalLangfuseManager:
    """Test the global langfuse_manager instance."""

    def setup_method(self):
        """Reset global manager before each test."""
        langfuse_manager.reset()

    @patch("src.llm.observability.langfuse.CallbackHandler")
    def test_global_manager_singleton_behavior(self, mock_callback_handler):
        """Test that global manager behaves as singleton."""
        mock_handler = MagicMock()
        mock_callback_handler.return_value = mock_handler

        with patch.object(langfuse_manager, "is_enabled", return_value=True):
            # Multiple calls should return the same handler
            handler1 = langfuse_manager.get_handler()
            handler2 = langfuse_manager.get_handler()

            assert handler1 is handler2
            assert handler1 is mock_handler
            assert mock_callback_handler.call_count == 1

    def test_global_manager_get_config(self):
        """Test that global manager get_config works correctly."""
        mock_handler = MagicMock()

        with patch.object(langfuse_manager, "get_handler", return_value=mock_handler):
            config = langfuse_manager.get_config({"temperature": 0.7})

            expected = {
                "callbacks": [mock_handler],
                "temperature": 0.7,
            }
            assert config == expected

    def test_global_manager_when_disabled(self):
        """Test global manager behavior when disabled."""
        with patch.object(langfuse_manager, "is_enabled", return_value=False):
            handler = langfuse_manager.get_handler()
            config = langfuse_manager.get_config()

            assert handler is None
            assert config == {}

    @patch("src.llm.observability.langfuse._workflow_context")
    def test_global_manager_workflow_config(self, mock_context):
        """Test global manager get_workflow_config."""
        mock_handler = MagicMock()

        with patch.object(langfuse_manager, "get_handler", return_value=mock_handler):
            config = langfuse_manager.get_workflow_config({"custom": "value"})

            mock_context.set.assert_called_with(True)
            expected = {
                "callbacks": [mock_handler],
                "custom": "value",
            }
            assert config == expected


class TestConfigIntegration:
    """Test integration with the configuration system."""

    def test_langfuse_enabled_in_dev_environment(self):
        """Test that Langfuse can be enabled in development environment."""
        with patch.dict(
            os.environ,
            {
                "APP_ENV": "dev",
                "ANTHROPIC_API_KEY": "test-anthropic-key",
                "LANGFUSE_PUBLIC_KEY": "test_public",
                "LANGFUSE_SECRET_KEY": "test_secret",
            },
        ):
            from src.config import config

            config.reload()

            manager = LangfuseManager()
            enabled = manager.is_enabled()
            assert enabled is True

    def test_langfuse_disabled_in_stage_environment(self):
        """Test that Langfuse is disabled in stage environment."""
        with patch.dict(os.environ, {"APP_ENV": "stage"}):
            from src.config import config

            config.reload()

            manager = LangfuseManager()
            enabled = manager.is_enabled()
            assert enabled is False


class TestLangfuseManagerEdgeCases:
    """Test edge cases and error scenarios."""

    def setup_method(self):
        """Setup for each test."""
        self.manager = LangfuseManager()
        self.manager.reset()

    def test_multiple_resets(self):
        """Test that multiple resets don't cause issues."""
        self.manager.reset()
        self.manager.reset()
        self.manager.reset()

        # Should still work normally
        with patch.object(self.manager, "is_enabled", return_value=False):
            handler = self.manager.get_handler()
            assert handler is None

    def test_get_config_with_none_additional_config(self):
        """Test get_config with None as additional_config."""
        with patch.object(self.manager, "get_handler", return_value=None):
            config = self.manager.get_config(None)
            assert config == {}

    def test_get_config_with_empty_additional_config(self):
        """Test get_config with empty dict as additional_config."""
        mock_handler = MagicMock()

        with patch.object(self.manager, "get_handler", return_value=mock_handler):
            config = self.manager.get_config({})

            expected = {"callbacks": [mock_handler]}
            assert config == expected
