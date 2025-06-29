"""
Unit tests for the Anthropic LLM client.

Tests the AnthropicClient class including initialization, configuration validation,
API key handling, client creation, invoke method, and error handling.
"""

import os
import time
from unittest.mock import MagicMock, Mock, patch

import pytest

from src.config.models import LLMProfileConfig
from src.exceptions.llm import LLMProviderError, LLMResponseError
from src.llm.clients.anthropic import AnthropicClient


class TestAnthropicClientInitialization:
    """Test AnthropicClient initialization and configuration validation."""

    def test_successful_initialization_with_valid_config(self):
        """Test successful client initialization with valid configuration."""
        config = LLMProfileConfig(
            provider="anthropic",
            model="claude-3-5-haiku-20241022",
            temperature=0.7,
            max_tokens=1000,
            api_key="test-api-key",
        )

        client = AnthropicClient(config)

        assert client.config == config
        assert client.get_model_name() == "claude-3-5-haiku-20241022"
        assert client._client is None  # Lazy initialization

    def test_invalid_provider_raises_error(self):
        """Test that invalid provider raises LLMProviderError."""
        # Since LLMProfileConfig validates the provider, we need to test the AnthropicClient's
        # own validation by creating a config with valid provider but then changing it
        config = LLMProfileConfig(
            provider="anthropic", model="claude-3-5-haiku-20241022", api_key="test-key"
        )

        # Manually change the provider to test AnthropicClient validation
        config.provider = "openai"

        with pytest.raises(
            LLMProviderError, match="Expected anthropic provider, got: openai"
        ):
            AnthropicClient(config)

    def test_missing_api_key_in_config_and_env_raises_error(self):
        """Test that missing API key raises LLMProviderError."""
        config = LLMProfileConfig(
            provider="anthropic",
            model="claude-3-5-haiku-20241022",
            api_key=None,  # No API key in config
        )

        # Ensure environment variable is not set
        with patch.dict(os.environ, {}, clear=True):
            with pytest.raises(LLMProviderError, match="API key not found"):
                AnthropicClient(config)

    def test_api_key_from_environment_variable(self):
        """Test that API key can be loaded from environment variable."""
        config = LLMProfileConfig(
            provider="anthropic",
            model="claude-3-5-haiku-20241022",
            api_key=None,  # No API key in config
        )

        with patch.dict(os.environ, {"ANTHROPIC_API_KEY": "env-api-key"}):
            client = AnthropicClient(config)
            # The _ensure_api_key method should have found the key
            assert client.config.api_key is None  # Config unchanged
            # But the client should be created successfully

    def test_config_api_key_takes_precedence_over_environment(self):
        """Test that config API key takes precedence over environment variable."""
        config = LLMProfileConfig(
            provider="anthropic",
            model="claude-3-5-haiku-20241022",
            api_key="config-api-key",
        )

        with patch.dict(os.environ, {"ANTHROPIC_API_KEY": "env-api-key"}):
            client = AnthropicClient(config)
            assert client.config.api_key == "config-api-key"


