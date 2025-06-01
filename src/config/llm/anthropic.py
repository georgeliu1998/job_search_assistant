"""
Anthropic LLM provider configuration.
"""

import os
from enum import Enum
from typing import Optional

from pydantic import Field

from src.config.llm.base import BaseLLMConfig


class AnthropicModel(str, Enum):
    """Available Anthropic models."""

    CLAUDE_3_5_HAIKU_20241022 = "claude-3-5-haiku-20241022"
    CLAUDE_3_5_HAIKU_LATEST = "claude-3-5-haiku-latest"
    CLAUDE_3_HAIKU_20240307 = "claude-3-haiku-20240307"
    CLAUDE_SONNET_4_20250514 = "claude-sonnet-4-20250514"


class AnthropicConfig(BaseLLMConfig):
    """Anthropic-specific configuration."""

    model: AnthropicModel = AnthropicModel.CLAUDE_3_5_HAIKU_20241022
    api_key: Optional[str] = Field(
        default_factory=lambda: os.getenv("ANTHROPIC_API_KEY")
    )
