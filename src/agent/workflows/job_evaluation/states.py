"""
State definitions for the job evaluation workflow.

This module defines the state structure for the job evaluation workflow,
using type-safe Pydantic models instead of generic dictionaries.
"""

from typing import Any, Dict, List, Optional

from typing_extensions import TypedDict

from src.models.job import JobPostingExtractionSchema


class JobEvaluationWorkflowState(TypedDict):
    """
    State for the job evaluation workflow.

    This state uses type-safe Pydantic models for extracted information
    instead of generic dictionaries, providing better type safety and validation.
    """

    # Input
    job_posting_text: str

    # Intermediate results - now type-safe!
    extracted_info: Optional[JobPostingExtractionSchema]
    is_valid: Optional[bool]  # Validation result from extraction
    evaluation_result: Optional[Dict[str, Any]]

    # Final results - provided by evaluation agent
    recommendation: Optional[str]  # "APPLY", "DO_NOT_APPLY", or "ERROR"
    reasoning: Optional[str]  # Human-readable explanation
    passed_criteria: Optional[int]  # Number of criteria that passed
    total_criteria: Optional[int]  # Total number of criteria evaluated

    # Metadata
    messages: List[Dict[str, Any]]  # LLM conversation tracking
    langfuse_handler: Optional[Any]  # Langfuse callback handler

    # Additional workflow metadata
    workflow_version: str  # Track which version of workflow was used
    extraction_duration: Optional[float]  # Time taken for extraction
    evaluation_duration: Optional[float]  # Time taken for evaluation


def create_initial_state(
    job_posting_text: str, langfuse_handler: Optional[Any] = None
) -> JobEvaluationWorkflowState:
    """
    Create the initial state for the job evaluation workflow.

    Args:
        job_posting_text: The raw job posting text to evaluate
        langfuse_handler: Optional Langfuse handler for tracing

    Returns:
        JobEvaluationWorkflowState: Initial state with defaults
    """
    return JobEvaluationWorkflowState(
        job_posting_text=job_posting_text,
        extracted_info=None,
        is_valid=None,
        evaluation_result=None,
        recommendation=None,
        reasoning=None,
        passed_criteria=None,
        total_criteria=None,
        messages=[],
        langfuse_handler=langfuse_handler,
        workflow_version="3.0",  # Updated version with new agents
        extraction_duration=None,
        evaluation_duration=None,
    )


def is_extraction_successful(state: JobEvaluationWorkflowState) -> bool:
    """
    Check if extraction was successful.

    Args:
        state: The current workflow state

    Returns:
        bool: True if extraction was successful
    """
    return state["extracted_info"] is not None and isinstance(
        state["extracted_info"], JobPostingExtractionSchema
    )


def is_evaluation_successful(state: JobEvaluationWorkflowState) -> bool:
    """
    Check if evaluation was successful.

    Args:
        state: The current workflow state

    Returns:
        bool: True if evaluation was successful
    """
    return (
        state.get("recommendation") is not None
        and state.get("recommendation") != "ERROR"
        and state.get("evaluation_result") is not None
    )


def get_extracted_info_as_dict(state: JobEvaluationWorkflowState) -> Dict[str, Any]:
    """
    Convert extracted info to dictionary format for backward compatibility.

    This is needed for the existing evaluate_job_against_criteria function
    which expects a dictionary format.

    Args:
        state: The current workflow state

    Returns:
        Dict[str, Any]: Extracted info in dictionary format
    """
    if not is_extraction_successful(state):
        return {}

    extracted_info = state["extracted_info"]

    # Convert JobPostingExtractionSchema to dictionary format
    # that matches what evaluate_job_against_criteria expects
    return {
        "title": extracted_info.title,
        "company": extracted_info.company,
        "salary_min": extracted_info.salary_min,
        "salary_max": extracted_info.salary_max,
        "location_policy": extracted_info.location_policy,
        "role_type": extracted_info.role_type,
        # Additional fields that might be expected by the evaluator
        "job_title": extracted_info.title,  # Alternative name
        "company_name": extracted_info.company,  # Alternative name
    }


def add_message(
    state: JobEvaluationWorkflowState,
    role: str,
    content: Optional[str] = None,
    error: Optional[str] = None,
    metadata: Optional[Dict[str, Any]] = None,
) -> JobEvaluationWorkflowState:
    """
    Add a message to the workflow state.

    Args:
        state: The current workflow state
        role: The role/source of the message
        content: The message content
        error: Error message if applicable
        metadata: Additional metadata

    Returns:
        JobEvaluationWorkflowState: Updated state with new message
    """
    message = {"role": role}

    # Include all non-None parameters in the message
    if content is not None:
        message["content"] = content
    if error is not None:
        message["error"] = error
    if metadata is not None:
        message["metadata"] = metadata

    updated_messages = state["messages"] + [message]

    return {
        **state,
        "messages": updated_messages,
    }
