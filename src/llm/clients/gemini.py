"""
Gemini LLM client implementation using Google's GenerativeAI SDK.
"""

import time
from typing import Any, List, Optional

import google.generativeai as genai
from langchain_core.messages import BaseMessage

from src.config.llm.gemini import GeminiConfig
from src.exceptions.llm import LLMProviderError
from src.llm.clients.base import BaseLLMClient


class GeminiClient(BaseLLMClient):
    """
    Gemini LLM client using Google's GenerativeAI SDK.

    Provides a consistent interface for interacting with Gemini models
    while handling authentication, error management, and response formatting.
    """

    def __init__(self, config: GeminiConfig):
        """
        Initialize Gemini client.

        Args:
            config: Gemini-specific configuration
        """
        super().__init__(config)
        self._client: Optional[Any] = None
        self._api_key: Optional[str] = None

    def invoke(self, messages: List[BaseMessage], config: dict = None) -> Any:
        """
        Send messages to Gemini and get response.

        Args:
            messages: List of LangChain messages
            config: Optional configuration including callbacks for tracing

        Returns:
            Response object with content attribute

        Raises:
            LLMProviderError: If the request fails
        """
        start_time = time.time()
        callbacks = config.get("callbacks", []) if config else []

        # Initialize tracing if callbacks are provided
        langfuse_handler = None
        if callbacks:
            for callback in callbacks:
                if hasattr(callback, "on_llm_start"):
                    langfuse_handler = callback
                    break

        try:
            client = self._get_client()

            # Convert LangChain messages to Gemini format
            prompt = self._convert_messages_to_prompt(messages)

            # Start Langfuse tracing if available
            if langfuse_handler:
                try:
                    # Call on_llm_start for tracing
                    langfuse_handler.on_llm_start(
                        serialized={
                            "name": self.config.model,
                            "provider": "gemini",
                            "temperature": self.config.temperature,
                            "max_tokens": self.config.max_tokens,
                        },
                        prompts=[prompt],
                        run_id=None,
                    )
                except Exception as e:
                    self.logger.warning(f"Failed to start Langfuse tracing: {e}")

            # Configure generation parameters with safety settings
            generation_config = genai.types.GenerationConfig(
                temperature=self.config.temperature,
                max_output_tokens=self.config.max_tokens,
            )

            # Configure safety settings to be more permissive for business content
            safety_settings = [
                {
                    "category": "HARM_CATEGORY_HARASSMENT",
                    "threshold": "BLOCK_ONLY_HIGH",
                },
                {
                    "category": "HARM_CATEGORY_HATE_SPEECH",
                    "threshold": "BLOCK_ONLY_HIGH",
                },
                {
                    "category": "HARM_CATEGORY_SEXUALLY_EXPLICIT",
                    "threshold": "BLOCK_ONLY_HIGH",
                },
                {
                    "category": "HARM_CATEGORY_DANGEROUS_CONTENT",
                    "threshold": "BLOCK_ONLY_HIGH",
                },
            ]

            # Generate content
            response = client.generate_content(
                prompt,
                generation_config=generation_config,
                safety_settings=safety_settings,
            )

            # Handle response with proper safety checking
            response_text = self._extract_response_text(response)

            # Create response object compatible with existing code
            class GeminiResponse:
                def __init__(self, text: str):
                    self.content = text

            duration = time.time() - start_time
            gemini_response = GeminiResponse(response_text)

            # End Langfuse tracing if available
            if langfuse_handler:
                try:
                    # Call on_llm_end for tracing
                    langfuse_handler.on_llm_end(
                        response={"generations": [[{"text": response_text}]]},
                        run_id=None,
                    )
                except Exception as e:
                    self.logger.warning(f"Failed to end Langfuse tracing: {e}")

            self._log_llm_call(messages, gemini_response, duration)
            return gemini_response

        except Exception as e:
            # Error Langfuse tracing if available
            if langfuse_handler:
                try:
                    langfuse_handler.on_llm_error(error=e, run_id=None)
                except Exception as trace_e:
                    self.logger.warning(f"Failed to trace error to Langfuse: {trace_e}")

            self._log_error(e, messages)
            raise LLMProviderError(f"Gemini API call failed: {e}")

    def get_model_name(self) -> str:
        """Get the Gemini model identifier."""
        return self.config.model

    def _get_client(self) -> Any:
        """
        Get or create Gemini client instance.

        Returns:
            Configured Gemini GenerationalModel

        Raises:
            LLMProviderError: If client initialization fails
        """
        if self._client is None:
            try:
                # Ensure API key is available
                if not self._api_key:
                    self._api_key = self._ensure_api_key(
                        "GEMINI_API_KEY", "Enter your Gemini API key: "
                    )

                # Configure Gemini with API key
                genai.configure(api_key=self._api_key)

                # Create generative model
                self._client = genai.GenerativeModel(self.config.model)

                self.logger.info(
                    f"Gemini client initialized with model: {self.config.model}"
                )

            except Exception as e:
                raise LLMProviderError(f"Failed to initialize Gemini client: {e}")

        return self._client

    def _convert_messages_to_prompt(self, messages: List[BaseMessage]) -> str:
        """
        Convert LangChain messages to a single prompt string for Gemini.

        Args:
            messages: List of LangChain messages

        Returns:
            Combined prompt string
        """
        prompt_parts = []

        for message in messages:
            content = message.content
            if hasattr(message, "type"):
                if message.type == "human":
                    prompt_parts.append(f"Human: {content}")
                elif message.type == "ai":
                    prompt_parts.append(f"Assistant: {content}")
                elif message.type == "system":
                    prompt_parts.append(f"System: {content}")
                else:
                    prompt_parts.append(str(content))
            else:
                prompt_parts.append(str(content))

        return "\n\n".join(prompt_parts)

    def _extract_response_text(self, response: Any) -> str:
        """
        Safely extract text from Gemini response, handling safety blocks.

        Args:
            response: Gemini API response

        Returns:
            Response text or appropriate error message

        Raises:
            LLMProviderError: If response cannot be processed
        """
        try:
            # Check if response was blocked for safety
            if hasattr(response, "candidates") and response.candidates:
                candidate = response.candidates[0]

                # Check finish reason
                if hasattr(candidate, "finish_reason"):
                    finish_reason = candidate.finish_reason

                    # Map finish reasons to user-friendly messages
                    if finish_reason == 1:  # STOP - normal completion
                        try:
                            return response.text
                        except ValueError:
                            return self._extract_partial_content(candidate)
                    elif finish_reason == 2:  # MAX_TOKENS
                        # Try to get partial content for truncated responses
                        partial_content = self._extract_partial_content(candidate)
                        if partial_content:
                            return f"{partial_content}\n\n[Note: Response was truncated due to length limits. Try with shorter input.]"
                        else:
                            return "Response was truncated due to length limits. Please try with shorter input."
                    elif finish_reason == 3:  # SAFETY
                        safety_msg = "Response was blocked due to safety filters. This may happen with certain business terms or content. Please try rephrasing your input or contact support."

                        # Try to get partial content if available
                        partial_content = self._extract_partial_content(candidate)
                        if partial_content:
                            return f"{partial_content}\n\n[Note: Response was partially blocked by safety filters]"

                        raise LLMProviderError(safety_msg)
                    elif finish_reason == 4:  # RECITATION
                        partial_content = self._extract_partial_content(candidate)
                        if partial_content:
                            return f"{partial_content}\n\n[Note: Response contained potential recitation.]"
                        else:
                            return "Response contained potential recitation. Please try with different input."
                    else:
                        partial_content = self._extract_partial_content(candidate)
                        if partial_content:
                            return f"{partial_content}\n\n[Note: Response ended with reason: {finish_reason}]"
                        else:
                            return f"Response ended with reason: {finish_reason}"

            # Fallback to direct text access
            return response.text

        except ValueError as e:
            if "finish_reason" in str(e) and "SAFETY" in str(e):
                raise LLMProviderError(
                    "Response was blocked by Gemini's safety filters. This can happen with business content. "
                    "Try simplifying your job description or resume content, or contact support for assistance."
                )
            else:
                raise LLMProviderError(f"Failed to extract response text: {e}")
        except Exception as e:
            raise LLMProviderError(f"Unexpected error processing response: {e}")

    def _extract_partial_content(self, candidate: Any) -> str:
        """
        Safely extract partial content from a candidate response.

        Args:
            candidate: Gemini response candidate

        Returns:
            Partial text content or empty string if not available
        """
        try:
            if (
                hasattr(candidate, "content")
                and candidate.content
                and hasattr(candidate.content, "parts")
            ):
                parts = candidate.content.parts
                if parts and hasattr(parts[0], "text"):
                    partial_text = parts[0].text
                    if partial_text and partial_text.strip():
                        return partial_text.strip()
            return ""
        except Exception:
            return ""
