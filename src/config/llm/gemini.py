"""
Gemini LLM provider configuration.
"""

import os
from enum import Enum
from typing import Optional

from pydantic import Field

from src.config.llm.base import BaseLLMConfig


class GeminiModel(str, Enum):
    """Available Gemini models."""

    GEMINI_1_5_FLASH = "gemini-1.5-flash"
    GEMINI_1_5_FLASH_LATEST = "gemini-1.5-flash-latest"
    GEMINI_1_5_PRO = "gemini-1.5-pro"
    GEMINI_1_5_PRO_LATEST = "gemini-1.5-pro-latest"
    GEMINI_2_0_FLASH = "gemini-2.0-flash"
    GEMINI_2_5_FLASH_PREVIEW = "gemini-2.5-flash-preview-05-20"


class GeminiConfig(BaseLLMConfig):
    """Gemini-specific configuration."""

    model: GeminiModel = GeminiModel.GEMINI_2_0_FLASH
    api_key: Optional[str] = Field(default_factory=lambda: os.getenv("GEMINI_API_KEY"))
