"""
LLM-based fit assessment.

Unlike the rule-based criteria in :mod:`src.core.job_evaluation.evaluator`,
this criterion uses an LLM to judge semantic alignment between the user's
target role/skills and the job's actual focus.
"""

from typing import Any, Dict, Literal

from langchain_core.messages import HumanMessage
from pydantic import BaseModel, Field

from src.agent.prompts.evaluation.fit import FIT_ASSESSMENT_PROMPT
from src.config import config
from src.llm import get_chat_model_by_profile_name, langfuse_manager
from src.models.user import JobPreferences, NonePolicy
from src.utils.logging import get_logger
from src.utils.text import (
    MAX_JOB_DESCRIPTION_CHARS,
    MAX_ROLE_DESCRIPTION_CHARS,
    truncate_text,
)

logger = get_logger(__name__)


class FitAssessment(BaseModel):
    """Structured output for the fit assessment LLM call."""

    verdict: Literal["good_fit", "poor_fit"] = Field(
        ..., description="Whether the job is a good fit for the candidate"
    )
    reasoning: str = Field(..., description="Short explanation for the verdict")


def _result(
    passed: bool, reason: str, config_obj, extracted_value: Any
) -> Dict[str, Any]:
    """Build a criterion result dict matching the rule-based evaluator shape."""
    return {
        "pass": passed,
        "reason": reason,
        "mode": config_obj.mode.value,
        "extracted_value": extracted_value,
    }


def evaluate_fit(job_posting_text: str, preferences: JobPreferences) -> Dict[str, Any]:
    """Assess fit between the posting and the user's profile via an LLM call.

    Skipped (treated per ``fit_config.none_policy``) when the user has not
    provided a target role description.

    Args:
        job_posting_text: Raw job posting text.
        preferences: The user's job-search preferences.

    Returns:
        A criterion result dict with the same shape as the rule-based criteria.
    """
    fit_config = preferences.fit_config

    if not preferences.target_role_description.strip():
        passed = fit_config.none_policy == NonePolicy.PASS
        decision = "pass" if passed else "fail"
        reason = (
            "No target role description provided; fit not assessed and counted "
            f"as {decision} per preference"
        )
        return _result(passed, reason, fit_config, None)

    model = get_chat_model_by_profile_name(config.agents.job_evaluation_fit)
    structured_llm = model.with_structured_output(FitAssessment)

    prompt_content = FIT_ASSESSMENT_PROMPT.format(
        target_role_description=truncate_text(
            preferences.target_role_description,
            MAX_ROLE_DESCRIPTION_CHARS,
            "target role description",
        ),
        key_skills=", ".join(preferences.key_skills) or "(none provided)",
        job_text=truncate_text(
            job_posting_text, MAX_JOB_DESCRIPTION_CHARS, "job posting"
        ),
    )

    config_dict = langfuse_manager.get_config()
    logger.info("Assessing job fit via LLM")
    assessment: FitAssessment = structured_llm.invoke(
        [HumanMessage(content=prompt_content)], config=config_dict
    )

    passed = assessment.verdict == "good_fit"
    return _result(passed, assessment.reasoning, fit_config, assessment.verdict)
