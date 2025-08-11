"""Data models for interview preparation functionality."""

from datetime import datetime
from enum import Enum
from typing import Dict, List, Optional

from pydantic import Field

from src.models.base import BaseDataModel


class InterviewType(str, Enum):
    """Interview type classification by purpose."""

    HR_SCREEN = "hr_screen"
    HIRING_MANAGER = "hiring_manager"
    PEER = "peer"


class InterviewFormat(str, Enum):
    """Interview format classification."""

    INDIVIDUAL = "individual"
    PANEL = "panel"
    PHONE = "phone"
    VIDEO = "video"
    IN_PERSON = "in_person"


class InterviewDetails(BaseDataModel):
    """Interview specifications and context."""

    type: InterviewType = Field(..., description="Purpose/role of the interviewer")
    format: InterviewFormat = Field(
        default=InterviewFormat.INDIVIDUAL, description="Interview format"
    )
    is_panel: bool = Field(
        default=False, description="Convenience flag for panel interviews"
    )
    company: Optional[str] = Field(None, description="Company name")
    role: Optional[str] = Field(None, description="Role being interviewed for")
    duration_minutes: Optional[int] = Field(
        None, description="Expected interview duration"
    )
    interviewer_count: Optional[int] = Field(
        default=1, description="Number of interviewers"
    )


class ResearchCitation(BaseDataModel):
    """Research source with verification data."""

    url: str = Field(..., description="Source URL")
    title: str = Field(..., description="Page/article title")
    accessed_at: datetime = Field(..., description="When the source was accessed")
    reliability_score: float = Field(..., description="Reliability score 0.0-1.0")
    content_snippet: str = Field(..., description="Relevant content excerpt")


class PIIRedactionResult(BaseDataModel):
    """Result of PII redaction process."""

    redacted_resume_text: str = Field(..., description="Resume text with PII redacted")
    redactions_map: Dict[str, str] = Field(
        default_factory=dict, description="Map of redaction tokens to descriptions"
    )
    complete: bool = Field(
        ..., description="True if all PII successfully redacted (zero matches remain)"
    )
    redaction_log: List[str] = Field(
        default_factory=list, description="Log of redaction operations"
    )


class QuestionCategory(str, Enum):
    """Interview question categorization."""

    GENERAL = "general"
    BEHAVIORAL = "behavioral"
    TECHNICAL = "technical"
    CULTURE = "culture"
    SITUATIONAL = "situational"


class DifficultyLevel(str, Enum):
    """Question difficulty classification."""

    EASY = "easy"
    MEDIUM = "medium"
    HARD = "hard"


class AnswerStyle(str, Enum):
    """Answer delivery style classification."""

    CONCISE = "concise"
    DETAILED = "detailed"
    STAR = "star"


class QuestionItem(BaseDataModel):
    """Individual interview question with metadata."""

    question: str = Field(..., description="Interview question")
    category: QuestionCategory = Field(..., description="Question category")
    rationale: str = Field(..., description="Why this question is relevant")
    difficulty: DifficultyLevel = Field(
        default=DifficultyLevel.MEDIUM, description="Question difficulty level"
    )


class AnswerItem(BaseDataModel):
    """Personalized answer suggestion for an interview question."""

    question: str = Field(..., description="The interview question")
    answer: str = Field(..., description="Personalized answer suggestion")
    style: AnswerStyle = Field(..., description="Answer style")
    key_points: List[str] = Field(
        default_factory=list, description="Key points to cover"
    )
    examples: List[str] = Field(
        default_factory=list, description="Specific examples from resume"
    )


class QAPair(BaseDataModel):
    """Question and answer pair for interview preparation."""

    question: QuestionItem = Field(..., description="Interview question details")
    answer: AnswerItem = Field(..., description="Personalized answer")


class InterviewGuide(BaseDataModel):
    """Complete interview preparation guide."""

    research_summary: Optional[str] = Field(
        None, description="Company/role research summary"
    )
    qa_pairs: List[QAPair] = Field(
        default_factory=list, description="Question and answer pairs"
    )
    preparation_tips: List[str] = Field(
        default_factory=list, description="General preparation advice"
    )
    citations: List[ResearchCitation] = Field(
        default_factory=list, description="Research sources"
    )
