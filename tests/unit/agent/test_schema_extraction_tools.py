"""
Tests for job posting extraction tools
"""

from unittest.mock import Mock, patch

import pytest

from src.agent.tools.extraction.schema_extraction_tool import (
    _extract_with_schema,
    extract_job_posting,
    get_extraction_summary,
    validate_extraction_result,
)
from src.exceptions.llm import LLMProviderError
from src.models.job import JobPostingExtractionSchema


class TestExtractJobPosting:
    """Test cases for the extract_job_posting function."""

    @patch("src.agent.tools.extraction.schema_extraction_tool._extract_with_schema")
    def test_extract_job_posting_success(self, mock_extract_with_schema):
        """Test successful job posting extraction."""
        expected_result = {
            "title": "Senior Software Engineer",
            "company": "TechCorp",
            "salary_min": 140000,
            "salary_max": 170000,
            "location_policy": "remote",
            "role_type": "ic",
        }
        mock_extract_with_schema.return_value = expected_result

        result = extract_job_posting(
            "Software Engineer at TechCorp, remote, $140k-$170k"
        )

        assert result == expected_result
        mock_extract_with_schema.assert_called_once()

    @patch("src.agent.tools.extraction.schema_extraction_tool._extract_with_schema")
    def test_extract_job_posting_partial_info(self, mock_extract_with_schema):
        """Test job posting extraction with partial information."""
        expected_result = {
            "title": "Software Engineer",
            "company": None,
            "salary_min": None,
            "salary_max": None,
            "location_policy": "unclear",
            "role_type": "unclear",
        }
        mock_extract_with_schema.return_value = expected_result

        result = extract_job_posting("Software Engineer position available")

        assert result == expected_result
        assert result["title"] == "Software Engineer"
        assert result["company"] is None


class TestValidateExtractionResult:
    """Test cases for the validate_extraction_result function."""

    def test_validate_job_posting_valid_complete(self):
        """Test validation of complete job posting data."""
        extraction_result = {
            "title": "Senior Software Engineer",
            "company": "TechCorp",
            "salary_min": 140000,
            "salary_max": 170000,
            "location_policy": "remote",
            "role_type": "ic",
        }

        result = validate_extraction_result(extraction_result, "job_posting")
        assert result is True

    def test_validate_job_posting_valid_minimal(self):
        """Test validation with minimal but sufficient data."""
        extraction_result = {
            "title": "Software Engineer",
            "company": None,
            "salary_min": None,
            "salary_max": 150000,
            "location_policy": "unclear",
            "role_type": "unclear",
        }

        result = validate_extraction_result(extraction_result, "job_posting")
        assert result is True  # Has title and salary_max

    def test_validate_job_posting_invalid_insufficient_data(self):
        """Test validation with insufficient data."""
        extraction_result = {
            "title": None,
            "company": None,
            "salary_min": None,
            "salary_max": None,
            "location_policy": "unclear",
            "role_type": "unclear",
        }

        result = validate_extraction_result(extraction_result, "job_posting")
        assert result is False

    def test_validate_job_posting_invalid_empty_strings(self):
        """Test validation with empty string values."""
        extraction_result = {
            "title": "",
            "company": "   ",
            "salary_min": None,
            "salary_max": None,
            "location_policy": "unclear",
            "role_type": "unclear",
        }

        result = validate_extraction_result(extraction_result, "job_posting")
        assert result is False

    def test_validate_extraction_result_empty_dict(self):
        """Test validation with empty extraction result."""
        result = validate_extraction_result({}, "job_posting")
        assert result is False

    def test_validate_extraction_result_none(self):
        """Test validation with None extraction result."""
        result = validate_extraction_result(None, "job_posting")
        assert result is False

    def test_validate_extraction_result_invalid_schema(self):
        """Test validation with invalid schema name."""
        extraction_result = {"field1": "value1", "field2": "value2"}
        with pytest.raises(ValueError, match="Only 'job_posting' schema is supported"):
            validate_extraction_result(extraction_result, "unknown_schema")


