"""
Job evaluation component

This module provides core job evaluation functionality using the centralized
configuration system for evaluation criteria.
"""

from src.core.job_evaluation.evaluator import evaluate_job_against_criteria

__all__ = ["evaluate_job_against_criteria"]
