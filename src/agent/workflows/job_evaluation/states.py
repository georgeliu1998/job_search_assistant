"""
Graph state for job evaluation workflow using Pydantic.

This state contains only the essential fields needed for the
extract → evaluate → recommend flow with added validation.
"""

from typing import Any, Dict, Literal, Optional

from pydantic import BaseModel, ConfigDict, Field


class JobEvaluationState(BaseModel):
    """State for job evaluation workflow with validation."""

    # Use ConfigDict instead of deprecated Config class
    model_config = ConfigDict(
        # Allow extra fields for future extensibility
        extra="allow",
        # Use enum values for serialization
        use_enum_values=True,
    )

    # Input
    job_posting_text: str = Field(
        ..., min_length=1, description="The job posting text to evaluate"
    )

    # Intermediate results
    extracted_info: Optional[Dict[str, Any]] = Field(
        default=None, description="Structured information extracted from job posting"
    )
    evaluation_result: Optional[Dict[str, Any]] = Field(
        default=None, description="Results of evaluating job against criteria"
    )

    # Final output
    recommendation: Optional[Literal["APPLY", "DO_NOT_APPLY", "ERROR"]] = Field(
        default=None, description="Final recommendation for the job"
    )
    reasoning: Optional[str] = Field(
        default=None, description="Detailed reasoning for the recommendation"
    )
