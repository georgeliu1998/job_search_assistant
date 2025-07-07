"""
Defines the job evaluation workflow using a StateGraph.
"""

from typing import Any, Optional

from langgraph.graph import END, StateGraph

from src.agent.agents.extraction.job_extraction_agent import (
    evaluation_node,
    extraction_node,
    validation_node,
)
from src.agent.workflows.job_evaluation.states import JobEvaluationWorkflowState
from src.utils.logging import get_logger

logger = get_logger(__name__)


class JobEvaluationWorkflow:
    """
    Manages the job evaluation process as a compiled LangGraph workflow.
    """

    def __init__(self):
        self.workflow = self._build_graph()
        self.app = self.workflow.compile()

    def _build_graph(self) -> StateGraph:
        """Builds the StateGraph for the job evaluation workflow."""
        workflow = StateGraph(JobEvaluationWorkflowState)

        # Add nodes
        workflow.add_node("extract", extraction_node)
        workflow.add_node("validate", validation_node)
        workflow.add_node("evaluate", evaluation_node)

        # Define edges
        workflow.set_entry_point("extract")
        workflow.add_edge("extract", "validate")
        workflow.add_edge("validate", "evaluate")
        workflow.add_edge("evaluate", END)

        return workflow

    def run(
        self, job_posting_text: str, langfuse_handler: Optional[Any] = None
    ) -> dict:
        """
        Executes the job evaluation workflow.

        Args:
            job_posting_text: The raw job posting text.
            langfuse_handler: Optional Langfuse handler for tracing.

        Returns:
            The final state of the workflow.
        """
        logger.info("Starting JobEvaluationWorkflow run")
        initial_state = {
            "job_posting_text": job_posting_text,
            "extracted_info": None,
            "evaluation_result": None,
            "messages": [],
            "langfuse_handler": langfuse_handler,
            "workflow_version": "2.0",
            "extraction_duration": None,
            "evaluation_duration": None,
        }

        config = {}
        if langfuse_handler:
            config = {"callbacks": [langfuse_handler]}

        final_state = self.app.invoke(initial_state, config=config)
        logger.info("JobEvaluationWorkflow run completed")
        return final_state


# Backward compatibility functions for existing code
def generate_recommendation_from_results(
    evaluation_results: dict,
) -> tuple[str, str]:
    """
    Generate final recommendation and reasoning from evaluation results.

    This function maintains backward compatibility with existing code.

    Args:
        evaluation_results: Dictionary with evaluation results for each criteria

    Returns:
        tuple[str, str]: (recommendation, reasoning)
    """
    if not evaluation_results or "error" in evaluation_results:
        return "DO_NOT_APPLY", "Unable to evaluate job posting due to extraction errors"

    # Check if all criteria pass
    all_pass = all(
        result.get("pass", False)
        for result in evaluation_results.values()
        if isinstance(result, dict)
    )

    if all_pass:
        recommendation = "APPLY"
        reasoning = "All criteria met: " + "; ".join(
            [
                result["reason"]
                for result in evaluation_results.values()
                if isinstance(result, dict) and result.get("pass")
            ]
        )
    else:
        recommendation = "DO_NOT_APPLY"
        failed_reasons = [
            result["reason"]
            for result in evaluation_results.values()
            if isinstance(result, dict) and not result.get("pass")
        ]
        reasoning = "Failed criteria: " + "; ".join(failed_reasons)

    return recommendation, reasoning


def create_job_evaluation_workflow() -> JobEvaluationWorkflow:
    """
    Create a new job evaluation workflow instance.

    Returns:
        JobEvaluationWorkflow: New workflow instance
    """
    return JobEvaluationWorkflow()
