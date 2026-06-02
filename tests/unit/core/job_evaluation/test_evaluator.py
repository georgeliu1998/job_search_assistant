"""
Unit tests for core job evaluation logic.
"""

from src.core.job_evaluation import evaluate_job_against_criteria
from src.models.user import CriterionConfig, JobPreferences


def _full_match_info():
    """Extracted info that passes the default preferences across the board."""
    return {
        "title": "Staff Software Engineer",
        "company": "TechCorp",
        "salary_min": 150000,
        "salary_max": 180000,
        "location_policy": "remote",
        "role_type": "ic",
        "seniority_level": "staff",
        "visa_sponsorship": "yes",
        "employment_type": "full-time",
        "travel_required": "no",
        "education_requirement": "bachelor",
        "equity_offered": ["rsus"],
        "benefits_offered": ["health", "dental", "401k", "pto"],
    }


class TestSalaryCriterion:
    def test_salary_passes_when_max_meets_floor(self):
        prefs = JobPreferences(min_salary=100000)
        result = evaluate_job_against_criteria(_full_match_info(), prefs)
        assert result["salary"]["pass"] is True

    def test_high_range_passes_low_floor(self):
        """A $200k-$250k posting passes a $100k floor (regression guard)."""
        prefs = JobPreferences(min_salary=100000)
        info = _full_match_info()
        info.update(salary_min=200000, salary_max=250000)
        result = evaluate_job_against_criteria(info, prefs)
        assert result["salary"]["pass"] is True

    def test_salary_below_floor_fails(self):
        prefs = JobPreferences(min_salary=160000)
        info = _full_match_info()
        info["salary_max"] = 120000
        result = evaluate_job_against_criteria(info, prefs)
        assert result["salary"]["pass"] is False

    def test_missing_salary_defaults_to_pass(self):
        info = _full_match_info()
        info["salary_max"] = None
        # Default salary none_policy is PASS (wide net).
        result = evaluate_job_against_criteria(info, JobPreferences())
        assert result["salary"]["pass"] is True

    def test_missing_salary_fails_with_fail_policy(self):
        info = _full_match_info()
        info["salary_max"] = None
        prefs = JobPreferences()
        prefs.salary_config = CriterionConfig(mode="required", none_policy="fail")
        result = evaluate_job_against_criteria(info, prefs)
        assert result["salary"]["pass"] is False


class TestMembershipCriteria:
    def test_location_not_acceptable_fails(self):
        prefs = JobPreferences(acceptable_locations=["remote"])
        info = _full_match_info()
        info["location_policy"] = "onsite"
        result = evaluate_job_against_criteria(info, prefs)
        assert result["location"]["pass"] is False

    def test_seniority_not_acceptable_fails(self):
        prefs = JobPreferences(acceptable_seniority=["staff", "principal"])
        info = _full_match_info()
        info["seniority_level"] = "junior"
        result = evaluate_job_against_criteria(info, prefs)
        assert result["seniority"]["pass"] is False

    def test_unclear_membership_defaults_to_pass(self):
        info = _full_match_info()
        info["location_policy"] = "unclear"
        # Default location none_policy is PASS (wide net).
        result = evaluate_job_against_criteria(info, JobPreferences())
        assert result["location"]["pass"] is True

    def test_unclear_membership_fails_with_fail_policy(self):
        info = _full_match_info()
        info["location_policy"] = "unclear"
        prefs = JobPreferences()
        prefs.location_config = CriterionConfig(mode="required", none_policy="fail")
        result = evaluate_job_against_criteria(info, prefs)
        assert result["location"]["pass"] is False


class TestVisaCriterion:
    def test_not_required_always_passes(self):
        prefs = JobPreferences(visa_sponsorship_required=False)
        info = _full_match_info()
        info["visa_sponsorship"] = "no"
        result = evaluate_job_against_criteria(info, prefs)
        assert result["visa"]["pass"] is True

    def test_required_and_not_offered_fails(self):
        prefs = JobPreferences(visa_sponsorship_required=True)
        info = _full_match_info()
        info["visa_sponsorship"] = "no"
        result = evaluate_job_against_criteria(info, prefs)
        assert result["visa"]["pass"] is False


