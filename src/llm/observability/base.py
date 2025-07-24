"""
Abstract base classes for observability handlers.

This module defines the interface that all observability handlers must implement,
ensuring consistent behavior across different observability providers.
"""

from abc import ABC, abstractmethod
from typing import Any, Dict, Optional


class ObservabilityHandler(ABC):
    """
    Abstract base class for observability handlers.

    This class defines the interface that all observability providers
    (e.g., Langfuse, DataDog, New Relic) must implement.
    """

    @abstractmethod
    def get_callback_config(self) -> Dict[str, Any]:
        """
        Get configuration dict for LLM callbacks.

        Returns:
            Dictionary containing callback configuration for the LLM client.
            Should return empty dict if observability is disabled.
        """
        pass

    @abstractmethod
    def is_enabled(self) -> bool:
        """
        Check if observability is enabled.

        Returns:
            True if observability is enabled and properly configured, False otherwise.
        """
        pass

    @abstractmethod
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
        pass

    @abstractmethod
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
        pass

    @abstractmethod
    def add_trace_metadata(self, trace_id: str, metadata: Dict[str, Any]) -> None:
        """
        Add metadata to an existing trace.

        Args:
            trace_id: The trace ID to add metadata to
            metadata: Dictionary of metadata to add
        """
        pass

    def get_provider_name(self) -> str:
        """
        Get the name of the observability provider.

        Returns:
            String identifier for the observability provider
        """
        return self.__class__.__name__.replace("Handler", "").lower()


class NoOpObservabilityHandler(ObservabilityHandler):
    """
    No-operation observability handler for when observability is disabled.

    This handler provides a null object pattern implementation that does
    nothing but satisfies the ObservabilityHandler interface.
    """

    def get_callback_config(self) -> Dict[str, Any]:
        """Return empty config dict."""
        return {}

    def is_enabled(self) -> bool:
        """Always returns False since this is the no-op handler."""
        return False

    def start_trace(
        self, operation_name: str, metadata: Optional[Dict[str, Any]] = None
    ) -> Optional[str]:
        """Return None since tracing is disabled."""
        return None

    def end_trace(
        self, trace_id: str, success: bool = True, error: Optional[Exception] = None
    ) -> None:
        """Do nothing since tracing is disabled."""
        pass

    def add_trace_metadata(self, trace_id: str, metadata: Dict[str, Any]) -> None:
        """Do nothing since tracing is disabled."""
        pass
