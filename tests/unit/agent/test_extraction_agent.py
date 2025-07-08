"""
Unit tests for job extraction agent nodes.

This module contains comprehensive tests for the individual agent nodes
that form the job evaluation workflow.
"""

from unittest.mock import Mock, patch

import pytest

from src.agent.agents.extraction.job_extraction_agent import (
    evaluation_node,
    extraction_node,
    validation_node,
)
from src.agent.workflows.job_evaluation.states import JobEvaluationWorkflowState
from src.exceptions.llm import LLMProviderError
from src.models.job import JobPostingExtractionSchema


class TestExtractionNode:
    """Test cases for the extraction_node function."""

    def test_extraction_node_success(self):
        """Test successful extraction with valid job posting."""
        state = JobEvaluationWorkflowState(
            job_posting_text="Software Engineer at TechCorp. Remote position. Salary: $140,000-$170,000",
            extracted_info=None,
            evaluation_result=None,
            messages=[],
            langfuse_handler=None,
            workflow_version="2.0",
            extraction_duration=None,
            evaluation_duration=None,
        )

        expected_extraction = {
            "title": "Software Engineer",
            "company": "TechCorp",
            "salary_min": 140000,
            "salary_max": 170000,
            "location_policy": "remote",
            "role_type": "ic",
        }

        with patch(
            "src.agent.agents.extraction.job_extraction_agent.extract_job_posting"
        ) as mock_extract:
            mock_extract.invoke.return_value = expected_extraction

            result = extraction_node(state)

            assert result["extracted_info"] == expected_extraction
            assert len(result["messages"]) == 1
            assert result["messages"][0][0] == "extract_node"
            assert isinstance(result["messages"][0][1], (dict, str))
            mock_extract.invoke.assert_called_once_with(
                {"job_text": state["job_posting_text"]}
            )

    def test_extraction_node_empty_text(self):
        """Test extraction with empty job posting text."""
        state = JobEvaluationWorkflowState(
            job_posting_text="",
            extracted_info=None,
            evaluation_result=None,
            messages=[],
            langfuse_handler=None,
            workflow_version="2.0",
            extraction_duration=None,
            evaluation_duration=None,
        )

        with patch(
            "src.agent.agents.extraction.job_extraction_agent.extract_job_posting"
        ) as mock_extract:
            mock_extract.invoke.return_value = {}

            result = extraction_node(state)

            assert result["extracted_info"] == {}
            assert len(result["messages"]) == 1
            assert result["messages"][0][0] == "extract_node"

    def test_extraction_node_llm_error(self):
        """Test extraction when LLM raises an error."""
        state = JobEvaluationWorkflowState(
            job_posting_text="Valid job posting text",
            extracted_info=None,
            evaluation_result=None,
            messages=[],
            langfuse_handler=None,
            workflow_version="2.0",
            extraction_duration=None,
            evaluation_duration=None,
        )

        with patch(
            "src.agent.agents.extraction.job_extraction_agent.extract_job_posting"
        ) as mock_extract:
            mock_extract.invoke.side_effect = LLMProviderError(
                "API rate limit exceeded"
            )

            result = extraction_node(state)

            assert result["extracted_info"] is None
            assert len(result["messages"]) == 1
            assert result["messages"][0][0] == "extract_node"
            assert "failed" in result["messages"][0][1].lower()

    def test_extraction_node_partial_extraction(self):
        """Test extraction with partial/incomplete data."""
        state = JobEvaluationWorkflowState(
            job_posting_text="Software Engineer position available",
            extracted_info=None,
            evaluation_result=None,
            messages=[],
            langfuse_handler=None,
            workflow_version="2.0",
            extraction_duration=None,
            evaluation_duration=None,
        )

        partial_extraction = {
            "title": "Software Engineer",
            "company": None,
            "salary_min": None,
            "salary_max": None,
            "location_policy": "unclear",
            "role_type": "unclear",
        }

        with patch(
            "src.agent.agents.extraction.job_extraction_agent.extract_job_posting"
        ) as mock_extract:
            mock_extract.invoke.return_value = partial_extraction

            result = extraction_node(state)

            assert result["extracted_info"] == partial_extraction
            assert len(result["messages"]) == 1


