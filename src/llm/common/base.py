"""
Enhanced base LLM client class with integrated observability and metrics.

This module provides an enhanced base class that integrates observability,
metrics collection, and improved error handling.
"""

import os
import time
from abc import ABC, abstractmethod
from typing import Any, Dict, List, Optional

from src.config.models import LLMProfileConfig
from src.exceptions.llm import (
    LLMConfigurationError,
    LLMObservabilityError,
    LLMProviderError,
)
from src.llm.observability.base import NoOpObservabilityHandler, ObservabilityHandler
from src.llm.observability.langfuse import get_langfuse_handler
from src.llm.observability.metrics import MetricsCollector
from src.utils.logging import get_logger


class BaseLLMClient(ABC):
    """
    Enhanced abstract base class for all LLM clients with integrated observability.

    This class provides a common interface for all LLM provider clients with
    automatic observability injection, metrics collection, and improved error handling.

    Subclasses should implement the `_invoke_implementation` method to provide
    provider-specific communication logic. The public `invoke` method handles
    observability and metrics automatically.
    """

    def __init__(self, config: LLMProfileConfig):
        """
        Initialize the enhanced LLM client.

        Args:
            config: LLM profile configuration object

        Raises:
            LLMConfigurationError: If configuration is invalid
        """
        self.config = config
        self.logger = get_logger(f"llm.{self.__class__.__name__.lower()}")
        self._client = None  # For lazy initialization

        # Integrated observability
        self.observability_handler = self._create_observability_handler()

        # Metrics collection (if enabled)
        self.metrics_collector = self._create_metrics_collector()

        # Validate configuration
        self._validate_config()

        self.logger.debug(
            f"Initialized {self.__class__.__name__} with model: {config.model}"
        )

    def _validate_config(self) -> None:
        """
        Validate the client configuration.

        Raises:
            LLMConfigurationError: If configuration is invalid
        """
        if not self.config.model:
            raise LLMConfigurationError("Model name is required", "model")

        if self.config.temperature < 0 or self.config.temperature > 2:
            raise LLMConfigurationError(
                f"Temperature must be between 0 and 2, got: {self.config.temperature}",
                "temperature",
            )

        if self.config.max_tokens <= 0:
            raise LLMConfigurationError(
                f"Max tokens must be positive, got: {self.config.max_tokens}",
                "max_tokens",
            )

    def _create_observability_handler(self) -> ObservabilityHandler:
        """
        Create the appropriate observability handler.

        Returns:
            ObservabilityHandler instance based on configuration
        """
        try:
            # For now, we only support Langfuse, but this can be extended
            # to support other observability providers based on configuration
            return get_langfuse_handler()
        except Exception as e:
            self.logger.error(f"Failed to create observability handler: {e}")
            return NoOpObservabilityHandler()

    def _create_metrics_collector(self) -> Optional[MetricsCollector]:
        """
        Create metrics collector if metrics collection is enabled.

        Returns:
            MetricsCollector instance if enabled, None otherwise
        """
        try:
            # Check if metrics collection is enabled in the global config
            from src.config import config

            if config.observability.metrics.track_performance:
                return MetricsCollector()
            else:
                self.logger.debug("Metrics collection disabled via configuration")
                return None
        except Exception as e:
            self.logger.error(f"Failed to create metrics collector: {e}")
            return None

    def invoke(self, messages: List[Any], config: dict = None) -> Any:
        """
        Send messages to the LLM and get a response with automatic observability.

        This method provides the public interface for LLM communication with
        automatic observability injection and metrics collection.

        Args:
            messages: List of messages to send to the LLM
            config: Optional configuration dictionary

        Returns:
            The response from the LLM provider

        Raises:
            LLMProviderError: If there's an error communicating with the LLM
        """
        start_time = time.time()
        trace_id = None

        try:
            # Start observability trace
            trace_id = self.observability_handler.start_trace(
                operation_name=f"llm_invoke_{self.get_model_name()}",
                metadata={
                    "model": self.get_model_name(),
                    "provider": self.config.provider,
                    "message_count": len(messages),
                    "temperature": self.config.temperature,
                    "max_tokens": self.config.max_tokens,
                },
            )

            # Prepare configuration with observability
            merged_config = self._prepare_config_with_observability(config)

            # Invoke the provider-specific implementation
            response = self._invoke_implementation(messages, merged_config)

            # Calculate metrics
            duration = time.time() - start_time
            input_tokens = self._count_tokens(messages)
            output_tokens = self._count_tokens([response])

            # Record successful metrics
            if self.metrics_collector:
                self.metrics_collector.record_success(
                    model=self.get_model_name(),
                    duration=duration,
                    input_tokens=input_tokens,
                    output_tokens=output_tokens,
                )

            # Add trace metadata and end trace
            if trace_id:
                self.observability_handler.add_trace_metadata(
                    trace_id,
                    {
                        "input_tokens": input_tokens,
                        "output_tokens": output_tokens,
                        "total_tokens": input_tokens + output_tokens,
                        "duration": duration,
                    },
                )
                self.observability_handler.end_trace(trace_id, success=True)

            # Log the successful call
            self._log_llm_call(messages, response, duration)

            return response

        except Exception as e:
            duration = time.time() - start_time

            # Record error metrics
            if self.metrics_collector:
                self.metrics_collector.record_error(
                    model=self.get_model_name(),
                    error_type=type(e).__name__,
                    duration=duration,
                )

            # End trace with error
            if trace_id:
                self.observability_handler.end_trace(trace_id, success=False, error=e)

            # Log the error
            self._log_error(e, messages)

            # Re-raise the exception
            raise

    def _prepare_config_with_observability(self, config: dict = None) -> dict:
        """
        Prepare configuration dictionary with observability callbacks.

        Args:
            config: Optional user-provided configuration

        Returns:
            Merged configuration with observability callbacks
        """
        # Start with user config or empty dict
        merged_config = config.copy() if config else {}

        # Get observability configuration
        observability_config = self.observability_handler.get_callback_config()

        # Merge observability callbacks with existing callbacks
        if observability_config and "callbacks" in observability_config:
            existing_callbacks = merged_config.get("callbacks", [])
            merged_config["callbacks"] = (
                existing_callbacks + observability_config["callbacks"]
            )

        return merged_config

    @abstractmethod
    def _invoke_implementation(self, messages: List[Any], config: dict) -> Any:
        """
        Provider-specific invoke implementation.

        This method must be implemented by each provider-specific client
        to handle the actual communication with the LLM service.

        Args:
            messages: List of messages to send to the LLM
            config: Configuration dictionary (including observability callbacks)

        Returns:
            The response from the LLM provider

        Raises:
            LLMProviderError: If there's an error communicating with the LLM
        """
        raise NotImplementedError(
            "Subclasses must implement the '_invoke_implementation' method."
        )

    @abstractmethod
    def get_model_name(self) -> str:
        """
        Get the model identifier for this client.

        Returns:
            String identifier for the model being used
        """
        pass

    def _get_client(self) -> Any:
        """
        Get or create the underlying LLM client instance.

        This default implementation uses lazy initialization and stores the client
        in self._client. Subclasses should override this method only if they require
        custom initialization logic.

        Returns:
            The provider-specific client instance

        Raises:
            LLMProviderError: If client initialization fails
        """
        if self._client is None:
            self._client = self._initialize_client()
        return self._client

    @abstractmethod
    def _initialize_client(self) -> Any:
        """
        Initialize the provider-specific client instance.

        Subclasses must implement this method to create and return the
        provider-specific client instance.

        Returns:
            The initialized client instance

        Raises:
            LLMProviderError: If client initialization fails
        """
        raise NotImplementedError(
            "Subclasses must implement the '_initialize_client' method."
        )

    def _ensure_api_key(self, env_var_name: str, prompt_text: str = None) -> str:
        """
        Generic API key management method that can be used by all providers.

        Args:
            env_var_name: Environment variable name for the API key
            prompt_text: Optional custom prompt text (deprecated, no longer used)

        Returns:
            The API key value

        Raises:
            LLMProviderError: If API key cannot be obtained
        """
        # First, try to get from config
        api_key = getattr(self.config, "api_key", None)

        if not api_key:
            # Try to get from environment
            api_key = os.getenv(env_var_name)

        if not api_key:
            raise LLMProviderError(
                f"API key not found. Please set {env_var_name} in your environment or .env file. "
                f"See README.md for setup instructions.",
                provider=self.config.provider,
            )

        return api_key

    def _count_tokens(self, messages: List[Any]) -> int:
        """
        Count tokens in messages.

        This is a basic implementation that estimates token count.
        Subclasses can override this for more accurate provider-specific counting.

        Args:
            messages: List of messages to count tokens for

        Returns:
            Estimated token count
        """
        if not messages:
            return 0

        # Basic estimation: ~4 characters per token for English text
        total_chars = sum(len(str(msg)) for msg in messages)
        return max(1, total_chars // 4)

    def _log_llm_call(
        self, messages: List[Any], response: Any, duration: float
    ) -> None:
        """
        Log details about an LLM call for monitoring and debugging.

        Args:
            messages: The input messages sent to the LLM
            response: The response received from the LLM
            duration: Time taken for the call in seconds
        """
        input_tokens = self._count_tokens(messages)
        output_tokens = self._count_tokens([response])
        total_tokens = input_tokens + output_tokens

        self.logger.info(
            f"LLM call completed - Model: {self.get_model_name()}, "
            f"Input tokens: {input_tokens}, "
            f"Output tokens: {output_tokens}, "
            f"Total tokens: {total_tokens}, "
            f"Duration: {duration:.2f}s, "
            f"Tokens/sec: {total_tokens/duration:.1f}"
        )

    def _log_error(self, error: Exception, messages: List[Any] = None) -> None:
        """
        Log errors with context for debugging.

        Args:
            error: The exception that occurred
            messages: Optional input messages for context
        """
        context = {"provider": self.config.provider, "model": self.get_model_name()}

        if messages:
            context["input_tokens"] = self._count_tokens(messages)
            context["message_count"] = len(messages)

        self.logger.error(
            f"LLM call failed - {context}, Error: {error}",
            exc_info=True,
        )

    def get_client_info(self) -> Dict[str, Any]:
        """
        Get information about the client state.

        Returns:
            Dictionary containing client state information
        """
        return {
            "provider": self.config.provider,
            "model": self.get_model_name(),
            "temperature": self.config.temperature,
            "max_tokens": self.config.max_tokens,
            "client_initialized": self._client is not None,
            "observability_enabled": self.observability_handler.is_enabled(),
            "metrics_enabled": self.metrics_collector is not None,
            "observability_provider": self.observability_handler.get_provider_name(),
        }

    def get_metrics_summary(self) -> str:
        """
        Get a summary of metrics for this client.

        Returns:
            Human-readable metrics summary, or message if metrics disabled
        """
        if not self.metrics_collector:
            return "Metrics collection is disabled"

        return self.metrics_collector.get_metrics_summary()
