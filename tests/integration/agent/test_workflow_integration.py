"""
Integration tests for the complete job evaluation workflow.

This module contains comprehensive integration tests that verify
the entire workflow from job posting text to final recommendation.
"""

from unittest.mock import Mock, patch

import pytest

from src.agent.workflows.job_evaluation.main import (
    JobEvaluationWorkflow,
    create_job_evaluation_workflow,
    evaluate_job_posting,
    generate_recommendation_from_results,
)
from src.agent.workflows.job_evaluation.states import (
    JobEvaluationWorkflowState,
    create_initial_state,
    is_extraction_successful,
)
from src.exceptions.llm import LLMProviderError


class TestJobEvaluationWorkflow:
    """Integration tests for the JobEvaluationWorkflow class."""

    def test_workflow_creation(self):
        """Test that workflow can be created and compiled."""
        workflow = JobEvaluationWorkflow()

        assert workflow.workflow is not None
        assert workflow.app is not None
        assert hasattr(workflow, "run")

    def test_create_job_evaluation_workflow_factory(self):
        """Test the factory function for creating workflows."""
        workflow = create_job_evaluation_workflow()

        assert isinstance(workflow, JobEvaluationWorkflow)
        assert workflow.workflow is not None

    @patch("src.agent.agents.extraction.job_extraction_agent.extract_job_posting")
    @patch(
        "src.agent.agents.extraction.job_extraction_agent.validate_extraction_result"
    )
    @patch(
        "src.agent.agents.extraction.job_extraction_agent.evaluate_job_against_criteria"
    )
    def test_workflow_run_success(self, mock_evaluate, mock_validate, mock_extract):
        """Test successful workflow run with all nodes executing."""
        # Setup mocks
        mock_extract.invoke.return_value = {
            "title": "Senior Software Engineer",
            "company": "TechCorp",
            "salary_min": 140000,
            "salary_max": 170000,
            "location_policy": "remote",
            "role_type": "ic",
        }
        mock_validate.invoke.return_value = True
        mock_evaluate.return_value = {
            "salary": {"pass": True, "reason": "Salary meets requirement"},
            "remote": {"pass": True, "reason": "Position is remote"},
            "title_level": {
                "pass": True,
                "reason": "IC role has appropriate seniority",
            },
        }

        workflow = JobEvaluationWorkflow()
        result = workflow.run(
            "Senior Software Engineer at TechCorp, remote, $140k-$170k"
        )

        assert result is not None
        assert result["extracted_info"] is not None
        assert result["evaluation_result"] is not None
        assert result["workflow_version"] == "2.0"
        assert len(result["messages"]) > 0

    @patch("src.agent.agents.extraction.job_extraction_agent.extract_job_posting")
    def test_workflow_run_with_extraction_failure(self, mock_extract):
        """Test workflow run when extraction fails."""
        mock_extract.invoke.side_effect = LLMProviderError("API error")

        workflow = JobEvaluationWorkflow()
        result = workflow.run("Some job posting")

        assert result is not None
        assert result["extracted_info"] is None
        assert result["evaluation_result"] is None

    def test_workflow_run_with_langfuse_handler(self):
        """Test workflow run with Langfuse handler."""
        mock_langfuse_handler = Mock()

        with patch(
            "src.agent.agents.extraction.job_extraction_agent.extract_job_posting"
        ) as mock_extract:
            mock_extract.invoke.return_value = {
                "title": "Software Engineer",
                "company": "TechCorp",
            }

            workflow = JobEvaluationWorkflow()
            result = workflow.run(
                "Software Engineer at TechCorp", langfuse_handler=mock_langfuse_handler
            )

            assert result is not None
            assert result["langfuse_handler"] == mock_langfuse_handler


