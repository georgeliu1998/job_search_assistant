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
    """

    def __init__(self, config: LLMProfileConfig):
        """
        Initialize the LLM client.

        Args:
            config: LLM profile configuration object
        """
        self.config = config
        self.logger = get_logger(f"llm.{self.__class__.__name__.lower()}")

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
        pass

    @abstractmethod
    def get_model_name(self) -> str:
        """
        Get the model identifier for this client.

        Returns:
            String identifier for the model being used
        """
        pass

    @abstractmethod
    def _get_client(self) -> Any:
        """
        Get or create the underlying LLM client instance.

        This method should implement lazy initialization of the provider-specific
        client (e.g., ChatAnthropic). Different providers may need
        different initialization parameters or patterns.

        Returns:
            The provider-specific client instance

        Raises:
            LLMProviderError: If client initialization fails
        """
        pass

    def _ensure_api_key(self, env_var_name: str, prompt_text: str = None) -> str:
        """
        Generic API key management method that can be used by all providers.

        Args:
            env_var_name: Environment variable name for the API key
            prompt_text: Optional custom prompt text (defaults to env_var_name)

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
            # Prompt user for API key
            try:
                import getpass

                prompt = prompt_text or f"{env_var_name}: "
                api_key = getpass.getpass(prompt)
                if not api_key:
                    raise LLMProviderError("No API key provided")

                # Set in environment for future use
                os.environ[env_var_name] = api_key

                # Update config if it has api_key attribute
                if hasattr(self.config, "api_key"):
                    self.config.api_key = api_key

                self.logger.debug(
                    f"API key obtained and set in environment: {env_var_name}"
                )

            except (KeyboardInterrupt, EOFError):
                raise LLMProviderError("API key input was cancelled")
            except Exception as e:
                raise LLMProviderError(f"Failed to get API key: {e}")

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
