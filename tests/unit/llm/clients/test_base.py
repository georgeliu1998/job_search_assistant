"""Unit tests for LLM clients base module."""

import os
from unittest.mock import Mock, patch

import pytest

from src.config.models import LLMProfileConfig
from src.exceptions.llm import LLMProviderError
from src.llm.common.base import BaseLLMClient


class ConcreteLLMClient(BaseLLMClient):
    """Concrete implementation of BaseLLMClient for testing."""

    def __init__(self, config: LLMProfileConfig, fail_init: bool = False):
        super().__init__(config)
        self.fail_init = fail_init
        self.invoke_calls = []
        self.mock_client = Mock()

    def invoke(self, messages, config=None):
        """Mock implementation of invoke method."""
        self.invoke_calls.append({"messages": messages, "config": config})
        return f"Response for {len(messages)} messages"

    def get_model_name(self):
        """Mock implementation of get_model_name method."""
        return f"test-model-{self.config.model}"

    def _initialize_client(self):
        """Mock implementation of _initialize_client method."""
        if self.fail_init:
            raise Exception("Client initialization failed")
        return self.mock_client


class TestBaseLLMClient:
    """Test the BaseLLMClient abstract base class."""

    def test_cannot_instantiate_abstract_class(self):
        """Test that BaseLLMClient cannot be instantiated directly."""
        config = LLMProfileConfig(
            provider="anthropic", model="test-model", api_key="test-key"
        )

        with pytest.raises(TypeError, match="Can't instantiate abstract class"):
            BaseLLMClient(config)

    def test_concrete_client_initialization(self):
        """Test initialization of concrete client."""
        config = LLMProfileConfig(
            provider="anthropic", model="test-model", api_key="test-key"
        )

        client = ConcreteLLMClient(config)

        assert client.config == config
        assert client._client is None  # Lazy initialization
        assert client.logger.name == "llm.concretellmclient"

    def test_logger_name_format(self):
        """Test that logger name is formatted correctly."""
        config = LLMProfileConfig(
            provider="anthropic", model="test-model", api_key="test-key"
        )

        client = ConcreteLLMClient(config)

        # Should be lowercase class name
        assert client.logger.name == "llm.concretellmclient"

    def test_invoke_method_implementation(self):
        """Test that concrete invoke method works."""
        config = LLMProfileConfig(
            provider="anthropic", model="test-model", api_key="test-key"
        )

        client = ConcreteLLMClient(config)
        messages = [{"role": "user", "content": "Hello"}]

        result = client.invoke(messages)

        assert result == "Response for 1 messages"
        assert len(client.invoke_calls) == 1
        assert client.invoke_calls[0]["messages"] == messages
        assert client.invoke_calls[0]["config"] is None

    def test_invoke_method_with_config(self):
        """Test invoke method with config parameter."""
        config = LLMProfileConfig(
            provider="anthropic", model="test-model", api_key="test-key"
        )

        client = ConcreteLLMClient(config)
        messages = [{"role": "user", "content": "Hello"}]
        invoke_config = {"temperature": 0.7}

        result = client.invoke(messages, config=invoke_config)

        assert result == "Response for 1 messages"
        assert client.invoke_calls[0]["config"] == invoke_config

    def test_get_model_name_implementation(self):
        """Test that concrete get_model_name method works."""
        config = LLMProfileConfig(
            provider="anthropic", model="gpt-4", api_key="test-key"
        )

        client = ConcreteLLMClient(config)

        assert client.get_model_name() == "test-model-gpt-4"

    def test_get_client_lazy_initialization(self):
        """Test that _get_client performs lazy initialization."""
        config = LLMProfileConfig(
            provider="anthropic", model="test-model", api_key="test-key"
        )

        client = ConcreteLLMClient(config)

        # Initially no client
        assert client._client is None

        # First call should initialize
        result = client._get_client()
        assert result == client.mock_client
        assert client._client == client.mock_client

        # Second call should return cached client
        result2 = client._get_client()
        assert result2 == client.mock_client
        assert result2 is result

    def test_get_client_initialization_failure(self):
        """Test _get_client when initialization fails."""
        config = LLMProfileConfig(
            provider="anthropic", model="test-model", api_key="test-key"
        )

        client = ConcreteLLMClient(config, fail_init=True)

        # Should raise the exception from _initialize_client
        with pytest.raises(Exception, match="Client initialization failed"):
            client._get_client()

    def test_ensure_api_key_from_config(self):
        """Test _ensure_api_key when API key is in config."""
        config = LLMProfileConfig(
            provider="anthropic", model="test-model", api_key="config-api-key"
        )

        client = ConcreteLLMClient(config)

        api_key = client._ensure_api_key("TEST_API_KEY")
        assert api_key == "config-api-key"

    def test_ensure_api_key_from_environment(self):
        """Test _ensure_api_key when API key is in environment."""
        config = LLMProfileConfig(
            provider="anthropic", model="test-model"  # No API key in config
        )

        client = ConcreteLLMClient(config)

        with patch.dict(os.environ, {"TEST_API_KEY": "env-api-key"}):
            api_key = client._ensure_api_key("TEST_API_KEY")
            assert api_key == "env-api-key"

    def test_ensure_api_key_config_takes_precedence(self):
        """Test that config API key takes precedence over environment."""
        config = LLMProfileConfig(
            provider="anthropic", model="test-model", api_key="config-api-key"
        )

        client = ConcreteLLMClient(config)

        with patch.dict(os.environ, {"TEST_API_KEY": "env-api-key"}):
            api_key = client._ensure_api_key("TEST_API_KEY")
            assert api_key == "config-api-key"

    def test_ensure_api_key_missing_raises_error(self):
        """Test _ensure_api_key raises error when API key is missing."""
        config = LLMProfileConfig(
            provider="anthropic", model="test-model"  # No API key
        )

        client = ConcreteLLMClient(config)

        with patch.dict(os.environ, {}, clear=True):
            with pytest.raises(LLMProviderError, match="API key not found"):
                client._ensure_api_key("MISSING_API_KEY")

    def test_ensure_api_key_error_message_content(self):
        """Test that _ensure_api_key error message contains helpful information."""
        config = LLMProfileConfig(provider="anthropic", model="test-model")

        client = ConcreteLLMClient(config)

        with patch.dict(os.environ, {}, clear=True):
            with pytest.raises(LLMProviderError) as exc_info:
                client._ensure_api_key("MY_API_KEY")

            error_message = str(exc_info.value)
            assert "MY_API_KEY" in error_message
            assert "environment" in error_message
            assert "README.md" in error_message

    def test_log_llm_call(self):
        """Test _log_llm_call method."""
        config = LLMProfileConfig(
            provider="anthropic", model="test-model", api_key="test-key"
        )

        client = ConcreteLLMClient(config)

        messages = [{"role": "user", "content": "Hello world"}]
        response = "Hi there!"
        duration = 1.5

        with patch.object(client.logger, "info") as mock_info:
            client._log_llm_call(messages, response, duration)

            mock_info.assert_called_once()
            call_args = mock_info.call_args[0][0]

            assert "LLM call completed" in call_args
            assert "test-model-test-model" in call_args  # Model name
            assert "Input length:" in call_args
            assert "Response length:" in call_args
            assert "Duration: 1.50s" in call_args

    def test_log_llm_call_with_none_response(self):
        """Test _log_llm_call with None response."""
        config = LLMProfileConfig(
            provider="anthropic", model="test-model", api_key="test-key"
        )

        client = ConcreteLLMClient(config)

        messages = [{"role": "user", "content": "Hello"}]
        response = None
        duration = 0.5

        with patch.object(client.logger, "info") as mock_info:
            client._log_llm_call(messages, response, duration)

            mock_info.assert_called_once()
            call_args = mock_info.call_args[0][0]

            assert "Response length: 0" in call_args

    def test_log_llm_call_input_length_calculation(self):
        """Test that _log_llm_call correctly calculates input length."""
        config = LLMProfileConfig(
            provider="anthropic", model="test-model", api_key="test-key"
        )

        client = ConcreteLLMClient(config)

        messages = [
            {"role": "user", "content": "Hello"},  # 5 chars in content
            {"role": "assistant", "content": "Hi"},  # 2 chars in content
        ]

        with patch.object(client.logger, "info") as mock_info:
            client._log_llm_call(messages, "response", 1.0)

            call_args = mock_info.call_args[0][0]
            # Should include the string representation of the entire message objects
            assert "Input length:" in call_args

    def test_log_error(self):
        """Test _log_error method."""
        config = LLMProfileConfig(
            provider="anthropic", model="test-model", api_key="test-key"
        )

        client = ConcreteLLMClient(config)

        error = ValueError("Test error")
        messages = [{"role": "user", "content": "Hello"}]

        with patch.object(client.logger, "error") as mock_error:
            client._log_error(error, messages)

            mock_error.assert_called_once()
            call_args = mock_error.call_args[0][0]

            assert "LLM call failed" in call_args
            assert "test-model-test-model" in call_args
            assert "Error: Test error" in call_args
            assert "Context:" in call_args

            # Check that exc_info=True was passed
            assert mock_error.call_args[1]["exc_info"] is True

    def test_log_error_without_messages(self):
        """Test _log_error method without messages."""
        config = LLMProfileConfig(
            provider="anthropic", model="test-model", api_key="test-key"
        )

        client = ConcreteLLMClient(config)

        error = RuntimeError("Another error")

        with patch.object(client.logger, "error") as mock_error:
            client._log_error(error)

            mock_error.assert_called_once()
            call_args = mock_error.call_args[0][0]

            assert "LLM call failed" in call_args
            assert "Error: Another error" in call_args
            assert "Context: {}" in call_args

    def test_log_error_context_calculation(self):
        """Test that _log_error correctly calculates context information."""
        config = LLMProfileConfig(
            provider="anthropic", model="test-model", api_key="test-key"
        )

        client = ConcreteLLMClient(config)

        messages = [
            {"role": "user", "content": "Hello"},
            {"role": "assistant", "content": "Hi"},
        ]
        error = Exception("Test")

        with patch.object(client.logger, "error") as mock_error:
            client._log_error(error, messages)

            call_args = mock_error.call_args[0][0]

            assert "message_count': 2" in call_args
            assert "input_length'" in call_args