class TestGetExtractionSummary:
    """Test cases for the get_extraction_summary function."""

    def test_get_extraction_summary_complete_job_posting(self):
        """Test summary generation for complete job posting."""
        extraction_result = {
            "title": "Senior Software Engineer",
            "company": "TechCorp",
            "salary_min": 140000,
            "salary_max": 170000,
            "location_policy": "remote",
            "role_type": "ic",
        }

        result = get_extraction_summary(extraction_result, "job_posting")

        assert "Title: Senior Software Engineer" in result
        assert "Company: TechCorp" in result
        assert "Salary: $140,000 - $170,000" in result
        assert "Location: Remote" in result
        assert "Role: Individual Contributor" in result

    def test_get_extraction_summary_partial_job_posting(self):
        """Test summary generation for partial job posting."""
        extraction_result = {
            "title": "Software Engineer",
            "company": None,
            "salary_min": None,
            "salary_max": 150000,
            "location_policy": "unclear",
            "role_type": "unclear",
        }

        result = get_extraction_summary(extraction_result, "job_posting")

        assert "Title: Software Engineer" in result
        assert "Salary: Up to $150,000" in result
        assert "Company:" not in result
        assert "Location:" not in result
        assert "Role:" not in result

    def test_get_extraction_summary_salary_only_min(self):
        """Test summary generation with only minimum salary."""
        extraction_result = {
            "title": "Software Engineer",
            "company": "TechCorp",
            "salary_min": 120000,
            "salary_max": None,
            "location_policy": "remote",
            "role_type": "ic",
        }

        result = get_extraction_summary(extraction_result, "job_posting")

        assert "Title: Software Engineer" in result
        assert "Company: TechCorp" in result
        assert "Salary: From $120,000" in result
        assert "Location: Remote" in result
        assert "Role: Individual Contributor" in result

    def test_get_extraction_summary_manager_role(self):
        """Test summary generation for manager role."""
        extraction_result = {
            "title": "Engineering Manager",
            "company": "TechCorp",
            "salary_min": 160000,
            "salary_max": 200000,
            "location_policy": "hybrid",
            "role_type": "manager",
        }

        result = get_extraction_summary(extraction_result, "job_posting")

        assert "Title: Engineering Manager" in result
        assert "Company: TechCorp" in result
        assert "Salary: $160,000 - $200,000" in result
        assert "Location: Hybrid" in result
        assert "Role: Manager" in result

    def test_get_extraction_summary_empty_data(self):
        """Test summary generation with empty data."""
        extraction_result = {}
        result = get_extraction_summary(extraction_result, "job_posting")
        assert result == "No data extracted"

    def test_get_extraction_summary_no_meaningful_data(self):
        """Test summary generation with no meaningful data."""
        extraction_result = {
            "title": None,
            "company": "",
            "salary_min": None,
            "salary_max": None,
            "location_policy": "unclear",
            "role_type": "unclear",
        }

        result = get_extraction_summary(extraction_result, "job_posting")
        assert result == "No meaningful information extracted"

    def test_get_extraction_summary_invalid_schema(self):
        """Test summary generation with invalid schema name."""
        extraction_result = {"field1": "value1", "field2": "value2"}
        with pytest.raises(ValueError, match="Only 'job_posting' schema is supported"):
            get_extraction_summary(extraction_result, "unknown_schema")


class TestExtractWithSchema:
    """Test cases for the _extract_with_schema function."""

    @patch("src.agent.tools.extraction.schema_extraction_tool._get_extraction_client")
    def test_extract_with_schema_success(self, mock_get_client):
        """Test successful extraction with schema."""
        from src.agent.prompts.extraction.job_posting import (
            JOB_POSTING_EXTRACTION_PROMPT,
        )

        # Mock the client and its methods
        mock_client = Mock()
        mock_anthropic_client = Mock()
        mock_structured_llm = Mock()
        mock_result = Mock()
        mock_result.model_dump.return_value = {"title": "Software Engineer"}

        mock_get_client.return_value = mock_client
        mock_client._get_client.return_value = mock_anthropic_client
        mock_anthropic_client.with_structured_output.return_value = mock_structured_llm
        mock_structured_llm.invoke.return_value = mock_result

        result = _extract_with_schema(
            "Software Engineer position",
            JobPostingExtractionSchema,
            JOB_POSTING_EXTRACTION_PROMPT,
        )

        assert result == mock_result.model_dump.return_value
        mock_structured_llm.invoke.assert_called_once()

    @patch("src.llm.observability.langfuse_manager.get_config")
    @patch("src.agent.tools.extraction.schema_extraction_tool._get_extraction_client")
    def test_extract_with_schema_with_langfuse(self, mock_get_client, mock_get_config):
        """Test extraction with Langfuse manager integration."""
        from src.agent.prompts.extraction.job_posting import (
            JOB_POSTING_EXTRACTION_PROMPT,
        )

        # Mock the client and its methods
        mock_client = Mock()
        mock_anthropic_client = Mock()
        mock_structured_llm = Mock()
        mock_result = Mock()
        mock_result.model_dump.return_value = {"title": "Software Engineer"}

        mock_get_client.return_value = mock_client
        mock_client._get_client.return_value = mock_anthropic_client
        mock_anthropic_client.with_structured_output.return_value = mock_structured_llm
        mock_structured_llm.invoke.return_value = mock_result

        # Mock Langfuse manager config
        mock_langfuse_handler = Mock()
        mock_config = {"callbacks": [mock_langfuse_handler]}
        mock_get_config.return_value = mock_config

        result = _extract_with_schema(
            "Software Engineer position",
            JobPostingExtractionSchema,
            JOB_POSTING_EXTRACTION_PROMPT,
        )

        assert result == mock_result.model_dump.return_value
        # Verify that langfuse manager get_config was called
        mock_get_config.assert_called_once()
        # Verify that invoke was called with the config from langfuse manager
        mock_structured_llm.invoke.assert_called_once()
        call_args = mock_structured_llm.invoke.call_args
        assert call_args.kwargs["config"] == mock_config

    @patch("src.agent.tools.extraction.schema_extraction_tool._get_extraction_client")
    def test_extract_with_schema_client_error(self, mock_get_client):
        """Test extraction when client initialization fails."""
        from src.agent.prompts.extraction.job_posting import (
            JOB_POSTING_EXTRACTION_PROMPT,
        )

        mock_get_client.side_effect = LLMProviderError("Client initialization failed")

        with pytest.raises(LLMProviderError, match="Client initialization failed"):
            _extract_with_schema(
                "Software Engineer position",
                JobPostingExtractionSchema,
                JOB_POSTING_EXTRACTION_PROMPT,
            )
