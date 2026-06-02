"""
Unit tests for individual job evaluation workflow nodes.
"""

from src.agent.workflows.job_evaluation.main import extract_job_info, validate_input
from src.agent.workflows.job_evaluation.states import JobEvaluationState
from src.utils.text import MAX_JOB_DESCRIPTION_CHARS


class TestValidateInput:
    def test_empty_text_returns_error(self):
        out = validate_input(JobEvaluationState(job_posting_text="   "))
        assert out["recommendation"] == "ERROR"

    def test_bounds_text_once_and_stores_on_state(self):
        long_text = "x" * (MAX_JOB_DESCRIPTION_CHARS + 500)
        out = validate_input(JobEvaluationState(job_posting_text=long_text))

        bounded = out["job_posting_text"]
        assert bounded.endswith("[truncated]")
        assert len(bounded) <= MAX_JOB_DESCRIPTION_CHARS + len("\n[truncated]")

    def test_short_text_is_left_unchanged(self):
        out = validate_input(JobEvaluationState(job_posting_text="Short JD"))
        assert out["job_posting_text"] == "Short JD"


class TestExtractUsesBoundedText:
    def test_extract_does_not_re_truncate(self, monkeypatch):
        """extract_job_info should pass state text straight through (already bounded)."""
        captured = {}

        def fake_extract(text):
            captured["text"] = text
            return {"title": "Engineer", "company": "Acme", "salary_max": 200000}

        monkeypatch.setattr(
            "src.agent.workflows.job_evaluation.main.extract_job_posting",
            fake_extract,
        )
        monkeypatch.setattr(
            "src.agent.workflows.job_evaluation.main.validate_extraction_result",
            lambda result, schema: True,
        )

        state = JobEvaluationState(job_posting_text="already bounded text")
        extract_job_info(state)
        assert captured["text"] == "already bounded text"
