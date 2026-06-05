"""
Unit tests for job recommendation core logic.
"""

from src.core.job_evaluation.recommender import generate_recommendation_from_evaluation


def _crit(passed, mode="required", reason="reason"):
    return {"pass": passed, "reason": reason, "mode": mode, "extracted_value": None}


class TestGenerateRecommendation:
    def test_all_required_pass_recommends_apply(self):
        evaluation = {
            "salary": _crit(True),
            "location": _crit(True),
        }
        rec, reasoning = generate_recommendation_from_evaluation(evaluation)
        assert rec == "APPLY"
        assert "All required criteria passed" in reasoning

    def test_required_failure_blocks_apply(self):
        evaluation = {
            "salary": _crit(False, reason="Salary too low"),
            "location": _crit(True),
        }
        rec, reasoning = generate_recommendation_from_evaluation(evaluation)
        assert rec == "DO_NOT_APPLY"
        # Reasoning is brief: lists failed criterion names, not full reasons
        # (the breakdown UI shows the per-criterion reasons).
        assert reasoning == "Required criteria failed: salary."

    def test_optional_failure_does_not_block(self):
        """An optional criterion failing must not change APPLY."""
        evaluation = {
            "salary": _crit(True),
            "benefits": _crit(False, mode="optional", reason="Missing dental"),
        }
        rec, reasoning = generate_recommendation_from_evaluation(evaluation)
        assert rec == "APPLY"
        assert "Optional concerns" in reasoning
        assert "benefits" in reasoning
        # Full per-criterion reason text stays out of the recommender summary.
        assert "Missing dental" not in reasoning

    def test_required_failure_reports_optional_concerns_too(self):
        evaluation = {
            "salary": _crit(False, reason="Salary too low"),
            "benefits": _crit(False, mode="optional", reason="Missing dental"),
        }
        rec, reasoning = generate_recommendation_from_evaluation(evaluation)
        assert rec == "DO_NOT_APPLY"
        assert "Required criteria failed: salary." in reasoning
        assert "Optional concerns: benefits." in reasoning

    def test_multiple_required_failures_listed_with_readable_names(self):
        evaluation = {
            "salary": _crit(False),
            "employment_type": _crit(False),
            "location": _crit(True),
        }
        _, reasoning = generate_recommendation_from_evaluation(evaluation)
        # underscores normalized to spaces for readability
        assert reasoning == "Required criteria failed: salary, employment type."

    def test_empty_returns_error(self):
        rec, reasoning = generate_recommendation_from_evaluation({})
        assert rec == "ERROR"

    def test_error_key_returns_error(self):
        rec, _ = generate_recommendation_from_evaluation({"error": "boom"})
        assert rec == "ERROR"

    def test_malformed_entries_ignored(self):
        evaluation = {
            "salary": _crit(True),
            "junk": "not a dict",
            "missing_mode": {"pass": False, "reason": "x"},
        }
        rec, _ = generate_recommendation_from_evaluation(evaluation)
        assert rec == "APPLY"
