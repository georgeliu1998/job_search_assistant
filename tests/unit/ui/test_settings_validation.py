"""
Unit tests for the Settings page validation helper.

The Settings page itself is Streamlit-driven and exercised manually, but the
pure validation helper is testable in isolation.
"""

from ui.pages.settings import (
    SALARY_TIERS,
    _salary_slider_options,
    _validate_required_lists,
)


class TestSalarySliderOptions:
    def test_persisted_tier_value_keeps_tiers(self):
        assert _salary_slider_options(100000) == sorted(SALARY_TIERS)

    def test_non_tier_value_is_included_and_sorted(self):
        options = _salary_slider_options(90000)
        assert 90000 in options
        assert options == sorted(options)
        # The fixed tiers are still present.
        assert set(SALARY_TIERS).issubset(options)

    def test_value_above_range_is_included(self):
        options = _salary_slider_options(300000)
        assert options[-1] == 300000

    def test_no_duplicate_when_value_is_a_tier(self):
        options = _salary_slider_options(60000)
        assert options.count(60000) == 1


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