class TestAnthropicClientCreation:
    """Test the underlying ChatAnthropic client creation."""

    def test_client_lazy_initialization(self):
        """Test that the underlying client is created lazily."""
        config = LLMProfileConfig(
            provider="anthropic", model="claude-3-5-haiku-20241022", api_key="test-key"
        )

        client = AnthropicClient(config)
        assert client._client is None

        # Mock the ChatAnthropic creation
        with patch("src.llm.clients.anthropic.ChatAnthropic") as mock_chat_anthropic:
            mock_chat_instance = MagicMock()
            mock_chat_anthropic.return_value = mock_chat_instance

            # First call should initialize the client
            underlying_client = client._get_client()
            assert underlying_client is mock_chat_instance
            assert client._client is mock_chat_instance

            # Second call should return the same instance
            second_call = client._get_client()
            assert second_call is mock_chat_instance

            # ChatAnthropic should only be called once
            mock_chat_anthropic.assert_called_once_with(
                model="claude-3-5-haiku-20241022",
                temperature=0.0,  # Default temperature
                max_tokens=512,  # Default max_tokens (from config)
                api_key="test-key",
            )

    def test_client_initialization_with_custom_parameters(self):
        """Test client initialization with custom temperature and max_tokens."""
        config = LLMProfileConfig(
            provider="anthropic",
            model="claude-3-5-sonnet-20241022",
            temperature=0.8,
            max_tokens=2000,
            api_key="test-key",
        )

        client = AnthropicClient(config)

        with patch("src.llm.clients.anthropic.ChatAnthropic") as mock_chat_anthropic:
            mock_chat_instance = MagicMock()
            mock_chat_anthropic.return_value = mock_chat_instance

            client._get_client()

            mock_chat_anthropic.assert_called_once_with(
                model="claude-3-5-sonnet-20241022",
                temperature=0.8,
                max_tokens=2000,
                api_key="test-key",
            )

    def test_client_initialization_failure_raises_error(self):
        """Test that client initialization failure raises LLMProviderError."""
        config = LLMProfileConfig(
            provider="anthropic", model="claude-3-5-haiku-20241022", api_key="test-key"
        )

        client = AnthropicClient(config)

        with patch("src.llm.clients.anthropic.ChatAnthropic") as mock_chat_anthropic:
            mock_chat_anthropic.side_effect = Exception("Connection failed")

            with pytest.raises(
                LLMProviderError,
                match="Failed to initialize Anthropic client: Connection failed",
            ):
                client._get_client()

    def test_get_model_name(self):
        """Test get_model_name method returns correct model."""
        config = LLMProfileConfig(
            provider="anthropic", model="claude-3-5-haiku-20241022", api_key="test-key"
        )

        client = AnthropicClient(config)
        assert client.get_model_name() == "claude-3-5-haiku-20241022"


class TestAnthropicClientInvoke:
    """Test the invoke method of AnthropicClient."""

    def setup_method(self):
        """Set up test fixtures."""
        self.config = LLMProfileConfig(
            provider="anthropic", model="claude-3-5-haiku-20241022", api_key="test-key"
        )
        self.client = AnthropicClient(self.config)

    def test_successful_invoke_without_config(self):
        """Test successful invoke call without additional config."""
        messages = [{"role": "user", "content": "Hello"}]
        expected_response = MagicMock()
        expected_response.content = "Hello! How can I help you?"

        with patch("src.llm.clients.anthropic.ChatAnthropic") as mock_chat_anthropic:
            mock_chat_instance = MagicMock()
            mock_chat_instance.invoke.return_value = expected_response
            mock_chat_anthropic.return_value = mock_chat_instance

            with patch("time.time", side_effect=[1000.0, 1001.5]):  # Mock timing
                response = self.client.invoke(messages)

            assert response is expected_response
            mock_chat_instance.invoke.assert_called_once_with(messages)

    def test_successful_invoke_with_config(self):
        """Test successful invoke call with additional config."""
        messages = [{"role": "user", "content": "Hello"}]
        config = {"callbacks": ["callback1"]}
        expected_response = MagicMock()

        with patch("src.llm.clients.anthropic.ChatAnthropic") as mock_chat_anthropic:
            mock_chat_instance = MagicMock()
            mock_chat_instance.invoke.return_value = expected_response
            mock_chat_anthropic.return_value = mock_chat_instance

            with patch("time.time", side_effect=[1000.0, 1001.0]):
                response = self.client.invoke(messages, config)

            assert response is expected_response
            mock_chat_instance.invoke.assert_called_once_with(messages, config=config)

    def test_invoke_logs_successful_call(self):
        """Test that successful invoke calls are logged."""
        messages = [{"role": "user", "content": "Test message"}]
        expected_response = MagicMock()
        expected_response.__str__ = lambda: "Test response"

        with patch("src.llm.clients.anthropic.ChatAnthropic") as mock_chat_anthropic:
            mock_chat_instance = MagicMock()
            mock_chat_instance.invoke.return_value = expected_response
            mock_chat_anthropic.return_value = mock_chat_instance

            with patch("time.time", side_effect=[1000.0, 1001.5]):
                with patch.object(self.client, "_log_llm_call") as mock_log:
                    self.client.invoke(messages)

                    mock_log.assert_called_once_with(messages, expected_response, 1.5)

    def test_invoke_rate_limit_error(self):
        """Test handling of rate limit errors."""
        messages = [{"role": "user", "content": "Hello"}]

        with patch("src.llm.clients.anthropic.ChatAnthropic") as mock_chat_anthropic:
            mock_chat_instance = MagicMock()
            mock_chat_instance.invoke.side_effect = Exception("Rate limit exceeded")
            mock_chat_anthropic.return_value = mock_chat_instance

            with pytest.raises(LLMProviderError, match="Rate limit exceeded"):
                self.client.invoke(messages)

    def test_invoke_api_key_error(self):
        """Test handling of API key errors."""
        messages = [{"role": "user", "content": "Hello"}]

        with patch("src.llm.clients.anthropic.ChatAnthropic") as mock_chat_anthropic:
            mock_chat_instance = MagicMock()
            mock_chat_instance.invoke.side_effect = Exception("Invalid API key")
            mock_chat_anthropic.return_value = mock_chat_instance

            with pytest.raises(LLMProviderError, match="API key error"):
                self.client.invoke(messages)

    def test_invoke_generic_error(self):
        """Test handling of generic errors."""
        messages = [{"role": "user", "content": "Hello"}]

        with patch("src.llm.clients.anthropic.ChatAnthropic") as mock_chat_anthropic:
            mock_chat_instance = MagicMock()
            mock_chat_instance.invoke.side_effect = Exception("Network timeout")
            mock_chat_anthropic.return_value = mock_chat_instance

            with pytest.raises(LLMProviderError, match="Anthropic API error"):
                self.client.invoke(messages)

    def test_invoke_logs_errors(self):
        """Test that errors are logged during invoke."""
        messages = [{"role": "user", "content": "Hello"}]
        error = Exception("Test error")

        with patch("src.llm.clients.anthropic.ChatAnthropic") as mock_chat_anthropic:
            mock_chat_instance = MagicMock()
            mock_chat_instance.invoke.side_effect = error
            mock_chat_anthropic.return_value = mock_chat_instance

            with patch.object(self.client, "_log_error") as mock_log_error:
                with pytest.raises(LLMProviderError):
                    self.client.invoke(messages)

                mock_log_error.assert_called_once_with(error, messages)


