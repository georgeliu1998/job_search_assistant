"""
Models package for the Job Search Assistant.

This package contains all the data models and enums used throughout the application.
"""

from src.models.base import BaseDataModel
from src.models.enums import Environment, JobSource, JobStatus
from src.models.evaluation import EvaluationResult
from src.models.job import JobDescription
from src.models.resume import Education, Experience, Resume
from src.models.user import UserPreferences

__all__ = [
    # Base
    "BaseDataModel",
    # Enums
    "Environment",
    "JobSource",
    "JobStatus",
    # Domain models
    "EvaluationResult",
    "JobDescription",
    "Education",
    "Experience",
    "Resume",
    "UserPreferences",
]
