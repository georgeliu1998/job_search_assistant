"""
Base LLM client class providing a common interface for all LLM providers.
"""

import os
from abc import ABC, abstractmethod
from typing import Any, List

from src.config.models import LLMProfileConfig
from src.exceptions.llm import LLMProviderError
from src.utils.logging import get_logger


class BaseLLMClient(ABC):
    """
    Abstract base class for all LLM clients.

    This class defines the common interface that all LLM provider clients
    must implement, ensuring consistency across different providers.

    Subclasses should implement the `_initialize_client` method to provide
    provider-specific client initialization. The `_get_client` method provides
    a default lazy initialization pattern and should only be overridden if
    custom logic is required.
    """

    def __init__(self, config: LLMProfileConfig):
        """
        Initialize the LLM client.

        Args:
            config: LLM profile configuration object
        """
        self.config = config
        self.logger = get_logger(f"llm.{self.__class__.__name__.lower()}")
        self._client = None  # For lazy initialization

    @abstractmethod
    def invoke(self, messages: List[Any], config: dict = None) -> Any:
        """
        Send messages to the LLM and get a response.

        This method should be implemented by each provider-specific client
        to handle the actual communication with the LLM service.

        Args:
            messages: List of messages to send to the LLM
            config: Optional configuration dictionary (e.g., for callbacks)

        Returns:
            The response from the LLM provider

        Raises:
            LLMProviderError: If there's an error communicating with the LLM
        """
        raise NotImplementedError("Subclasses must implement the 'invoke' method.")

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
        Subclasses must implement this method to create and return the provider-specific client instance.
        This method is called by the default _get_client implementation for lazy initialization.
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
                f"See README.md for setup instructions."
            )

        return api_key

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
        input_length = sum(len(str(msg)) for msg in messages)
        response_length = len(str(response)) if response else 0

        self.logger.info(
            f"LLM call completed - Model: {self.get_model_name()}, "
            f"Input length: {input_length}, "
            f"Response length: {response_length}, "
            f"Duration: {duration:.2f}s"
        )

    def _log_error(self, error: Exception, messages: List[Any] = None) -> None:
        """
        Log errors with context for debugging.

        Args:
            error: The exception that occurred
            messages: Optional input messages for context
        """
        context = {}
        if messages:
            context["input_length"] = sum(len(str(msg)) for msg in messages)
            context["message_count"] = len(messages)

        self.logger.error(
            f"LLM call failed - Model: {self.get_model_name()}, "
            f"Error: {error}, Context: {context}",
            exc_info=True,
        )
