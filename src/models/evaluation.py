"""Evaluation-related models for the job search assistant."""

from typing import List

from pydantic import Field, field_validator

from src.models.base import BaseDataModel
from src.models.job import JobDescription


class EvaluationResult(BaseDataModel):
    """Model representing the result of evaluating a job against user preferences."""

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
