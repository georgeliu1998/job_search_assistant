"""Data models for the job search assistant."""

# Import all models from the new separated files
from src.models.enums import JobSource, JobStatus
from src.models.evaluation import EvaluationResult
from src.models.job import JobDescription
from src.models.resume import Education, Experience, Resume
from src.models.user import UserPreferences

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
