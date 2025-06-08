"""
Data models for interview preparation functionality.
"""

from enum import Enum
from typing import Optional

from pydantic import BaseModel, Field

from src.models.base import BaseJobSearchModel


class InterviewType(str, Enum):
    """Types of interviews supported."""

    HR_PRESCREEN = "HR pre-screen"
    HIRING_MANAGER = "hiring manager interview"
    TECHNICAL = "technical interview"


class InterviewPrepInput(BaseJobSearchModel):
    """Input data for interview preparation."""

    job_description: str = Field(..., description="Full job description text")

    interview_type: InterviewType = Field(
        ..., description="Type of interview to prepare for"
    )

    resume_text: str = Field(..., description="Resume content (from PDF or text input)")

    interviewer_name: Optional[str] = Field(
        None, description="Interviewer's name if known"
    )

    interviewer_title: Optional[str] = Field(
        None, description="Interviewer's job title if known"
    )

    interviewer_linkedin: Optional[str] = Field(
        None, description="LinkedIn profile text or URL"
    )

    company_website: Optional[str] = Field(
        None, description="Company website URL for additional context"
    )


class InterviewPrepOutput(BaseJobSearchModel):
    """Output from interview preparation agent."""

    guide_content: str = Field(..., description="Complete interview preparation guide")

    estimated_prep_time: Optional[str] = Field(
        None, description="Recommended preparation time"
    )

    interview_type: InterviewType = Field(
        ..., description="Type of interview this guide is for"
    )

    job_title_extracted: Optional[str] = Field(
        None, description="Job title extracted from description"
    )

    company_name_extracted: Optional[str] = Field(
        None, description="Company name extracted from description"
    )
