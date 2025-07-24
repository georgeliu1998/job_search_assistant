"""
LLM observability modules for the Job Search Assistant application.

This module provides observability and tracing capabilities for LLM operations,
including Langfuse integration for monitoring and debugging.
"""

from src.llm.observability.langfuse import (
    GlobalLangfuseManager,
    LangfuseManager,
    get_langfuse_handler,
    is_langfuse_enabled,
    langfuse_manager,
    reset_langfuse_handler,
)

__all__ = [
    # New OOP interface
    "LangfuseManager",
    "GlobalLangfuseManager",
    "langfuse_manager",
    # Backward compatibility
    "get_langfuse_handler",
    "is_langfuse_enabled",
    "reset_langfuse_handler",
]
