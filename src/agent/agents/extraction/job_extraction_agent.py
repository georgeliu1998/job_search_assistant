"""
Provides the nodes for the job evaluation workflow graph.

These functions act as the "specialist" agents for extraction and evaluation,
each performing a single, well-defined task within the larger workflow.
"""

from src.agent.tools.extraction.schema_extraction_tool import (
    extract_job_posting,
    validate_extraction_result,
)
from src.agent.workflows.job_evaluation.states import JobEvaluationWorkflowState
from src.core.job_evaluation import evaluate_job_against_criteria
from src.utils.logging import get_logger

logger = get_logger(__name__)


def extraction_node(state: JobEvaluationWorkflowState) -> dict:
    """
    Extracts structured information from the job posting text.

    This is the primary LLM-calling node in the workflow.
    """
    logger.info("Node: extract_job_info")
    job_text = state["job_posting_text"]

    try:
        extracted_data = extract_job_posting.invoke({"job_text": job_text})
        logger.info(f"Successfully extracted job information: {extracted_data}")

        return {
            "extracted_info": extracted_data,
            "messages": [
                (
                    "extract_node",
                    (
                        extracted_data
                        if isinstance(extracted_data, dict)
                        else str(extracted_data)
                    ),
                )
            ],
        }
    except Exception as e:
        logger.error(f"Failed to extract job information: {e}")
        return {
            "extracted_info": None,
            "messages": [("extract_node", f"Extraction failed: {str(e)}")],
        }


def validation_node(state: JobEvaluationWorkflowState) -> dict:
    """
    Validates the data extracted by the extraction_node.
    """
    logger.info("Node: validate_extraction")

    if not state.get("extracted_info"):
        logger.warning("No extracted info to validate")
        return {
            "is_valid": False,
            "messages": [("validation_node", "No extracted info to validate")],
        }

    try:
        is_valid = validate_extraction_result.invoke(
            {"extraction_result": state["extracted_info"], "schema_name": "job_posting"}
        )
        logger.info(f"Validation result: {is_valid}")

        return {
            "is_valid": is_valid,
            "messages": [("validation_node", f"is_valid: {is_valid}")],
        }
    except Exception as e:
        logger.error(f"Failed to validate extraction: {e}")
        return {
            "is_valid": False,
            "messages": [("validation_node", f"Validation failed: {str(e)}")],
        }


def evaluation_node(state: JobEvaluationWorkflowState) -> dict:
    """
    Evaluates the extracted job information against predefined criteria.
    """
    logger.info("Node: evaluate_job")

    if not state.get("extracted_info"):
        logger.warning("Skipping evaluation due to missing extraction.")
        return {
            "evaluation_result": None,
            "messages": [("evaluation_node", "Skipped due to missing extraction")],
        }

    try:
        # Convert extracted info to dict format for the core evaluation function
        extracted_info = state["extracted_info"]
        if hasattr(extracted_info, "model_dump"):
            extracted_info_dict = extracted_info.model_dump()
        elif isinstance(extracted_info, dict):
            extracted_info_dict = extracted_info
        else:
            # Handle the case where extracted_info might be a different format
            extracted_info_dict = dict(extracted_info) if extracted_info else {}

        evaluation_result = evaluate_job_against_criteria(extracted_info_dict)
        logger.info(f"Job evaluation completed: {evaluation_result}")

        return {
            "evaluation_result": evaluation_result,
            "messages": [
                (
                    "evaluation_node",
                    f"Evaluation completed with {len(evaluation_result)} criteria",
                )
            ],
        }
    except Exception as e:
        logger.error(f"Failed to evaluate job: {e}")
        return {
            "evaluation_result": None,
            "messages": [("evaluation_node", f"Evaluation failed: {str(e)}")],
        }