class TestValidationNode:
    """Test cases for the validation_node function."""

    def test_validation_node_success(self):
        """Test successful validation with valid extracted data."""
        state = JobEvaluationWorkflowState(
            job_posting_text="job text",
            extracted_info={
                "title": "Senior Software Engineer",
                "company": "TechCorp",
                "salary_min": 140000,
                "salary_max": 170000,
                "location_policy": "remote",
                "role_type": "ic",
            },
            evaluation_result=None,
            messages=[],
            langfuse_handler=None,
            workflow_version="2.0",
            extraction_duration=None,
            evaluation_duration=None,
        )

        with patch(
            "src.agent.agents.extraction.job_extraction_agent.validate_extraction_result"
        ) as mock_validate:
            mock_validate.invoke.return_value = True

            result = validation_node(state)

            assert result["is_valid"] is True
            assert len(result["messages"]) == 1
            assert result["messages"][0][0] == "validation_node"
            assert "is_valid: True" in result["messages"][0][1]
            mock_validate.invoke.assert_called_once_with(
                {
                    "extraction_result": state["extracted_info"],
                    "schema_name": "job_posting",
                }
            )

    def test_validation_node_failure(self):
        """Test validation with invalid extracted data."""
        state = JobEvaluationWorkflowState(
            job_posting_text="job text",
            extracted_info={
                "title": None,
                "company": None,
                "salary_min": None,
                "salary_max": None,
                "location_policy": "unclear",
                "role_type": "unclear",
            },
            evaluation_result=None,
            messages=[],
            langfuse_handler=None,
            workflow_version="2.0",
            extraction_duration=None,
            evaluation_duration=None,
        )

        with patch(
            "src.agent.agents.extraction.job_extraction_agent.validate_extraction_result"
        ) as mock_validate:
            mock_validate.invoke.return_value = False

            result = validation_node(state)

            assert result["is_valid"] is False
            assert len(result["messages"]) == 1
            assert result["messages"][0][0] == "validation_node"
            assert "is_valid: False" in result["messages"][0][1]

    def test_validation_node_no_extracted_info(self):
        """Test validation when no extracted info is available."""
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

        result = validation_node(state)

        assert result["is_valid"] is False
        assert len(result["messages"]) == 1
        assert result["messages"][0][0] == "validation_node"
        assert "No extracted info to validate" in result["messages"][0][1]

    def test_validation_node_validation_error(self):
        """Test validation when validation tool raises an error."""
        state = JobEvaluationWorkflowState(
            job_posting_text="job text",
            extracted_info={"title": "Software Engineer"},
            evaluation_result=None,
            messages=[],
            langfuse_handler=None,
            workflow_version="2.0",
            extraction_duration=None,
            evaluation_duration=None,
        )

        with patch(
            "src.agent.agents.extraction.job_extraction_agent.validate_extraction_result"
        ) as mock_validate:
            mock_validate.invoke.side_effect = Exception("Validation service error")

            result = validation_node(state)

            assert result["is_valid"] is False
            assert len(result["messages"]) == 1
            assert result["messages"][0][0] == "validation_node"
            assert "failed" in result["messages"][0][1].lower()


