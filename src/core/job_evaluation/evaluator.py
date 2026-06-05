"""
Job evaluation core logic.

Evaluates extracted job information against a user's :class:`JobPreferences`.
Each criterion produces a result dict with a uniform shape::

    {
        "pass": bool,
        "reason": str,
        "mode": "required" | "optional",
        "extracted_value": Any | None,
    }

This module covers the rule-based criteria only. The LLM-based "fit" criterion
lives in :mod:`src.core.job_evaluation.fit_evaluator` and is folded into the
results by the workflow.
"""

import re
from typing import Any, Dict, List, Optional

from src.models.user import CriterionConfig, JobPreferences, NonePolicy
from src.utils.logging import get_logger

logger = get_logger(__name__)

# Ordinal ranking for education levels (higher = more advanced).
_EDUCATION_RANK = {"associate": 1, "bachelor": 2, "master": 3, "phd": 4}


def _result(
    passed: bool, reason: str, config: CriterionConfig, extracted_value: Any
) -> Dict[str, Any]:
    """Build a uniform criterion result dict."""
    return {
        "pass": passed,
        "reason": reason,
        "mode": config.mode.value,
        "extracted_value": extracted_value,
    }


def _none_result(
    config: CriterionConfig, extracted_value: Any, label: str
) -> Dict[str, Any]:
    """Build a result for a criterion whose data is missing from the posting."""
    passed = config.none_policy == NonePolicy.PASS
    decision = "pass" if passed else "fail"
    reason = f"{label} not specified in posting; counted as {decision} per preference"
    return _result(passed, reason, config, extracted_value)


def _words(text: str) -> set:
    """Tokenize ``text`` into a set of lowercase alphanumeric words."""
    return set(re.findall(r"[a-z0-9]+", text.lower()))


def _find_blacklist_match(company: str, blacklist: List[str]) -> Optional[str]:
    """Return the blacklist entry that matches ``company``, if any.

    Uses word-boundary-aware normalized matching: every word in a blacklist
    entry must appear as a word in the company name. So "Microsoft" matches
    "Microsoft Co. Ltd." but "Meta" does not match "Metadata Inc.".
    """
    company_words = _words(company)
    for entry in blacklist:
        entry_words = _words(entry)
        if entry_words and entry_words.issubset(company_words):
            return entry
    return None


def _evaluate_salary(info: Dict[str, Any], prefs: JobPreferences) -> Dict[str, Any]:
    config = prefs.salary_config
    salary_max = info.get("salary_max")
    if salary_max is None:
        return _none_result(config, None, "Salary")

    if salary_max >= prefs.min_salary:
        reason = (
            f"Top-of-range salary (${salary_max:,}) meets minimum "
            f"(${prefs.min_salary:,})"
        )
        return _result(True, reason, config, salary_max)

    reason = (
        f"Top-of-range salary (${salary_max:,}) is below minimum "
        f"(${prefs.min_salary:,})"
    )
    return _result(False, reason, config, salary_max)


def _evaluate_membership(
    value: Optional[str],
    acceptable: List[str],
    config: CriterionConfig,
    label: str,
    unclear_value: str = "unclear",
) -> Dict[str, Any]:
    """Generic check: extracted ``value`` must be in ``acceptable``."""
    if not value or value == unclear_value:
        return _none_result(config, value, label)

    normalized = value.strip().lower()
    if normalized in acceptable:
        return _result(True, f"{label} '{value}' is acceptable", config, value)
    return _result(
        False,
        f"{label} '{value}' is not in acceptable list ({', '.join(acceptable)})",
        config,
        value,
    )


def _evaluate_visa(info: Dict[str, Any], prefs: JobPreferences) -> Dict[str, Any]:
    config = prefs.visa_config
    value = info.get("visa_sponsorship", "unclear")

    if not prefs.visa_sponsorship_required:
        return _result(True, "Visa sponsorship not required by user", config, value)

    if value == "unclear":
        return _none_result(config, value, "Visa sponsorship")

    if value == "yes":
        return _result(True, "Posting offers visa sponsorship", config, value)
    return _result(False, "Posting does not offer visa sponsorship", config, value)


def _evaluate_blacklist(info: Dict[str, Any], prefs: JobPreferences) -> Dict[str, Any]:
    config = prefs.blacklist_config
    company = info.get("company")

    if not prefs.company_blacklist:
        return _result(True, "No companies blacklisted", config, company)

    if not company or not str(company).strip():
        return _none_result(config, company, "Company")

    match = _find_blacklist_match(str(company), prefs.company_blacklist)
    if match is not None:
        return _result(
            False,
            f"Company '{company}' matches blacklist entry '{match}'",
            config,
            company,
        )
    return _result(True, f"Company '{company}' is not blacklisted", config, company)


