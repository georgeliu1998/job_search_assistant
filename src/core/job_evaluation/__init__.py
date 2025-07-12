"""
Job evaluation component

This module provides core job evaluation functionality using the centralized
configuration system for evaluation criteria.
"""

from src.core.job_evaluation.evaluator import evaluate_job_against_criteria
from src.core.job_evaluation.recommender import generate_recommendation_from_evaluation

__all__ = ["evaluate_job_against_criteria", "generate_recommendation_from_evaluation"]
