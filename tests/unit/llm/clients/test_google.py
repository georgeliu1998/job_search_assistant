"""
Unit tests for the Google LLM client.

Tests the GoogleClient class including initialization, configuration validation,
API key handling, client creation, invoke method, and error handling.
"""

import os
import time
from unittest.mock import MagicMock, Mock, patch

import pytest

from src.config.models import LLMProfileConfig
from src.exceptions.llm import LLMProviderError, LLMResponseError
from src.llm.clients.google import GoogleClient


class TestGoogleClientInitialization:
    """Test GoogleClient initialization and configuration validation."""

    def test_successful_initialization_with_valid_config(self):
        """Test successful client initialization with valid google provider configuration."""
        config = LLMProfileConfig(
            provider="google",
            model="gemini-2.5-pro",
            temperature=0.7,
            max_tokens=1000,
            api_key="test-api-key",
        )

        client = GoogleClient(config)

        assert client.config == config
        assert client.get_model_name() == "gemini-2.5-pro"
        assert client._client is None  # Lazy initialization

    def test_successful_initialization_with_different_model(self):
        """Test successful client initialization with different Gemini model."""
        config = LLMProfileConfig(
            provider="google",
            model="gemini-2.5-flash",
            temperature=0.2,
            max_tokens=512,
            api_key="test-api-key",
        )

        client = GoogleClient(config)

        assert client.config == config
        assert client.get_model_name() == "gemini-2.5-flash"
        assert client._client is None  # Lazy initialization

    def test_invalid_provider_raises_error(self):
        """Test that invalid provider raises LLMProviderError."""
        # Since LLMProfileConfig validates the provider, we need to test the GoogleClient's
        # own validation by creating a config with valid provider but then changing it
        config = LLMProfileConfig(
            provider="google", model="gemini-2.5-pro", api_key="test-key"
        )

        # Manually change the provider to test GoogleClient validation
        config.provider = "openai"

        with pytest.raises(
            LLMProviderError, match="Expected google provider, got: openai"
        ):
            GoogleClient(config)

    @patch.dict(os.environ, {}, clear=True)
    @patch.dict(
        os.environ, {"APP_ENV": "stage"}
    )  # Use stage environment to skip validation
    def test_missing_api_key_raises_error(self):
        """Test that missing API key raises LLMProviderError."""
        config = LLMProfileConfig(
            provider="google", model="gemini-2.5-pro", api_key=None
        )

        with pytest.raises(LLMProviderError, match="API key not found.*GOOGLE_API_KEY"):
            GoogleClient(config)

    @patch.dict(os.environ, {"GOOGLE_API_KEY": "env-api-key"})
    def test_api_key_from_environment(self):
        """Test that API key can be loaded from environment."""
        config = LLMProfileConfig(
            provider="google", model="gemini-2.5-pro", api_key=None
        )

        # Should not raise an error because API key is available in environment
        client = GoogleClient(config)
        assert client.config == config


class TestGoogleClientCreation:
    """Test the underlying ChatGoogleGenerativeAI client creation."""

    def test_client_lazy_initialization(self):
        """Test that the underlying client is created lazily."""
        config = LLMProfileConfig(
            provider="google", model="gemini-2.5-pro", api_key="test-key"
        )

        client = GoogleClient(config)
        assert client._client is None

        # Mock the ChatGoogleGenerativeAI creation
        with patch("src.llm.clients.google.ChatGoogleGenerativeAI") as mock_chat_google:
            mock_chat_instance = MagicMock()
            mock_chat_google.return_value = mock_chat_instance

            # First call should initialize the client
            underlying_client = client._get_client()
            assert underlying_client is mock_chat_instance
            assert client._client is mock_chat_instance

            # Second call should return the same instance
            second_call = client._get_client()
            assert second_call is mock_chat_instance

            # ChatGoogleGenerativeAI should only be called once
            mock_chat_google.assert_called_once_with(
                model="gemini-2.5-pro",
                temperature=0.0,  # Default temperature
                max_tokens=512,  # Default max_tokens (from config)
                google_api_key="test-key",
            )

    def test_client_initialization_with_custom_config(self):
        """Test client initialization with custom configuration parameters."""
        config = LLMProfileConfig(
            provider="google",
            model="gemini-2.5-flash",
            temperature=0.8,
            max_tokens=2048,
            api_key="custom-key",
        )

        client = GoogleClient(config)

        with patch("src.llm.clients.google.ChatGoogleGenerativeAI") as mock_chat_google:
            mock_chat_instance = MagicMock()
            mock_chat_google.return_value = mock_chat_instance

            client._get_client()

            mock_chat_google.assert_called_once_with(
                model="gemini-2.5-flash",
                temperature=0.8,
                max_tokens=2048,
                google_api_key="custom-key",
            )

    def test_client_initialization_failure(self):
        """Test handling of client initialization failure."""
        config = LLMProfileConfig(
            provider="google", model="gemini-2.5-pro", api_key="test-key"
        )

        client = GoogleClient(config)

        with patch("src.llm.clients.google.ChatGoogleGenerativeAI") as mock_chat_google:
            mock_chat_google.side_effect = Exception("Initialization failed")

            with pytest.raises(
                LLMProviderError, match="Failed to initialize Google client"
            ):
                client._get_client()