class TestBaseLLMClientAbstractMethods:
    """Test that abstract methods raise NotImplementedError."""

    def test_abstract_invoke_not_implemented(self):
        """Test that abstract invoke method raises NotImplementedError."""

        # Create a class that doesn't implement invoke properly
        class IncompleteClient(BaseLLMClient):
            def invoke(self, messages, config=None):
                # Call the parent's abstract method to trigger NotImplementedError
                return super().invoke(messages, config)

            def get_model_name(self):
                return "test"

            def _initialize_client(self):
                return Mock()

        config = LLMProfileConfig(
            provider="anthropic", model="test-model", api_key="test-key"
        )

        client = IncompleteClient(config)

        # Should raise NotImplementedError when calling the abstract method
        with pytest.raises(
            NotImplementedError, match="Subclasses must implement the 'invoke' method"
        ):
            client.invoke([])

    def test_abstract_get_model_name_not_implemented(self):
        """Test that abstract get_model_name method returns None when not implemented."""

        # Create a class that doesn't implement get_model_name properly
        class IncompleteClient(BaseLLMClient):
            def invoke(self, messages, config=None):
                return "response"

            def get_model_name(self):
                # Call the parent's abstract method which uses 'pass'
                return super().get_model_name()

            def _initialize_client(self):
                return Mock()

        config = LLMProfileConfig(
            provider="anthropic", model="test-model", api_key="test-key"
        )

        client = IncompleteClient(config)

        # get_model_name should return None (from 'pass' in base class)
        result = client.get_model_name()
        assert result is None

    def test_abstract_initialize_client_not_implemented(self):
        """Test that abstract _initialize_client method raises NotImplementedError."""

        # Create a class that doesn't implement _initialize_client properly
        class IncompleteClient(BaseLLMClient):
            def invoke(self, messages, config=None):
                return "response"

            def get_model_name(self):
                return "test"

            def _initialize_client(self):
                # Call the parent's abstract method to trigger NotImplementedError
                return super()._initialize_client()

        config = LLMProfileConfig(
            provider="anthropic", model="test-model", api_key="test-key"
        )

        client = IncompleteClient(config)

        # _get_client should raise NotImplementedError when calling _initialize_client
        with pytest.raises(
            NotImplementedError,
            match="Subclasses must implement the '_initialize_client' method",
        ):
            client._get_client()


