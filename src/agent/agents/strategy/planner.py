"""Planner Agent for multi-agent interview preparation workflow.

The Planner Agent analyzes input context and creates intelligent execution strategies
for other specialized agents in the workflow.
"""

from typing import Any, Dict

from src.agent.agents.common.base import BaseAgent
from src.agent.prompts.interview.planner import (
    PLANNER_SYSTEM_PROMPT,
    PLANNER_USER_PROMPT_TEMPLATE,
)
from src.agent.workflows.interview_prep.multi_agent_states import (
    MultiAgentInterviewPrepState,
    WorkflowPhase,
)
from src.config import config
from src.models.agent_plans import ExecutionPlan


class PlannerAgent(BaseAgent):
    """Planner Agent that creates execution strategies for other agents."""

    def __init__(self):
        """Initialize the Planner Agent."""
        super().__init__(name="planner", llm_profile=config.agents.interview_planner)

    def check_prerequisites(self, state: MultiAgentInterviewPrepState) -> bool:
        """Check if planner prerequisites are met.

        Args:
            state: Current multi-agent workflow state

        Returns:
            True if job description and interview details are present
        """
        return bool(state.job_description and state.interview_details)

    def execute(self, state: MultiAgentInterviewPrepState) -> Dict[str, Any]:
        """Create execution plan for all agents.

        Args:
            state: Current multi-agent workflow state

        Returns:
            Dict containing execution plan and strategies
        """
        state.current_phase = WorkflowPhase.PLANNING

        # Prepare context for planning
        resume_context = self._prepare_resume_context(state)
        existing_research = self._prepare_existing_research_context(state)
        question_mix_str = self._format_question_mix(
            state.interview_details.question_mix
        )

        # Build the planning prompt
        user_prompt = PLANNER_USER_PROMPT_TEMPLATE.format(
            job_description=state.job_description,
            company=state.interview_details.company or "Not specified",
            role=state.interview_details.role or "Not specified",
            interview_type=state.interview_details.type,
            interview_format=state.interview_details.format,
            duration=state.interview_details.duration,
            question_mix=question_mix_str,
            resume_context=resume_context,
            existing_research=existing_research,
        )

        # Generate structured execution plan
        self.logger.info("Generating structured execution plan")
        execution_plan = self.invoke_llm(
            system_prompt=PLANNER_SYSTEM_PROMPT,
            user_prompt=user_prompt,
            structured_output=ExecutionPlan,
        )

        self.logger.info("Successfully created structured execution plan")

        # Validate execution plan structure
        if not execution_plan:
            raise ValueError("Generated execution plan is None")

        # Validate required strategy fields
        missing_strategies = []
        if not execution_plan.research_strategy:
            missing_strategies.append("research_strategy")
        if not execution_plan.question_strategy:
            missing_strategies.append("question_strategy")
        if not execution_plan.answer_strategy:
            missing_strategies.append("answer_strategy")
        if not execution_plan.compilation_strategy:
            missing_strategies.append("compilation_strategy")

        if missing_strategies:
            self.logger.error(
                f"Execution plan is missing required strategies: {missing_strategies}"
            )
            raise ValueError(
                f"Generated execution plan is incomplete. Missing strategies: {', '.join(missing_strategies)}"
            )

        # Safe logging with null checks
        if execution_plan.research_strategy and hasattr(
            execution_plan.research_strategy, "primary_queries"
        ):
            self.logger.debug(
                f"Execution plan research queries: {execution_plan.research_strategy.primary_queries}"
            )
        else:
            self.logger.warning(
                "Research strategy or primary_queries not available for logging"
            )

        # Update state with plan (convert to dict for consistency)
        state.execution_plan = execution_plan.model_dump()

        # Set individual strategies for agents (convert to dict for compatibility)
        state.research_strategy = execution_plan.research_strategy.model_dump()
        state.question_strategy = execution_plan.question_strategy.model_dump()
        state.answer_strategy = execution_plan.answer_strategy.model_dump()
        state.compilation_strategy = execution_plan.compilation_strategy.model_dump()

        self.logger.info("Context analysis and strategy creation completed")

        return {
            "execution_plan": state.execution_plan,  # Already converted to dict above
            "research_strategy": state.research_strategy,
            "question_strategy": state.question_strategy,
            "answer_strategy": state.answer_strategy,
            "compilation_strategy": state.compilation_strategy,
            "current_phase": WorkflowPhase.RESEARCH,  # Move to next phase
        }

    def _prepare_resume_context(self, state: MultiAgentInterviewPrepState) -> str:
        """Prepare resume context for planning analysis.

        Args:
            state: Current multi-agent workflow state

        Returns:
            Formatted resume context string
        """
        if state.pii_redaction_result:
            return (
                f"Redacted Resume:\n{state.pii_redaction_result.redacted_resume_text}"
            )
        return f"Original Resume:\n{state.resume_text}"

    def _prepare_existing_research_context(
        self, state: MultiAgentInterviewPrepState
    ) -> str:
        """Prepare existing research context for planning.

        Args:
            state: Current multi-agent workflow state

        Returns:
            Formatted research context string
        """
        if not state.research_results:
            return "No existing research available."

        research_snippets = []
        for citation in state.research_results[:3]:  # Top 3 for context
            if citation.is_accessible:
                research_snippets.append(
                    f"- {citation.title}: {citation.content_snippet}"
                )

        return (
            "Existing Research:\n" + "\n".join(research_snippets)
            if research_snippets
            else "No accessible research available."
        )

    def _format_question_mix(self, question_mix: Dict[str, int]) -> str:
        """Format question mix for display in prompt.

        Args:
            question_mix: Dictionary of question categories and counts

        Returns:
            Formatted question mix string
        """
        return ", ".join(
            [
                f"{category.replace('_', ' ').title()}: {count}"
                for category, count in question_mix.items()
                if count > 0
            ]
        )


# Create singleton instance for backward compatibility
planner_agent_instance = PlannerAgent()


def planner_agent(state: MultiAgentInterviewPrepState) -> Dict[str, Any]:
    """
    Backward compatible function interface for planner agent.

    Args:
        state: Current multi-agent workflow state

    Returns:
        Dict containing execution plan and updated state
    """
    return planner_agent_instance(state)
