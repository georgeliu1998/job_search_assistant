"""
LLM model factory for multi-provider support.

Thin utility that returns configured LangChain BaseChatModel instances
directly, eliminating the need for a custom wrapper layer.
"""

import os
from typing import Any

from langchain_core.language_models import BaseChatModel

from src.config.models import LLMProfileConfig
from src.exceptions.llm import LLMProviderError
from src.utils.logging import get_logger

logger = get_logger(__name__)

_PROVIDER_CONSTRUCTORS = {
    "anthropic": "_create_anthropic_model",
    "google": "_create_google_model",
}


def _ensure_api_key(config: LLMProfileConfig, env_var_name: str) -> str:
    """Get API key from config or environment, raising if missing."""
    api_key = getattr(config, "api_key", None)
    if not api_key:
        api_key = os.getenv(env_var_name)
    if not api_key:
        raise LLMProviderError(
            f"API key not found. Please set {env_var_name} in your environment or .env file. "
            f"See README.md for setup instructions."
        )
    return api_key


def _create_anthropic_model(config: LLMProfileConfig) -> BaseChatModel:
    from langchain_anthropic import ChatAnthropic

    api_key = _ensure_api_key(config, "ANTHROPIC_API_KEY")
    return ChatAnthropic(
        model=config.model,
        temperature=config.temperature,
        max_tokens=config.max_tokens,
        api_key=api_key,
    )


def _create_google_model(config: LLMProfileConfig) -> BaseChatModel:
    from langchain_google_genai import ChatGoogleGenerativeAI

    api_key = _ensure_api_key(config, "GOOGLE_API_KEY")
    return ChatGoogleGenerativeAI(
        model=config.model,
        temperature=config.temperature,
        max_tokens=config.max_tokens,
        google_api_key=api_key,
    )


def get_chat_model(config: LLMProfileConfig) -> BaseChatModel:
    """
    Create a configured LangChain chat model for the given profile.

    Args:
        config: LLM profile configuration containing provider and model info

    Returns:
        A LangChain BaseChatModel instance ready for use

    Raises:
        LLMProviderError: If the provider is not supported or creation fails
    """
    provider = config.provider.lower()
    constructor_name = _PROVIDER_CONSTRUCTORS.get(provider)

    if constructor_name is None:
        available = ", ".join(sorted(_PROVIDER_CONSTRUCTORS.keys()))
        raise LLMProviderError(
            f"Unsupported LLM provider: '{provider}'. "
            f"Available providers: {available}."
        )

    try:
        constructor = globals()[constructor_name]
        model = constructor(config)
        logger.debug(f"Created {provider} chat model: {config.model}")
        return model
    except LLMProviderError:
        raise
    except ImportError as e:
        raise LLMProviderError(
            f"Failed to import dependencies for provider '{provider}': {e}. "
            f"Make sure the required packages are installed."
        ) from e
    except Exception as e:
        raise LLMProviderError(
            f"Failed to create chat model for provider '{provider}': {e}"
        ) from e


def get_chat_model_by_profile_name(profile_name: str) -> BaseChatModel:
    """
    Create a LangChain chat model by configuration profile name.

    Args:
        profile_name: Name of the LLM profile in the configuration

    Returns:
        A LangChain BaseChatModel instance
    """
    from src.config import config

    profile = config.get_llm_profile(profile_name)
    return get_chat_model(profile)
