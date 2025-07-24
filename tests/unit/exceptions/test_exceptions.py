"""
Unit tests for exception classes.

Tests all custom exception classes including base exceptions,
configuration exceptions, and LLM exceptions.
"""

import pytest

from src.exceptions.base import JobSearchAssistantError
from src.exceptions.config import (
    ConfigError,
    ConfigFileError,
    ConfigValidationError,
    EnvironmentError,
)
from src.exceptions.llm import (
    LLMConfigurationError,
    LLMError,
    LLMObservabilityError,
    LLMProviderError,
    LLMResponseError,
)


class TestJobSearchAssistantError:
    """Test the base JobSearchAssistantError class."""

    def test_basic_exception_creation(self):
        """Test creating exception with just a message."""
        message = "Something went wrong"
        error = JobSearchAssistantError(message)

        assert str(error) == message
        assert error.message == message
        assert error.details == {}
        assert isinstance(error, Exception)

    def test_exception_with_details(self):
        """Test creating exception with details dictionary."""
        message = "Configuration error"
        details = {"file": "config.toml", "line": 42}
        error = JobSearchAssistantError(message, details)

        assert error.message == message
        assert error.details == details
        assert str(error) == f"{message} (Details: {details})"

    def test_exception_with_empty_details(self):
        """Test that empty details dictionary doesn't affect string representation."""
        message = "Error message"
        error = JobSearchAssistantError(message, {})

        assert str(error) == message
        assert error.details == {}

    def test_exception_with_none_details(self):
        """Test that None details are converted to empty dictionary."""
        message = "Error message"
        error = JobSearchAssistantError(message, None)

        assert str(error) == message
        assert error.details == {}

    def test_exception_inheritance(self):
        """Test that JobSearchAssistantError properly inherits from Exception."""
        error = JobSearchAssistantError("test")

        assert isinstance(error, Exception)
        assert isinstance(error, JobSearchAssistantError)

    def test_exception_can_be_raised_and_caught(self):
        """Test that exception can be raised and caught properly."""
        message = "Test error"
        details = {"context": "unit test"}

        with pytest.raises(JobSearchAssistantError) as exc_info:
            raise JobSearchAssistantError(message, details)

        caught_error = exc_info.value
        assert caught_error.message == message
        assert caught_error.details == details
        assert str(caught_error) == f"{message} (Details: {details})"


class TestConfigError:
    """Test the ConfigError class and its subclasses."""

    def test_config_error_basic_creation(self):
        """Test creating ConfigError with just a message."""
        message = "Configuration failed"
        error = ConfigError(message)

        assert str(error) == message
        assert error.message == message
        assert error.config_path is None
        assert isinstance(error, JobSearchAssistantError)
        assert isinstance(error, ConfigError)

    def test_config_error_with_path(self):
        """Test creating ConfigError with config path."""
        message = "File not found"
        config_path = "/path/to/config.toml"
        error = ConfigError(message, config_path)

        assert error.message == message
        assert error.config_path == config_path
        assert str(error) == message  # Path doesn't affect string representation

    def test_config_error_with_details_and_path(self):
        """Test ConfigError with both details and config path."""
        message = "Parse error"
        config_path = "/path/to/config.toml"
        details = {"line": 10, "column": 5}

        # ConfigError inherits from JobSearchAssistantError, so it should support details
        error = ConfigError(message, config_path)
        error.details = details  # Set details manually since ConfigError doesn't take it in __init__

        assert error.message == message
        assert error.config_path == config_path
        assert error.details == details

    def test_config_error_inheritance_chain(self):
        """Test the inheritance chain for ConfigError."""
        error = ConfigError("test")

        assert isinstance(error, Exception)
        assert isinstance(error, JobSearchAssistantError)
        assert isinstance(error, ConfigError)

    def test_config_file_error(self):
        """Test ConfigFileError subclass."""
        message = "File operation failed"
        config_path = "/path/to/file.toml"
        error = ConfigFileError(message, config_path)

        assert error.message == message
        assert error.config_path == config_path
        assert isinstance(error, ConfigError)
        assert isinstance(error, ConfigFileError)
        assert isinstance(error, JobSearchAssistantError)

    def test_config_validation_error(self):
        """Test ConfigValidationError subclass."""
        message = "Validation failed"
        error = ConfigValidationError(message)

        assert error.message == message
        assert isinstance(error, ConfigError)
        assert isinstance(error, ConfigValidationError)
        assert isinstance(error, JobSearchAssistantError)

    def test_environment_error(self):
        """Test EnvironmentError subclass."""
        message = "Environment variable missing"
        error = EnvironmentError(message)

        assert error.message == message
        assert isinstance(error, ConfigError)
        assert isinstance(error, EnvironmentError)
        assert isinstance(error, JobSearchAssistantError)

    def test_config_error_subclasses_can_be_caught_as_config_error(self):
        """Test that config error subclasses can be caught as ConfigError."""
        # Test ConfigFileError
        with pytest.raises(ConfigError):
            raise ConfigFileError("file error")

        # Test ConfigValidationError
        with pytest.raises(ConfigError):
            raise ConfigValidationError("validation error")

        # Test EnvironmentError
        with pytest.raises(ConfigError):
            raise EnvironmentError("env error")

    def test_config_error_subclasses_can_be_caught_as_base_error(self):
        """Test that config error subclasses can be caught as JobSearchAssistantError."""
        # Test ConfigError itself
        with pytest.raises(JobSearchAssistantError):
            raise ConfigError("config error")

        # Test ConfigFileError
        with pytest.raises(JobSearchAssistantError):
            raise ConfigFileError("file error")

        # Test ConfigValidationError
        with pytest.raises(JobSearchAssistantError):
            raise ConfigValidationError("validation error")

        # Test EnvironmentError
        with pytest.raises(JobSearchAssistantError):
            raise EnvironmentError("env error")


