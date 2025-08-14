"""State management for interview preparation workflow."""

from typing import Any, Dict, List, Optional

from pydantic import ConfigDict, Field

from src.models.base import BaseDataModel
from src.models.interview import (
    InterviewDetails,
    InterviewGuide,
    PIIRedactionResult,
    QAPair,
    ResearchCitation,
)


class InterviewPrepState(BaseDataModel):
    """State for interview preparation workflow with validation."""

    # CRITICAL: ConfigDict for gradual state accumulation
    model_config = ConfigDict(
        extra="allow",
        use_enum_values=True,
    )

    # Inputs
    job_description: str = Field(..., description="Job posting text")
    resume_text: str = Field(..., description="Original resume content")
    interview_details: InterviewDetails = Field(
        ..., description="Interview specifications"
    )

    # CRITICAL: Error handling for workflow short-circuiting
    error: Optional[str] = Field(default=None, description="Workflow error message")

    # Intermediate results
    pii_redaction_result: Optional[PIIRedactionResult] = Field(
        None, description="PII redaction results"
    )
    research_results: Optional[List[ResearchCitation]] = Field(
        None, description="Research findings"
    )
    qa_pairs: Optional[List[QAPair]] = Field(None, description="Generated Q&A pairs")

    # Final output
    interview_guide: Optional[InterviewGuide] = Field(
        None, description="Complete interview preparation guide"
    )

    @property
    def num_questions(self) -> int:
        """Get total number of questions from interview details."""
        return self.interview_details.total_questions
