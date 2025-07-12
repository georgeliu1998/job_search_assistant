"""
Unit tests for job recommendation core logic.

This module tests the recommendation generation functionality
in the core business logic layer.
"""

import pytest

from src.core.job_evaluation.recommender import generate_recommendation_from_evaluation


class TestGenerateRecommendationFromEvaluation:
    """Test the core recommendation generation function."""

    def test_all_criteria_passed_should_recommend_apply(self):
        """Test recommendation when all criteria pass."""
        evaluation_result = {
            "salary": {"pass": True, "reason": "Salary meets requirement"},
            "remote": {"pass": True, "reason": "Position is remote"},
            "title_level": {
                "pass": True,
                "reason": "IC role has appropriate seniority",
            },
        }

        recommendation, reasoning = generate_recommendation_from_evaluation(
            evaluation_result
        )

        assert recommendation == "APPLY"
        assert "All criteria passed" in reasoning
        assert "salary: Salary meets requirement" in reasoning
        assert "remote: Position is remote" in reasoning
        assert "title_level: IC role has appropriate seniority" in reasoning

    def test_some_criteria_failed_should_recommend_do_not_apply(self):
        """Test recommendation when some criteria fail."""
        evaluation_result = {
            "salary": {"pass": True, "reason": "Salary meets requirement"},
            "remote": {"pass": False, "reason": "Position is not remote"},
            "title_level": {"pass": False, "reason": "IC role lacks seniority"},
        }

        recommendation, reasoning = generate_recommendation_from_evaluation(
            evaluation_result
        )

        assert recommendation == "DO_NOT_APPLY"
        assert "Failed criteria" in reasoning
        assert "remote: Position is not remote" in reasoning
        assert "title_level: IC role lacks seniority" in reasoning
        assert (
            "salary: Salary meets requirement" not in reasoning
        )  # Only failed criteria in reasoning

    def test_all_criteria_failed_should_recommend_do_not_apply(self):
        """Test recommendation when all criteria fail."""
        evaluation_result = {
            "salary": {"pass": False, "reason": "Salary too low"},
            "remote": {"pass": False, "reason": "Position is not remote"},
            "title_level": {"pass": False, "reason": "IC role lacks seniority"},
        }

        recommendation, reasoning = generate_recommendation_from_evaluation(
            evaluation_result
        )

        assert recommendation == "DO_NOT_APPLY"
        assert "Failed criteria" in reasoning
        assert "salary: Salary too low" in reasoning
        assert "remote: Position is not remote" in reasoning
        assert "title_level: IC role lacks seniority" in reasoning

    def test_single_criterion_passed_should_recommend_do_not_apply(self):
        """Test recommendation with only one criterion passing."""
        evaluation_result = {
            "salary": {"pass": True, "reason": "Salary meets requirement"},
            "remote": {"pass": False, "reason": "Position is not remote"},
        }

        recommendation, reasoning = generate_recommendation_from_evaluation(
            evaluation_result
        )

        assert recommendation == "DO_NOT_APPLY"
        assert "Failed criteria" in reasoning
        assert "remote: Position is not remote" in reasoning

    def test_empty_evaluation_result_should_return_error(self):
        """Test recommendation with empty evaluation result."""
        recommendation, reasoning = generate_recommendation_from_evaluation({})

        assert recommendation == "ERROR"
        assert reasoning == "Unable to evaluate job posting"

    def test_none_evaluation_result_should_return_error(self):
        """Test recommendation with None evaluation result."""
        recommendation, reasoning = generate_recommendation_from_evaluation(None)

        assert recommendation == "ERROR"
        assert reasoning == "Unable to evaluate job posting"

    def test_evaluation_result_with_error_should_return_error(self):
        """Test recommendation when evaluation result contains error."""
        evaluation_result = {"error": "Evaluation failed"}

        recommendation, reasoning = generate_recommendation_from_evaluation(
            evaluation_result
        )

        assert recommendation == "ERROR"
        assert reasoning == "Unable to evaluate job posting"

    def test_malformed_evaluation_result_should_handle_gracefully(self):
        """Test recommendation with malformed evaluation result."""
        evaluation_result = {
            "salary": {"pass": True, "reason": "Salary meets requirement"},
            "malformed": "not a dict",  # Malformed criterion
            "remote": {"pass": False, "reason": "Position is not remote"},
        }

        recommendation, reasoning = generate_recommendation_from_evaluation(
            evaluation_result
        )

        # Should still work, ignoring malformed entries
        assert recommendation == "DO_NOT_APPLY"
        assert "Failed criteria" in reasoning
        assert "remote: Position is not remote" in reasoning
        assert "salary: Salary meets requirement" not in reasoning

    def test_evaluation_result_missing_pass_field_should_handle_gracefully(self):
        """Test recommendation with evaluation result missing 'pass' field."""
        evaluation_result = {
            "salary": {"reason": "Salary meets requirement"},  # Missing 'pass' field
            "remote": {"pass": False, "reason": "Position is not remote"},
        }

        recommendation, reasoning = generate_recommendation_from_evaluation(
            evaluation_result
        )

        # Should still work, ignoring malformed entries
        assert recommendation == "DO_NOT_APPLY"
        assert "Failed criteria" in reasoning
        assert "remote: Position is not remote" in reasoning

    def test_evaluation_result_with_no_valid_criteria_should_recommend_apply(self):
        """Test recommendation when no valid criteria are found."""
        evaluation_result = {
            "malformed1": "not a dict",
            "malformed2": {"reason": "missing pass field"},
        }

        recommendation, reasoning = generate_recommendation_from_evaluation(
            evaluation_result
        )

        # If no valid criteria found, no failed criteria means APPLY
        assert recommendation == "APPLY"
        assert "All criteria passed" in reasoning

    def test_mixed_valid_and_invalid_criteria_should_work_correctly(self):
        """Test recommendation with mix of valid and invalid criteria."""
        evaluation_result = {
            "salary": {"pass": True, "reason": "Salary meets requirement"},
            "invalid": "not a dict",
            "remote": {"pass": False, "reason": "Position is not remote"},
            "malformed": {"reason": "missing pass field"},
            "title_level": {
                "pass": True,
                "reason": "IC role has appropriate seniority",
            },
        }

        recommendation, reasoning = generate_recommendation_from_evaluation(
            evaluation_result
        )

        assert recommendation == "DO_NOT_APPLY"
        assert "Failed criteria" in reasoning
        assert "remote: Position is not remote" in reasoning
        # Should ignore invalid/malformed entries and only consider valid ones