class TestLLMError:
    """Test the LLMError class and its subclasses."""

    def test_llm_error_basic_creation(self):
        """Test creating LLMError with basic parameters."""
        message = "LLM operation failed"
        error = LLMError(message)

        assert str(error) == message
        assert error.message == message
        assert isinstance(error, JobSearchAssistantError)
        assert isinstance(error, LLMError)

    def test_llm_error_with_details(self):
        """Test LLMError with details dictionary."""
        message = "API call failed"
        details = {"status_code": 429, "retry_after": 60}
        error = LLMError(message, details)

        assert error.message == message
        assert error.details == details
        assert str(error) == f"{message} (Details: {details})"

    def test_llm_error_inheritance_chain(self):
        """Test the inheritance chain for LLMError."""
        error = LLMError("test")

        assert isinstance(error, Exception)
        assert isinstance(error, JobSearchAssistantError)
        assert isinstance(error, LLMError)

    def test_llm_provider_error(self):
        """Test LLMProviderError subclass."""
        message = "API key invalid"
        provider = "anthropic"
        error_code = "AUTH_001"
        details = {"key_length": 0}
        error = LLMProviderError(
            message, provider=provider, error_code=error_code, details=details
        )

        assert error.message == message
        assert error.provider == provider
        assert error.error_code == error_code
        # Enhanced details should include original details plus provider and error_code
        expected_details = {
            "key_length": 0,
            "provider": provider,
            "error_code": error_code,
        }
        assert error.details == expected_details
        assert isinstance(error, LLMError)
        assert isinstance(error, LLMProviderError)
        assert isinstance(error, JobSearchAssistantError)

    def test_llm_response_error(self):
        """Test LLMResponseError subclass."""
        message = "Response parsing failed"
        response_data = "invalid json here"
        details = {"expected_format": "json"}
        error = LLMResponseError(message, response_data=response_data, details=details)

        assert error.message == message
        assert error.response_data == response_data
        # Enhanced details should include original details plus response_data
        expected_details = {"expected_format": "json", "response_data": response_data}
        assert error.details == expected_details
        assert isinstance(error, LLMError)
        assert isinstance(error, LLMResponseError)
        assert isinstance(error, JobSearchAssistantError)

    def test_llm_configuration_error(self):
        """Test LLMConfigurationError subclass."""
        message = "Invalid configuration"
        config_key = "temperature"
        error = LLMConfigurationError(message, config_key=config_key)

        assert error.message == message
        assert error.config_key == config_key
        assert error.details == {"config_key": config_key}
        assert isinstance(error, LLMError)
        assert isinstance(error, LLMConfigurationError)
        assert isinstance(error, JobSearchAssistantError)

    def test_llm_observability_error(self):
        """Test LLMObservabilityError subclass."""
        message = "Observability system failure"
        details = {"system": "langfuse", "error_type": "connection"}
        error = LLMObservabilityError(message, details)

        assert error.message == message
        assert error.details == details
        assert isinstance(error, LLMError)
        assert isinstance(error, LLMObservabilityError)
        assert isinstance(error, JobSearchAssistantError)

    def test_llm_error_subclasses_can_be_caught_as_llm_error(self):
        """Test that LLM error subclasses can be caught as LLMError."""
        # Test LLMProviderError
        with pytest.raises(LLMError):
            raise LLMProviderError("provider error")

        # Test LLMResponseError
        with pytest.raises(LLMError):
            raise LLMResponseError("response error")

        # Test LLMConfigurationError
        with pytest.raises(LLMError):
            raise LLMConfigurationError("config error")

        # Test LLMObservabilityError
        with pytest.raises(LLMError):
            raise LLMObservabilityError("observability error")

    def test_llm_error_subclasses_can_be_caught_as_base_error(self):
        """Test that LLM error subclasses can be caught as JobSearchAssistantError."""
        # Test LLMError itself
        with pytest.raises(JobSearchAssistantError):
            raise LLMError("llm error")

        # Test LLMProviderError
        with pytest.raises(JobSearchAssistantError):
            raise LLMProviderError("provider error")

        # Test LLMResponseError
        with pytest.raises(JobSearchAssistantError):
            raise LLMResponseError("response error")

        # Test LLMConfigurationError
        with pytest.raises(JobSearchAssistantError):
            raise LLMConfigurationError("config error")

        # Test LLMObservabilityError
        with pytest.raises(JobSearchAssistantError):
            raise LLMObservabilityError("observability error")