class TestEvaluateJobPosting:
    """Integration tests for the main evaluate_job_posting function."""

    @patch("src.agent.agents.extraction.job_extraction_agent.extract_job_posting")
    @patch(
        "src.agent.agents.extraction.job_extraction_agent.validate_extraction_result"
    )
    @patch(
        "src.agent.agents.extraction.job_extraction_agent.evaluate_job_against_criteria"
    )
    def test_evaluate_job_posting_should_apply(
        self, mock_evaluate, mock_validate, mock_extract
    ):
        """Test complete workflow resulting in APPLY recommendation."""
        # Setup successful extraction
        mock_extract.invoke.return_value = {
            "title": "Senior Software Engineer",
            "company": "TechCorp",
            "salary_min": 140000,
            "salary_max": 170000,
            "location_policy": "remote",
            "role_type": "ic",
        }
        mock_validate.invoke.return_value = True
        mock_evaluate.return_value = {
            "salary": {"pass": True, "reason": "Salary meets requirement"},
            "remote": {"pass": True, "reason": "Position is remote"},
            "title_level": {
                "pass": True,
                "reason": "IC role has appropriate seniority",
            },
        }

        result = evaluate_job_posting(
            "Senior Software Engineer at TechCorp, remote, $140k-$170k"
        )

        assert result["recommendation"] == "APPLY"
        assert "criteria met" in result["reasoning"].lower()
        assert result["extracted_info"] is not None
        assert result["evaluation_result"] is not None
        assert result["extracted_info"]["title"] == "Senior Software Engineer"
        assert result["extracted_info"]["company"] == "TechCorp"

    @patch("src.agent.agents.extraction.job_extraction_agent.extract_job_posting")
    @patch(
        "src.agent.agents.extraction.job_extraction_agent.validate_extraction_result"
    )
    @patch(
        "src.agent.agents.extraction.job_extraction_agent.evaluate_job_against_criteria"
    )
    def test_evaluate_job_posting_should_not_apply(
        self, mock_evaluate, mock_validate, mock_extract
    ):
        """Test complete workflow resulting in DO_NOT_APPLY recommendation."""
        # Setup extraction with failing criteria
        mock_extract.invoke.return_value = {
            "title": "Junior Software Engineer",
            "company": "TechCorp",
            "salary_min": 70000,
            "salary_max": 90000,
            "location_policy": "onsite",
            "role_type": "ic",
        }
        mock_validate.invoke.return_value = True
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
        assert "failed criteria" in result["reasoning"].lower()
        assert result["extracted_info"] is not None
        assert result["evaluation_result"] is not None

    @patch("src.agent.agents.extraction.job_extraction_agent.extract_job_posting")
    @patch(
        "src.agent.agents.extraction.job_extraction_agent.validate_extraction_result"
    )
    @patch(
        "src.agent.agents.extraction.job_extraction_agent.evaluate_job_against_criteria"
    )
    def test_evaluate_job_posting_mixed_results(
        self, mock_evaluate, mock_validate, mock_extract
    ):
        """Test workflow with mixed pass/fail criteria."""
        mock_extract.invoke.return_value = {
            "title": "Senior Software Engineer",
            "company": "TechCorp",
            "salary_min": 90000,
            "salary_max": 110000,
            "location_policy": "remote",
            "role_type": "ic",
        }
        mock_validate.invoke.return_value = True
        mock_evaluate.return_value = {
            "salary": {"pass": False, "reason": "Salary too low"},
            "remote": {"pass": True, "reason": "Position is remote"},
            "title_level": {
                "pass": True,
                "reason": "IC role has appropriate seniority",
            },
        }

        result = evaluate_job_posting(
            "Senior Software Engineer at TechCorp, remote, $90k-$110k"
        )

        assert result["recommendation"] == "DO_NOT_APPLY"
        assert "failed criteria" in result["reasoning"].lower()
        assert "salary too low" in result["reasoning"].lower()

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
        """Test evaluation with whitespace-only text."""
        result = evaluate_job_posting("   \n\t  ")

        assert result["recommendation"] == "ERROR"
        assert "empty" in result["reasoning"].lower()
        assert result["extracted_info"] == {}
        assert result["evaluation_result"] == {}

    @patch("src.agent.workflows.job_evaluation.main.JobEvaluationWorkflow.run")
    def test_evaluate_job_posting_workflow_exception(self, mock_run):
        """Test evaluation when workflow raises an exception."""
        mock_run.side_effect = Exception("Workflow error")

        result = evaluate_job_posting("Valid job posting")

        assert result["recommendation"] == "ERROR"
        assert "unexpected error" in result["reasoning"].lower()
        assert result["extracted_info"] == {}
        assert result["evaluation_result"] == {}

    @patch("src.agent.agents.extraction.job_extraction_agent.extract_job_posting")
    @patch(
        "src.agent.agents.extraction.job_extraction_agent.validate_extraction_result"
    )
    def test_evaluate_job_posting_no_evaluation_result(
        self, mock_validate, mock_extract
    ):
        """Test evaluation when no evaluation result is generated."""
        mock_extract.invoke.return_value = {
            "title": "Software Engineer",
            "company": "TechCorp",
        }
        mock_validate.invoke.return_value = True

        with patch(
            "src.agent.agents.extraction.job_extraction_agent.evaluate_job_against_criteria"
        ) as mock_evaluate:
            mock_evaluate.return_value = None

            result = evaluate_job_posting("Software Engineer at TechCorp")

            assert result["recommendation"] == "ERROR"
            assert "no evaluation result" in result["reasoning"].lower()

    def test_evaluate_job_posting_with_sample_data(self, sample_job_description):
        """Test evaluation with the sample job description fixture."""
        # This test uses real sample data but mocks the LLM calls
        with patch(
            "src.agent.agents.extraction.job_extraction_agent.extract_job_posting"
        ) as mock_extract:
            mock_extract.invoke.return_value = {
                "title": "Software Engineer",
                "company": "TechInnovate Inc.",
                "salary_min": 130000,
                "salary_max": 170000,
                "location_policy": "hybrid",
                "role_type": "ic",
            }

            with patch(
                "src.agent.agents.extraction.job_extraction_agent.validate_extraction_result"
            ) as mock_validate:
                mock_validate.invoke.return_value = True

                with patch(
                    "src.agent.agents.extraction.job_extraction_agent.evaluate_job_against_criteria"
                ) as mock_evaluate:
                    mock_evaluate.return_value = {
                        "salary": {"pass": True, "reason": "Salary meets requirement"},
                        "remote": {"pass": False, "reason": "Position is not remote"},
                        "title_level": {
                            "pass": False,
                            "reason": "IC role lacks required seniority",
                        },
                    }

                    result = evaluate_job_posting(sample_job_description)

                    assert result["recommendation"] == "DO_NOT_APPLY"
                    assert result["extracted_info"]["company"] == "TechInnovate Inc."
                    assert result["extracted_info"]["location_policy"] == "hybrid"


