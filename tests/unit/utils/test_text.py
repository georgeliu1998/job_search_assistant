"""
Unit tests for text utilities.
"""

from src.utils.text import truncate_text


class TestTruncateText:
    def test_within_limit_unchanged(self):
        text = "short text"
        assert truncate_text(text, 100) == text

    def test_over_limit_truncated_with_marker(self):
        text = "a" * 50
        result = truncate_text(text, 10, "job posting")
        assert result.startswith("a" * 10)
        assert result.endswith("[truncated]")
        assert len(result) <= 10 + len("\n[truncated]")

    def test_exact_limit_unchanged(self):
        text = "a" * 10
        assert truncate_text(text, 10) == text

    def test_none_passthrough(self):
        assert truncate_text(None, 10) is None