class TestBlacklistCriterion:
    def test_empty_blacklist_passes(self):
        prefs = JobPreferences(company_blacklist=[])
        result = evaluate_job_against_criteria(_full_match_info(), prefs)
        assert result["blacklist"]["pass"] is True

    def test_word_boundary_match_fails(self):
        prefs = JobPreferences(company_blacklist=["Microsoft"])
        info = _full_match_info()
        info["company"] = "Microsoft Co. Ltd."
        result = evaluate_job_against_criteria(info, prefs)
        assert result["blacklist"]["pass"] is False

    def test_partial_word_does_not_match(self):
        prefs = JobPreferences(company_blacklist=["Meta"])
        info = _full_match_info()
        info["company"] = "Metadata Inc."
        result = evaluate_job_against_criteria(info, prefs)
        assert result["blacklist"]["pass"] is True


class TestTravelCriterion:
    def test_willing_always_passes(self):
        prefs = JobPreferences(willing_to_travel=True)
        info = _full_match_info()
        info["travel_required"] = "yes"
        result = evaluate_job_against_criteria(info, prefs)
        assert result["travel"]["pass"] is True

    def test_not_willing_and_required_fails(self):
        prefs = JobPreferences(willing_to_travel=False)
        info = _full_match_info()
        info["travel_required"] = "yes"
        result = evaluate_job_against_criteria(info, prefs)
        assert result["travel"]["pass"] is False


class TestEducationCriterion:
    def test_user_meets_requirement(self):
        prefs = JobPreferences(education_level="master")
        info = _full_match_info()
        info["education_requirement"] = "bachelor"
        result = evaluate_job_against_criteria(info, prefs)
        assert result["education"]["pass"] is True

    def test_user_below_requirement_fails(self):
        prefs = JobPreferences(education_level="bachelor")
        info = _full_match_info()
        info["education_requirement"] = "phd"
        result = evaluate_job_against_criteria(info, prefs)
        assert result["education"]["pass"] is False

    def test_none_requirement_passes(self):
        prefs = JobPreferences(education_level="associate")
        info = _full_match_info()
        info["education_requirement"] = "none"
        result = evaluate_job_against_criteria(info, prefs)
        assert result["education"]["pass"] is True


class TestEquityAndBenefits:
    def test_equity_no_preference_passes(self):
        prefs = JobPreferences(acceptable_equity_types=[])
        info = _full_match_info()
        info["equity_offered"] = []
        result = evaluate_job_against_criteria(info, prefs)
        assert result["equity"]["pass"] is True

    def test_equity_overlap_passes(self):
        prefs = JobPreferences(acceptable_equity_types=["rsus"])
        info = _full_match_info()
        info["equity_offered"] = ["rsus", "stock_options"]
        result = evaluate_job_against_criteria(info, prefs)
        assert result["equity"]["pass"] is True

    def test_benefits_missing_required_fails(self):
        prefs = JobPreferences(required_benefits=["health", "401k"])
        info = _full_match_info()
        info["benefits_offered"] = ["health"]
        result = evaluate_job_against_criteria(info, prefs)
        assert result["benefits"]["pass"] is False


class TestResultShape:
    def test_each_result_has_required_keys(self):
        result = evaluate_job_against_criteria(_full_match_info(), JobPreferences())
        for criterion in result.values():
            assert set(criterion) == {"pass", "reason", "mode", "extracted_value"}

    def test_mode_reflects_config(self):
        prefs = JobPreferences()
        prefs.salary_config = CriterionConfig(mode="optional", none_policy="pass")
        result = evaluate_job_against_criteria(_full_match_info(), prefs)
        assert result["salary"]["mode"] == "optional"

    def test_empty_info_returns_error(self):
        assert "error" in evaluate_job_against_criteria({}, JobPreferences())
