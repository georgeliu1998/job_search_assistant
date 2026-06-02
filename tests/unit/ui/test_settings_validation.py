"""
Unit tests for the Settings page validation helper.

The Settings page itself is Streamlit-driven and exercised manually, but the
pure validation helper is testable in isolation.
"""

from ui.pages.settings import _validate_required_lists


class TestValidateRequiredLists:
    def test_all_populated_returns_no_errors(self):
        errors = _validate_required_lists(
            acceptable_locations=["remote"],
            acceptable_employment_types=["full-time"],
            acceptable_levels=["ic"],
            acceptable_seniority=["senior"],
        )
        assert errors == []

    def test_each_empty_list_reports_one_error(self):
        errors = _validate_required_lists(
            acceptable_locations=[],
            acceptable_employment_types=["full-time"],
            acceptable_levels=["ic"],
            acceptable_seniority=["senior"],
        )
        assert len(errors) == 1
        assert "location" in errors[0]

    def test_all_empty_reports_all_errors(self):
        errors = _validate_required_lists([], [], [], [])
        assert len(errors) == 4
