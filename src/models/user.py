"""User-related models for the job search assistant."""

from enum import StrEnum
from typing import List, Literal

from pydantic import BaseModel, Field


class CriterionMode(StrEnum):
    """Whether a criterion must pass for an APPLY recommendation."""

    REQUIRED = "required"  # Must pass for APPLY
    OPTIONAL = "optional"  # Evaluated and reported, but does not block APPLY


class NonePolicy(StrEnum):
    """How to treat a criterion when the job posting lacks the data to judge it."""

    PASS = "pass"  # Treat missing data as passing
    FAIL = "fail"  # Treat missing data as failing


class CriterionConfig(BaseModel):
    """Per-criterion configuration: required/optional and how to handle missing data."""

    mode: CriterionMode = CriterionMode.REQUIRED
    # Matches the JobPreferences product-wide default so hand-edited YAML with
    # only `mode` set picks up the same none_policy as the full factories.
    none_policy: NonePolicy = NonePolicy.PASS


def _config(mode: CriterionMode, none_policy: NonePolicy) -> CriterionConfig:
    """Helper to build a default CriterionConfig for use in default_factory."""
    return CriterionConfig(mode=mode, none_policy=none_policy)


class JobPreferences(BaseModel):
    """User job-search preferences used to evaluate postings.

    Each evaluable attribute pairs a value (what the user wants) with a
    ``CriterionConfig`` (whether it is required and how to treat missing data).
    """

    # --- Criterion values ---
    min_salary: int = Field(
        default=100_000, ge=0, description="Minimum acceptable annual salary (USD)"
    )
    acceptable_locations: List[Literal["onsite", "remote", "hybrid"]] = Field(
        default_factory=lambda: ["remote"],
        description="Acceptable work-location policies",
    )
    acceptable_levels: List[Literal["ic", "manager"]] = Field(
        default_factory=lambda: ["ic", "manager"],
        description="Acceptable role types",
    )
    acceptable_seniority: List[
        Literal["junior", "mid", "senior", "staff", "principal", "lead"]
    ] = Field(
        default_factory=lambda: ["senior", "staff", "principal", "lead"],
        description="Acceptable seniority levels",
    )
    visa_sponsorship_required: bool = Field(
        default=False, description="Whether the user requires visa sponsorship"
    )
    company_blacklist: List[str] = Field(
        default_factory=list, description="Companies the user will not apply to"
    )
    acceptable_employment_types: List[
        Literal["full-time", "part-time", "contract", "internship"]
    ] = Field(
        default_factory=lambda: ["full-time"],
        description="Acceptable employment types",
    )
    willing_to_travel: bool = Field(
        default=False, description="Whether the user is willing to travel"
    )
    education_level: Literal["associate", "bachelor", "master", "phd"] = Field(
        default="bachelor", description="The user's own highest education level"
    )
    acceptable_equity_types: List[Literal["stock_options", "rsus"]] = Field(
        default_factory=list,
        description="Equity types the user wants (empty = no equity preference)",
    )
    required_benefits: List[
        Literal["health", "vision", "dental", "life", "std", "ltd", "401k", "pto"]
    ] = Field(
        default_factory=list,
        description="Benefits the user requires (empty = no benefit preference)",
    )

    # --- Fit profile (used by the LLM fit evaluation) ---
    target_role_description: str = Field(
        default="",
        description="Free-text description of the user's target role and focus",
    )
    key_skills: List[str] = Field(
        default_factory=list, description="The user's key skills"
    )

    # --- Per-criterion configuration ---
    # Note: every criterion defaults to none_policy=PASS so that a posting only
    # fails a criterion when it explicitly contains disqualifying info, never
    # just for omitting it (casting a wide net).
    salary_config: CriterionConfig = Field(
        default_factory=lambda: _config(CriterionMode.REQUIRED, NonePolicy.PASS)
    )
    location_config: CriterionConfig = Field(
        default_factory=lambda: _config(CriterionMode.REQUIRED, NonePolicy.PASS)
    )
    level_config: CriterionConfig = Field(
        default_factory=lambda: _config(CriterionMode.OPTIONAL, NonePolicy.PASS)
    )
    seniority_config: CriterionConfig = Field(
        default_factory=lambda: _config(CriterionMode.OPTIONAL, NonePolicy.PASS)
    )
    visa_config: CriterionConfig = Field(
        default_factory=lambda: _config(CriterionMode.OPTIONAL, NonePolicy.PASS)
    )
    blacklist_config: CriterionConfig = Field(
        default_factory=lambda: _config(CriterionMode.REQUIRED, NonePolicy.PASS)
    )
    employment_type_config: CriterionConfig = Field(
        default_factory=lambda: _config(CriterionMode.REQUIRED, NonePolicy.PASS)
    )
    travel_config: CriterionConfig = Field(
        default_factory=lambda: _config(CriterionMode.OPTIONAL, NonePolicy.PASS)
    )
    education_config: CriterionConfig = Field(
        default_factory=lambda: _config(CriterionMode.OPTIONAL, NonePolicy.PASS)
    )
    equity_config: CriterionConfig = Field(
        default_factory=lambda: _config(CriterionMode.OPTIONAL, NonePolicy.PASS)
    )
    benefits_config: CriterionConfig = Field(
        default_factory=lambda: _config(CriterionMode.OPTIONAL, NonePolicy.PASS)
    )
    fit_config: CriterionConfig = Field(
        # Optional + pass by default so a fresh user with no target role
        # description does not get DO_NOT_APPLY for every job.
        default_factory=lambda: _config(CriterionMode.OPTIONAL, NonePolicy.PASS)
    )