class TestGenerateRecommendationFromResults:
    """Tests for the generate_recommendation_from_results function."""

    def test_generate_recommendation_all_pass(self):
        """Test recommendation generation when all criteria pass."""
        evaluation_results = {
            "salary": {"pass": True, "reason": "Salary meets requirement"},
            "remote": {"pass": True, "reason": "Position is remote"},
            "title_level": {
                "pass": True,
                "reason": "IC role has appropriate seniority",
            },
        }

        recommendation, reasoning = generate_recommendation_from_results(
            evaluation_results
        )

        assert recommendation == "APPLY"
        assert "all criteria met" in reasoning.lower()
        assert "salary meets requirement" in reasoning
        assert "position is remote" in reasoning
        assert "ic role has appropriate seniority" in reasoning

    def test_generate_recommendation_some_fail(self):
        """Test recommendation generation when some criteria fail."""
        evaluation_results = {
            "salary": {"pass": False, "reason": "Salary too low"},
            "remote": {"pass": True, "reason": "Position is remote"},
            "title_level": {
                "pass": True,
                "reason": "IC role has appropriate seniority",
            },
        }

        recommendation, reasoning = generate_recommendation_from_results(
            evaluation_results
        )

        assert recommendation == "DO_NOT_APPLY"
        assert "failed criteria" in reasoning.lower()
        assert "salary too low" in reasoning

    def test_generate_recommendation_all_fail(self):
        """Test recommendation generation when all criteria fail."""
        evaluation_results = {
            "salary": {"pass": False, "reason": "Salary too low"},
            "remote": {"pass": False, "reason": "Position is not remote"},
            "title_level": {
                "pass": False,
                "reason": "IC role lacks required seniority",
            },
        }

        recommendation, reasoning = generate_recommendation_from_results(
            evaluation_results
        )

        assert recommendation == "DO_NOT_APPLY"
        assert "failed criteria" in reasoning.lower()
        assert "salary too low" in reasoning
        assert "position is not remote" in reasoning
        assert "ic role lacks required seniority" in reasoning

    def test_generate_recommendation_empty_results(self):
        """Test recommendation generation with empty results."""
        recommendation, reasoning = generate_recommendation_from_results({})

        assert recommendation == "DO_NOT_APPLY"
        assert "unable to evaluate" in reasoning.lower()

    def test_generate_recommendation_error_results(self):
        """Test recommendation generation with error in results."""
        evaluation_results = {"error": "Extraction failed"}

        recommendation, reasoning = generate_recommendation_from_results(
            evaluation_results
        )

        assert recommendation == "DO_NOT_APPLY"
        assert "unable to evaluate" in reasoning.lower()
        assert "extraction errors" in reasoning.lower()

    def test_generate_recommendation_mixed_result_types(self):
        """Test recommendation generation with mixed result types."""
        evaluation_results = {
            "salary": {"pass": True, "reason": "Salary meets requirement"},
            "remote": {"pass": False, "reason": "Position is not remote"},
            "error": "Some error occurred",
            "title_level": {
                "pass": True,
                "reason": "IC role has appropriate seniority",
            },
        }

        recommendation, reasoning = generate_recommendation_from_results(
            evaluation_results
        )

        assert recommendation == "DO_NOT_APPLY"
        assert "failed criteria" in reasoning.lower()
        assert "position is not remote" in reasoning


