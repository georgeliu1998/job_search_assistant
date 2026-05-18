"""
LLM client modules for the Job Search Assistant application.

Provides get_chat_model() and get_chat_model_by_profile_name() to create
configured LangChain BaseChatModel instances for different providers.
"""

from src.llm.factory import get_chat_model, get_chat_model_by_profile_name
from src.llm.langfuse import GlobalLangfuseManager, LangfuseManager, langfuse_manager

__all__ = [
    "get_chat_model",
    "get_chat_model_by_profile_name",
    "LangfuseManager",
    "GlobalLangfuseManager",
    "langfuse_manager",
]
