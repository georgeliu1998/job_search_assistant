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


def generate_recommendation_from_evaluation(
    evaluation_result: Dict[str, Any],
) -> Tuple[str, str]:
    """Generate an application recommendation from evaluation results.

    Args:
        evaluation_result: Mapping of criterion name to its result dict
            (``pass``, ``reason``, ``mode``, ``extracted_value``).

    Returns:
        Tuple of (recommendation, reasoning) where recommendation is one of
        "APPLY", "DO_NOT_APPLY", or "ERROR".
    """
    if not evaluation_result or "error" in evaluation_result:
        logger.warning("Invalid or empty evaluation result for recommendation")
        return "ERROR", "Unable to evaluate job posting"

    logger.info("Generating recommendation from evaluation results")

    required_failures: List[str] = []
    optional_failures: List[str] = []
    required_passes: List[str] = []

    for criterion, result in evaluation_result.items():
        if not _is_criterion(result):
            continue

        reason = result.get("reason", "")
        entry = f"{criterion}: {reason}"
        is_required = result["mode"] == CriterionMode.REQUIRED.value

        if result["pass"]:
            if is_required:
                required_passes.append(entry)
        else:
            if is_required:
                required_failures.append(entry)
            else:
                optional_failures.append(entry)

    if required_failures:
        recommendation = "DO_NOT_APPLY"
        reasoning = f"Required criteria failed: {'; '.join(required_failures)}"
        if optional_failures:
            reasoning += f". Optional concerns: {'; '.join(optional_failures)}"
        logger.info(
            "Recommendation: DO_NOT_APPLY - %d required criteria failed",
            len(required_failures),
        )
        return recommendation, reasoning

    recommendation = "APPLY"
    reasoning = "All required criteria passed"
    if required_passes:
        reasoning += f": {'; '.join(required_passes)}"
    if optional_failures:
        reasoning += (
            f". Optional concerns (non-blocking): {'; '.join(optional_failures)}"
        )
    logger.info("Recommendation: APPLY - no required criteria failed")
    return recommendation, reasoning
