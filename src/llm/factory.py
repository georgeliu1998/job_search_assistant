"""
LLM model factory for multi-provider support.

Thin utility that returns configured LangChain BaseChatModel instances
directly, eliminating the need for a custom wrapper layer.
"""

import os

from langchain_core.language_models import BaseChatModel

from src.config.models import LLMConfig
from src.exceptions.llm import LLMProviderError
from src.utils.logging import get_logger

logger = get_logger(__name__)

_PROVIDER_CONSTRUCTORS = {
    "anthropic": "_create_anthropic_model",
    "google": "_create_google_model",
}

# Single source of truth for provider -> API key env var name, shared with
# src/llm/resilience.py so the two stay in sync as providers are added.
PROVIDER_ENV_VARS = {
    "anthropic": "ANTHROPIC_API_KEY",
    "google": "GOOGLE_API_KEY",
}


def _ensure_api_key(config: LLMConfig, env_var_name: str) -> str:
    """Get API key from config or environment, raising if missing."""
    api_key = getattr(config, "api_key", None)
    if not api_key:
        api_key = os.getenv(env_var_name)
    if not api_key:
        raise LLMProviderError(
            f"API key not found. Please set {env_var_name} in your "
            f"environment or .env file. "
            f"See README.md for setup instructions."
        )
    return api_key


def _create_anthropic_model(config: LLMConfig) -> BaseChatModel:
    from langchain_anthropic import ChatAnthropic

    api_key = _ensure_api_key(config, PROVIDER_ENV_VARS["anthropic"])
    return ChatAnthropic(
        model=config.model,
        temperature=config.temperature,
        max_tokens=config.max_tokens,
        api_key=api_key,
    )


def _create_google_model(config: LLMConfig) -> BaseChatModel:
    from langchain_google_genai import ChatGoogleGenerativeAI

    api_key = _ensure_api_key(config, PROVIDER_ENV_VARS["google"])
    return ChatGoogleGenerativeAI(
        model=config.model,
        temperature=config.temperature,
        max_tokens=config.max_tokens,
        google_api_key=api_key,
    )


def get_chat_model(config: LLMConfig) -> BaseChatModel:
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
            f"Unsupported LLM provider: '{provider}'. Available providers: {available}."
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
        raise LLMProviderError(f"Failed to create chat model for provider '{provider}': {e}") from e
