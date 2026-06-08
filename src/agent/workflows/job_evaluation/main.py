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
    evaluate_fit,
    evaluate_job_against_criteria,
    generate_recommendation_from_evaluation,
)
from src.core.preferences import load_preferences
from src.llm import langfuse_manager
from src.models.user import JobPreferences
from src.utils.logging import get_logger
from src.utils.text import MAX_JOB_DESCRIPTION_CHARS, truncate_text

logger = get_logger(__name__)


def load_user_preferences(state: JobEvaluationState) -> Dict[str, Any]:
    """Load user preferences so they are available to downstream nodes."""
    logger.info("Loading user preferences")

    if state.user_preferences is not None:
        return {}

    return {"user_preferences": load_preferences()}


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
    # Bound the posting text once here so every downstream node (extraction and
    # fit) works from the same truncated text and the warning is logged once.
    bounded_text = truncate_text(job_text, MAX_JOB_DESCRIPTION_CHARS, "job posting")
    return {"job_posting_text": bounded_text}


def extract_job_info(state: JobEvaluationState) -> Dict[str, Any]:
    """Extract structured information from job posting text."""
    logger.info("Extracting job information")

    # Text was already bounded in validate_input.
    try:
        extracted_info = extract_job_posting(state.job_posting_text)

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
    """Evaluate extracted job information against user preferences."""
    logger.info("Evaluating job against criteria")

    extracted_info = state.extracted_info

    if not extracted_info:
        logger.warning("No extracted info to evaluate")
        return {
            "evaluation_result": None,
            "recommendation": "ERROR",
            "reasoning": "No job information available for evaluation",
        }

    preferences = state.user_preferences or JobPreferences()

    try:
        evaluation_result = evaluate_job_against_criteria(extracted_info, preferences)

        # Fold in the LLM-based fit assessment as an additional criterion.
        # evaluate_fit never raises (it falls back to its none policy on any
        # failure), so a fit problem cannot discard the rule-based results here.
        evaluation_result["fit"] = evaluate_fit(state.job_posting_text, preferences)

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

    evaluation_result = state.evaluation_result

    if not evaluation_result:
        logger.warning("No evaluation result to generate recommendation from")
        return {
            "recommendation": "ERROR",
            "reasoning": "No evaluation result available for recommendation",
        }

    try:
        recommendation, reasoning = generate_recommendation_from_evaluation(evaluation_result)

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


def _route_on_error(state: JobEvaluationState) -> str:
    """Route to END if an error occurred, otherwise continue to the next node."""
    if state.recommendation == "ERROR":
        logger.info("Error detected, short-circuiting workflow")
        return END
    return "continue"


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

        workflow.add_node("load_preferences", load_user_preferences)
        workflow.add_node("validate", validate_input)
        workflow.add_node("extract", extract_job_info)
        workflow.add_node("evaluate", evaluate_job)
        workflow.add_node("recommend", generate_recommendation)

        workflow.add_edge(START, "load_preferences")
        # Every node routes through _route_on_error so the graph stays uniform:
        # if any node (now or in the future) sets recommendation="ERROR" the
        # workflow short-circuits to END.
        workflow.add_conditional_edges(
            "load_preferences", _route_on_error, {"continue": "validate", END: END}
        )
        workflow.add_conditional_edges(
            "validate", _route_on_error, {"continue": "extract", END: END}
        )
        workflow.add_conditional_edges(
            "extract", _route_on_error, {"continue": "evaluate", END: END}
        )
        workflow.add_conditional_edges(
            "evaluate", _route_on_error, {"continue": "recommend", END: END}
        )
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

        # Configure context-aware Langfuse tracing
        execution_config = langfuse_manager.get_workflow_config(config)

        # Run workflow
        final_state_dict = workflow.invoke(initial_state, config=execution_config)

        final_state = JobEvaluationState.model_validate(final_state_dict)

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
