"""Enums used across the job search assistant models."""

from enum import Enum


class JobSource(Enum):
    """Source platforms for job postings."""

    LINKEDIN = "linkedin"
    INDEED = "indeed"
    ZIPRECRUITER = "ziprecruiter"
    OTHER = "other"


class JobStatus(Enum):
    """Status of a job application in the pipeline."""

    PENDING_EVALUATION = "pending_evaluation"
    EVALUATING = "evaluating"
    PASS = "pass"
    REJECT = "reject"
    APPLIED = "applied"
    INTERVIEWING = "interviewing"
    OFFER = "offer"
    HIRED = "hired"
