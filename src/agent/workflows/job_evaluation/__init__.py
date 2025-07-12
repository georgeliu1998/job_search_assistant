"""
Simplified job evaluation workflow implementation.

This module provides a clean, straightforward workflow for evaluating job postings
against user criteria using LangGraph for orchestration.
"""

from src.agent.workflows.job_evaluation.main import evaluate_job_posting

__all__ = [
    "evaluate_job_posting",
]
