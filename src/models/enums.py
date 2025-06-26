"""Enums used across the job search assistant models."""

from enum import Enum


class Environment(Enum):
    """Application deployment environments."""

    DEV = "dev"
    STAGE = "stage"
    PROD = "prod"

    @property
    def full_name(self) -> str:
        """Get the full environment name."""
        mapping = {
            self.DEV: "development",
            self.STAGE: "staging",
            self.PROD: "production",
        }
        return mapping[self]

    @classmethod
    def from_string(cls, env_str: str) -> "Environment":
        """Create Environment from string, supporting both short and full forms."""
        env_str = env_str.lower().strip()

        # Direct mapping for short forms
        for env in cls:
            if env.value == env_str:
                return env

        # Mapping for full forms
        full_form_mapping = {
            "development": cls.DEV,
            "staging": cls.STAGE,
            "production": cls.PROD,
        }

        if env_str in full_form_mapping:
            return full_form_mapping[env_str]

        valid_values = ", ".join([e.value for e in cls])
        raise ValueError(
            f"Invalid environment: '{env_str}'. Valid values: {valid_values}"
        )


class JobSource(Enum):
    """Source platforms for job postings."""

    LINKEDIN = "linkedin"
    INDEED = "indeed"
    ZIPRECRUITER = "ziprecruiter"
    OTHER = "other"


class JobStatus(Enum):
    """Status of a job application in the pipeline."""

    PENDING_EVALUATION = "pending_evaluation"
    EVALUATING = "evaluating"
    PASS = "pass"
    REJECT = "reject"
    APPLIED = "applied"
    INTERVIEWING = "interviewing"
    OFFER = "offer"
    HIRED = "hired"
