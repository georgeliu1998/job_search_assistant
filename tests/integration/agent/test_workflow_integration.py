"""
Integration tests for the simplified job evaluation workflow.

This module contains comprehensive integration tests that verify
the entire workflow from job posting text to final recommendation.
"""

from unittest.mock import Mock, patch

import pytest

from src.agent.workflows.job_evaluation import evaluate_job_posting
from src.exceptions.llm import LLMProviderError


class TestEvaluateJobPosting:
    """Integration tests for the main evaluate_job_posting function."""

    @patch("src.agent.tools.extraction.schema_extraction_tool._extract_with_schema")
    @patch(
        "src.agent.tools.extraction.schema_extraction_tool.validate_extraction_result"
    )
    @patch("src.core.job_evaluation.evaluator.evaluate_job_against_criteria")
    def test_evaluate_job_posting_should_apply(
        self, mock_evaluate, mock_validate, mock_extract_schema
    ):
        """Test complete workflow resulting in APPLY recommendation."""
        # Setup extraction with passing criteria
        mock_extract_schema.return_value = {
            "title": "Staff Software Engineer",
            "company": "TechCorp",
            "salary_min": 140000,
            "salary_max": 170000,
            "location_policy": "remote",
            "role_type": "ic",
        }
        mock_validate.return_value = True
        mock_evaluate.return_value = {
            "salary": {"pass": True, "reason": "Salary meets requirement"},
            "remote": {"pass": True, "reason": "Position is remote"},
            "title_level": {
                "pass": True,
                "reason": "IC role has appropriate seniority",
            },
        }

        result = evaluate_job_posting(
            "Staff Software Engineer at TechCorp, remote, $140k-$170k"
        )

        assert result["recommendation"] == "APPLY"
        assert "criteria passed" in result["reasoning"].lower()
        assert result["extracted_info"] is not None
        assert result["evaluation_result"] is not None
        assert result["extracted_info"]["title"] == "Staff Software Engineer"
        assert result["extracted_info"]["company"] == "TechCorp"

    @patch("src.agent.tools.extraction.schema_extraction_tool._extract_with_schema")
    @patch(
        "src.agent.tools.extraction.schema_extraction_tool.validate_extraction_result"
    )
    @patch("src.core.job_evaluation.evaluator.evaluate_job_against_criteria")
    def test_evaluate_job_posting_should_not_apply(
        self, mock_evaluate, mock_validate, mock_extract_schema
    ):
        """Test complete workflow resulting in DO_NOT_APPLY recommendation."""
        # Setup extraction with failing criteria
        mock_extract_schema.return_value = {
            "title": "Junior Software Engineer",
            "company": "TechCorp",
            "salary_min": 70000,
            "salary_max": 90000,
            "location_policy": "onsite",
            "role_type": "ic",
        }
        mock_validate.return_value = True
        mock_evaluate.return_value = {
            "salary": {"pass": False, "reason": "Salary too low"},
            "remote": {"pass": False, "reason": "Position is not remote"},
            "title_level": {
                "pass": False,
                "reason": "IC role lacks required seniority",
            },
        }

        result = evaluate_job_posting(
            "Junior Software Engineer at TechCorp, onsite, $70k-$90k"
        )

        assert result["recommendation"] == "DO_NOT_APPLY"
        assert "failed" in result["reasoning"].lower()
        assert result["extracted_info"] is not None
        assert result["evaluation_result"] is not None

    @patch("src.agent.tools.extraction.schema_extraction_tool._extract_with_schema")
    @patch(
        "src.agent.tools.extraction.schema_extraction_tool.validate_extraction_result"
    )
    @patch("src.core.job_evaluation.evaluator.evaluate_job_against_criteria")
    def test_evaluate_job_posting_mixed_results(
        self, mock_evaluate, mock_validate, mock_extract_schema
    ):
        """Test workflow with mixed evaluation results."""
        mock_extract_schema.return_value = {
            "title": "Senior Software Engineer",
            "company": "TechCorp",
            "salary_min": 120000,
            "salary_max": 140000,
            "location_policy": "remote",
            "role_type": "ic",
        }
        mock_validate.return_value = True
        mock_evaluate.return_value = {
            "salary": {"pass": True, "reason": "Salary meets requirement"},
            "remote": {"pass": True, "reason": "Position is remote"},
            "title_level": {
                "pass": False,
                "reason": "IC role lacks required seniority",
            },
        }

        result = evaluate_job_posting(
            "Senior Software Engineer at TechCorp, remote, $120k-$140k"
        )

        assert result["recommendation"] == "DO_NOT_APPLY"
        assert "failed" in result["reasoning"].lower()
        assert result["extracted_info"] is not None
        assert result["evaluation_result"] is not None

    def test_evaluate_job_posting_empty_text(self):
        """Test evaluation with empty job posting text."""
        result = evaluate_job_posting("")

        assert result["recommendation"] == "ERROR"
        assert "empty" in result["reasoning"].lower()
        assert result["extracted_info"] == {}
        assert result["evaluation_result"] == {}

    def test_evaluate_job_posting_none_text(self):
        """Test evaluation with None job posting text."""
        result = evaluate_job_posting(None)

        assert result["recommendation"] == "ERROR"
        assert "empty" in result["reasoning"].lower()
        assert result["extracted_info"] == {}
        assert result["evaluation_result"] == {}

    def test_evaluate_job_posting_whitespace_only(self):
        """Test evaluation with whitespace-only job posting text."""
        result = evaluate_job_posting("   \n\t  ")

        assert result["recommendation"] == "ERROR"
        assert "empty" in result["reasoning"].lower()
        assert result["extracted_info"] == {}
        assert result["evaluation_result"] == {}

    @patch("src.agent.workflows.job_evaluation.main.get_compiled_workflow")
    def test_evaluate_job_posting_workflow_exception(self, mock_get_compiled_workflow):
        """Test evaluation when workflow creation fails."""
        mock_get_compiled_workflow.side_effect = Exception("Workflow creation failed")

        result = evaluate_job_posting("Some job posting")

        assert result["recommendation"] == "ERROR"
        assert "failed" in result["reasoning"].lower()
        assert result["extracted_info"] == {}
        assert result["evaluation_result"] == {}

    @patch("src.agent.tools.extraction.schema_extraction_tool._extract_with_schema")
    @patch(
        "src.agent.tools.extraction.schema_extraction_tool.validate_extraction_result"
    )
    def test_evaluate_job_posting_extraction_failure(
        self, mock_validate, mock_extract_schema
    ):
        """Test evaluation when extraction fails."""
        mock_extract_schema.side_effect = LLMProviderError("API error")

        result = evaluate_job_posting("Some job posting")

        assert result["recommendation"] == "ERROR"
        assert "no job information available" in result["reasoning"].lower()
        assert result["extracted_info"] is None
        assert result["evaluation_result"] is None

    @patch("src.agent.tools.extraction.schema_extraction_tool._extract_with_schema")
    @patch(
        "src.agent.tools.extraction.schema_extraction_tool.validate_extraction_result"
    )
    def test_evaluate_job_posting_invalid_extraction(
        self, mock_validate, mock_extract_schema
    ):
        """Test evaluation when extraction is invalid."""
        mock_extract_schema.return_value = {"title": "", "company": ""}
        mock_validate.return_value = False

        result = evaluate_job_posting("Some job posting")

        assert result["recommendation"] == "ERROR"
        assert "no job information available" in result["reasoning"].lower()
        assert result["extracted_info"] is None
        assert result["evaluation_result"] is None

    @pytest.mark.parametrize(
        "sample_job_description", ["software_engineer"], indirect=True
    )
    def test_evaluate_job_posting_with_sample_data(self, sample_job_description):
        """Test evaluation with real sample job description."""
        result = evaluate_job_posting(sample_job_description)

        # Since this is a real evaluation, we just check structure
        assert "recommendation" in result
        assert "reasoning" in result
        assert "extracted_info" in result
        assert "evaluation_result" in result
        assert result["recommendation"] in ["APPLY", "DO_NOT_APPLY", "ERROR"]

    def test_evaluate_job_posting_integration_success(self):
        """Test end-to-end evaluation with a well-formed job posting."""
        job_posting = """
        Staff Software Engineer at TechCorp
        Location: Remote
        Salary: $150,000 - $180,000

        We are seeking a Staff Software Engineer to join our team.
        This is a fully remote position with excellent benefits.

        Requirements:
        - 5+ years of software engineering experience
        - Strong Python skills
        - Experience with cloud platforms
        """

        result = evaluate_job_posting(job_posting)

        # Check that we get a proper response structure
        assert "recommendation" in result
        assert "reasoning" in result
        assert "extracted_info" in result
        assert "evaluation_result" in result
        assert result["recommendation"] in ["APPLY", "DO_NOT_APPLY", "ERROR"]

        # If extraction succeeded, check structure
        if result["recommendation"] != "ERROR":
            assert isinstance(result["extracted_info"], dict)
            assert isinstance(result["evaluation_result"], dict)
