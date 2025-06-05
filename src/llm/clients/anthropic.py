"""
Anthropic LLM client implementation using LangChain.
"""

import time
from typing import Any, List

from langchain_anthropic import ChatAnthropic

from src.config.llm.anthropic import AnthropicConfig
from src.exceptions.llm import LLMProviderError, LLMResponseError
from src.llm.clients.base import BaseLLMClient


class AnthropicClient(BaseLLMClient):
    """
    Anthropic LLM client implementation.

    This client wraps the LangChain ChatAnthropic client and provides
    the standardized interface defined by BaseLLMClient.
    """

    def __init__(self, config: AnthropicConfig):
        """
        Initialize the Anthropic client.

        Args:
            config: Anthropic-specific configuration

        Raises:
            LLMProviderError: If API key is missing or invalid
        """
        super().__init__(config)
        self.config: AnthropicConfig = config
        self._client = None
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
                    model=self.config.model.value,
                    temperature=self.config.temperature,
                    max_tokens=self.config.max_tokens,
                    api_key=self.config.api_key,
                )
                self.logger.debug(
                    f"Initialized Anthropic client with model: "
                    f"{self.config.model.value}"
                )
            except Exception as e:
                raise LLMProviderError(f"Failed to initialize Anthropic client: {e}")
        return self._client

    def invoke(self, messages: List[Any]) -> Any:
        """
        Send messages to Anthropic and get a response.

        Args:
            messages: List of messages to send to the LLM

        Returns:
            The response from Anthropic

        Raises:
            LLMProviderError: If there's an error communicating with Anthropic
            LLMResponseError: If the response is invalid
        """
        start_time = time.time()

        try:
            client = self._get_client()
            response = client.invoke(messages)
            duration = time.time() - start_time

            # Validate response
            if not response or not hasattr(response, "content"):
                raise LLMResponseError(
                    "Received empty or invalid response from Anthropic"
                )

            self._log_llm_call(messages, response, duration)
            return response

        except LLMProviderError:
            # Re-raise provider errors as-is
            raise
        except LLMResponseError:
            # Re-raise response errors as-is
            raise
        except Exception as e:
            self._log_error(e, messages)
            # Convert any other errors to provider errors
            raise LLMProviderError(f"Anthropic API call failed: {e}")

    def get_model_name(self) -> str:
        """
        Get the Anthropic model identifier.

        Returns:
            String identifier for the Anthropic model
        """
        return self.config.model.value
