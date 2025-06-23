"""
Exception classes for the Job Search Assistant application.

This module provides a hierarchy of custom exceptions for different components
of the application, enabling better error handling and debugging.
"""

from src.exceptions.base import JobSearchAssistantError
from src.exceptions.config import (
    ConfigError,
    ConfigFileError,
    ConfigValidationError,
    EnvironmentError,
)
from src.exceptions.llm import LLMError, LLMProviderError, LLMResponseError

__all__ = [
    # Base exceptions
    "JobSearchAssistantError",
    # Configuration exceptions
    "ConfigError",
    "ConfigFileError",
    "ConfigValidationError",
    "EnvironmentError",
    # LLM exceptions
    "LLMError",
    "LLMProviderError",
    "LLMResponseError",
]