class TestBaseLLMClientEdgeCases:
    """Test edge cases and error conditions."""

    def test_config_without_api_key_attribute(self):
        """Test handling of config without api_key attribute."""

        # Create a minimal config-like object
        class MinimalConfig:
            provider = "test"
            model = "test-model"
            # No api_key attribute

        config = MinimalConfig()
        client = ConcreteLLMClient(config)

        # Should handle missing api_key gracefully
        with patch.dict(os.environ, {"TEST_KEY": "env-key"}):
            api_key = client._ensure_api_key("TEST_KEY")
            assert api_key == "env-key"

    def test_empty_messages_logging(self):
        """Test logging with empty messages list."""
        config = LLMProfileConfig(
            provider="anthropic", model="test-model", api_key="test-key"
        )

        client = ConcreteLLMClient(config)

        with patch.object(client.logger, "info") as mock_info:
            client._log_llm_call([], "response", 1.0)

            call_args = mock_info.call_args[0][0]
            assert "Input length: 0" in call_args

    def test_very_long_messages_logging(self):
        """Test logging with very long messages."""
        config = LLMProfileConfig(
            provider="anthropic", model="test-model", api_key="test-key"
        )

        client = ConcreteLLMClient(config)

        # Create a very long message
        long_content = "x" * 10000
        messages = [{"role": "user", "content": long_content}]

        with patch.object(client.logger, "info") as mock_info:
            client._log_llm_call(messages, "response", 1.0)

            call_args = mock_info.call_args[0][0]
            # Should handle long messages without issues
            assert "Input length:" in call_args

    def test_client_reinitialization_after_failure(self):
        """Test that client can be reinitialized after failure."""
        config = LLMProfileConfig(
            provider="anthropic", model="test-model", api_key="test-key"
        )

        client = ConcreteLLMClient(config, fail_init=True)

        # First call should fail
        with pytest.raises(Exception, match="Client initialization failed"):
            client._get_client()

        # Client should still be None
        assert client._client is None

        # Fix the initialization and try again
        client.fail_init = False
        result = client._get_client()
        assert result == client.mock_client

    def test_multiple_error_logging_calls(self):
        """Test multiple calls to _log_error."""
        config = LLMProfileConfig(
            provider="anthropic", model="test-model", api_key="test-key"
        )

        client = ConcreteLLMClient(config)

        with patch.object(client.logger, "error") as mock_error:
            # Log multiple errors
            client._log_error(ValueError("Error 1"))
            client._log_error(RuntimeError("Error 2"))

            assert mock_error.call_count == 2
