"""
Job evaluation workflow using LangGraph.

This workflow provides a complete end-to-end job evaluation process
with input validation, extraction, evaluation, and output formatting.
"""

from typing import Any, Dict, Optional

from langgraph.graph import END, START, StateGraph

from src.agent.tools.extraction.schema_extraction_tool import (
    extract_job_posting,
    validate_extraction_result,
)
from src.agent.workflows.job_evaluation.states import JobEvaluationState
from src.core.job_evaluation import (
    evaluate_job_against_criteria,
    generate_recommendation_from_evaluation,
)
from src.llm.langfuse_handler import get_langfuse_handler
from src.utils.logging import get_logger

logger = get_logger(__name__)


def validate_input(state: JobEvaluationState) -> Dict[str, Any]:
    """Validate job posting input and handle empty/invalid inputs."""
    logger.info("Validating job posting input")

    job_text = state.job_posting_text

    if not job_text or not job_text.strip():
        logger.warning("Empty job posting text provided")
        return {
            "recommendation": "ERROR",
            "reasoning": "Job posting text was empty",
            "extracted_info": {},
            "evaluation_result": {},
        }

    logger.info("Job posting input validation passed")
    return {}


def extract_job_info(state: JobEvaluationState) -> Dict[str, Any]:
    """Extract structured information from job posting text."""
    logger.info("Extracting job information")

    # Skip extraction if validation failed
    if state.recommendation == "ERROR":
        logger.info("Skipping extraction due to validation error")
        return {}

    job_text = state.job_posting_text

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

    # Skip evaluation if previous steps failed
    if state.recommendation == "ERROR":
        logger.info("Skipping evaluation due to previous error")
        return {}

    extracted_info = state.extracted_info

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

        logger.info("Job evaluation completed successfully")
        return {"evaluation_result": evaluation_result}

    except Exception as e:
        logger.error(f"Evaluation failed: {e}")
        return {
            "evaluation_result": None,
            "recommendation": "ERROR",
            "reasoning": f"Evaluation failed: {str(e)}",
        }


def generate_recommendation(state: JobEvaluationState) -> Dict[str, Any]:
    """Generate recommendation based on evaluation results."""
    logger.info("Generating recommendation")

    # Skip recommendation if previous steps failed
    if state.recommendation == "ERROR":
        logger.info("Skipping recommendation due to previous error")
        return {}

    evaluation_result = state.evaluation_result

    # Skip recommendation if evaluation failed
    if not evaluation_result:
        logger.warning("No evaluation result to generate recommendation from")
        return {
            "recommendation": "ERROR",
            "reasoning": "No evaluation result available for recommendation",
        }

    try:
        # Generate recommendation
        recommendation, reasoning = generate_recommendation_from_evaluation(
            evaluation_result
        )

        logger.info(f"Recommendation generated: {recommendation}")
        return {
            "recommendation": recommendation,
            "reasoning": reasoning,
        }

    except Exception as e:
        logger.error(f"Recommendation generation failed: {e}")
        return {
            "recommendation": "ERROR",
            "reasoning": f"Recommendation generation failed: {str(e)}",
        }


_compiled_workflow: Optional[StateGraph] = None


def get_job_evaluation_workflow() -> StateGraph:
    """
    Creates and compiles the job evaluation workflow, caching the compiled result
    for reuse.

    Returns:
        Compiled LangGraph workflow ready for execution
    """
    global _compiled_workflow
    if _compiled_workflow is None:
        logger.info("Compiling job evaluation workflow")

        workflow = StateGraph(JobEvaluationState)

        # Add workflow nodes
        workflow.add_node("validate", validate_input)
        workflow.add_node("extract", extract_job_info)
        workflow.add_node("evaluate", evaluate_job)
        workflow.add_node("recommend", generate_recommendation)

        # Define workflow flow
        workflow.add_edge(START, "validate")
        workflow.add_edge("validate", "extract")
        workflow.add_edge("extract", "evaluate")
        workflow.add_edge("evaluate", "recommend")
        workflow.add_edge("recommend", END)

        _compiled_workflow = workflow.compile()
        logger.info("Job evaluation workflow compiled successfully")

    return _compiled_workflow


def run_job_evaluation_workflow(
    job_posting_text: str, config: Optional[Dict[str, Any]] = None
) -> JobEvaluationState:
    """
    Convenience function to run the job evaluation workflow with automatic
    Langfuse configuration.

    Args:
        job_posting_text: The job posting text to evaluate
        config: Optional additional configuration for workflow execution

    Returns:
        Final workflow state with all results
    """
    logger.info("Starting job evaluation workflow")

    # Handle None input
    if job_posting_text is None:
        job_posting_text = ""

    try:
        # Get compiled workflow
        workflow = get_job_evaluation_workflow()

        # Create initial state
        initial_state = JobEvaluationState(job_posting_text=job_posting_text)

        # Configure Langfuse if available
        langfuse_handler = get_langfuse_handler()
        execution_config = {"callbacks": [langfuse_handler]} if langfuse_handler else {}

        # Merge with provided config
        if config:
            execution_config.update(config)

        # Run workflow
        final_state_dict = workflow.invoke(initial_state, config=execution_config)

        # Convert the AddableValuesDict to JobEvaluationState
        final_state = JobEvaluationState(
            job_posting_text=final_state_dict.get("job_posting_text", job_posting_text),
            extracted_info=final_state_dict.get("extracted_info"),
            evaluation_result=final_state_dict.get("evaluation_result"),
            recommendation=final_state_dict.get("recommendation"),
            reasoning=final_state_dict.get("reasoning"),
        )

        logger.info("Job evaluation workflow completed successfully")
        return final_state

    except Exception as e:
        logger.error(f"Job evaluation workflow failed: {e}")
        # Return error state
        return JobEvaluationState(
            job_posting_text=job_posting_text,
            recommendation="ERROR",
            reasoning=f"Workflow execution failed: {str(e)}",
            extracted_info={},
            evaluation_result={},
        )
