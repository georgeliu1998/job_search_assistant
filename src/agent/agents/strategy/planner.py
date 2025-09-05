"""Planner Agent for multi-agent interview preparation workflow.

The Planner Agent analyzes input context and creates intelligent execution strategies
for other specialized agents in the workflow.
"""

import logging
from typing import Any, Dict

from langchain_core.messages import HumanMessage, SystemMessage

from src.agent.prompts.interview.planner import (
    PLANNER_SYSTEM_PROMPT,
    PLANNER_USER_PROMPT_TEMPLATE,
)
from src.agent.workflows.interview_prep.multi_agent_states import (
    AgentPlan,
    AgentStatus,
    MultiAgentInterviewPrepState,
    WorkflowPhase,
)
from src.config import config
from src.llm.common.factory import get_llm_client_by_profile_name
from src.llm.observability import langfuse_manager
from src.models.agent_plans import ExecutionPlan

logger = logging.getLogger(__name__)


def planner_agent(state: MultiAgentInterviewPrepState) -> Dict[str, Any]:
    """
    Planner Agent that analyzes context and creates execution strategies.

    This agent serves as the "brain" of the multi-agent system, analyzing
    all available context to create intelligent strategies for other agents.

    Args:
        state: Current multi-agent workflow state

    Returns:
        Dict containing execution plan and updated state
    """
    logger.info("Planner Agent: Starting context analysis and strategy creation")

    # Skip if previous error
    if state.has_errors:
        logger.info("Planner Agent: Skipping due to previous errors")
        return {}

    try:
        # Update agent status
        state.set_agent_status("planner", AgentStatus.IN_PROGRESS)
        state.current_agent = "planner"
        state.current_phase = WorkflowPhase.PLANNING

        # Get LLM client for planning
        llm_client = get_llm_client_by_profile_name(
            config.agents.interview_question_generation  # Reuse existing config
        )

        # Create structured LLM with ExecutionPlan schema
        structured_llm = llm_client._get_client().with_structured_output(ExecutionPlan)

        # Prepare context for planning
        resume_context = _prepare_resume_context(state)
        existing_research = _prepare_existing_research_context(state)
        question_mix_str = _format_question_mix(state.interview_details.question_mix)

        # Create prompts
        system_message = SystemMessage(content=PLANNER_SYSTEM_PROMPT)
        user_message = HumanMessage(
            content=PLANNER_USER_PROMPT_TEMPLATE.format(
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
        )

        messages = [system_message, user_message]

        # Get tracing config
        config_dict = langfuse_manager.get_config()

        # Generate structured execution plan
        logger.info("Planner Agent: Generating structured execution plan")
        execution_plan = structured_llm.invoke(messages, config=config_dict)

        logger.info("Planner Agent: Successfully created structured execution plan")
        logger.debug(
            f"Execution plan research queries: {execution_plan.research_strategy.primary_queries}"
        )

        # Update state with structured plan
        state.set_agent_status("planner", AgentStatus.COMPLETED)
        state.execution_plan = execution_plan

        # Set individual strategies for agents (convert to dict for compatibility)
        state.research_strategy = execution_plan.research_strategy.model_dump()
        state.question_strategy = execution_plan.question_strategy.model_dump()
        state.answer_strategy = execution_plan.answer_strategy.model_dump()
        state.compilation_strategy = execution_plan.compilation_strategy.model_dump()

        logger.info("Planner Agent: Context analysis and strategy creation completed")

        return {
            "execution_plan": execution_plan,
            "research_strategy": state.research_strategy,
            "question_strategy": state.question_strategy,
            "answer_strategy": state.answer_strategy,
            "compilation_strategy": state.compilation_strategy,
            "agent_status": state.agent_status,
            "current_phase": WorkflowPhase.RESEARCH,  # Move to next phase
        }

    except Exception as e:
        logger.error(f"Planner Agent failed: {e}", exc_info=True)
        state.set_agent_error("planner", f"Planning failed: {str(e)}")
        return {
            "error": f"Planner Agent failed: {str(e)}",
            "agent_status": state.agent_status,
        }


def _prepare_resume_context(state: MultiAgentInterviewPrepState) -> str:
    """Prepare resume context for planning analysis."""
    if state.pii_redaction_result:
        return f"Redacted Resume:\n{state.pii_redaction_result.redacted_resume_text}"
    return f"Original Resume:\n{state.resume_text}"


def _prepare_existing_research_context(state: MultiAgentInterviewPrepState) -> str:
    """Prepare existing research context for planning."""
    if not state.research_results:
        return "No existing research available."

    research_snippets = []
    for citation in state.research_results[:3]:  # Top 3 for context
        if citation.is_accessible:
            research_snippets.append(f"- {citation.title}: {citation.content_snippet}")

    return (
        "Existing Research:\n" + "\n".join(research_snippets)
        if research_snippets
        else "No accessible research available."
    )


def _format_question_mix(question_mix: Dict[str, int]) -> str:
    """Format question mix for display in prompt."""
    return ", ".join(
        [
            f"{category.replace('_', ' ').title()}: {count}"
            for category, count in question_mix.items()
            if count > 0
        ]
    )
