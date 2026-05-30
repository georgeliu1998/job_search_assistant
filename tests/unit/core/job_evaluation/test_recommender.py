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
        assert "Salary too low" in reasoning

    def test_optional_failure_does_not_block(self):
        """An optional criterion failing must not change APPLY."""
        evaluation = {
            "salary": _crit(True),
            "benefits": _crit(False, mode="optional", reason="Missing dental"),
        }
        rec, reasoning = generate_recommendation_from_evaluation(evaluation)
        assert rec == "APPLY"
        assert "Optional concerns" in reasoning
        assert "Missing dental" in reasoning

    def test_required_failure_reports_optional_concerns_too(self):
        evaluation = {
            "salary": _crit(False, reason="Salary too low"),
            "benefits": _crit(False, mode="optional", reason="Missing dental"),
        }
        rec, reasoning = generate_recommendation_from_evaluation(evaluation)
        assert rec == "DO_NOT_APPLY"
        assert "Salary too low" in reasoning
        assert "Missing dental" in reasoning

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
