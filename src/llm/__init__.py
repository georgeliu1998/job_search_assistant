"""
LLM client modules for the Job Search Assistant application.

This module provides a unified interface for working with different LLM
providers through enhanced base classes, factory patterns, and integrated
observability.

Phase 1 Refactor Complete:
- Enhanced base class with automatic observability and metrics
- Multi-provider factory with singleton management
- Class-based observability handlers
- Comprehensive metrics collection
- Ready for Gemini integration
"""

from src.exceptions.llm import (
    LLMConfigurationError,
    LLMObservabilityError,
    LLMProviderError,
    LLMResponseError,
)

# Provider clients
from src.llm.clients.anthropic import AnthropicClient
from src.llm.common.base import BaseLLMClient

# New enhanced infrastructure
from src.llm.common.factory import (
    LLMClientFactory,
    get_available_providers,
    get_llm_client,
)

# Observability (new class-based system)
from src.llm.observability.langfuse import (
    LangfuseHandler,
    get_langfuse_handler,
    is_langfuse_enabled,
    reset_langfuse_handler,
)
from src.llm.observability.metrics import MetricsCollector

# Note: GeminiClient available but not yet implemented


# Clean public API
def get_llm_client(profile_name: str) -> BaseLLMClient:
    """
    Get LLM client for the specified profile.

    This is the primary interface for getting LLM clients. It uses the
    factory pattern with singleton management for optimal performance.

    Args:
        profile_name: Name of the LLM profile from configuration

    Returns:
        BaseLLMClient instance (singleton per profile)
    """
    factory = LLMClientFactory()
    return factory.get_client(profile_name)


__all__ = [
    # Primary interfaces
    "get_llm_client",
    "LLMClientFactory",
    "BaseLLMClient",
    # Provider clients
    "AnthropicClient",
    # Observability
    "LangfuseHandler",
    "get_langfuse_handler",
    "is_langfuse_enabled",
    "reset_langfuse_handler",
    "MetricsCollector",
    # Exceptions
    "LLMProviderError",
    "LLMResponseError",
    "LLMConfigurationError",
    "LLMObservabilityError",
    # Utilities
    "get_available_providers",
]
