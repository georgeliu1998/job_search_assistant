"""
Fireworks LLM provider configuration.
"""

import os
from enum import Enum
from typing import Optional

from pydantic import Field

from src.config.llm.base import BaseLLMConfig


class FireworksModel(str, Enum):
    """Available Fireworks models for NLU & extraction tasks."""

    # Low-latency NLU & extraction models (recommended)
    LLAMA_3_1_8B = "accounts/fireworks/models/llama-v3p1-8b-instruct"
    LLAMA_3_2_3B = "accounts/fireworks/models/llama-v3p2-3b-instruct"
    LLAMA_3_2_1B = "accounts/fireworks/models/llama-v3p2-1b-instruct"
    QWEN_2_5_7B = "accounts/fireworks/models/qwen2p5-7b-instruct"
    QWEN_2_5_3B = "accounts/fireworks/models/qwen2p5-3b-instruct"
    QWEN_2_5_0_5B = "accounts/fireworks/models/qwen2p5-0p5b-instruct"


class FireworksConfig(BaseLLMConfig):
    """Fireworks-specific configuration."""

    model: FireworksModel = FireworksModel.LLAMA_3_1_8B
    api_key: Optional[str] = Field(
        default_factory=lambda: os.getenv("FIREWORKS_API_KEY")
    )
    # Optimized settings for structured tasks
    temperature: float = Field(default=0.1, ge=0.0, le=1.0)
    max_tokens: int = Field(default=1024, gt=0)
