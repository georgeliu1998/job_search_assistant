"""
Class-based Langfuse handler with singleton pattern.

This module provides a class-based Langfuse handler that implements the
ObservabilityHandler interface and uses the singleton pattern for efficient
resource management.
"""

import uuid
from typing import Any, Dict, Optional
from urllib.parse import urlparse

from langfuse.callback import CallbackHandler

from src.config import config
from src.exceptions.llm import LLMObservabilityError
from src.llm.observability.base import NoOpObservabilityHandler, ObservabilityHandler
from src.utils.logging import get_logger
from src.utils.singleton import singleton

logger = get_logger(__name__)


@singleton
class LangfuseHandler(ObservabilityHandler):
    """
    Class-based Langfuse handler with singleton pattern.

    This handler provides Langfuse observability capabilities with efficient
    resource management through the singleton pattern. Different configurations
    will create different singleton instances.
    """

    def __init__(self, langfuse_config=None):
        """
        Initialize the Langfuse handler.

        Args:
            langfuse_config: Optional Langfuse configuration. If None, uses global config.
        """
        self.config = langfuse_config or config.observability.langfuse
        self.logger = get_logger(__name__)
        self._handler: Optional[CallbackHandler] = None
        self._active_traces: Dict[str, Any] = {}

        # Validate configuration on initialization
        self._is_valid = self._validate_configuration()

        if self._is_valid:
            self.logger.debug("Langfuse handler initialized with valid configuration")
        else:
            self.logger.debug(
                "Langfuse handler initialized but configuration is invalid"
            )

    def _validate_configuration(self) -> bool:
        """
        Validate the Langfuse configuration.

        Returns:
            True if configuration is valid and complete, False otherwise
        """
        if not self.config.enabled:
            self.logger.debug("Langfuse is disabled via configuration")
            return False

        if not self.config.public_key or not self.config.secret_key:
            self.logger.warning("Langfuse configuration incomplete - missing API keys")
            if not self.config.public_key:
                self.logger.debug("Missing LANGFUSE_PUBLIC_KEY")
            if not self.config.secret_key:
                self.logger.debug("Missing LANGFUSE_SECRET_KEY")
            return False

        if not self._validate_host(self.config.host):
            self.logger.error(f"Invalid Langfuse host URL: {self.config.host}")
            return False

        return True

    def _validate_host(self, host: str) -> bool:
        """Validate that the host URL is properly formatted."""
        try:
            parsed = urlparse(host)
            return bool(parsed.scheme and parsed.netloc)
        except Exception:
            return False

    def get_callback_config(self) -> Dict[str, Any]:
        """
        Get Langfuse callback configuration.

        Returns:
            Dictionary containing callback configuration for LLM clients.
            Returns empty dict if observability is disabled or invalid.
        """
        if not self.is_enabled():
            return {}

        handler = self._get_or_create_handler()
        return {"callbacks": [handler]} if handler else {}

    def is_enabled(self) -> bool:
        """
        Check if Langfuse observability is enabled and properly configured.

        Returns:
            True if enabled and configured, False otherwise
        """
        return self._is_valid and self.config.enabled

    def start_trace(
        self, operation_name: str, metadata: Optional[Dict[str, Any]] = None
    ) -> Optional[str]:
        """
        Start a new trace for an operation.

        Args:
            operation_name: Name of the operation being traced
            metadata: Optional metadata to attach to the trace

        Returns:
            Trace ID if successful, None if tracing is disabled
        """
        if not self.is_enabled():
            return None

        try:
            trace_id = str(uuid.uuid4())
            trace_data = {
                "operation_name": operation_name,
                "metadata": metadata or {},
                "start_time": None,  # Will be set by Langfuse
                "handler": self._get_or_create_handler(),
            }

            self._active_traces[trace_id] = trace_data
            self.logger.debug(
                f"Started trace {trace_id} for operation: {operation_name}"
            )
            return trace_id

        except Exception as e:
            self.logger.error(f"Failed to start trace for {operation_name}: {e}")
            return None

    def end_trace(
        self, trace_id: str, success: bool = True, error: Optional[Exception] = None
    ) -> None:
        """
        End an existing trace.

        Args:
            trace_id: The trace ID returned from start_trace
            success: Whether the operation completed successfully
            error: Optional exception if the operation failed
        """
        if not self.is_enabled() or trace_id not in self._active_traces:
            return

        try:
            trace_data = self._active_traces.pop(trace_id)
            operation_name = trace_data["operation_name"]

            # Add final metadata
            final_metadata = trace_data["metadata"].copy()
            final_metadata.update(
                {
                    "success": success,
                    "error": str(error) if error else None,
                    "error_type": type(error).__name__ if error else None,
                }
            )

            self.logger.debug(
                f"Ended trace {trace_id} for operation: {operation_name} (success: {success})"
            )

        except Exception as e:
            self.logger.error(f"Failed to end trace {trace_id}: {e}")

    def add_trace_metadata(self, trace_id: str, metadata: Dict[str, Any]) -> None:
        """
        Add metadata to an existing trace.

        Args:
            trace_id: The trace ID to add metadata to
            metadata: Dictionary of metadata to add
        """
        if not self.is_enabled() or trace_id not in self._active_traces:
            return

        try:
            self._active_traces[trace_id]["metadata"].update(metadata)
            self.logger.debug(
                f"Added metadata to trace {trace_id}: {list(metadata.keys())}"
            )

        except Exception as e:
            self.logger.error(f"Failed to add metadata to trace {trace_id}: {e}")

    def _get_or_create_handler(self) -> Optional[CallbackHandler]:
        """
        Get or create the Langfuse callback handler with lazy initialization.

        Returns:
            CallbackHandler instance if successful, None if failed
        """
        if not self.is_enabled():
            return None

        if self._handler is None:
            self._handler = self._create_handler()

        return self._handler

    def _create_handler(self) -> Optional[CallbackHandler]:
        """
        Create a new Langfuse callback handler.

        Returns:
            CallbackHandler instance if successful, None if failed
        """
        try:
            self.logger.info(f"Creating Langfuse handler with host: {self.config.host}")

            handler = CallbackHandler(
                public_key=self.config.public_key,
                secret_key=self.config.secret_key,
                host=self.config.host,
            )

            self.logger.info("Langfuse handler created successfully")
            return handler

        except Exception as e:
            self.logger.error(f"Failed to create Langfuse handler: {e}")
            self.logger.debug("This could be due to:")
            self.logger.debug("- Invalid API keys")
            self.logger.debug("- Network connectivity issues")
            self.logger.debug("- Langfuse service unavailability")
            return None

    def get_provider_name(self) -> str:
        """Get the provider name for this handler."""
        return "langfuse"

    def reset_handler(self) -> None:
        """
        Reset the handler instance.

        This is primarily useful for testing or when configuration changes.
        """
        self.logger.debug("Resetting Langfuse handler")
        self._handler = None
        self._active_traces.clear()

    def get_active_trace_count(self) -> int:
        """
        Get the number of currently active traces.

        Returns:
            Number of active traces
        """
        return len(self._active_traces)

    def get_handler_info(self) -> Dict[str, Any]:
        """
        Get information about the handler state.

        Returns:
            Dictionary containing handler state information
        """
        return {
            "enabled": self.is_enabled(),
            "handler_created": self._handler is not None,
            "active_traces": self.get_active_trace_count(),
            "host": self.config.host,
            "has_public_key": bool(self.config.public_key),
            "has_secret_key": bool(self.config.secret_key),
            "configuration_valid": self._is_valid,
        }


