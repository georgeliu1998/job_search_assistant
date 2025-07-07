"""
Job evaluation workflow implementation.

This module contains the workflow for evaluating job postings against
user criteria, including extraction and evaluation steps.
"""

from src.agent.workflows.job_evaluation.main import (
    JobEvaluationWorkflow,
    create_job_evaluation_workflow,
    evaluate_job_posting,
    generate_recommendation_from_results,
)
from src.agent.workflows.job_evaluation.states import (
    JobEvaluationWorkflowState,
    add_message,
    create_initial_state,
    get_extracted_info_as_dict,
    is_extraction_successful,
)

__all__ = [
    # Public API
    "evaluate_job_posting",
    # State management
    "JobEvaluationWorkflowState",
    "create_initial_state",
    "is_extraction_successful",
    "get_extracted_info_as_dict",
    "add_message",
    # Workflow
    "JobEvaluationWorkflow",
    "create_job_evaluation_workflow",
    "generate_recommendation_from_results",
]