class TestAnthropicClientErrorHandling:
    """Test error handling and edge cases."""

    def test_error_message_classification(self):
        """Test that different error messages are classified correctly."""
        config = LLMProfileConfig(
            provider="anthropic", model="claude-3-5-haiku-20241022", api_key="test-key"
        )
        client = AnthropicClient(config)

        error_cases = [
            ("Rate limit exceeded for requests", "Rate limit exceeded"),
            ("RATE LIMIT REACHED", "Rate limit exceeded"),
            ("Invalid API key provided", "API key error"),
            ("API KEY IS INVALID", "API key error"),
            ("Network connection failed", "Anthropic API error"),
            ("Timeout occurred", "Anthropic API error"),
        ]

        with patch("src.llm.clients.anthropic.ChatAnthropic") as mock_chat_anthropic:
            mock_chat_instance = MagicMock()
            mock_chat_anthropic.return_value = mock_chat_instance

            for error_message, expected_prefix in error_cases:
                mock_chat_instance.invoke.side_effect = Exception(error_message)

                with pytest.raises(LLMProviderError) as exc_info:
                    client.invoke([{"role": "user", "content": "test"}])

                assert expected_prefix in str(exc_info.value)

    def test_empty_messages_handling(self):
        """Test handling of empty messages list."""
        config = LLMProfileConfig(
            provider="anthropic", model="claude-3-5-haiku-20241022", api_key="test-key"
        )
        client = AnthropicClient(config)

        with patch("src.llm.clients.anthropic.ChatAnthropic") as mock_chat_anthropic:
            mock_chat_instance = MagicMock()
            mock_chat_instance.invoke.return_value = MagicMock()
            mock_chat_anthropic.return_value = mock_chat_instance

            # Should not raise an error, but pass empty list to underlying client
            client.invoke([])
            mock_chat_instance.invoke.assert_called_once_with([])

    def test_none_response_handling(self):
        """Test handling when underlying client returns None."""
        config = LLMProfileConfig(
            provider="anthropic", model="claude-3-5-haiku-20241022", api_key="test-key"
        )
        client = AnthropicClient(config)

        with patch("src.llm.clients.anthropic.ChatAnthropic") as mock_chat_anthropic:
            mock_chat_instance = MagicMock()
            mock_chat_instance.invoke.return_value = None
            mock_chat_anthropic.return_value = mock_chat_instance

            with patch("time.time", side_effect=[1000.0, 1001.0]):
                response = client.invoke([{"role": "user", "content": "test"}])

            assert response is None


