"""
Integration tests for the job evaluation workflow.

This module contains comprehensive integration tests that verify
the entire workflow from job posting text to final recommendation.
"""

from unittest.mock import Mock, patch

import pytest

from src.agent.workflows.job_evaluation import (
    JobEvaluationState,
    run_job_evaluation_workflow,
)
from src.exceptions.llm import LLMProviderError


class TestJobEvaluationWorkflow:
    """Integration tests for the job evaluation workflow."""

    @patch("src.agent.tools.extraction.schema_extraction_tool._extract_with_schema")
    @patch(
        "src.agent.tools.extraction.schema_extraction_tool.validate_extraction_result"
    )
    @patch("src.core.job_evaluation.evaluator.evaluate_job_against_criteria")
    def test_workflow_should_apply(
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

        final_state = run_job_evaluation_workflow(
            "Staff Software Engineer at TechCorp, remote, $140k-$170k"
        )

        assert final_state.recommendation == "APPLY"
        assert "criteria passed" in final_state.reasoning.lower()
        assert final_state.extracted_info is not None
        assert final_state.evaluation_result is not None
        assert final_state.extracted_info["title"] == "Staff Software Engineer"
        assert final_state.extracted_info["company"] == "TechCorp"

    @patch("src.agent.tools.extraction.schema_extraction_tool._extract_with_schema")
    @patch(
        "src.agent.tools.extraction.schema_extraction_tool.validate_extraction_result"
    )
    @patch("src.core.job_evaluation.evaluator.evaluate_job_against_criteria")
    def test_workflow_should_not_apply(
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

        final_state = run_job_evaluation_workflow(
            "Junior Software Engineer at TechCorp, onsite, $70k-$90k"
        )

        assert final_state.recommendation == "DO_NOT_APPLY"
        assert "failed" in final_state.reasoning.lower()
        assert final_state.extracted_info is not None
        assert final_state.evaluation_result is not None

    @patch("src.agent.tools.extraction.schema_extraction_tool._extract_with_schema")
    @patch(
        "src.agent.tools.extraction.schema_extraction_tool.validate_extraction_result"
    )
    @patch("src.core.job_evaluation.evaluator.evaluate_job_against_criteria")
    def test_workflow_mixed_results(
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

        final_state = run_job_evaluation_workflow(
            "Senior Software Engineer at TechCorp, remote, $120k-$140k"
        )

        assert final_state.recommendation == "DO_NOT_APPLY"
        assert "failed" in final_state.reasoning.lower()
        assert final_state.extracted_info is not None
        assert final_state.evaluation_result is not None

    def test_workflow_empty_text(self):
        """Test evaluation with empty job posting text."""
        final_state = run_job_evaluation_workflow("")

        assert final_state.recommendation == "ERROR"
        assert "empty" in final_state.reasoning.lower()
        assert final_state.extracted_info == {}
        assert final_state.evaluation_result == {}

    def test_workflow_none_text(self):
        """Test evaluation with None job posting text."""
        final_state = run_job_evaluation_workflow(None)

        assert final_state.recommendation == "ERROR"
        assert "empty" in final_state.reasoning.lower()
        assert final_state.extracted_info == {}
        assert final_state.evaluation_result == {}

    def test_workflow_whitespace_only(self):
        """Test evaluation with whitespace-only job posting text."""
        final_state = run_job_evaluation_workflow("   \n\t  ")

        assert final_state.recommendation == "ERROR"
        assert "empty" in final_state.reasoning.lower()
        assert final_state.extracted_info == {}
        assert final_state.evaluation_result == {}

    @patch("src.agent.workflows.job_evaluation.main.get_job_evaluation_workflow")
    def test_workflow_exception(self, mock_get_workflow):
        """Test evaluation when workflow creation fails."""
        mock_get_workflow.side_effect = Exception("Workflow creation failed")

        final_state = run_job_evaluation_workflow("Some job posting")

        assert final_state.recommendation == "ERROR"
        assert "failed" in final_state.reasoning.lower()
        assert final_state.extracted_info == {}
        assert final_state.evaluation_result == {}

    @patch("src.agent.tools.extraction.schema_extraction_tool._extract_with_schema")
    @patch(
        "src.agent.tools.extraction.schema_extraction_tool.validate_extraction_result"
    )
    def test_workflow_extraction_failure(self, mock_validate, mock_extract_schema):
        """Test evaluation when extraction fails."""
        mock_extract_schema.side_effect = LLMProviderError("API error")

        final_state = run_job_evaluation_workflow("Some job posting")

        assert final_state.recommendation == "ERROR"
        assert "extraction failed" in final_state.reasoning.lower()
        assert final_state.extracted_info is None
        assert final_state.evaluation_result is None

    @patch("src.agent.tools.extraction.schema_extraction_tool._extract_with_schema")
    @patch(
        "src.agent.tools.extraction.schema_extraction_tool.validate_extraction_result"
    )
    def test_workflow_invalid_extraction(self, mock_validate, mock_extract_schema):
        """Test evaluation when extraction is invalid."""
        mock_extract_schema.return_value = {"title": "", "company": ""}
        mock_validate.return_value = False

        final_state = run_job_evaluation_workflow("Some job posting")

        assert final_state.recommendation == "ERROR"
        assert "failed to extract meaningful" in final_state.reasoning.lower()
        assert final_state.extracted_info is None
        assert final_state.evaluation_result is None

    @pytest.mark.parametrize(
        "sample_job_description", ["software_engineer"], indirect=True
    )
    def test_workflow_with_sample_data(self, sample_job_description):
        """Test evaluation with real sample job description."""
        final_state = run_job_evaluation_workflow(sample_job_description)

        # Since this is a real evaluation, we just check structure
        assert hasattr(final_state, "recommendation")
        assert hasattr(final_state, "reasoning")
        assert hasattr(final_state, "extracted_info")
        assert hasattr(final_state, "evaluation_result")
        assert final_state.recommendation in ["APPLY", "DO_NOT_APPLY", "ERROR"]

    def test_workflow_integration_success(self):
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

        final_state = run_job_evaluation_workflow(job_posting)

        # Check that we get a proper response structure
        assert hasattr(final_state, "recommendation")
        assert hasattr(final_state, "reasoning")
        assert hasattr(final_state, "extracted_info")
        assert hasattr(final_state, "evaluation_result")
        assert final_state.recommendation in ["APPLY", "DO_NOT_APPLY", "ERROR"]

        # If extraction succeeded, check structure
        if final_state.recommendation != "ERROR":
            assert final_state.extracted_info is not None
            assert final_state.evaluation_result is not None
