"""
Langfuse observability manager for LLM tracing.

Provides a clean interface for Langfuse integration optimized for
LangChain and LangGraph workflows.
"""

from typing import Optional

from langfuse.callback import CallbackHandler

from src.config import config
from src.utils.logging import get_logger
from src.utils.singleton import singleton


class LangfuseManager:
    """
    Simplified manager for Langfuse observability integration.

    Optimized for LangChain/LangGraph workflows following official
    Langfuse integration patterns.
    """

    def __init__(self):
        """Initialize the Langfuse manager."""
        self.config = config.observability.langfuse
        self.logger = get_logger(__name__)
        self._handler: Optional[CallbackHandler] = None

    def get_handler(self) -> Optional[CallbackHandler]:
        """
        Get the Langfuse callback handler for LangChain integration.

        Returns:
            CallbackHandler instance if enabled, None otherwise

        Note:
            Handler is created lazily and cached for reuse across calls.
        """
        if not self.is_enabled():
            return None

        if self._handler is None:
            try:
                # Direct instantiation as shown in Langfuse docs
                self._handler = CallbackHandler()
                self.logger.info("Langfuse CallbackHandler initialized")
            except Exception as e:
                self.logger.error(f"Failed to create Langfuse handler: {e}")
                self._log_setup_help()
                return None

        return self._handler

    def get_config(self, additional_config: Optional[dict] = None) -> dict:
        """
        Get execution config with Langfuse callback handler.

        Args:
            additional_config: Optional additional configuration to merge

        Returns:
            Configuration dict ready for LangChain runnable methods

        Example:
            config = langfuse_manager.get_config()
            chain.invoke(input, config=config)
        """
        handler = self.get_handler()
        execution_config = {"callbacks": [handler]} if handler else {}

        if additional_config:
            execution_config.update(additional_config)

        return execution_config

    def is_enabled(self) -> bool:
        """Check if Langfuse tracing is enabled and properly configured."""
        return self.config.enabled and self.config.is_valid()

    def reset(self) -> None:
        """Reset the handler (useful for testing)."""
        self.logger.debug("Resetting Langfuse handler")
        self._handler = None

    def _log_setup_help(self) -> None:
        """Log setup instructions when configuration fails."""
        self.logger.info("To enable Langfuse tracing:")
        self.logger.info("1. Set environment variables:")
        self.logger.info("   - LANGFUSE_PUBLIC_KEY=pk-lf-...")
        self.logger.info("   - LANGFUSE_SECRET_KEY=sk-lf-...")
        self.logger.info("   - LANGFUSE_HOST=https://cloud.langfuse.com (optional)")
        self.logger.info("2. Enable in config: observability.langfuse.enabled=true")


@singleton
class GlobalLangfuseManager(LangfuseManager):
    """Global singleton Langfuse manager."""

    pass


# Global instance for application use
langfuse_manager = GlobalLangfuseManager()
