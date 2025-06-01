from enum import Enum
from typing import Any, Dict, List, Optional

from pydantic import BaseModel, Field, validator


class JobSource(Enum):
    LINKEDIN = "linkedin"
    INDEED = "indeed"
    ZIPRECRUITER = "ziprecruiter"
    OTHER = "other"


class JobStatus(Enum):
    PENDING_EVALUATION = "pending_evaluation"
    EVALUATING = "evaluating"
    PASS = "pass"
    REJECT = "reject"
    APPLIED = "applied"
    INTERVIEWING = "interviewing"
    OFFER = "offer"
    HIRED = "hired"


class UserPreferences(BaseModel):
    job_titles: List[str] = Field(..., description="List of desired job titles.")
    # TODO: Add more preferences like salary, location, company size, etc.
    # TODO: Add weights to preferences
    # TODO: Add must-have vs. nice-to-have preferences
    # TODO: Add ability to specify how to evaluate each preference


class JobDescription(BaseModel):
    raw_text: str = Field(..., description="Raw text of the job description.")
    # extracted_info: Optional[Dict[str, Any]] = Field(None, description="Structured information extracted by LLM.")
    # TODO: Define the schema for structured information extracted from the job description
    # Examples:
    # company_name: Optional[str] = None
    # job_title: Optional[str] = None
    # location: Optional[str] = None
    # salary_range: Optional[str] = None # Consider using a structured type for salary
    # skills: Optional[List[str]] = None
    # experience_level: Optional[str] = None
    # responsibilities: Optional[List[str]] = None
    # qualifications: Optional[List[str]] = None
    # benefits: Optional[List[str]] = None

    # Metadata
    source: Optional[JobSource] = Field(
        None, description="Source of the job posting (e.g., LinkedIn, Indeed)."
    )
    url: Optional[str] = Field(None, description="URL of the job posting.")
    date_posted: Optional[str] = Field(
        None, description="Date the job was posted."
    )  # Consider using datetime
    date_scraped: Optional[str] = Field(
        None, description="Date the job was scraped."
    )  # Consider using datetime

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

    @validator("evaluation_score")
    def score_must_be_between_0_and_1(cls, v: Optional[float]) -> Optional[float]:
        if v is not None and not (0 <= v <= 1):
            raise ValueError("Evaluation score must be between 0 and 1")
        return v

    class Config:
        use_enum_values = (
            True  # Ensures enum values are used, not the enum objects themselves
        )
        # anystr_strip_whitespace = True # TODO: Need to decide if this is desired behavior


# Example Usage:
if __name__ == "__main__":
    # Example User Preferences
    user_prefs = UserPreferences(job_titles=["Software Engineer", "Data Scientist"])
    print("User Preferences:")
    print(user_prefs.model_dump_json(indent=2))

    # Example Job Description
    job_desc = JobDescription(
        raw_text="We are looking for a skilled Software Engineer...",
        source=JobSource.LINKEDIN,
        url="https://linkedin.com/jobs/123",
        date_posted="2023-10-01",
        date_scraped="2023-10-02",
        status=JobStatus.PENDING_EVALUATION,
    )
    print("\nJob Description:")
    print(job_desc.model_dump_json(indent=2))

    # Example of updating status and evaluation
    job_desc.status = JobStatus.PASS
    job_desc.evaluation_score = 0.85
    job_desc.evaluation_notes = "Good fit based on skills and experience."
    print("\nUpdated Job Description:")
    print(job_desc.model_dump_json(indent=2))
