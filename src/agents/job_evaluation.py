"""
Main entry point for the job evaluation agent.

This module provides a clean interface to the underlying job evaluation
workflow, handling input and formatting the output as needed.
"""

from typing import Any, Dict

from src.agent.workflows.job_evaluation.workflow import (
    JobEvaluationWorkflow,
    generate_recommendation_from_results,
)
from src.llm.langfuse_handler import get_langfuse_handler
from src.utils.logging import get_logger

logger = get_logger(__name__)


def evaluate_job_posting(job_posting_text: str) -> Dict[str, Any]:
    """
    Evaluates a job posting using the graph-based agent workflow.

    Args:
        job_posting_text: The raw job posting text to evaluate.

    Returns:
        A dictionary with evaluation results in the format expected by the UI.
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
