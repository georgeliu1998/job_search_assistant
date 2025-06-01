"""
LLM-specific exception classes for the Job Search Assistant application.
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
    Exception raised when there are issues with the LLM provider.

    This includes issues like:
    - Missing or invalid API keys
    - Network connectivity problems
    - Authentication failures
    - Service unavailability
    """

    pass


class LLMResponseError(LLMError):
    """
    Exception raised when there are issues with LLM responses.

    This includes issues like:
    - Malformed responses that can't be parsed
    - Unexpected response format
    - Empty or invalid responses
    """

    pass
