"""
Job recommendation core logic.

Turns per-criterion evaluation results into an APPLY / DO_NOT_APPLY decision,
respecting each criterion's ``mode`` (required vs. optional). Only required
criteria can block an APPLY recommendation; optional criteria are reported for
transparency but do not gate the decision.
"""

from typing import Any, Dict, List, Tuple

from src.models.user import CriterionMode
from src.utils.logging import get_logger

logger = get_logger(__name__)


def _is_criterion(result: Any) -> bool:
    """Return True if ``result`` is a well-formed criterion result dict."""
    return isinstance(result, dict) and "pass" in result and "mode" in result


def _display_name(criterion_key: str) -> str:
    """Turn 'employment_type' into 'employment type' for readable lists."""
    return criterion_key.replace("_", " ")


def generate_recommendation_from_evaluation(
    evaluation_result: Dict[str, Any],
) -> Tuple[str, str]:
    """Generate an application recommendation from evaluation results.

    Args:
        evaluation_result: Mapping of criterion name to its result dict
            (``pass``, ``reason``, ``mode``, ``extracted_value``).

    Returns:
        Tuple of (recommendation, reasoning) where recommendation is one of
        "APPLY", "DO_NOT_APPLY", or "ERROR". Reasoning is a brief summary that
        names which criteria failed; the per-criterion ``reason`` text is left
        to the criteria breakdown so the two views don't duplicate each other.
    """
    if not evaluation_result or "error" in evaluation_result:
        logger.warning("Invalid or empty evaluation result for recommendation")
        return "ERROR", "Unable to evaluate job posting"

    logger.info("Generating recommendation from evaluation results")

    required_failures: List[str] = []
    optional_failures: List[str] = []

    for criterion, result in evaluation_result.items():
        if not _is_criterion(result) or result["pass"]:
            continue
        if result["mode"] == CriterionMode.REQUIRED.value:
            required_failures.append(criterion)
        else:
            optional_failures.append(criterion)

    if required_failures:
        names = ", ".join(_display_name(c) for c in required_failures)
        reasoning = f"Required criteria failed: {names}."
        if optional_failures:
            opt = ", ".join(_display_name(c) for c in optional_failures)
            reasoning += f" Optional concerns: {opt}."
        logger.info(
            "Recommendation: DO_NOT_APPLY - %d required criteria failed",
            len(required_failures),
        )
        return "DO_NOT_APPLY", reasoning

    reasoning = "All required criteria passed."
    if optional_failures:
        opt = ", ".join(_display_name(c) for c in optional_failures)
        reasoning += f" Optional concerns (non-blocking): {opt}."
    logger.info("Recommendation: APPLY - no required criteria failed")
    return "APPLY", reasoning
