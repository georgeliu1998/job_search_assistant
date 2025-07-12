"""Job-related models for the job search assistant."""

from typing import Any, Dict, List, Literal, Optional

from pydantic import ConfigDict, Field, field_validator

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


class JobPostingExtractionSchema(BaseDataModel):
    """
    Schema for structured extraction from job postings using LLM.

    This schema is specifically designed for use with LangChain's structured
    outputs feature, providing type-safe extraction of key job information.
    """

    title: Optional[str] = Field(
        None,
        description="Job title exactly as written in the posting",
        examples=["Senior Software Engineer", "Lead Data Scientist", "Product Manager"],
    )

    company: Optional[str] = Field(
        None,
        description="Company name exactly as mentioned in the posting",
        examples=["Google", "Microsoft", "Startup Inc."],
    )

    salary_min: Optional[int] = Field(
        None,
        description="Minimum salary if specified (annual, in USD)",
        examples=[100000, 120000, 150000],
        ge=0,
    )

    salary_max: Optional[int] = Field(
        None,
        description="Maximum salary if specified (annual, in USD)",
        examples=[150000, 180000, 200000],
        ge=0,
    )

    location_policy: Literal["remote", "hybrid", "onsite", "unclear"] = Field(
        default="unclear",
        description="Work location policy based on job description",
        examples=["remote", "hybrid", "onsite", "unclear"],
    )

    role_type: Literal["ic", "manager", "unclear"] = Field(
        default="unclear",
        description="Role type classification - IC (Individual Contributor) or Manager",
        examples=["ic", "manager", "unclear"],
    )

    @field_validator("salary_max")
    @classmethod
    def salary_max_must_be_greater_than_min(
        cls, v: Optional[int], info
    ) -> Optional[int]:
        """Validate that salary_max is greater than salary_min if both are provided."""
        if v is not None and info.data.get("salary_min") is not None:
            salary_min = info.data["salary_min"]
            if v < salary_min:
                raise ValueError(
                    "salary_max must be greater than or equal to salary_min"
                )
        return v

    model_config = ConfigDict(
        # Enable JSON schema generation with examples
        json_schema_extra={
            "examples": [
                {
                    "title": "Senior Software Engineer",
                    "company": "TechCorp",
                    "salary_min": 140000,
                    "salary_max": 180000,
                    "location_policy": "remote",
                    "role_type": "ic",
                },
                {
                    "title": "Engineering Manager",
                    "company": "BigTech Inc.",
                    "salary_min": 160000,
                    "salary_max": 220000,
                    "location_policy": "hybrid",
                    "role_type": "manager",
                },
            ]
        }
    )
