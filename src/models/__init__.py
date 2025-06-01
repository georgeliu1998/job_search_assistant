"""Data models for the job search assistant."""

from .models import JobSource  # Also export Enums if they are used externally
from .models import (
    Education,
    EvaluationResult,
    Experience,
    JobDescription,
    JobStatus,
    Resume,
    UserPreferences,
)

__all__ = [
    "JobDescription",
    "UserPreferences",
    "Education",
    "Experience",
    "Resume",
    "EvaluationResult",
    "JobSource",
    "JobStatus",
]
