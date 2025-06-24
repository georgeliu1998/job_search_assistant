"""
Job evaluation core logic

This module contains the core business logic for evaluating job postings
against user-defined criteria. It's designed to be framework-agnostic
and reusable across different contexts.
"""

from typing import Any, Dict

from src.config import config
from src.utils.logging import get_logger

logger = get_logger(__name__)


def evaluate_job_against_criteria(extracted_job_info: Dict[str, Any]) -> Dict[str, Any]:
    """
    Evaluate extracted job information against evaluation criteria.

    This function contains the core business logic for job evaluation,
    independent of any specific workflow or state management framework.

    Args:
        extracted_job_info: Dictionary containing parsed job details

    Returns:
        Dictionary with evaluation results for each criteria
    """
    if not extracted_job_info:
        logger.warning("No extracted job information provided for evaluation")
        return {"error": "No extracted information available"}

    logger.info("Starting job evaluation against criteria")
    results = {}

    # Get evaluation criteria from centralized config
    criteria = config.evaluation_criteria

    # 1. Salary check
    salary_max = extracted_job_info.get("salary_max")
    if salary_max is None:
        results["salary"] = {"pass": False, "reason": "Salary not specified"}
        logger.debug("Salary evaluation: Failed - not specified")
    elif salary_max < criteria.min_salary:
        min_salary = criteria.min_salary
        results["salary"] = {
            "pass": False,
            "reason": (
                f"Highest salary (${salary_max:,}) is lower than required "
                f"salary (${min_salary:,})"
            ),
        }
        logger.debug(f"Salary evaluation: Failed - ${salary_max:,} < ${min_salary:,}")
    else:
        min_salary = criteria.min_salary
        results["salary"] = {
            "pass": True,
            "reason": (
                f"Salary (${salary_max:,}) meets minimum requirement "
                f"(${min_salary:,})"
            ),
        }
        logger.debug(f"Salary evaluation: Passed - ${salary_max:,} >= ${min_salary:,}")

    # 2. Remote policy check
    location_policy = extracted_job_info.get("location_policy", "").lower()
    if "remote" in location_policy:
        results["remote"] = {"pass": True, "reason": "Position is remote"}
        logger.debug("Remote policy evaluation: Passed - position is remote")
    else:
        results["remote"] = {
            "pass": False,
            "reason": f"Position is not remote (location policy: {location_policy})",
        }
        logger.debug(
            f"Remote policy evaluation: Failed - location policy: {location_policy}"
        )

    # 3. IC title level check (only for IC roles)
    role_type = extracted_job_info.get("role_type", "").lower()
    title = extracted_job_info.get("title", "").lower()

    if "ic" in role_type or "individual contributor" in role_type:
        # Check if title contains required seniority level
        ic_requirements = criteria.ic_title_requirements
        has_required_level = any(level in title for level in ic_requirements)
        if has_required_level:
            results["title_level"] = {
                "pass": True,
                "reason": "IC role has appropriate seniority level",
            }
            logger.debug(
                "Title level evaluation: Passed - IC role has appropriate seniority"
            )
        else:
            required_levels = ", ".join(ic_requirements)
            results["title_level"] = {
                "pass": False,
                "reason": (
                    f"IC role lacks required seniority (needs: {required_levels})"
                ),
            }
            logger.debug(
                f"Title level evaluation: Failed - IC role lacks seniority. Title: {title}"
            )
    else:
        # Not an IC role, so title level requirement doesn't apply
        results["title_level"] = {
            "pass": True,
            "reason": "Title level requirement not applicable (not IC role)",
        }
        logger.debug("Title level evaluation: Passed - not an IC role")

    passed_count = sum(
        1
        for result in results.values()
        if isinstance(result, dict) and result.get("pass", False)
    )
    total_count = len([r for r in results.values() if isinstance(r, dict)])

    logger.info(
        f"Job evaluation completed: {passed_count}/{total_count} criteria passed"
    )

    return results
