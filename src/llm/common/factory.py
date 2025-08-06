"""
LLM client factory for multi-provider support.

This module provides a factory pattern implementation that creates LLM clients
for different providers while maintaining compatibility with the singleton pattern.
The factory supports dynamic provider registration and provides clear error
messages for unsupported providers.
"""

import importlib
from typing import Dict, List, Type

from src.config.models import LLMProfileConfig
from src.exceptions.llm import LLMProviderError
from src.llm.common.base import BaseLLMClient
from src.utils.logging import get_logger


class LLMClientFactory:
    """
    Factory for creating LLM clients with multi-provider support.

    This factory implements the factory pattern to create appropriate LLM client
    instances based on provider configuration. It supports dynamic provider
    registration and works seamlessly with the singleton pattern used by
    individual client implementations.

    The factory uses lazy loading to avoid import-time dependencies on provider
    packages that may not be installed.

    Example:
        factory = LLMClientFactory()
        client = factory.create_client(config)

        # Or register a new provider
        factory.register_provider("openai", "src.llm.clients.openai.OpenAIClient")
    """

    # Default provider mappings - can be extended via register_provider
    _DEFAULT_PROVIDERS: Dict[str, str] = {
        "anthropic": "src.llm.clients.anthropic.AnthropicClient",
        "google": "src.llm.clients.google.GoogleClient",
    }

    def __init__(self):
        """Initialize the factory with default provider mappings."""
        self.logger = get_logger(__name__)
        # Copy default providers to allow instance-specific modifications
        self._providers: Dict[str, str] = self._DEFAULT_PROVIDERS.copy()

    def create_client(self, config: LLMProfileConfig) -> BaseLLMClient:
        """
        Create an LLM client for the given configuration.

        This method creates the appropriate client instance based on the provider
        specified in the configuration. The actual client instances are managed
        by the singleton pattern implemented in each client class.

        Args:
            config: LLM profile configuration containing provider and model info

        Returns:
            BaseLLMClient: An instance of the appropriate client implementation

        Raises:
            LLMProviderError: If the provider is not supported or client creation fails

        Example:
            config = LLMProfileConfig(provider="anthropic", model="claude-3-5-haiku-20241022")
            client = factory.create_client(config)
        """
        provider = config.provider.lower()

        if provider not in self._providers:
            available = ", ".join(sorted(self._providers.keys()))
            raise LLMProviderError(
                f"Unsupported LLM provider: '{provider}'. "
                f"Available providers: {available}. "
                f"Use register_provider() to add new providers."
            )

        try:
            client_class = self._load_client_class(provider)
            self.logger.debug(f"Creating client for provider: {provider}")
            return client_class(config)

        except ImportError as e:
            raise LLMProviderError(
                f"Failed to import client for provider '{provider}': {e}. "
                f"Make sure the required dependencies are installed."
            ) from e
        except Exception as e:
            raise LLMProviderError(
                f"Failed to create client for provider '{provider}': {e}"
            ) from e

    def register_provider(self, provider_name: str, client_class_path: str) -> None:
        """
        Register a new LLM provider with the factory.

        This allows the factory to be extended with new providers without
        modifying the core factory code. The client class will be loaded
        lazily when first requested.

        Args:
            provider_name: Name of the provider (e.g., "openai", "cohere")
            client_class_path: Full import path to the client class
                              (e.g., "src.llm.clients.openai.OpenAIClient")

        Example:
            factory.register_provider("openai", "src.llm.clients.openai.OpenAIClient")
            factory.register_provider("cohere", "src.llm.clients.cohere.CohereClient")
        """
        provider_name = provider_name.lower()
        self._providers[provider_name] = client_class_path
        self.logger.info(f"Registered provider: {provider_name} -> {client_class_path}")

    def get_supported_providers(self) -> List[str]:
        """
        Get a list of all supported provider names.

        Returns:
            List[str]: List of supported provider names in alphabetical order
        """
        return sorted(self._providers.keys())

    def is_provider_supported(self, provider_name: str) -> bool:
        """
        Check if a provider is supported by this factory.

        Args:
            provider_name: Name of the provider to check

        Returns:
            bool: True if the provider is supported, False otherwise
        """
        return provider_name.lower() in self._providers

    def _load_client_class(self, provider: str) -> Type[BaseLLMClient]:
        """
        Load the client class for the given provider.

        This method uses dynamic import to load the client class only when needed,
        avoiding import-time dependencies on optional packages.

        Args:
            provider: Provider name (must be registered)

        Returns:
            Type[BaseLLMClient]: The client class for the provider

        Raises:
            ImportError: If the module or class cannot be imported
            AttributeError: If the class doesn't exist in the module
        """
        client_class_path = self._providers[provider]

        try:
            # Split module path and class name
            module_path, class_name = client_class_path.rsplit(".", 1)

            # Dynamic import
            module = importlib.import_module(module_path)
            client_class = getattr(module, class_name)

            # Verify it's a BaseLLMClient subclass
            if not issubclass(client_class, BaseLLMClient):
                raise LLMProviderError(
                    f"Client class {client_class_path} must inherit from BaseLLMClient"
                )

            return client_class

        except (ImportError, AttributeError) as e:
            self.logger.error(f"Failed to load client class {client_class_path}: {e}")
            raise


# Global factory instance for convenience
_global_factory = LLMClientFactory()


def get_llm_client(config: LLMProfileConfig) -> BaseLLMClient:
    """
    Convenience function to create an LLM client using the global factory.

    This function provides a simple interface for creating LLM clients without
    needing to instantiate a factory. It uses a global factory instance.

    Args:
        config: LLM profile configuration

    Returns:
        BaseLLMClient: An instance of the appropriate client implementation

    Example:
        config = LLMProfileConfig(provider="anthropic", model="claude-3-5-haiku-20241022")
        client = get_llm_client(config)
    """
    return _global_factory.create_client(config)


def get_llm_client_by_profile_name(profile_name: str) -> BaseLLMClient:
    """
    Convenience function to create an LLM client by profile name.

    This function loads the profile configuration and creates the appropriate
    client instance. It requires the global config to be available.

    Args:
        profile_name: Name of the LLM profile in the configuration

    Returns:
        BaseLLMClient: An instance of the appropriate client implementation

    Example:
        client = get_llm_client_by_profile_name("anthropic_extraction")
    """
    from src.config import config

    profile = config.get_llm_profile(profile_name)
    return get_llm_client(profile)


def register_provider(provider_name: str, client_class_path: str) -> None:
    """
    Register a new provider with the global factory.

    This convenience function allows registering new providers without
    accessing the global factory directly.

    Args:
        provider_name: Name of the provider
        client_class_path: Full import path to the client class

    Example:
        register_provider("openai", "src.llm.clients.openai.OpenAIClient")
    """
    _global_factory.register_provider(provider_name, client_class_path)


def get_supported_providers() -> List[str]:
    """
    Get a list of all supported provider names from the global factory.

    Returns:
        List[str]: List of supported provider names in alphabetical order
    """
    return _global_factory.get_supported_providers()
