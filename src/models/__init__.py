"""Data models for the job search assistant."""

# Import all models from the new separated files
from .enums import JobSource, JobStatus
from .evaluation import EvaluationResult
from .job import JobDescription
from .resume import Education, Experience, Resume
from .user import UserPreferences

__all__ = [
    # Enums
    "JobSource",
    "JobStatus",
    # Job models
    "JobDescription",
    # Resume models
    "Education",
    "Experience",
    "Resume",
    # User models
    "UserPreferences",
    # Evaluation models
    "EvaluationResult",
]
