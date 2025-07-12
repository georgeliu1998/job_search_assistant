"""
Simplified job evaluation workflow using LangGraph.

This workflow extracts job information and evaluates it against criteria
in a simple, direct manner without unnecessary abstractions.
"""

from typing import Any, Dict, Optional

from langgraph.graph import END, START, StateGraph

from src.agent.tools.extraction.schema_extraction_tool import (
    extract_job_posting,
    validate_extraction_result,
)
from src.agent.workflows.job_evaluation.states import JobEvaluationState
from src.core.job_evaluation import evaluate_job_against_criteria
from src.llm.langfuse_handler import get_langfuse_handler
from src.utils.logging import get_logger

logger = get_logger(__name__)


def extract_job_info(state: JobEvaluationState) -> Dict[str, Any]:
    """Extract structured information from job posting text."""
    logger.info("Extracting job information")

    job_text = state["job_posting_text"]

    try:
        # Extract structured information
        extracted_info = extract_job_posting(job_text)

        # Validate extraction
        is_valid = validate_extraction_result(extracted_info, "job_posting")

        if not is_valid:
            logger.warning("Extraction validation failed")
            return {
                "extracted_info": None,
                "recommendation": "ERROR",
                "reasoning": "Failed to extract meaningful job information",
            }

        logger.info("Job information extracted successfully")
        return {"extracted_info": extracted_info}

    except Exception as e:
        logger.error(f"Extraction failed: {e}")
        return {
            "extracted_info": None,
            "recommendation": "ERROR",
            "reasoning": f"Extraction failed: {str(e)}",
        }


def evaluate_job(state: JobEvaluationState) -> Dict[str, Any]:
    """Evaluate extracted job information against criteria."""
    logger.info("Evaluating job against criteria")

    extracted_info = state["extracted_info"]

    # Skip evaluation if extraction failed
    if not extracted_info:
        logger.warning("No extracted info to evaluate")
        return {
            "evaluation_result": None,
            "recommendation": "ERROR",
            "reasoning": "No job information available for evaluation",
        }

    try:
        # Evaluate against criteria
        evaluation_result = evaluate_job_against_criteria(extracted_info)

        # Generate recommendation
        recommendation, reasoning = _generate_recommendation(evaluation_result)

        logger.info(f"Job evaluation completed: {recommendation}")
        return {
            "evaluation_result": evaluation_result,
            "recommendation": recommendation,
            "reasoning": reasoning,
        }

    except Exception as e:
        logger.error(f"Evaluation failed: {e}")
        return {
            "evaluation_result": None,
            "recommendation": "ERROR",
            "reasoning": f"Evaluation failed: {str(e)}",
        }


def _generate_recommendation(evaluation_result: Dict[str, Any]) -> tuple[str, str]:
    """Generate recommendation and reasoning from evaluation results."""
    if not evaluation_result or "error" in evaluation_result:
        return "ERROR", "Unable to evaluate job posting"

    # Count passed criteria
    passed_criteria = []
    failed_criteria = []

    for criterion, result in evaluation_result.items():
        if isinstance(result, dict) and "pass" in result:
            if result["pass"]:
                passed_criteria.append(f"{criterion}: {result['reason']}")
            else:
                failed_criteria.append(f"{criterion}: {result['reason']}")

    # Generate recommendation based on results
    if not failed_criteria:
        recommendation = "APPLY"
        reasoning = f"All criteria passed: {'; '.join(passed_criteria)}"
    else:
        recommendation = "DO_NOT_APPLY"
        if failed_criteria:
            reasoning = f"Failed criteria: {'; '.join(failed_criteria)}"
        else:
            reasoning = "Job does not meet evaluation criteria"

    return recommendation, reasoning


def create_workflow() -> StateGraph:
    """Create the job evaluation workflow."""
    workflow = StateGraph(JobEvaluationState)

    # Add nodes
    workflow.add_node("extract", extract_job_info)
    workflow.add_node("evaluate", evaluate_job)

    # Add edges
    workflow.add_edge(START, "extract")
    workflow.add_edge("extract", "evaluate")
    workflow.add_edge("evaluate", END)

    return workflow


def evaluate_job_posting(job_posting_text: str) -> Dict[str, Any]:
    """
    Main entry point for job evaluation.

    Args:
        job_posting_text: The raw job posting text to evaluate

    Returns:
        Dict with evaluation results in UI-expected format
    """
    logger.info("Starting job evaluation")

    if not job_posting_text or not job_posting_text.strip():
        logger.warning("Empty job posting text")
        return {
            "recommendation": "ERROR",
            "reasoning": "Job posting text was empty",
            "extracted_info": {},
            "evaluation_result": {},
        }

    try:
        # Create and run workflow
        workflow = create_workflow()
        app = workflow.compile()

        # Initial state
        initial_state = JobEvaluationState(
            job_posting_text=job_posting_text,
            extracted_info=None,
            evaluation_result=None,
            recommendation=None,
            reasoning=None,
        )

        # Configure with Langfuse if available
        langfuse_handler = get_langfuse_handler()
        config = {"callbacks": [langfuse_handler]} if langfuse_handler else {}

        # Run workflow
        final_state = app.invoke(initial_state, config=config)

        # Return results in expected format
        return {
            "recommendation": final_state.get("recommendation", "ERROR"),
            "reasoning": final_state.get("reasoning", "Unknown error"),
            "extracted_info": final_state.get("extracted_info", {}),
            "evaluation_result": final_state.get("evaluation_result", {}),
        }

    except Exception as e:
        logger.error(f"Job evaluation failed: {e}")
        return {
            "recommendation": "ERROR",
            "reasoning": f"Evaluation failed: {str(e)}",
            "extracted_info": {},
            "evaluation_result": {},
        }
