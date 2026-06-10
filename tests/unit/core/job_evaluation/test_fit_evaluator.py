"""
Unit tests for the LLM-based fit evaluator.
"""

from unittest.mock import Mock, patch

from src.core.job_evaluation.fit_evaluator import FitAssessment, evaluate_fit
from src.models.user import CriterionConfig, JobPreferences


class TestEvaluateFit:
    def test_skips_when_no_target_role(self):
        """With no target role description, fit is not assessed (no LLM call)."""
        prefs = JobPreferences(target_role_description="")
        # Default fit none_policy is PASS.
        result = evaluate_fit("some job text", prefs)
        assert result["pass"] is True
        assert result["extracted_value"] is None

    def test_skip_respects_fail_none_policy(self):
        prefs = JobPreferences(target_role_description="")
        prefs.fit_config = CriterionConfig(mode="required", none_policy="fail")
        result = evaluate_fit("some job text", prefs)
        assert result["pass"] is False

    @patch("src.core.job_evaluation.fit_evaluator.get_chat_model")
    def test_good_fit_passes(self, mock_get_model):
        structured = Mock()
        structured.invoke.return_value = FitAssessment(
            verdict="good_fit", reasoning="Strong alignment with LLM focus"
        )
        model = Mock()
        model.with_structured_output.return_value = structured
        mock_get_model.return_value = model

        prefs = JobPreferences(
            target_role_description="AI Engineer focused on LLMs",
            key_skills=["Python", "RAG"],
        )
        result = evaluate_fit("AI Engineer building RAG systems", prefs)

        assert result["pass"] is True
        assert result["extracted_value"] == "good_fit"

    @patch("src.core.job_evaluation.fit_evaluator.get_chat_model")
    def test_poor_fit_fails(self, mock_get_model):
        structured = Mock()
        structured.invoke.return_value = FitAssessment(
            verdict="poor_fit", reasoning="Role is A/B testing focused"
        )
        model = Mock()
        model.with_structured_output.return_value = structured
        mock_get_model.return_value = model

        prefs = JobPreferences(target_role_description="AI Engineer focused on LLMs")
        result = evaluate_fit("Data Scientist for A/B testing", prefs)

        assert result["pass"] is False
        assert result["extracted_value"] == "poor_fit"

    @patch("src.core.job_evaluation.fit_evaluator.get_chat_model")
    def test_llm_failure_falls_back_to_none_policy(self, mock_get_model):
        """A transient LLM failure must not raise; it returns a graceful result."""
        structured = Mock()
        structured.invoke.side_effect = RuntimeError("503 service unavailable")
        model = Mock()
        model.with_structured_output.return_value = structured
        mock_get_model.return_value = model

        # Default fit none_policy is PASS.
        prefs = JobPreferences(target_role_description="AI Engineer focused on LLMs")
        result = evaluate_fit("some job text", prefs)

        assert result["pass"] is True
        assert "Fit assessment failed" in result["reason"]
        assert result["extracted_value"] is None

    @patch("src.core.job_evaluation.fit_evaluator.get_chat_model")
    def test_llm_failure_with_fail_none_policy(self, mock_get_model):
        structured = Mock()
        structured.invoke.side_effect = RuntimeError("boom")
        model = Mock()
        model.with_structured_output.return_value = structured
        mock_get_model.return_value = model

        prefs = JobPreferences(target_role_description="AI Engineer focused on LLMs")
        prefs.fit_config = CriterionConfig(mode="required", none_policy="fail")
        result = evaluate_fit("some job text", prefs)

        assert result["pass"] is False
        assert "Fit assessment failed" in result["reason"]

    @patch("src.core.job_evaluation.fit_evaluator.get_chat_model")
    def test_model_construction_failure_does_not_raise(self, mock_get_model):
        """A failure before the LLM call (e.g. provider ImportError) is caught too."""
        mock_get_model.side_effect = ImportError("provider package missing")

        # Default fit none_policy is PASS.
        prefs = JobPreferences(target_role_description="AI Engineer focused on LLMs")
        result = evaluate_fit("some job text", prefs)

        assert result["pass"] is True
        assert "Fit assessment failed" in result["reason"]
        assert result["extracted_value"] is None
