"""
Job recommendation core logic

This module contains the core business logic for generating job application
recommendations based on evaluation results. It's designed to be framework-agnostic
and reusable across different contexts.
"""

from typing import Any, Dict, Tuple

from src.utils.logging import get_logger

logger = get_logger(__name__)


def generate_recommendation_from_evaluation(
    evaluation_result: Dict[str, Any],
) -> Tuple[str, str]:
    """
    Generate job application recommendation based on evaluation results.

    This function contains the core business logic for recommendation generation,
    independent of any specific workflow or state management framework.

    Args:
        evaluation_result: Dictionary containing evaluation results for each criteria

    Returns:
        Tuple of (recommendation, reasoning) where recommendation is one of
        "APPLY", "DO_NOT_APPLY", or "ERROR"
    """
    if not evaluation_result or "error" in evaluation_result:
        logger.warning("Invalid or empty evaluation result for recommendation")
        return "ERROR", "Unable to evaluate job posting"

    logger.info("Generating recommendation from evaluation results")

    # Count passed and failed criteria
    passed_criteria = []
    failed_criteria = []

    for criterion, result in evaluation_result.items():
        if isinstance(result, dict) and "pass" in result:
            if result["pass"]:
                passed_criteria.append(f"{criterion}: {result['reason']}")
                logger.debug(f"Criterion passed: {criterion}")
            else:
                failed_criteria.append(f"{criterion}: {result['reason']}")
                logger.debug(f"Criterion failed: {criterion}")

    # Generate recommendation based on results
    if not failed_criteria:
        recommendation = "APPLY"
        reasoning = f"All criteria passed: {'; '.join(passed_criteria)}"
        logger.info(
            f"Recommendation: APPLY - all {len(passed_criteria)} criteria passed"
        )
    else:
        recommendation = "DO_NOT_APPLY"
        if failed_criteria:
            reasoning = f"Failed criteria: {'; '.join(failed_criteria)}"
        else:
            reasoning = "Job does not meet evaluation criteria"
        logger.info(
            f"Recommendation: DO_NOT_APPLY - {len(failed_criteria)} criteria failed"
        )

    return recommendation, reasoning
