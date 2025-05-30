"""
OpenAI LLM provider configuration.
"""

import os
from enum import Enum
from typing import Optional

from pydantic import Field

from src.config.llm.base import BaseLLMConfig


class OpenAIModel(str, Enum):
    """Available OpenAI models."""

    GPT_4O = "gpt-4o"
    GPT_4O_MINI = "gpt-4o-mini"
    GPT_4_TURBO = "gpt-4-turbo"
    GPT_3_5_TURBO = "gpt-3.5-turbo"


class OpenAIConfig(BaseLLMConfig):
    """OpenAI-specific configuration."""

    model: OpenAIModel = OpenAIModel.GPT_4O_MINI
    api_key: Optional[str] = Field(default_factory=lambda: os.getenv("OPENAI_API_KEY"))