class TestExceptionInteroperability:
    """Test how different exception types work together."""

    def test_catching_all_custom_exceptions_as_base(self):
        """Test that all custom exceptions can be caught as JobSearchAssistantError."""
        exceptions_to_test = [
            JobSearchAssistantError("base error"),
            ConfigError("config error"),
            ConfigFileError("file error"),
            ConfigValidationError("validation error"),
            EnvironmentError("env error"),
            LLMError("llm error"),
            LLMProviderError("provider error"),
            LLMResponseError("response error"),
            LLMConfigurationError("config error"),
            LLMObservabilityError("observability error"),
        ]

        for exception in exceptions_to_test:
            with pytest.raises(JobSearchAssistantError):
                raise exception

    def test_exception_type_identification(self):
        """Test that we can identify specific exception types."""
        try:
            raise LLMProviderError("API key missing")
        except JobSearchAssistantError as e:
            assert isinstance(e, LLMProviderError)
            assert isinstance(e, LLMError)
            assert isinstance(e, JobSearchAssistantError)
            assert not isinstance(e, ConfigError)

    def test_multiple_exception_handling(self):
        """Test handling multiple exception types in a try/except block."""

        def raise_config_error():
            raise ConfigFileError("Config file not found")

        def raise_llm_error():
            raise LLMProviderError("API error")

        # Test catching specific types
        with pytest.raises(ConfigError):
            raise_config_error()

        with pytest.raises(LLMError):
            raise_llm_error()

        # Test catching as base type
        with pytest.raises(JobSearchAssistantError):
            raise_config_error()

        with pytest.raises(JobSearchAssistantError):
            raise_llm_error()

    def test_exception_details_preservation(self):
        """Test that exception details are preserved through inheritance."""
        original_details = {"error_code": "E001", "timestamp": "2024-01-01T00:00:00Z"}

        # Create specific exception with details
        specific_error = LLMProviderError("Specific error", details=original_details)

        # Catch as base type and verify details are preserved (enhanced behavior includes original details)
        try:
            raise specific_error
        except JobSearchAssistantError as caught_error:
            # The enhanced exception includes the original details
            assert all(key in caught_error.details for key in original_details.keys())
            assert caught_error.details["error_code"] == original_details["error_code"]
            assert caught_error.details["timestamp"] == original_details["timestamp"]
            assert caught_error.message == "Specific error"
            assert isinstance(caught_error, LLMProviderError)


class TestExceptionStringRepresentations:
    """Test string representations of exceptions."""

    def test_simple_message_representation(self):
        """Test string representation with simple messages."""
        exceptions = [
            JobSearchAssistantError("Base error"),
            ConfigError("Config error"),
            LLMError("LLM error"),
            LLMProviderError("Provider error"),
        ]

        for exception in exceptions:
            assert str(exception) == exception.message
            assert exception.details == {}

    def test_detailed_message_representation(self):
        """Test string representation with details."""
        details = {"key": "value", "number": 42}
        exceptions = [
            JobSearchAssistantError("Base error", details),
            LLMError("LLM error", details),
            LLMProviderError("Provider error", details=details),
        ]

        expected_str = f"Base error (Details: {details})"
        assert str(exceptions[0]) == expected_str

        expected_str = f"LLM error (Details: {details})"
        assert str(exceptions[1]) == expected_str

        # LLMProviderError with just details (no provider or error_code)
        expected_str = f"Provider error (Details: {details})"
        assert str(exceptions[2]) == expected_str

    def test_config_error_with_path_representation(self):
        """Test that ConfigError path doesn't affect string representation."""
        error = ConfigError("Config failed", "/path/to/config")
        assert str(error) == "Config failed"
        assert error.config_path == "/path/to/config"

        # Add details and test combined representation
        error.details = {"line": 10}
        assert str(error) == "Config failed (Details: {'line': 10})"
