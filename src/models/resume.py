"""Resume-related models for the job search assistant."""

from typing import Any, Dict, List, Optional

from pydantic import Field

from src.models.base import BaseJobSearchModel


class Education(BaseJobSearchModel):
    """Model representing educational background."""

    institution: str = Field(..., description="Name of the educational institution.")
    degree: str = Field(..., description="Degree obtained.")
    field_of_study: str = Field(..., description="Field of study.")
    start_date: Optional[str] = Field(None, description="Start date of education.")
    end_date: Optional[str] = Field(None, description="End date of education.")


class Experience(BaseJobSearchModel):
    """Model representing work experience."""

    company: str = Field(..., description="Company name.")
    title: str = Field(..., description="Job title.")
    start_date: Optional[str] = Field(None, description="Start date of employment.")
    end_date: Optional[str] = Field(None, description="End date of employment.")
    highlights: List[str] = Field(
        default_factory=list, description="Key highlights or achievements."
    )


class Resume(BaseJobSearchModel):
    """Model representing a complete resume."""

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
