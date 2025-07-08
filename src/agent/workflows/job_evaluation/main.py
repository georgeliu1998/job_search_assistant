"""
Defines the job evaluation workflow using a StateGraph.

This module provides the complete job evaluation workflow implementation,
including the public API function that serves as the main entry point.
"""

from typing import Any, Dict, Optional

from langgraph.graph import END, StateGraph

from src.agent.workflows.job_evaluation.states import JobEvaluationWorkflowState
from src.llm.langfuse_handler import get_langfuse_handler
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
        # Lazy import to avoid circular imports
        from src.agent.agents.extraction.job_extraction_agent import (
            evaluation_node,
            extraction_node,
            validation_node,
        )

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


def generate_recommendation_from_results(
    evaluation_results: dict,
) -> tuple[str, str]:
    """
    Generate final recommendation and reasoning from evaluation results.

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


def evaluate_job_posting(job_posting_text: str) -> Dict[str, Any]:
    """
    Evaluates a job posting using the graph-based agent workflow.

    This is the main public API for the job evaluation system. It provides
    a clean interface to the underlying LangGraph workflow system.

    Args:
        job_posting_text: The raw job posting text to evaluate.

    Returns:
        A dictionary with evaluation results in the format expected by the UI:
        - recommendation: "APPLY", "DO_NOT_APPLY", or "ERROR"
        - reasoning: Human-readable explanation of the recommendation
        - extracted_info: Dictionary with structured job information
        - evaluation_result: Dictionary with detailed evaluation criteria results
    """
    logger.info("Starting job evaluation with graph-based workflow.")

    if not job_posting_text or not job_posting_text.strip():
        logger.warning("Job posting text is empty.")
        return {
            "recommendation": "ERROR",
            "reasoning": "Job posting text was empty.",
            "extracted_info": {},
            "evaluation_result": {},
        }

    langfuse_handler = get_langfuse_handler()

    try:
        workflow = JobEvaluationWorkflow()
        final_state = workflow.run(job_posting_text, langfuse_handler)

        result = final_state.get("evaluation_result")
        if not result:
            logger.error("Workflow completed but no evaluation result was generated.")
            return {
                "recommendation": "ERROR",
                "reasoning": "Workflow failed to generate an evaluation result.",
                "extracted_info": final_state.get("extracted_info", {}),
                "evaluation_result": {},
            }

        recommendation, reasoning = generate_recommendation_from_results(result)

        # Convert extracted_info to dictionary format for UI compatibility
        extracted_info_dict = {}
        extracted_info = final_state.get("extracted_info")
        if extracted_info:
            if hasattr(extracted_info, "model_dump"):
                extracted_info_dict = extracted_info.model_dump()
            elif isinstance(extracted_info, dict):
                extracted_info_dict = extracted_info
            else:
                extracted_info_dict = dict(extracted_info) if extracted_info else {}

        logger.info(f"Job evaluation completed with recommendation: {recommendation}")

        return {
            "recommendation": recommendation,
            "reasoning": reasoning,
            "extracted_info": extracted_info_dict,
            "evaluation_result": result,
        }

    except Exception as e:
        logger.error(f"Job evaluation workflow failed: {e}", exc_info=True)
        return {
            "recommendation": "ERROR",
            "reasoning": f"An unexpected error occurred during the workflow: {e}",
            "extracted_info": {},
            "evaluation_result": {},
        }