class TestAnthropicClientLogging:
    """Test logging functionality."""

    def test_debug_logging_during_initialization(self):
        """Test that debug logging occurs during client initialization."""
        config = LLMProfileConfig(
            provider="anthropic", model="claude-3-5-haiku-20241022", api_key="test-key"
        )
        client = AnthropicClient(config)

        with patch("src.llm.clients.anthropic.ChatAnthropic") as mock_chat_anthropic:
            mock_chat_instance = MagicMock()
            mock_chat_anthropic.return_value = mock_chat_instance

            with patch.object(client.logger, "debug") as mock_debug:
                client._get_client()

                mock_debug.assert_called_once_with(
                    "Initialized Anthropic client with model: claude-3-5-haiku-20241022"
                )

    def test_logger_name_format(self):
        """Test that logger has correct name format."""
        config = LLMProfileConfig(
            provider="anthropic", model="claude-3-5-haiku-20241022", api_key="test-key"
        )
        client = AnthropicClient(config)

        # Logger name should be based on class name
        assert client.logger.name == "llm.anthropicclient"


class TestAnthropicClientIntegration:
    """Test integration scenarios and realistic usage patterns."""

    def test_multiple_invoke_calls_reuse_client(self):
        """Test that multiple invoke calls reuse the same underlying client."""
        config = LLMProfileConfig(
            provider="anthropic", model="claude-3-5-haiku-20241022", api_key="test-key"
        )
        client = AnthropicClient(config)

        with patch("src.llm.clients.anthropic.ChatAnthropic") as mock_chat_anthropic:
            mock_chat_instance = MagicMock()
            mock_chat_instance.invoke.return_value = MagicMock()
            mock_chat_anthropic.return_value = mock_chat_instance

            # Make multiple calls
            with patch("time.time", side_effect=[1000.0, 1001.0, 1002.0, 1003.0]):
                client.invoke([{"role": "user", "content": "First call"}])
                client.invoke([{"role": "user", "content": "Second call"}])

            # ChatAnthropic should only be instantiated once
            mock_chat_anthropic.assert_called_once()
            # But invoke should be called twice
            assert mock_chat_instance.invoke.call_count == 2

    def test_realistic_conversation_flow(self):
        """Test a realistic conversation flow with multiple messages."""
        config = LLMProfileConfig(
            provider="anthropic",
            model="claude-3-5-haiku-20241022",
            temperature=0.7,
            max_tokens=2000,
            api_key="test-key",
        )
        client = AnthropicClient(config)

        conversation = [
            {"role": "user", "content": "Hello, can you help me with Python?"},
            {
                "role": "assistant",
                "content": "Of course! I'd be happy to help you with Python.",
            },
            {"role": "user", "content": "How do I create a list comprehension?"},
        ]

        expected_response = MagicMock()
        expected_response.content = (
            "List comprehensions are created using [expression for item in iterable]"
        )

        with patch("src.llm.clients.anthropic.ChatAnthropic") as mock_chat_anthropic:
            mock_chat_instance = MagicMock()
            mock_chat_instance.invoke.return_value = expected_response
            mock_chat_anthropic.return_value = mock_chat_instance

            with patch("time.time", side_effect=[1000.0, 1002.5]):
                response = client.invoke(conversation)

            assert response is expected_response
            mock_chat_instance.invoke.assert_called_once_with(conversation)

            # Verify client was created with correct parameters
            mock_chat_anthropic.assert_called_once_with(
                model="claude-3-5-haiku-20241022",
                temperature=0.7,
                max_tokens=2000,
                api_key="test-key",
            )
