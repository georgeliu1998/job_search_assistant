"""
LLM client modules for the Job Search Assistant application.

Provides get_chat_model() and get_chat_model_by_profile_name() to create
configured LangChain BaseChatModel instances for different providers.
"""

from src.llm.common.factory import get_chat_model, get_chat_model_by_profile_name

# Observability
from src.llm.observability import langfuse_manager

__all__ = [
    "get_chat_model",
    "get_chat_model_by_profile_name",
    "langfuse_manager",
]