class TestGoogleClientSingleton:
    """Test the singleton behavior of GoogleClient."""

    def setUp(self):
        """Clear singleton cache before each test."""
        # Clear singleton cache if it exists
        if hasattr(GoogleClient, "_instances"):
            GoogleClient._instances.clear()

    def test_singleton_same_config_returns_same_instance(self):
        """Test that same configuration returns the same client instance."""
        config = LLMProfileConfig(
            provider="google",
            model="gemini-2.5-pro",
            temperature=0.5,
            max_tokens=1024,
            api_key="test-key",
        )

        client1 = GoogleClient(config)
        client2 = GoogleClient(config)

        assert client1 is client2

    def test_singleton_different_config_returns_different_instances(self):
        """Test that different configurations return different client instances."""
        config1 = LLMProfileConfig(
            provider="google", model="gemini-2.5-pro", api_key="key1"
        )
        config2 = LLMProfileConfig(
            provider="google", model="gemini-2.5-flash", api_key="key2"
        )

        client1 = GoogleClient(config1)
        client2 = GoogleClient(config2)

        assert client1 is not client2
        assert client1.config != client2.config

    def test_config_hashability(self):
        """Test that LLMProfileConfig is properly hashable for singleton pattern."""
        config1 = LLMProfileConfig(
            provider="google", model="gemini-2.5-pro", api_key="key1"
        )
        config2 = LLMProfileConfig(
            provider="google", model="gemini-2.5-pro", api_key="key1"
        )

        # Same configs should be equal and have same hash
        assert config1 == config2
        assert hash(config1) == hash(config2)

        # Different configs should not be equal
        config3 = LLMProfileConfig(
            provider="google", model="gemini-2.5-flash", api_key="key1"
        )
        assert config1 != config3
        assert hash(config1) != hash(config3)

    def test_multiple_clients_with_same_config(self):
        """Test creating multiple clients with identical config returns same instance."""
        config = LLMProfileConfig(
            provider="google", model="gemini-2.5-pro", api_key="test-key"
        )

        clients = [GoogleClient(config) for _ in range(5)]

        # All should be the same instance
        for client in clients[1:]:
            assert client is clients[0]


