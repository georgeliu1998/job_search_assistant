"""
Base classes and enums for LLM provider configurations.
"""

from enum import Enum

from pydantic import BaseModel, Field


class LLMProvider(str, Enum):
    """Supported LLM providers."""

    ANTHROPIC = "anthropic"
    OPENAI = "openai"
    FIREWORKS = "fireworks"


class BaseLLMConfig(BaseModel):
    """Base configuration for all LLM providers."""

    temperature: float = Field(default=0.0, ge=0.0, le=1.0)
    max_tokens: int = Field(default=512, gt=0)