def _evaluate_travel(info: Dict[str, Any], prefs: JobPreferences) -> Dict[str, Any]:
    config = prefs.travel_config
    value = info.get("travel_required", "unclear")

    if prefs.willing_to_travel:
        return _result(True, "User is willing to travel", config, value)

    if value == "unclear":
        return _none_result(config, value, "Travel requirement")

    if value == "yes":
        return _result(
            False, "Role requires travel but user is not willing", config, value
        )
    return _result(True, "Role does not require travel", config, value)


def _evaluate_education(info: Dict[str, Any], prefs: JobPreferences) -> Dict[str, Any]:
    config = prefs.education_config
    value = info.get("education_requirement", "unclear")

    if value == "unclear":
        return _none_result(config, value, "Education requirement")

    if value == "none":
        return _result(True, "Posting requires no specific degree", config, value)

    required_rank = _EDUCATION_RANK.get(value)
    user_rank = _EDUCATION_RANK.get(prefs.education_level, 0)
    if required_rank is None:
        return _none_result(config, value, "Education requirement")

    if user_rank >= required_rank:
        return _result(
            True,
            f"User education ({prefs.education_level}) meets requirement ({value})",
            config,
            value,
        )
    return _result(
        False,
        f"User education ({prefs.education_level}) is below requirement ({value})",
        config,
        value,
    )


def _evaluate_equity(info: Dict[str, Any], prefs: JobPreferences) -> Dict[str, Any]:
    config = prefs.equity_config
    offered = info.get("equity_offered") or []

    if not prefs.acceptable_equity_types:
        return _result(True, "No equity preference set", config, offered)

    # Limitation: the extraction schema defaults equity_offered to [] both when
    # the posting omits equity and when it explicitly states none, so the two
    # are indistinguishable here. Both are treated as "missing" and follow the
    # none policy rather than failing outright. Extracting a tri-state
    # (unclear/none/list) would be needed to tell them apart.
    if not offered:
        return _none_result(config, offered, "Equity")

    overlap = [e for e in prefs.acceptable_equity_types if e in offered]
    if overlap:
        return _result(
            True,
            f"Posting offers acceptable equity ({', '.join(overlap)})",
            config,
            offered,
        )
    return _result(
        False,
        f"Posting equity ({', '.join(offered)}) does not match preference",
        config,
        offered,
    )


def _evaluate_benefits(info: Dict[str, Any], prefs: JobPreferences) -> Dict[str, Any]:
    config = prefs.benefits_config
    offered = info.get("benefits_offered") or []

    if not prefs.required_benefits:
        return _result(True, "No benefits preference set", config, offered)

    # Same limitation as equity: an empty benefits_offered list conflates "not
    # mentioned" with "explicitly none", so both follow the none policy rather
    # than failing outright.
    if not offered:
        return _none_result(config, offered, "Benefits")

    missing = [b for b in prefs.required_benefits if b not in offered]
    if not missing:
        return _result(True, "Posting offers all required benefits", config, offered)
    return _result(
        False,
        f"Posting is missing required benefits ({', '.join(missing)})",
        config,
        offered,
    )


def evaluate_job_against_criteria(
    extracted_job_info: Dict[str, Any], preferences: JobPreferences
) -> Dict[str, Any]:
    """Evaluate extracted job information against user preferences.

    Args:
        extracted_job_info: Parsed job details (from the extraction schema).
        preferences: The user's job-search preferences.

    Returns:
        A dict mapping each rule-based criterion name to its result dict. The
        "fit" criterion is added separately by the workflow.
    """
    if not extracted_job_info:
        logger.warning("No extracted job information provided for evaluation")
        return {"error": "No extracted information available"}

    logger.info("Starting job evaluation against user preferences")

    results: Dict[str, Any] = {
        "salary": _evaluate_salary(extracted_job_info, preferences),
        "location": _evaluate_membership(
            extracted_job_info.get("location_policy"),
            preferences.acceptable_locations,
            preferences.location_config,
            "Location policy",
        ),
        "level": _evaluate_membership(
            extracted_job_info.get("role_type"),
            preferences.acceptable_levels,
            preferences.level_config,
            "Role type",
        ),
        "seniority": _evaluate_membership(
            extracted_job_info.get("seniority_level"),
            preferences.acceptable_seniority,
            preferences.seniority_config,
            "Seniority level",
        ),
        "visa": _evaluate_visa(extracted_job_info, preferences),
        "blacklist": _evaluate_blacklist(extracted_job_info, preferences),
        "employment_type": _evaluate_membership(
            extracted_job_info.get("employment_type"),
            preferences.acceptable_employment_types,
            preferences.employment_type_config,
            "Employment type",
        ),
        "travel": _evaluate_travel(extracted_job_info, preferences),
        "education": _evaluate_education(extracted_job_info, preferences),
        "equity": _evaluate_equity(extracted_job_info, preferences),
        "benefits": _evaluate_benefits(extracted_job_info, preferences),
    }

    passed_count = sum(1 for r in results.values() if r.get("pass"))
    logger.info(
        "Job evaluation completed: %d/%d criteria passed",
        passed_count,
        len(results),
    )

    return results
