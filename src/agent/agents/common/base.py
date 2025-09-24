"""Base agent abstraction for multi-agent workflows."""

import logging
from abc import ABC, abstractmethod
from typing import Any, Dict, Optional, Type

from langchain_core.messages import HumanMessage, SystemMessage
from pydantic import BaseModel

from src.agent.workflows.interview_prep.multi_agent_states import (
    AgentStatus,
    MultiAgentInterviewPrepState,
)
from src.config import config
from src.llm.common.factory import get_llm_client_by_profile_name
from src.llm.observability import langfuse_manager


class BaseAgent(ABC):
    """Base class for all agents in the multi-agent system."""

    def __init__(self, name: str, llm_profile: Optional[str] = None):
        """Initialize the base agent.

        Args:
            name: Name of the agent
            llm_profile: LLM profile to use (defaults to interview_question_generation)
        """
        self.name = name
        self.logger = logging.getLogger(f"{__name__}.{name}")
        self.llm_profile = llm_profile or config.agents.interview_question_generation

    def __call__(self, state: MultiAgentInterviewPrepState) -> Dict[str, Any]:
        """Execute the agent with automatic error handling and state management.

        Args:
            state: Current multi-agent workflow state

        Returns:
            Dict containing agent results and updated state
        """
        self.logger.info(f"{self.name} Agent: Starting execution")

        # Check for previous errors
        if state.has_errors:
            self.logger.info(f"{self.name} Agent: Skipping due to previous errors")
            return {}

        # Check prerequisites
        if not self.check_prerequisites(state):
            self.logger.warning(f"{self.name} Agent: Prerequisites not met")
            return self.handle_missing_prerequisites(state)

        try:
            # Update agent status
            state.set_agent_status(self.name, AgentStatus.IN_PROGRESS)
            state.current_agent = self.name

            # Execute agent logic
            result = self.execute(state)

            # Mark as completed
            state.set_agent_status(self.name, AgentStatus.COMPLETED)

            # Add agent status to result
            result["agent_status"] = state.agent_status

            self.logger.info(f"{self.name} Agent: Execution completed successfully")
            return result

        except Exception as e:
            self.logger.error(f"{self.name} Agent failed: {e}", exc_info=True)
            state.set_agent_error(self.name, f"{self.name} failed: {str(e)}")

            # Try fallback if available
            if self.has_fallback():
                self.logger.info(f"{self.name} Agent: Attempting fallback")
                return self.execute_fallback(state)

            return {
                "error": f"{self.name} Agent failed: {str(e)}",
                "agent_status": state.agent_status,
            }

    @abstractmethod
    def execute(self, state: MultiAgentInterviewPrepState) -> Dict[str, Any]:
        """Execute the main agent logic. Must be implemented by subclasses.

        Args:
            state: Current multi-agent workflow state

        Returns:
            Dict containing agent results
        """
        pass

    @abstractmethod
    def check_prerequisites(self, state: MultiAgentInterviewPrepState) -> bool:
        """Check if agent prerequisites are met.

        Args:
            state: Current multi-agent workflow state

        Returns:
            True if prerequisites are met, False otherwise
        """
        pass

    def handle_missing_prerequisites(
        self, state: MultiAgentInterviewPrepState
    ) -> Dict[str, Any]:
        """Handle missing prerequisites. Override for custom behavior.

        Args:
            state: Current multi-agent workflow state

        Returns:
            Dict containing error or alternative result
        """
        return {"error": f"{self.name}: Prerequisites not met"}

    def has_fallback(self) -> bool:
        """Check if agent has fallback. Override to enable fallback.

        Returns:
            True if fallback is available, False otherwise
        """
        return False

    def execute_fallback(self, state: MultiAgentInterviewPrepState) -> Dict[str, Any]:
        """Execute fallback logic. Override to implement fallback.

        Args:
            state: Current multi-agent workflow state

        Returns:
            Dict containing fallback results
        """
        return {"error": f"{self.name}: No fallback available"}

    def get_llm_client(self):
        """Get configured LLM client for this agent.

        Returns:
            Configured LLM client
        """
        return get_llm_client_by_profile_name(self.llm_profile)

    def invoke_llm(
        self,
        system_prompt: str,
        user_prompt: str,
        structured_output: Optional[Type[BaseModel]] = None,
    ) -> Any:
        """Helper to invoke LLM with proper configuration.

        Args:
            system_prompt: System prompt for the LLM
            user_prompt: User prompt for the LLM
            structured_output: Optional Pydantic model for structured output

        Returns:
            LLM response (structured or text)
        """
        llm_client = self.get_llm_client()

        if structured_output:
            llm_client = llm_client._get_client().with_structured_output(
                structured_output
            )

        messages = [
            SystemMessage(content=system_prompt),
            HumanMessage(content=user_prompt),
        ]

        config_dict = langfuse_manager.get_config()
        return llm_client.invoke(messages, config=config_dict)

    def prepare_resume_context(
        self, state: MultiAgentInterviewPrepState, max_length: Optional[int] = None
    ) -> str:
        """Prepare resume context from state.

        Args:
            state: Current multi-agent workflow state
            max_length: Optional maximum length for the context

        Returns:
            Formatted resume context string
        """
        if state.pii_redaction_result:
            context = state.pii_redaction_result.redacted_resume_text
        else:
            context = state.resume_text

        if max_length and len(context) > max_length:
            context = context[:max_length]

        return context