class TestWorkflowStateManagement:
    """Tests for workflow state management functions."""

    def test_create_initial_state(self):
        """Test creating initial workflow state."""
        job_text = "Software Engineer at TechCorp"
        mock_langfuse_handler = Mock()

        state = create_initial_state(job_text, mock_langfuse_handler)

        assert state["job_posting_text"] == job_text
        assert state["extracted_info"] is None
        assert state["evaluation_result"] is None
        assert state["messages"] == []
        assert state["langfuse_handler"] == mock_langfuse_handler
        assert state["workflow_version"] == "2.0"
        assert state["extraction_duration"] is None
        assert state["evaluation_duration"] is None

    def test_create_initial_state_without_langfuse(self):
        """Test creating initial state without Langfuse handler."""
        job_text = "Software Engineer at TechCorp"

        state = create_initial_state(job_text)

        assert state["job_posting_text"] == job_text
        assert state["langfuse_handler"] is None

    def test_is_extraction_successful_with_valid_data(self):
        """Test extraction success detection with valid data."""
        mock_schema = Mock()
        mock_schema.__class__ = Mock()
        mock_schema.__class__.__name__ = "JobPostingExtractionSchema"

        state = JobEvaluationWorkflowState(
            job_posting_text="job text",
            extracted_info=mock_schema,
            evaluation_result=None,
            messages=[],
            langfuse_handler=None,
            workflow_version="2.0",
            extraction_duration=None,
            evaluation_duration=None,
        )

        # Mock isinstance check
        with patch(
            "src.agent.workflows.job_evaluation.states.isinstance"
        ) as mock_isinstance:
            mock_isinstance.return_value = True
            result = is_extraction_successful(state)
            assert result is True

    def test_is_extraction_successful_with_none(self):
        """Test extraction success detection with None data."""
        state = JobEvaluationWorkflowState(
            job_posting_text="job text",
            extracted_info=None,
            evaluation_result=None,
            messages=[],
            langfuse_handler=None,
            workflow_version="2.0",
            extraction_duration=None,
            evaluation_duration=None,
        )

        result = is_extraction_successful(state)
        assert result is False

    def test_is_extraction_successful_with_wrong_type(self):
        """Test extraction success detection with wrong data type."""
        state = JobEvaluationWorkflowState(
            job_posting_text="job text",
            extracted_info={"some": "dict"},
            evaluation_result=None,
            messages=[],
            langfuse_handler=None,
            workflow_version="2.0",
            extraction_duration=None,
            evaluation_duration=None,
        )

        result = is_extraction_successful(state)
        assert result is False
