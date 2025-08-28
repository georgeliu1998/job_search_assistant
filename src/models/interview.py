"""Data models for interview preparation functionality."""

from datetime import datetime
from enum import Enum
from typing import Dict, List, Optional

from pydantic import Field, field_validator, model_validator

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


class QuestionCategory(str, Enum):
    """Interview question categorization."""

    GENERAL = "general"
    BEHAVIORAL = "behavioral"
    TECHNICAL = "technical"
    CULTURE = "culture"
    SITUATIONAL = "situational"


# Question mix configurations for different interview types
QUESTION_MIXES: Dict[InterviewType, Dict[QuestionCategory, int]] = {
    InterviewType.HR_SCREEN: {
        QuestionCategory.GENERAL: 2,
        QuestionCategory.BEHAVIORAL: 3,
        QuestionCategory.TECHNICAL: 0,
        QuestionCategory.CULTURE: 3,
        QuestionCategory.SITUATIONAL: 0,
    },
    InterviewType.HIRING_MANAGER: {
        QuestionCategory.GENERAL: 2,
        QuestionCategory.BEHAVIORAL: 3,
        QuestionCategory.TECHNICAL: 3,
        QuestionCategory.CULTURE: 0,
        QuestionCategory.SITUATIONAL: 2,
    },
    InterviewType.PEER: {
        QuestionCategory.GENERAL: 0,
        QuestionCategory.BEHAVIORAL: 0,
        QuestionCategory.TECHNICAL: 4,
        QuestionCategory.CULTURE: 0,
        QuestionCategory.SITUATIONAL: 2,
    },
}

# Default durations for different interview types (in minutes)
DEFAULT_DURATIONS: Dict[InterviewType, int] = {
    InterviewType.HR_SCREEN: 30,
    InterviewType.HIRING_MANAGER: 60,
    InterviewType.PEER: 60,
}


class InterviewDetails(BaseDataModel):
    """Interview specifications and context."""

    type: InterviewType = Field(..., description="Purpose/role of the interviewer")
    format: InterviewFormat = Field(
        default=InterviewFormat.INDIVIDUAL, description="Interview format"
    )
    company: Optional[str] = Field(None, description="Company name")
    role: Optional[str] = Field(None, description="Role being interviewed for")
    duration: Optional[int] = Field(
        None, description="Expected interview duration in minutes"
    )
    question_mix: Dict[QuestionCategory, int] = Field(
        default_factory=dict, description="Question distribution by category"
    )

    @model_validator(mode="before")
    @classmethod
    def set_defaults(cls, data):
        """Auto-populate question_mix and duration from defaults based on interview type."""
        if isinstance(data, dict):
            interview_type = data.get("type")

            if interview_type:
                # Ensure interview_type is an InterviewType enum
                if isinstance(interview_type, str):
                    interview_type = InterviewType(interview_type)
                elif hasattr(interview_type, "value"):
                    interview_type = InterviewType(interview_type.value)

                # Set default question_mix if not provided or empty
                if not data.get("question_mix"):
                    data["question_mix"] = QUESTION_MIXES.get(interview_type, {}).copy()

                # Set default duration if not provided
                if data.get("duration") is None:
                    data["duration"] = DEFAULT_DURATIONS.get(interview_type)

        return data

    @property
    def total_questions(self) -> int:
        """Get total number of questions from question mix."""
        return sum(self.question_mix.values())


class ResearchCitation(BaseDataModel):
    """Research source with verification data."""

    url: str = Field(..., description="Source URL")
    title: str = Field(..., description="Page/article title")
    accessed_at: datetime = Field(..., description="When the source was accessed")
    content_snippet: str = Field(..., description="Relevant content excerpt")
    is_accessible: bool = Field(..., description="Whether the URL is accessible")


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


class InterviewQuestions(BaseDataModel):
    """Schema for structured generation of interview questions."""

    questions: List[QuestionItem] = Field(
        ..., description="List of interview questions with metadata"
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

    num_questions: int = Field(
        default=10, description="Number of questions requested for this guide"
    )
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
