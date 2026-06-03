"""
Unit tests for the job results display helpers.

The render functions themselves are Streamlit-driven and exercised manually;
this module covers the pure helpers.
"""

from ui.components.job_results import _criterion_icon, _escape_md


class TestEscapeMd:
    def test_dollars_are_escaped(self):
        """Streamlit treats $...$ as LaTeX math; escape so dollars render literally."""
        assert _escape_md("$100,000") == r"\$100,000"
        assert _escape_md("$10 - $20") == r"\$10 - \$20"

    def test_text_without_dollars_unchanged(self):
        assert _escape_md("plain text") == "plain text"

    def test_handles_non_string(self):
        assert _escape_md(100) == "100"


class TestCriterionIcon:
    def test_required_pass(self):
        assert _criterion_icon({"pass": True, "mode": "required"}) == "✅"

    def test_required_fail(self):
        assert _criterion_icon({"pass": False, "mode": "required"}) == "❌"

    def test_optional_pass(self):
        assert _criterion_icon({"pass": True, "mode": "optional"}) == "🟢"

    def test_optional_fail(self):
        assert _criterion_icon({"pass": False, "mode": "optional"}) == "🟡"
