"""Job-related models for the job search assistant."""

from typing import Any, Dict, List, Optional

from pydantic import Field, field_validator

from src.models.base import BaseDataModel
from src.models.enums import JobSource, JobStatus


class JobDescription(BaseDataModel):
    """Model representing a job posting with evaluation metadata."""

    # Core job information
    title: Optional[str] = Field(None, description="Job title.")
    company: Optional[str] = Field(None, description="Company name.")
    description: Optional[str] = Field(None, description="Full job description text.")
    is_remote: Optional[bool] = Field(False, description="Is the job remote?")
    requirements: List[str] = Field(
        default_factory=list, description="Job requirements."
    )

    raw_text: str = Field(..., description="Raw text of the job description.")
    # extracted_info: Optional[Dict[str, Any]] = Field(
    #     None, description="Structured information extracted by LLM."
    # )
    # TODO: Define the schema for structured information

    # Metadata
    source: Optional[JobSource] = Field(
        None, description="Source of the job posting (e.g., LinkedIn, Indeed)."
    )
    url: Optional[str] = Field(None, description="URL of the job posting.")
    date_posted: Optional[str] = Field(None, description="Date the job was posted.")
    date_scraped: Optional[str] = Field(None, description="Date the job was scraped.")

    # Evaluation fields
    status: JobStatus = Field(
        default=JobStatus.PENDING_EVALUATION,
        description="Current status of the job application.",
    )
    evaluation_score: Optional[float] = Field(
        None, description="Score assigned by the evaluation agent."
    )
    evaluation_notes: Optional[str] = Field(
        None, description="Notes from the evaluation agent."
    )

    @field_validator("evaluation_score")
    @classmethod
    def score_must_be_between_0_and_1(cls, v: Optional[float]) -> Optional[float]:
        if v is not None and not (0 <= v <= 1):
            raise ValueError("Evaluation score must be between 0 and 1")
        return v
