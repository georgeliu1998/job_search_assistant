"""
Unit tests for core job evaluation logic
"""

import pytest

from src.core.job_evaluation import evaluate_job_against_criteria


class TestEvaluateJobAgainstCriteria:
    """Test the core job evaluation function"""

    def test_all_criteria_pass(self):
        """Test job that meets all criteria"""
        job_info = {
            "salary_max": 180000,
            "location_policy": "Remote",
            "role_type": "IC",
            "title": "Staff Software Engineer",
        }

        result = evaluate_job_against_criteria(job_info)

        assert result["salary"]["pass"] is True
        assert result["remote"]["pass"] is True
        assert result["title_level"]["pass"] is True

    def test_low_salary_fails(self):
        """Test job with salary below minimum"""
        job_info = {
            "salary_max": 120000,  # Below 160k minimum
            "location_policy": "Remote",
            "role_type": "IC",
            "title": "Staff Software Engineer",
        }

        result = evaluate_job_against_criteria(job_info)

        assert result["salary"]["pass"] is False
        assert "lower than required" in result["salary"]["reason"]

    def test_missing_salary_fails(self):
        """Test job with no salary information"""
        job_info = {
            "location_policy": "Remote",
            "role_type": "IC",
            "title": "Staff Software Engineer",
        }

        result = evaluate_job_against_criteria(job_info)

        assert result["salary"]["pass"] is False
        assert result["salary"]["reason"] == "Salary not specified"

    def test_not_remote_fails(self):
        """Test job that is not remote"""
        job_info = {
            "salary_max": 180000,
            "location_policy": "On-site",
            "role_type": "IC",
            "title": "Staff Software Engineer",
        }

        result = evaluate_job_against_criteria(job_info)

        assert result["remote"]["pass"] is False
        assert "not remote" in result["remote"]["reason"]

    def test_junior_ic_role_fails(self):
        """Test IC role without required seniority"""
        job_info = {
            "salary_max": 180000,
            "location_policy": "Remote",
            "role_type": "IC",
            "title": "Software Engineer",  # No senior/staff/lead/principal
        }

        result = evaluate_job_against_criteria(job_info)

        assert result["title_level"]["pass"] is False
        assert "lacks required seniority" in result["title_level"]["reason"]

    def test_non_ic_role_passes_title_check(self):
        """Test that non-IC roles pass title level requirement"""
        job_info = {
            "salary_max": 180000,
            "location_policy": "Remote",
            "role_type": "Manager",
            "title": "Engineering Manager",
        }

        result = evaluate_job_against_criteria(job_info)

        assert result["title_level"]["pass"] is True
        assert "not applicable" in result["title_level"]["reason"]

    def test_empty_job_info_returns_error(self):
        """Test behavior with empty job information"""
        result = evaluate_job_against_criteria({})

        assert "error" in result
        assert result["error"] == "No extracted information available"

    def test_none_job_info_returns_error(self):
        """Test behavior with None job information"""
        result = evaluate_job_against_criteria(None)

        assert "error" in result
        assert result["error"] == "No extracted information available"

    def test_various_seniority_levels_pass(self):
        """Test that various accepted seniority levels pass for IC roles"""
        seniority_levels = ["lead", "staff", "principal", "senior staff"]

        for level in seniority_levels:
            job_info = {
                "salary_max": 180000,
                "location_policy": "Remote",
                "role_type": "IC",
                "title": f"{level} software engineer",
            }

            result = evaluate_job_against_criteria(job_info)
            assert result["title_level"]["pass"] is True, f"Failed for {level} title"

    def test_case_insensitive_matching(self):
        """Test that matching is case insensitive"""
        job_info = {
            "salary_max": 180000,
            "location_policy": "REMOTE",
            "role_type": "ic",
            "title": "STAFF SOFTWARE ENGINEER",
        }

        result = evaluate_job_against_criteria(job_info)

        assert result["remote"]["pass"] is True
        assert result["title_level"]["pass"] is True
