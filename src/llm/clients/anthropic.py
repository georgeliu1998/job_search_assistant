"""
Anthropic LLM client implementation using LangChain.
"""

import time
from typing import Any, List

from langchain_anthropic import ChatAnthropic

from src.config.models import LLMProfileConfig
from src.exceptions.llm import LLMProviderError, LLMResponseError
from src.llm.clients.base import BaseLLMClient


class AnthropicClient(BaseLLMClient):
    """
    Anthropic LLM client implementation.

    This client wraps the LangChain ChatAnthropic client and provides
    the standardized interface defined by BaseLLMClient.
    """

    def __init__(self, config: LLMProfileConfig):
        """
        Initialize the Anthropic client.

        Args:
            config: LLM profile configuration

        Raises:
            LLMProviderError: If API key is missing or invalid
        """
        super().__init__(config)
        self.config: LLMProfileConfig = config
        self._client = None

        # Validate that this is an Anthropic config
        if config.provider != "anthropic":
            raise LLMProviderError(
                f"Expected anthropic provider, got: {config.provider}"
            )

        # Use the generic API key management from base class
        self._ensure_api_key("ANTHROPIC_API_KEY", "Enter your Anthropic API key: ")

    def _get_client(self) -> ChatAnthropic:
        """
        Get or create the underlying ChatAnthropic client.

        Returns:
            Configured ChatAnthropic instance

        Raises:
            LLMProviderError: If client initialization fails
        """
        if self._client is None:
            try:
                self._client = ChatAnthropic(
                    model=self.config.model,  # Now just a string, not an enum
                    temperature=self.config.temperature,
                    max_tokens=self.config.max_tokens,
                    api_key=self.config.api_key,
                )
                self.logger.debug(
                    f"Initialized Anthropic client with model: {self.config.model}"
                )
            except Exception as e:
                raise LLMProviderError(f"Failed to initialize Anthropic client: {e}")
        return self._client

    def get_model_name(self) -> str:
        """Get the model identifier for this client."""
        return self.config.model

    def invoke(self, messages: List[Any], config: dict = None) -> Any:
        """
        Send messages to the LLM and get a response.

        Args:
            messages: List of messages to send to the LLM
            config: Optional configuration dictionary (e.g., for callbacks)

        Returns:
            The response from the LLM

        Raises:
            LLMProviderError: If there's an error communicating with the LLM
            LLMResponseError: If the response format is invalid
        """
        start_time = time.time()

        try:
            client = self._get_client()

            # Pass config to the underlying LangChain client if provided
            if config:
                response = client.invoke(messages, config=config)
            else:
                response = client.invoke(messages)

            duration = time.time() - start_time
            self._log_llm_call(messages, response, duration)

            return response

        except Exception as e:
            self._log_error(e, messages)
            if "rate limit" in str(e).lower():
                raise LLMProviderError(f"Rate limit exceeded: {e}")
            elif "api key" in str(e).lower():
                raise LLMProviderError(f"API key error: {e}")
            else:
                raise LLMProviderError(f"Anthropic API error: {e}")
