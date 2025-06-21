"""
LLM provider configurations with type safety and validation.

DEPRECATED: This module is deprecated. Use src.config.settings instead.
This module now acts as a compatibility layer.

Supports Anthropic and Fireworks providers with model-specific
settings.
"""

import warnings
from typing import Optional

from pydantic import BaseModel, Field

from src.config.llm.anthropic import AnthropicConfig, AnthropicModel
from src.config.llm.base import BaseLLMConfig, LLMProvider
from src.config.llm.fireworks import FireworksConfig, FireworksModel


def _deprecation_warning():
    """Issue deprecation warning for this module."""
    warnings.warn(
        "src.config.llm is deprecated. Use 'from src.config.settings import settings' "
        "and access LLM profiles via settings.llm_profiles instead.",
        DeprecationWarning,
        stacklevel=3
    )


class LLMConfig(BaseModel):
    """Main LLM configuration managing all providers."""

    # Default provider
    default_provider: LLMProvider = LLMProvider.ANTHROPIC

    # Provider configurations
    anthropic: AnthropicConfig = Field(default_factory=AnthropicConfig)
    fireworks: FireworksConfig = Field(default_factory=FireworksConfig)

    def get_provider_config(
        self, provider: Optional[LLMProvider] = None
    ) -> BaseLLMConfig:
        """Get configuration for specified provider or default."""
        provider = provider or self.default_provider

        if provider == LLMProvider.ANTHROPIC:
            return self.anthropic
        elif provider == LLMProvider.FIREWORKS:
            return self.fireworks


# Global configuration instance
llm_config = LLMConfig()


# Convenience functions with deprecation warnings
def get_default_config() -> BaseLLMConfig:
    """Get configuration for the default provider."""
    _deprecation_warning()
    return llm_config.get_provider_config()


def get_anthropic_config() -> AnthropicConfig:
    """Get Anthropic configuration."""
    _deprecation_warning()
    
    # Try to use new settings system, fall back to legacy if not available
    try:
        from src.config.settings import settings
        # Get the default anthropic profile from new settings
        profile = settings.llm_profiles.get("anthropic_default")
        if profile and profile.provider == "anthropic":
            # Convert new format to legacy format
            legacy_config = AnthropicConfig()
            legacy_config.model = AnthropicModel(profile.model)
            legacy_config.temperature = profile.temperature
            legacy_config.max_tokens = profile.max_tokens
            if profile.api_key:
                legacy_config.api_key = profile.api_key
            return legacy_config
    except (ImportError, Exception):
        # Fall back to legacy configuration
        pass
    
    return llm_config.anthropic


def get_fireworks_config() -> FireworksConfig:
    """Get Fireworks configuration."""
    _deprecation_warning()
    
    # Try to use new settings system, fall back to legacy if not available
    try:
        from src.config.settings import settings
        # Get the fireworks profile from new settings
        profile = settings.llm_profiles.get("fireworks_fast")
        if profile and profile.provider == "fireworks":
            # Convert new format to legacy format
            legacy_config = FireworksConfig()
            legacy_config.model = FireworksModel(profile.model)
            legacy_config.temperature = profile.temperature
            legacy_config.max_tokens = profile.max_tokens
            if profile.api_key:
                legacy_config.api_key = profile.api_key
            return legacy_config
    except (ImportError, Exception):
        # Fall back to legacy configuration
        pass
    
    return llm_config.fireworks


# Export all public classes and functions
__all__ = [
    # Main classes
    "LLMConfig",
    "LLMProvider",
    "BaseLLMConfig",
    # Provider configs
    "AnthropicConfig",
    "FireworksConfig",
    # Model enums
    "AnthropicModel",
    "FireworksModel",
    # Convenience functions
    "get_default_config",
    "get_anthropic_config",
    "get_fireworks_config",
    # Global instance
    "llm_config",
]