class TestGoogleClientInvoke:
    """Test the invoke method functionality."""

    def setup_method(self):
        """Set up test fixtures."""
        self.config = LLMProfileConfig(
            provider="google", model="gemini-2.5-pro", api_key="test-key"
        )
        self.client = GoogleClient(self.config)

    def test_invoke_successful_call(self):
        """Test successful invoke call."""
        messages = [{"role": "user", "content": "Hello, world!"}]
        expected_response = MagicMock()
        expected_response.content = "Hello! How can I help you today?"

        with patch.object(self.client, "_get_client") as mock_get_client:
            mock_underlying_client = MagicMock()
            mock_underlying_client.invoke.return_value = expected_response
            mock_get_client.return_value = mock_underlying_client

            with patch.object(self.client, "_log_llm_call") as mock_log:
                result = self.client.invoke(messages)

                assert result == expected_response
                mock_underlying_client.invoke.assert_called_once_with(messages)
                mock_log.assert_called_once()

    def test_invoke_with_config(self):
        """Test invoke call with additional configuration."""
        messages = [{"role": "user", "content": "Hello"}]
        config = {"temperature": 0.5}
        expected_response = MagicMock()

        with patch.object(self.client, "_get_client") as mock_get_client:
            mock_underlying_client = MagicMock()
            mock_underlying_client.invoke.return_value = expected_response
            mock_get_client.return_value = mock_underlying_client

            result = self.client.invoke(messages, config=config)

            assert result == expected_response
            mock_underlying_client.invoke.assert_called_once_with(
                messages, config=config
            )

    def test_invoke_rate_limit_error(self):
        """Test handling of rate limit errors."""
        messages = [{"role": "user", "content": "Hello"}]

        with patch.object(self.client, "_get_client") as mock_get_client:
            mock_underlying_client = MagicMock()
            mock_underlying_client.invoke.side_effect = Exception("Rate limit exceeded")
            mock_get_client.return_value = mock_underlying_client

            with pytest.raises(LLMProviderError, match="Rate limit or quota exceeded"):
                self.client.invoke(messages)

    def test_invoke_api_key_error(self):
        """Test handling of API key errors."""
        messages = [{"role": "user", "content": "Hello"}]

        with patch.object(self.client, "_get_client") as mock_get_client:
            mock_underlying_client = MagicMock()
            mock_underlying_client.invoke.side_effect = Exception("API key invalid")
            mock_get_client.return_value = mock_underlying_client

            with pytest.raises(LLMProviderError, match="API key error"):
                self.client.invoke(messages)

    def test_invoke_model_not_found_error(self):
        """Test handling of model not found errors."""
        messages = [{"role": "user", "content": "Hello"}]

        with patch.object(self.client, "_get_client") as mock_get_client:
            mock_underlying_client = MagicMock()
            mock_underlying_client.invoke.side_effect = Exception("Model not found")
            mock_get_client.return_value = mock_underlying_client

            with pytest.raises(LLMProviderError, match="Model not available"):
                self.client.invoke(messages)

    def test_invoke_safety_filter_error(self):
        """Test handling of safety filter errors."""
        messages = [{"role": "user", "content": "Harmful content"}]

        with patch.object(self.client, "_get_client") as mock_get_client:
            mock_underlying_client = MagicMock()
            mock_underlying_client.invoke.side_effect = Exception(
                "Safety filter blocked"
            )
            mock_get_client.return_value = mock_underlying_client

            with pytest.raises(
                LLMProviderError, match="Content blocked by safety filters"
            ):
                self.client.invoke(messages)

    def test_invoke_generic_error(self):
        """Test handling of generic errors."""
        messages = [{"role": "user", "content": "Hello"}]

        with patch.object(self.client, "_get_client") as mock_get_client:
            mock_underlying_client = MagicMock()
            mock_underlying_client.invoke.side_effect = Exception("Unknown error")
            mock_get_client.return_value = mock_underlying_client

            with pytest.raises(LLMProviderError, match="Google API error"):
                self.client.invoke(messages)

    def test_invoke_logs_call_duration(self):
        """Test that invoke method logs call duration."""
        messages = [{"role": "user", "content": "Hello"}]
        expected_response = MagicMock()

        with patch.object(self.client, "_get_client") as mock_get_client:
            mock_underlying_client = MagicMock()
            mock_underlying_client.invoke.return_value = expected_response
            mock_get_client.return_value = mock_underlying_client

            with patch.object(self.client, "_log_llm_call") as mock_log:
                with patch(
                    "time.time", side_effect=[100.0, 102.5]
                ):  # 2.5 second duration
                    self.client.invoke(messages)

                # Should log with correct duration
                mock_log.assert_called_once_with(messages, expected_response, 2.5)

    def test_invoke_logs_errors(self):
        """Test that invoke method logs errors."""
        messages = [{"role": "user", "content": "Hello"}]
        error = Exception("Test error")

        with patch.object(self.client, "_get_client") as mock_get_client:
            mock_underlying_client = MagicMock()
            mock_underlying_client.invoke.side_effect = error
            mock_get_client.return_value = mock_underlying_client

            with patch.object(self.client, "_log_error") as mock_log_error:
                with pytest.raises(LLMProviderError):
                    self.client.invoke(messages)

                mock_log_error.assert_called_once_with(error, messages)


class TestGoogleClientLogging:
    """Test logging functionality."""

    def test_logger_name_correct(self):
        """Test that logger has correct name."""
        config = LLMProfileConfig(
            provider="google", model="gemini-2.5-pro", api_key="test-key"
        )
        client = GoogleClient(config)

        assert client.logger.name == "llm.googleclient"

    def test_debug_logging_on_client_initialization(self):
        """Test debug logging when client is initialized."""
        config = LLMProfileConfig(
            provider="google", model="gemini-2.5-flash", api_key="test-key"
        )
        client = GoogleClient(config)

        with patch("src.llm.clients.google.ChatGoogleGenerativeAI"):
            with patch.object(client.logger, "debug") as mock_debug:
                client._get_client()

                mock_debug.assert_called_once_with(
                    "Initialized Google client with model: gemini-2.5-flash"
                )
