"""
Google LLM client implementation using LangChain.
"""

import time
from typing import Any, List

from langchain_google_genai import ChatGoogleGenerativeAI

from src.config.models import LLMProfileConfig
from src.exceptions.llm import LLMProviderError, LLMResponseError
from src.llm.common.base import BaseLLMClient
from src.utils.singleton import singleton


@singleton
class GoogleClient(BaseLLMClient):
    """
    Singleton Google LLM client implementation.

    This client wraps the LangChain ChatGoogleGenerativeAI client and provides
    the standardized interface defined by BaseLLMClient. The singleton
    pattern ensures that multiple calls with the same configuration
    return the same instance, improving resource efficiency.

    One instance is created per unique configuration, allowing for
    different models, temperatures, or other settings to coexist.
    """

    def __init__(self, config: LLMProfileConfig):
        """
        Initialize the Google client.

        Args:
            config: LLM profile configuration

        Raises:
            LLMProviderError: If API key is missing or invalid
        """
        super().__init__(config)

        # Validate that this is a Google config
        if config.provider != "google":
            raise LLMProviderError(f"Expected google provider, got: {config.provider}")

        # Use the generic API key management from base class
        self._ensure_api_key("GOOGLE_API_KEY", "Enter your Google API key: ")

    def _initialize_client(self) -> ChatGoogleGenerativeAI:
        """
        Create and return the underlying ChatGoogleGenerativeAI client instance.

        Returns:
            Configured ChatGoogleGenerativeAI instance

        Raises:
            LLMProviderError: If client initialization fails
        """
        try:
            client = ChatGoogleGenerativeAI(
                model=self.config.model,
                temperature=self.config.temperature,
                max_tokens=self.config.max_tokens,
                google_api_key=self.config.api_key,
            )
            self.logger.debug(
                f"Initialized Google client with model: {self.config.model}"
            )
            return client
        except Exception as e:
            raise LLMProviderError(f"Failed to initialize Google client: {e}")

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
            if "quota" in str(e).lower() or "rate limit" in str(e).lower():
                raise LLMProviderError(f"Rate limit or quota exceeded: {e}")
            elif "api key" in str(e).lower() or "authentication" in str(e).lower():
                raise LLMProviderError(f"API key error: {e}")
            elif "model" in str(e).lower() and "not found" in str(e).lower():
                raise LLMProviderError(f"Model not available: {e}")
            elif "safety" in str(e).lower():
                raise LLMProviderError(f"Content blocked by safety filters: {e}")
            else:
                raise LLMProviderError(f"Google API error: {e}")
