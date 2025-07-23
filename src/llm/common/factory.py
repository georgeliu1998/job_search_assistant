"""
Multi-provider LLM client factory with singleton management.

This module provides a factory pattern for creating LLM clients with proper
singleton management and support for multiple providers.
"""

import importlib
from threading import Lock
from typing import Dict, List, Type

from src.config import config
from src.exceptions.llm import LLMConfigurationError, LLMProviderError
from src.llm.common.base import BaseLLMClient
from src.utils.logging import get_logger
from src.utils.singleton import singleton

logger = get_logger(__name__)


@singleton
class LLMClientFactory:
    """
    Thread-safe factory for creating LLM clients with proper singleton management.

    This factory supports multiple LLM providers and ensures that clients are
    created as singletons based on their configuration. Different configurations
    will create different singleton instances.
    """

    # Provider mapping - easily extensible for new providers
    _PROVIDER_MAP = {
        "anthropic": {
            "module": "src.llm.clients.anthropic",
            "class": "AnthropicClient",
            "description": "Anthropic Claude models",
        },
        "gemini": {
            "module": "src.llm.clients.gemini",
            "class": "GeminiClient",
            "description": "Google Gemini models (future implementation)",
        },
    }

    def __init__(self):
        """Initialize the factory with thread safety."""
        self._lock = Lock()
        self._loaded_classes: Dict[str, Type[BaseLLMClient]] = {}
        logger.debug("Initialized LLMClientFactory")

    def get_client(self, profile_name: str) -> BaseLLMClient:
        """
        Get LLM client for the specified profile.

        This method creates or retrieves a singleton client instance based on
        the profile configuration. The same profile will always return the
        same client instance.

        Args:
            profile_name: Name of the LLM profile from configuration

        Returns:
            BaseLLMClient instance (singleton per profile)

        Raises:
            LLMConfigurationError: If profile is not found or invalid
            LLMProviderError: If provider is not supported or client creation fails
        """
        try:
            # Get profile configuration
            profile = config.get_llm_profile(profile_name)
            if not profile:
                raise LLMConfigurationError(
                    f"LLM profile '{profile_name}' not found in configuration",
                    config_key=f"llm_profiles.{profile_name}",
                )

            # Validate provider
            if profile.provider not in self._PROVIDER_MAP:
                available = ", ".join(self._PROVIDER_MAP.keys())
                raise LLMProviderError(
                    f"Unsupported LLM provider: {profile.provider}. "
                    f"Available providers: {available}",
                    provider=profile.provider,
                )

            # Get the client class (with caching and thread safety)
            client_class = self._get_client_class(profile.provider)

            # Create and return client instance (singleton behavior handled by @singleton decorator)
            logger.debug(
                f"Creating client for profile '{profile_name}' with provider '{profile.provider}'"
            )
            return client_class(profile)

        except (LLMConfigurationError, LLMProviderError):
            # Re-raise our own exceptions
            raise
        except Exception as e:
            logger.error(
                f"Unexpected error creating client for profile '{profile_name}': {e}"
            )
            raise LLMProviderError(
                f"Failed to create LLM client for profile '{profile_name}': {e}"
            )

    def _get_client_class(self, provider: str) -> Type[BaseLLMClient]:
        """
        Get the client class for a provider with caching and thread safety.

        Args:
            provider: The provider name (e.g., 'anthropic', 'gemini')

        Returns:
            The client class

        Raises:
            LLMProviderError: If the provider is not supported or class cannot be loaded
        """
        # Check cache first (thread-safe read)
        if provider in self._loaded_classes:
            return self._loaded_classes[provider]

        # Use lock for write operations
        with self._lock:
            # Double-check pattern - another thread might have loaded it
            if provider in self._loaded_classes:
                return self._loaded_classes[provider]

            # Load the class
            provider_info = self._PROVIDER_MAP[provider]
            try:
                logger.debug(f"Loading client class for provider: {provider}")

                # Dynamic import to avoid circular dependencies
                module = importlib.import_module(provider_info["module"])
                client_class = getattr(module, provider_info["class"])

                # Validate that it's a proper BaseLLMClient subclass
                if not issubclass(client_class, BaseLLMClient):
                    raise LLMProviderError(
                        f"Client class {provider_info['class']} is not a subclass of BaseLLMClient",
                        provider=provider,
                    )

                # Cache the loaded class
                self._loaded_classes[provider] = client_class
                logger.debug(
                    f"Successfully loaded and cached client class for provider: {provider}"
                )

                return client_class

            except ImportError as e:
                logger.error(f"Failed to import module for provider {provider}: {e}")
                raise LLMProviderError(
                    f"Provider '{provider}' is not available. Module import failed: {e}",
                    provider=provider,
                )
            except AttributeError as e:
                logger.error(f"Client class not found for provider {provider}: {e}")
                raise LLMProviderError(
                    f"Client class '{provider_info['class']}' not found in module '{provider_info['module']}'",
                    provider=provider,
                )
            except Exception as e:
                logger.error(
                    f"Unexpected error loading client class for provider {provider}: {e}"
                )
                raise LLMProviderError(
                    f"Failed to load client class for provider '{provider}': {e}",
                    provider=provider,
                )

    def get_available_providers(self) -> List[Dict[str, str]]:
        """
        Get list of available LLM providers with descriptions.

        Returns:
            List of dictionaries containing provider information
        """
        return [
            {
                "name": provider,
                "description": info["description"],
                "available": self._is_provider_available(provider),
            }
            for provider, info in self._PROVIDER_MAP.items()
        ]

    def _is_provider_available(self, provider: str) -> bool:
        """
        Check if a provider is actually available (can be imported).

        Args:
            provider: The provider name

        Returns:
            True if provider can be imported, False otherwise
        """
        try:
            provider_info = self._PROVIDER_MAP[provider]
            importlib.import_module(provider_info["module"])
            return True
        except ImportError:
            return False
        except Exception:
            return False

    def get_provider_names(self) -> List[str]:
        """
        Get list of provider names.

        Returns:
            List of provider name strings
        """
        return list(self._PROVIDER_MAP.keys())

    def is_provider_supported(self, provider: str) -> bool:
        """
        Check if a provider is supported by the factory.

        Args:
            provider: The provider name to check

        Returns:
            True if provider is supported, False otherwise
        """
        return provider in self._PROVIDER_MAP

    def get_client_for_provider(self, provider: str, **kwargs) -> BaseLLMClient:
        """
        Get a client directly by provider name with custom configuration.

        This is a convenience method for advanced use cases where you want to
        create a client with specific parameters rather than using profiles.

        Args:
            provider: The provider name (e.g., 'anthropic', 'gemini')
            **kwargs: Configuration parameters for the client

        Returns:
            BaseLLMClient instance

        Raises:
            LLMProviderError: If provider is not supported
            LLMConfigurationError: If configuration is invalid
        """
        if not self.is_provider_supported(provider):
            available = ", ".join(self.get_provider_names())
            raise LLMProviderError(
                f"Unsupported LLM provider: {provider}. "
                f"Available providers: {available}",
                provider=provider,
            )

        # Create a mock profile configuration for direct provider access
        from src.config.models import LLMProfileConfig

        try:
            # Use defaults and override with provided kwargs
            profile_config = LLMProfileConfig(
                provider=provider,
                model=kwargs.get("model", "default"),
                temperature=kwargs.get("temperature", 0.7),
                max_tokens=kwargs.get("max_tokens", 1024),
                api_key=kwargs.get("api_key"),
                **{
                    k: v
                    for k, v in kwargs.items()
                    if k not in ["model", "temperature", "max_tokens", "api_key"]
                },
            )

            client_class = self._get_client_class(provider)
            return client_class(profile_config)

        except Exception as e:
            raise LLMConfigurationError(
                f"Failed to create client configuration for provider '{provider}': {e}"
            )

    def clear_cache(self) -> None:
        """
        Clear the loaded classes cache.

        This is primarily useful for testing or when you need to reload
        client classes after code changes.
        """
        with self._lock:
            self._loaded_classes.clear()
            logger.debug("Cleared client class cache")

    def get_factory_info(self) -> Dict[str, any]:
        """
        Get information about the factory state.

        Returns:
            Dictionary containing factory state information
        """
        return {
            "supported_providers": list(self._PROVIDER_MAP.keys()),
            "loaded_classes": list(self._loaded_classes.keys()),
            "available_providers": [
                p["name"] for p in self.get_available_providers() if p["available"]
            ],
        }


# Convenience functions for backward compatibility
def get_llm_client(profile_name: str) -> BaseLLMClient:
    """
    Get LLM client for the specified profile.

    This is a convenience function that uses the singleton factory.

    Args:
        profile_name: Name of the LLM profile from configuration

    Returns:
        BaseLLMClient instance
    """
    factory = LLMClientFactory()
    return factory.get_client(profile_name)


def get_available_providers() -> List[Dict[str, str]]:
    """
    Get list of available LLM providers.

    Returns:
        List of dictionaries containing provider information
    """
    factory = LLMClientFactory()
    return factory.get_available_providers()


def is_provider_supported(provider: str) -> bool:
    """
    Check if a provider is supported.

    Args:
        provider: The provider name to check

    Returns:
        True if provider is supported, False otherwise
    """
    factory = LLMClientFactory()
    return factory.is_provider_supported(provider)
