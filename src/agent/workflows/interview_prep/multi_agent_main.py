"""Multi-agent workflow for interview preparation.

This implements a sophisticated multi-agent system where specialized agents
work together to create personalized interview preparation guides.
"""

import logging
from typing import Any, Dict, Optional

from langgraph.graph import END, START, StateGraph

from src.agent.agents.content_generation import answer_agent, question_agent
from src.agent.agents.content_processing import editor_agent
from src.agent.agents.strategy import planner_agent, research_agent
from src.agent.workflows.interview_prep.main import (  # Reuse validation
    validate_and_redact_input,
)
from src.agent.workflows.interview_prep.multi_agent_states import (
    AgentStatus,
    MultiAgentInterviewPrepState,
    WorkflowPhase,
)
from src.llm.observability import langfuse_manager

logger = logging.getLogger(__name__)


def get_multi_agent_interview_prep_workflow() -> StateGraph:
    """Create the multi-agent interview preparation workflow."""
    workflow = StateGraph(MultiAgentInterviewPrepState)

    # Add all agents as nodes
    workflow.add_node("validate_and_redact", validate_and_redact_input)
    workflow.add_node("planner", planner_agent)
    workflow.add_node("research_agent", research_agent)
    workflow.add_node("question_agent", question_agent)
    workflow.add_node("answer_agent", answer_agent)
    workflow.add_node("editor_agent", editor_agent)

    # Add conditional routing logic
    workflow.add_edge(START, "validate_and_redact")
    workflow.add_edge("validate_and_redact", "planner")

    # Conditional routing from planner based on execution plan
    workflow.add_conditional_edges(
        "planner",
        route_after_planning,
        {
            "research": "research_agent",
            "questions": "question_agent",
            "answers": "answer_agent",
            "editor": "editor_agent",
            "end": END,
        },
    )

    # Conditional routing from research agent
    workflow.add_conditional_edges(
        "research_agent",
        route_after_research,
        {"questions": "question_agent", "end": END},
    )

    # Conditional routing from question agent
    workflow.add_conditional_edges(
        "question_agent",
        route_after_questions,
        {
            "answers": "answer_agent",
            "research": "research_agent",  # May need more research
            "end": END,
        },
    )

    # Conditional routing from answer agent
    workflow.add_conditional_edges(
        "answer_agent",
        route_after_answers,
        {
            "editor": "editor_agent",
            "questions": "question_agent",  # May need better questions
            "end": END,
        },
    )

    # Editor agent to END
    workflow.add_edge("editor_agent", END)

    return workflow.compile()


def route_after_planning(state: MultiAgentInterviewPrepState) -> str:
    """Route workflow after planner agent based on execution plan."""

    # Handle errors
    if state.has_errors:
        logger.error("Routing to END due to errors in planning")
        return "end"

    # Check if we have a valid execution plan
    if not state.execution_plan:
        logger.error("No execution plan created by planner")
        return "end"

    # Start with research phase
    logger.info("Routing to research agent after planning")
    return "research"


def route_after_research(state: MultiAgentInterviewPrepState) -> str:
    """Route workflow after research agent."""

    if state.has_errors:
        return "end"

    # Move to question generation
    logger.info("Routing to question agent after research")
    return "questions"


def route_after_questions(state: MultiAgentInterviewPrepState) -> str:
    """Route workflow after question agent."""

    if state.has_errors:
        return "end"

    # Check if we need more research based on question analysis
    if state.question_analysis and state.question_analysis.get(
        "needs_more_research", False
    ):
        logger.info("Question agent determined more research is needed")
        return "research"

    # Move to answer generation
    logger.info("Routing to answer agent after questions")
    return "answers"


def route_after_answers(state: MultiAgentInterviewPrepState) -> str:
    """Route workflow after answer agent."""

    if state.has_errors:
        return "end"

    # Check if we need better questions
    if state.answer_strategy and state.answer_strategy.get(
        "needs_better_questions", False
    ):
        logger.info("Answer agent determined better questions are needed")
        return "questions"

    # Move to final compilation
    logger.info("Routing to editor agent after answers")
    return "editor"


# Placeholder agent functions - will be implemented in subsequent phases

# Research agent now implemented - see agents/research.py


# Question agent now implemented - see agents/question.py


# Answer agent now implemented - see agents/answer.py


# All agents now implemented!


def run_multi_agent_interview_prep_workflow(
    initial_state: MultiAgentInterviewPrepState, config: Optional[Dict[str, Any]] = None
) -> Dict[str, Any]:
    """
    Run the multi-agent interview preparation workflow with enhanced tracing.

    Args:
        initial_state: Initial workflow state with multi-agent extensions
        config: Optional additional configuration for workflow execution

    Returns:
        Final workflow state as a dict
    """
    logger.info("Starting multi-agent interview preparation workflow")
    logger.debug(
        f"Initial state: company={initial_state.interview_details.company}, "
        f"role={initial_state.interview_details.role}, "
        f"phase={initial_state.current_phase}"
    )

    try:
        # Initialize agent statuses
        agent_names = [
            "planner",
            "research_agent",
            "question_agent",
            "answer_agent",
            "editor_agent",
        ]
        for agent_name in agent_names:
            initial_state.set_agent_status(agent_name, AgentStatus.PENDING)

        # Get workflow
        workflow = get_multi_agent_interview_prep_workflow()

        # Configure enhanced tracing for multi-agent workflow
        execution_config = langfuse_manager.get_workflow_config(config)
        execution_config.update(
            {
                "tags": ["multi-agent", "interview-prep"],
                "metadata": {
                    "workflow_type": "multi_agent_interview_prep",
                    "agent_count": len(agent_names),
                    "max_iterations": initial_state.max_iterations,
                },
            }
        )

        # Run workflow
        final_state_dict = workflow.invoke(initial_state, config=execution_config)

        # Enhanced logging for multi-agent workflow
        if final_state_dict.get("error") or final_state_dict.get("agent_errors"):
            failed_agents = final_state_dict.get("failed_agents", [])
            logger.error(
                f"Multi-agent workflow completed with errors. "
                f"Failed agents: {failed_agents}, "
                f"Main error: {final_state_dict.get('error')}"
            )
        else:
            completed_agents = final_state_dict.get("completed_agents", [])
            qa_count = len(final_state_dict.get("qa_pairs", []))
            has_guide = "interview_guide" in final_state_dict

            logger.info(
                f"Multi-agent interview preparation workflow completed successfully: "
                f"Completed agents: {completed_agents}, "
                f"{qa_count} QA pairs generated, "
                f"guide created: {has_guide}, "
                f"iterations: {final_state_dict.get('iteration_count', 0)}"
            )

        return final_state_dict

    except Exception as e:
        logger.error(
            f"Multi-agent interview preparation workflow failed: {e}", exc_info=True
        )
        return {
            "error": f"Multi-agent workflow execution failed: {str(e)}",
            "failed_agents": ["workflow_executor"],
        }
