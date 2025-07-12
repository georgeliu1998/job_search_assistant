"""
Simplified state for job evaluation workflow.

This state contains only the essential fields needed for the
extract → evaluate → recommend flow.
"""

from typing import Any, Dict, Optional

from typing_extensions import TypedDict


class JobEvaluationState(TypedDict):
    """State for job evaluation workflow."""

    # Input
    job_posting_text: str

    # Intermediate results
    extracted_info: Optional[Dict[str, Any]]
    evaluation_result: Optional[Dict[str, Any]]

    # Final output
    recommendation: Optional[str]  # "APPLY", "DO_NOT_APPLY", or "ERROR"
    reasoning: Optional[str]
