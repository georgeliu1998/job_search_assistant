"""
LLM-specific exception classes for the Job Search Assistant application.

This module provides comprehensive exception classes for handling LLM-related errors
with proper error categorization, context, and recovery guidance.
"""

from src.exceptions.base import JobSearchAssistantError


class LLMError(JobSearchAssistantError):
    """
    Base exception class for all LLM-related errors.

    This serves as the parent class for more specific LLM error types.
    """

    pass


class LLMProviderError(LLMError):
    """
    Exception raised for errors in LLM provider communication.

    This includes API key issues, rate limiting, network errors,
    and other provider-specific problems.
    """

    def __init__(
        self,
        message: str,
        provider: str = None,
        error_code: str = None,
        details: dict = None,
    ):
        """
        Initialize the provider error.

        Args:
            message: Human-readable error message
            provider: Name of the LLM provider (e.g., 'anthropic', 'gemini')
            error_code: Provider-specific error code
            details: Additional error context
        """
        # Enhance details with provider information
        enhanced_details = details or {}
        if provider:
            enhanced_details["provider"] = provider
        if error_code:
            enhanced_details["error_code"] = error_code

        super().__init__(message, enhanced_details)
        self.provider = provider
        self.error_code = error_code

    def __str__(self) -> str:
        """Return enhanced string representation."""
        base_message = self.message
        if self.provider:
            base_message = f"[{self.provider}] {base_message}"
        if self.error_code:
            base_message = f"{base_message} (Code: {self.error_code})"
        if self.details:
            base_message = f"{base_message} (Details: {self.details})"
        return base_message


class LLMResponseError(LLMError):
    """
    Exception raised for errors in LLM response processing.

    This includes malformed responses, unexpected formats,
    and response validation failures.
    """

    def __init__(self, message: str, response_data: str = None, details: dict = None):
        """
        Initialize the response error.

        Args:
            message: Human-readable error message
            response_data: The raw response data that caused the error
            details: Additional error context
        """
        # Enhance details with response information
        enhanced_details = details or {}
        if response_data:
            # Truncate long response data for readability
            truncated_data = (
                response_data[:100] + "..."
                if len(response_data) > 100
                else response_data
            )
            enhanced_details["response_data"] = truncated_data

        super().__init__(message, enhanced_details)
        self.response_data = response_data

    def __str__(self) -> str:
        """Return enhanced string representation."""
        base_message = self.message
        if self.response_data:
            truncated_data = (
                self.response_data[:100] + "..."
                if len(self.response_data) > 100
                else self.response_data
            )
            base_message = f"{base_message} (Response: {truncated_data})"
        if self.details:
            base_message = f"{base_message} (Details: {self.details})"
        return base_message


class LLMConfigurationError(LLMError):
    """
    Exception raised for LLM configuration issues.

    This includes invalid models, malformed configurations,
    and missing required settings.
    """

    def __init__(self, message: str, config_key: str = None, details: dict = None):
        """
        Initialize the configuration error.

        Args:
            message: Human-readable error message
            config_key: The configuration key that caused the issue
            details: Additional error context
        """
        # Enhance details with configuration information
        enhanced_details = details or {}
        if config_key:
            enhanced_details["config_key"] = config_key

        super().__init__(message, enhanced_details)
        self.config_key = config_key

    def __str__(self) -> str:
        """Return enhanced string representation."""
        base_message = self.message
        if self.config_key:
            base_message = f"{base_message} (Config key: {self.config_key})"
        if self.details:
            base_message = f"{base_message} (Details: {self.details})"
        return base_message


class LLMObservabilityError(LLMError):
    """
    Exception raised for observability system errors.

    This includes tracing failures, metrics collection issues,
    and monitoring system problems.
    """

    pass