def get_langfuse_handler(langfuse_config=None) -> ObservabilityHandler:
    """
    Get a Langfuse handler instance.

    This function provides backward compatibility with the existing interface
    while using the new class-based singleton approach.

    Args:
        langfuse_config: Optional Langfuse configuration

    Returns:
        LangfuseHandler instance if configuration is valid, NoOpObservabilityHandler otherwise
    """
    try:
        handler = LangfuseHandler(langfuse_config)
        if handler.is_enabled():
            return handler
        else:
            logger.debug("Langfuse not enabled or configured, returning no-op handler")
            return NoOpObservabilityHandler()

    except Exception as e:
        logger.error(f"Failed to create Langfuse handler: {e}")
        return NoOpObservabilityHandler()


def reset_langfuse_handler() -> None:
    """
    Reset the global Langfuse handler instance.

    This function provides backward compatibility with the existing interface.
    """
    try:
        # Use the singleton's reload method to reset the instance
        handler = LangfuseHandler()
        handler.reset_handler()

        # Also reset the singleton instance itself
        if hasattr(LangfuseHandler, "_instances"):
            LangfuseHandler._instances.clear()

        logger.debug("Reset Langfuse handler instance")

    except Exception as e:
        logger.error(f"Failed to reset Langfuse handler: {e}")


def is_langfuse_enabled() -> bool:
    """
    Check if Langfuse tracing is enabled.

    This function provides backward compatibility with the existing interface.

    Returns:
        True if Langfuse is enabled and configured, False otherwise
    """
    try:
        handler = LangfuseHandler()
        return handler.is_enabled()
    except Exception as e:
        logger.error(f"Failed to check Langfuse status: {e}")
        return False