class TestEvaluationNode:
    """Test cases for the evaluation_node function."""

    def test_evaluation_node_success(self):
        """Test successful evaluation with valid extracted data."""
        state = JobEvaluationWorkflowState(
            job_posting_text="job text",
            extracted_info={
                "title": "Senior Software Engineer",
                "company": "TechCorp",
                "salary_min": 140000,
                "salary_max": 170000,
                "location_policy": "remote",
                "role_type": "ic",
            },
            evaluation_result=None,
            messages=[],
            langfuse_handler=None,
            workflow_version="2.0",
            extraction_duration=None,
            evaluation_duration=None,
        )

        expected_evaluation = {
            "salary": {"pass": True, "reason": "Salary meets requirement"},
            "remote": {"pass": True, "reason": "Position is remote"},
            "title_level": {
                "pass": True,
                "reason": "IC role has appropriate seniority",
            },
        }

        with patch(
            "src.agent.agents.extraction.job_extraction_agent.evaluate_job_against_criteria"
        ) as mock_evaluate:
            mock_evaluate.return_value = expected_evaluation

            result = evaluation_node(state)

            assert result["evaluation_result"] == expected_evaluation
            assert len(result["messages"]) == 1
            assert result["messages"][0][0] == "evaluation_node"
            assert "Evaluation completed" in result["messages"][0][1]
            mock_evaluate.assert_called_once()

    def test_evaluation_node_with_pydantic_model(self):
        """Test evaluation when extracted_info is a Pydantic model."""
        # Create a mock Pydantic model
        mock_model = Mock(spec=JobPostingExtractionSchema)
        mock_model.model_dump.return_value = {
            "title": "Senior Software Engineer",
            "company": "TechCorp",
            "salary_min": 140000,
            "salary_max": 170000,
            "location_policy": "remote",
            "role_type": "ic",
        }

        state = JobEvaluationWorkflowState(
            job_posting_text="job text",
            extracted_info=mock_model,
            evaluation_result=None,
            messages=[],
            langfuse_handler=None,
            workflow_version="2.0",
            extraction_duration=None,
            evaluation_duration=None,
        )

        expected_evaluation = {
            "salary": {"pass": True, "reason": "Salary meets requirement"},
            "remote": {"pass": True, "reason": "Position is remote"},
            "title_level": {
                "pass": True,
                "reason": "IC role has appropriate seniority",
            },
        }

        with patch(
            "src.agent.agents.extraction.job_extraction_agent.evaluate_job_against_criteria"
        ) as mock_evaluate:
            mock_evaluate.return_value = expected_evaluation

            result = evaluation_node(state)

            assert result["evaluation_result"] == expected_evaluation
            mock_model.model_dump.assert_called_once()

    def test_evaluation_node_no_extracted_info(self):
        """Test evaluation when no extracted info is available."""
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

        result = evaluation_node(state)

        assert result["evaluation_result"] is None
        assert len(result["messages"]) == 1
        assert result["messages"][0][0] == "evaluation_node"
        assert "Skipped due to missing extraction" in result["messages"][0][1]

    def test_evaluation_node_evaluation_error(self):
        """Test evaluation when core evaluation function raises an error."""
        state = JobEvaluationWorkflowState(
            job_posting_text="job text",
            extracted_info={"title": "Software Engineer"},
            evaluation_result=None,
            messages=[],
            langfuse_handler=None,
            workflow_version="2.0",
            extraction_duration=None,
            evaluation_duration=None,
        )

        with patch(
            "src.agent.agents.extraction.job_extraction_agent.evaluate_job_against_criteria"
        ) as mock_evaluate:
            mock_evaluate.side_effect = Exception("Evaluation service error")

            result = evaluation_node(state)

            assert result["evaluation_result"] is None
            assert len(result["messages"]) == 1
            assert result["messages"][0][0] == "evaluation_node"
            assert "failed" in result["messages"][0][1].lower()

    def test_evaluation_node_with_non_standard_format(self):
        """Test evaluation when extracted_info is in non-standard format."""
        # Test with an object that can be converted to dict
        mock_obj = Mock()
        mock_obj.__dict__ = {
            "title": "Software Engineer",
            "company": "TechCorp",
            "salary_max": 150000,
        }

        state = JobEvaluationWorkflowState(
            job_posting_text="job text",
            extracted_info=mock_obj,
            evaluation_result=None,
            messages=[],
            langfuse_handler=None,
            workflow_version="2.0",
            extraction_duration=None,
            evaluation_duration=None,
        )

        expected_evaluation = {
            "salary": {"pass": True, "reason": "Salary meets requirement"}
        }

        with patch(
            "src.agent.agents.extraction.job_extraction_agent.evaluate_job_against_criteria"
        ) as mock_evaluate:
            mock_evaluate.return_value = expected_evaluation

            result = evaluation_node(state)

            assert result["evaluation_result"] == expected_evaluation
            mock_evaluate.assert_called_once()
