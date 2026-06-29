"""
LLM client modules for the Job Search Assistant application.

Provides get_chat_model() to create configured LangChain BaseChatModel
instances for different providers.
"""

from src.llm.factory import get_chat_model
from src.llm.langfuse import GlobalLangfuseManager, LangfuseManager, langfuse_manager
from src.llm.resilience import (
    TransientLLMError,
    build_resilient_llm,
    is_transient_error,
)

__all__ = [
    "get_chat_model",
    "LangfuseManager",
    "GlobalLangfuseManager",
    "langfuse_manager",
    "build_resilient_llm",
    "is_transient_error",
    "TransientLLMError",
]
