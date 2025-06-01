from enum import Enum
from typing import Any, Dict, List, Optional

from pydantic import ConfigDict  # For Pydantic V2 model_config
from pydantic import BaseModel, Field, field_validator


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
    # Fields from original test_models.py for JobDescription
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

    @field_validator("evaluation_score")
    @classmethod
    def score_must_be_between_0_and_1(cls, v: Optional[float]) -> Optional[float]:
        if v is not None and not (0 <= v <= 1):
            raise ValueError("Evaluation score must be between 0 and 1")
        return v

    model_config = ConfigDict(
        use_enum_values=True,
        # anystr_strip_whitespace = True  # TODO: Decide if desired
    )


class Education(BaseModel):
    institution: str = Field(..., description="Name of the educational institution.")
    degree: str = Field(..., description="Degree obtained.")
    field_of_study: str = Field(..., description="Field of study.")
    start_date: Optional[str] = Field(None, description="Start date of education.")
    end_date: Optional[str] = Field(None, description="End date of education.")


class Experience(BaseModel):
    company: str = Field(..., description="Company name.")
    title: str = Field(..., description="Job title.")
    start_date: Optional[str] = Field(None, description="Start date of employment.")
    end_date: Optional[str] = Field(None, description="End date of employment.")
    highlights: List[str] = Field(
        default_factory=list, description="Key highlights or achievements."
    )


class Resume(BaseModel):
    personal_info: Dict[str, Any] = Field(
        ..., description="Personal information (e.g., name, email, phone)."
    )
    summary: Optional[str] = Field(
        None, description="Professional summary or objective."
    )
    education: List[Education] = Field(
        default_factory=list, description="List of educational qualifications."
    )
    experience: List[Experience] = Field(
        default_factory=list, description="List of professional experiences."
    )
    skills: List[str] = Field(default_factory=list, description="List of skills.")


class EvaluationResult(BaseModel):
    job: JobDescription = Field(..., description="The job description being evaluated.")
    is_good_fit: bool = Field(
        ..., description="Whether the job is considered a good fit."
    )
    score: float = Field(
        ..., description="Numerical score of the evaluation (0.0 to 1.0)."
    )
    reasoning: str = Field(..., description="Reasoning behind the evaluation outcome.")
    matching_skills: List[str] = Field(
        default_factory=list, description="Skills that match the job requirements."
    )

    @field_validator("score")
    @classmethod
    def score_must_be_valid(cls, v: float) -> float:
        if not (0 <= v <= 1):
            raise ValueError("Score must be between 0 and 1")
        return v

    model_config = ConfigDict(use_enum_values=True)


# Example Usage:
if __name__ == "__main__":
    # Example User Preferences
    user_prefs = UserPreferences(job_titles=["Software Engineer", "Data Scientist"])
    print("User Preferences:")
    print(user_prefs.model_dump_json(indent=2))

    # Example Job Description
    job_desc_data = {
        "raw_text": "We are looking for a skilled Software Engineer...",
        "title": "Software Engineer",  # Added for consistency with test
        "company": "Tech Solutions Inc.",  # Added for consistency with test
        "description": "Detailed description here.",  # Added for consistency with test
        "source": JobSource.LINKEDIN,
        "url": "https://linkedin.com/jobs/123",
        "date_posted": "2023-10-01",
        "date_scraped": "2023-10-02",
        "status": JobStatus.PENDING_EVALUATION,
    }
    job_desc = JobDescription(**job_desc_data)
    print("\nJob Description:")
    print(job_desc.model_dump_json(indent=2))

    # Example of updating status and evaluation
    job_desc.status = JobStatus.PASS
    job_desc.evaluation_score = 0.85
    job_desc.evaluation_notes = "Good fit based on skills and experience."
    print("\nUpdated Job Description:")
    print(job_desc.model_dump_json(indent=2))

    # Example Education
    edu = Education(
        institution="State University",
        degree="B.Sc.",
        field_of_study="Computer Science",
    )
    print("\nEducation:")
    print(edu.model_dump_json(indent=2))

    # Example Experience
    exp = Experience(
        company="Innovatech", title="Developer", highlights=["Developed new features"]
    )
    print("\nExperience:")
    print(exp.model_dump_json(indent=2))

    # Example Resume
    res = Resume(
        personal_info={"name": "Jane Doe", "email": "jane@example.com"},
        summary="Experienced developer.",
        education=[edu],
        experience=[exp],
        skills=["Python", "Pydantic"],
    )
    print("\nResume:")
    print(res.model_dump_json(indent=2))

    # Example Evaluation Result
    eval_res = EvaluationResult(
        job=job_desc,
        is_good_fit=True,
        score=0.9,
        reasoning="Excellent match based on skills and experience listed.",
        matching_skills=["Python", "API Design"],
    )
    print("\nEvaluation Result:")
    print(eval_res.model_dump_json(indent=2))
