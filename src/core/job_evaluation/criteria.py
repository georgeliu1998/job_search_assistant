"""
Job evaluation criteria configuration.

DEPRECATED: This module is deprecated. Use src.config (configs) instead.
This module now acts as a compatibility layer.
"""

import warnings


def _deprecation_warning():
    """Issue deprecation warning for this module."""
    warnings.warn(
        "src.core.job_evaluation.criteria is deprecated. Use 'from src.config import config' "
        "and access criteria via config.evaluation_criteria instead.",
        DeprecationWarning,
        stacklevel=3,
    )


def _get_evaluation_criteria():
    """Get evaluation criteria from new config system or fallback to hardcoded values."""
    try:
        from src.config import config

        criteria = config.evaluation_criteria
        return {
            "min_salary": criteria.min_salary,
            "remote_required": criteria.remote_required,
            "ic_title_requirements": criteria.ic_title_requirements,
        }
    except (ImportError, Exception):
        # Fall back to hardcoded criteria for prototype
        return {
            "min_salary": 160000,
            "remote_required": True,
            "ic_title_requirements": [
                "lead",
                "staff",
                "principal",
                "senior staff",
            ],  # For IC roles
        }


# Create a lazy-loaded EVALUATION_CRITERIA that issues deprecation warning
class _EvaluationCriteriaProxy:
    """Proxy object that issues deprecation warning and loads criteria."""

    def __init__(self):
        self._criteria = None

    def _load_criteria(self):
        if self._criteria is None:
            _deprecation_warning()
            self._criteria = _get_evaluation_criteria()
        return self._criteria

    def __getitem__(self, key):
        return self._load_criteria()[key]

    def __contains__(self, key):
        return key in self._load_criteria()

    def __iter__(self):
        return iter(self._load_criteria())

    def get(self, key, default=None):
        return self._load_criteria().get(key, default)

    def keys(self):
        return self._load_criteria().keys()

    def values(self):
        return self._load_criteria().values()

    def items(self):
        return self._load_criteria().items()


# Backward compatibility - acts like the old dict but with deprecation warning
EVALUATION_CRITERIA = _EvaluationCriteriaProxy()
