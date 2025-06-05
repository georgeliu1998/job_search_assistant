"""
LLM provider configurations with type safety and validation.

Supports Anthropic and Fireworks providers with model-specific
settings.
"""

from typing import Optional

from pydantic import BaseModel, Field

from src.config.llm.anthropic import AnthropicConfig, AnthropicModel
from src.config.llm.base import BaseLLMConfig, LLMProvider
from src.config.llm.fireworks import FireworksConfig, FireworksModel


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


# Convenience functions
def get_default_config() -> BaseLLMConfig:
    """Get configuration for the default provider."""
    return llm_config.get_provider_config()


def get_anthropic_config() -> AnthropicConfig:
    """Get Anthropic configuration."""
    return llm_config.anthropic


def get_fireworks_config() -> FireworksConfig:
    """Get Fireworks configuration."""
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
