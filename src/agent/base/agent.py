"""
Base agent class for LangGraph agents.

This module provides a minimal base class for agents that use LangGraph's
tool calling capabilities, focusing on common patterns without over-engineering.
"""

from abc import ABC, abstractmethod
from typing import Any, Dict, List, Optional

from langchain_core.tools import BaseTool
from langgraph.prebuilt import create_react_agent

from src.config import config
from src.llm.clients.anthropic import AnthropicClient
from src.utils.logging import get_logger

logger = get_logger(__name__)


class BaseAgent(ABC):
    """
    Minimal base class for LangGraph agents with tool calling.

    This class provides common patterns for agents that use tools,
    while keeping the implementation simple and focused.
    """

    def __init__(self, tools: List[BaseTool]):
        """
        Initialize the base agent.

        Args:
            tools: List of tools available to this agent
        """
        self.tools = tools
        self.agent = None
        self._client = None

    def _get_client(self) -> AnthropicClient:
        """Get or create the LLM client."""
        if self._client is None:
            # Subclasses can override this to use different profiles
            profile_name = self._get_llm_profile_name()
            profile = config.get_llm_profile(profile_name)
            self._client = AnthropicClient(profile)
            logger.debug(f"Initialized LLM client with profile: {profile_name}")
        return self._client

    def _get_llm_profile_name(self) -> str:
        """
        Get the LLM profile name for this agent.

        Subclasses should override this to specify their profile.
        """
        return "default"

    def _get_model_with_tools(self):
        """Get the model with tools bound for tool calling."""
        client = self._get_client()
        model = client._get_client()

        # Bind tools to the model for tool calling
        if self.tools:
            model = model.bind_tools(self.tools)
            logger.debug(f"Bound {len(self.tools)} tools to model")

        return model

    def _create_agent(self):
        """Create the LangGraph agent with tool calling capabilities."""
        if self.agent is None:
            model = self._get_model_with_tools()

            # Create the react agent with tools
            self.agent = create_react_agent(model=model, tools=self.tools)
            logger.debug(f"Created react agent with {len(self.tools)} tools")

        return self.agent

    @abstractmethod
    def invoke(self, input_data: Dict[str, Any]) -> Dict[str, Any]:
        """
        Standard interface for agent invocation.

        Args:
            input_data: Input data for the agent

        Returns:
            Dict containing the agent's response
        """
        pass

    def get_available_tools(self) -> List[str]:
        """Get list of available tool names."""
        return [tool.name for tool in self.tools]
