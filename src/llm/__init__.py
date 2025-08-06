"""
LLM client modules for the Job Search Assistant application.

This module provides a unified interface for working with different LLM
providers through a factory pattern that supports multi-provider operations.
The factory pattern makes it easy to add new providers and maintains
compatibility with the singleton pattern used by individual clients.

Primary Interface:
    - LLMClientFactory: Main factory class for creating clients
    - get_llm_client(): Convenience function for creating clients from config
    - get_llm_client_by_profile_name(): Convenience function for creating clients by profile name
    - register_provider(): Register new providers dynamically
    - get_supported_providers(): Get list of available providers
"""

# Base class for implementing new providers
from src.llm.common.base import BaseLLMClient

# Factory pattern interface (primary and only interface)
from src.llm.common.factory import (
    LLMClientFactory,
    get_llm_client,
    get_llm_client_by_profile_name,
    get_supported_providers,
    register_provider,
)

# Observability
from src.llm.observability import langfuse_manager

# Public exports
__all__ = [
    # Factory pattern interface
    "LLMClientFactory",
    "get_llm_client",
    "get_llm_client_by_profile_name",
    "get_supported_providers",
    "register_provider",
    # Base class for new provider implementations
    "BaseLLMClient",
    # Observability
    "langfuse_manager",
]
