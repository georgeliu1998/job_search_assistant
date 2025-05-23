"""
Data models for the Job Search Assistant
"""

from datetime import datetime
from typing import Dict, List, Optional

from pydantic import BaseModel, Field


class Education(BaseModel):
    """Education entry in a resume"""

    institution: str
    degree: str
    field_of_study: str
    start_date: Optional[datetime] = None
    end_date: Optional[datetime] = None
    description: Optional[str] = None
    gpa: Optional[float] = None


class Experience(BaseModel):
    """Work experience entry in a resume"""

    company: str
    title: str
    start_date: Optional[datetime] = None
    end_date: Optional[datetime] = None
    location: Optional[str] = None
    description: Optional[str] = None
    highlights: List[str] = Field(default_factory=list)


class Resume(BaseModel):
    """User resume data"""

    personal_info: Dict[str, str]
    summary: Optional[str] = None
    education: List[Education] = Field(default_factory=list)
    experience: List[Experience] = Field(default_factory=list)
    skills: List[str] = Field(default_factory=list)
    certifications: List[Dict[str, str]] = Field(default_factory=list)
    projects: List[Dict[str, str]] = Field(default_factory=list)
    languages: List[Dict[str, str]] = Field(default_factory=list)
    references: List[Dict[str, str]] = Field(default_factory=list)


class JobDescription(BaseModel):
    """Job description data"""

    title: str
    company: str
    location: Optional[str] = None
    is_remote: bool = False
    url: Optional[str] = None
    date_posted: Optional[datetime] = None
    description: str
    requirements: List[str] = Field(default_factory=list)
    responsibilities: List[str] = Field(default_factory=list)
    salary_range: Optional[str] = None
    benefits: List[str] = Field(default_factory=list)
    raw_text: Optional[str] = None


class EvaluationResult(BaseModel):
    """Job evaluation result"""

    job: JobDescription
    is_good_fit: bool
    score: float = Field(ge=0.0, le=1.0)
    reasoning: str
    matching_skills: List[str] = Field(default_factory=list)
    missing_skills: List[str] = Field(default_factory=list)
    recommendations: List[str] = Field(default_factory=list)
