"""
Unit tests for workflow state management.

This module contains comprehensive tests for the workflow state
management functions and utilities.
"""

from unittest.mock import Mock

import pytest

from src.agent.workflows.job_evaluation.states import (
    JobEvaluationWorkflowState,
    add_message,
    create_initial_state,
    get_extracted_info_as_dict,
    is_extraction_successful,
)
from src.models.job import JobPostingExtractionSchema


class TestCreateInitialState:
    """Test cases for the create_initial_state function."""

    def test_create_initial_state_basic(self):
        """Test creating initial state with basic parameters."""
        job_text = "Software Engineer at TechCorp"

        state = create_initial_state(job_text)

        assert state["job_posting_text"] == job_text
        assert state["extracted_info"] is None
        assert state["evaluation_result"] is None
        assert state["messages"] == []
        assert state["langfuse_handler"] is None
        assert state["workflow_version"] == "3.0"
        assert state["extraction_duration"] is None
        assert state["evaluation_duration"] is None

    def test_create_initial_state_with_langfuse(self, mock_langfuse_handler):
        """Test creating initial state with Langfuse handler."""
        job_text = "Software Engineer at TechCorp"

        state = create_initial_state(job_text, mock_langfuse_handler)

        assert state["job_posting_text"] == job_text
        assert state["langfuse_handler"] == mock_langfuse_handler
        assert state["workflow_version"] == "3.0"

    def test_create_initial_state_empty_text(self):
        """Test creating initial state with empty job text."""
        state = create_initial_state("")

        assert state["job_posting_text"] == ""
        assert state["extracted_info"] is None

    def test_create_initial_state_long_text(self):
        """Test creating initial state with long job text."""
        long_text = "A" * 10000  # Very long job posting text

        state = create_initial_state(long_text)

        assert state["job_posting_text"] == long_text
        assert len(state["job_posting_text"]) == 10000


class TestIsExtractionSuccessful:
    """Test cases for the is_extraction_successful function."""

    def test_is_extraction_successful_with_valid_schema(
        self, workflow_state_factory, mock_pydantic_extraction_result
    ):
        """Test extraction success detection with valid Pydantic schema."""
        state = workflow_state_factory(extracted_info=mock_pydantic_extraction_result)

        result = is_extraction_successful(state)

        assert result is True

    def test_is_extraction_successful_with_none(self, workflow_state_factory):
        """Test extraction success detection with None extracted info."""
        state = workflow_state_factory(extracted_info=None)

        result = is_extraction_successful(state)

        assert result is False

    def test_is_extraction_successful_with_dict(self, workflow_state_factory):
        """Test extraction success detection with dictionary (should fail)."""
        state = workflow_state_factory(extracted_info={"title": "Software Engineer"})

        result = is_extraction_successful(state)

        assert result is False

    def test_is_extraction_successful_with_empty_dict(self, workflow_state_factory):
        """Test extraction success detection with empty dictionary."""
        state = workflow_state_factory(extracted_info={})

        result = is_extraction_successful(state)

        assert result is False

    def test_is_extraction_successful_with_mock_schema(self, workflow_state_factory):
        """Test extraction success detection with mock schema object."""
        mock_schema = Mock(spec=JobPostingExtractionSchema)
        state = workflow_state_factory(extracted_info=mock_schema)

        result = is_extraction_successful(state)

        assert result is True

    def test_is_extraction_successful_with_wrong_type(self, workflow_state_factory):
        """Test extraction success detection with wrong object type."""
        state = workflow_state_factory(extracted_info="string value")

        result = is_extraction_successful(state)

        assert result is False


class TestGetExtractedInfoAsDict:
    """Test cases for the get_extracted_info_as_dict function."""

    def test_get_extracted_info_as_dict_successful_extraction(
        self, workflow_state_factory, mock_pydantic_extraction_result
    ):
        """Test converting successful extraction to dict."""
        state = workflow_state_factory(extracted_info=mock_pydantic_extraction_result)

        result = get_extracted_info_as_dict(state)

        assert isinstance(result, dict)
        assert result["title"] == "Senior Software Engineer"
        assert result["company"] == "TechCorp"
        assert result["salary_min"] == 140000
        assert result["salary_max"] == 170000
        assert result["location_policy"] == "remote"
        assert result["role_type"] == "ic"
        # Should also have alternative field names
        assert result["job_title"] == "Senior Software Engineer"
        assert result["company_name"] == "TechCorp"

    def test_get_extracted_info_as_dict_failed_extraction(self, workflow_state_factory):
        """Test converting failed extraction to dict."""
        state = workflow_state_factory(extracted_info=None)

        result = get_extracted_info_as_dict(state)

        assert result == {}

    def test_get_extracted_info_as_dict_empty_extraction(self, workflow_state_factory):
        """Test converting empty extraction to dict."""
        empty_schema = JobPostingExtractionSchema()
        state = workflow_state_factory(extracted_info=empty_schema)

        result = get_extracted_info_as_dict(state)

        assert isinstance(result, dict)
        assert result["title"] is None
        assert result["company"] is None
        assert result["salary_min"] is None
        assert result["salary_max"] is None
        assert result["location_policy"] == "unclear"  # Default value
        assert result["role_type"] == "unclear"  # Default value

    def test_get_extracted_info_as_dict_partial_extraction(
        self, workflow_state_factory
    ):
        """Test converting partial extraction to dict."""
        partial_schema = JobPostingExtractionSchema(
            title="Software Engineer",
            company=None,
            salary_min=None,
            salary_max=150000,
            location_policy="remote",
            role_type="unclear",
        )
        state = workflow_state_factory(extracted_info=partial_schema)

        result = get_extracted_info_as_dict(state)

        assert result["title"] == "Software Engineer"
        assert result["company"] is None
        assert result["salary_max"] == 150000
        assert result["location_policy"] == "remote"
        assert result["job_title"] == "Software Engineer"
        assert result["company_name"] is None


class TestAddMessage:
    """Test cases for the add_message function."""

    def test_add_message_basic(self, workflow_state_factory):
        """Test adding a basic message to state."""
        state = workflow_state_factory(messages=[])

        updated_state = add_message(state, "test_role", "test content")

        assert len(updated_state["messages"]) == 1
        message = updated_state["messages"][0]
        assert message["role"] == "test_role"
        assert message["content"] == "test content"
        assert "error" not in message
        assert "metadata" not in message

    def test_add_message_with_error(self, workflow_state_factory):
        """Test adding a message with error information."""
        state = workflow_state_factory(messages=[])

        updated_state = add_message(state, "extraction_node", error="Extraction failed")

        assert len(updated_state["messages"]) == 1
        message = updated_state["messages"][0]
        assert message["role"] == "extraction_node"
        assert message["error"] == "Extraction failed"
        assert "content" not in message

    def test_add_message_with_metadata(self, workflow_state_factory):
        """Test adding a message with metadata."""
        metadata = {"duration": 1.5, "tokens_used": 100}
        state = workflow_state_factory(messages=[])

        updated_state = add_message(state, "llm_call", "Success", metadata=metadata)

        assert len(updated_state["messages"]) == 1
        message = updated_state["messages"][0]
        assert message["role"] == "llm_call"
        assert message["content"] == "Success"
        assert message["metadata"] == metadata

    def test_add_message_complete(self, workflow_state_factory):
        """Test adding a message with all fields."""
        metadata = {"step": "extraction", "duration": 2.1}
        state = workflow_state_factory(messages=[])

        updated_state = add_message(
            state,
            "extraction_node",
            content="Extraction completed",
            error="Minor warning",
            metadata=metadata,
        )

        assert len(updated_state["messages"]) == 1
        message = updated_state["messages"][0]
        assert message["role"] == "extraction_node"
        assert message["content"] == "Extraction completed"
        assert message["error"] == "Minor warning"
        assert message["metadata"] == metadata

    def test_add_message_to_existing_messages(self, workflow_state_factory):
        """Test adding a message to state that already has messages."""
        existing_messages = [{"role": "start", "content": "Starting workflow"}]
        state = workflow_state_factory(messages=existing_messages)

        updated_state = add_message(state, "extraction_node", "Extraction done")

        assert len(updated_state["messages"]) == 2
        assert updated_state["messages"][0] == existing_messages[0]
        assert updated_state["messages"][1]["role"] == "extraction_node"
        assert updated_state["messages"][1]["content"] == "Extraction done"

    def test_add_message_preserves_other_state(self, workflow_state_factory):
        """Test that adding a message preserves other state fields."""
        original_state = workflow_state_factory(
            job_posting_text="Test job",
            extracted_info={"title": "Engineer"},
            evaluation_result={"pass": True},
            messages=[],
            workflow_version="3.0",
        )

        updated_state = add_message(original_state, "test", "message")

        # Check that other fields are preserved
        assert updated_state["job_posting_text"] == "Test job"
        assert updated_state["extracted_info"] == {"title": "Engineer"}
        assert updated_state["evaluation_result"] == {"pass": True}
        assert updated_state["workflow_version"] == "3.0"
        # But messages should be updated
        assert len(updated_state["messages"]) == 1

    def test_add_message_none_values(self, workflow_state_factory):
        """Test adding a message with None values."""
        state = workflow_state_factory(messages=[])

        updated_state = add_message(
            state, "test_role", content=None, error=None, metadata=None
        )

        assert len(updated_state["messages"]) == 1
        message = updated_state["messages"][0]
        assert message["role"] == "test_role"
        # None values should not be included in the message
        assert "content" not in message
        assert "error" not in message
        assert "metadata" not in message

    def test_add_message_empty_strings(self, workflow_state_factory):
        """Test adding a message with empty string values."""
        state = workflow_state_factory(messages=[])

        updated_state = add_message(
            state, "test_role", content="", error="", metadata={}
        )

        assert len(updated_state["messages"]) == 1
        message = updated_state["messages"][0]
        assert message["role"] == "test_role"
        assert message["content"] == ""
        assert message["error"] == ""
        assert message["metadata"] == {}


class TestJobEvaluationWorkflowState:
    """Test cases for the JobEvaluationWorkflowState TypedDict."""

    def test_workflow_state_creation(self):
        """Test creating a workflow state with all fields."""
        state = JobEvaluationWorkflowState(
            job_posting_text="Test job posting",
            extracted_info=None,
            evaluation_result=None,
            messages=[],
            langfuse_handler=None,
            workflow_version="3.0",
            extraction_duration=None,
            evaluation_duration=None,
        )

        assert state["job_posting_text"] == "Test job posting"
        assert state["extracted_info"] is None
        assert state["evaluation_result"] is None
        assert state["messages"] == []
        assert state["langfuse_handler"] is None
        assert state["workflow_version"] == "3.0"
        assert state["extraction_duration"] is None
        assert state["evaluation_duration"] is None

    def test_workflow_state_with_data(
        self, mock_pydantic_extraction_result, mock_evaluation_result
    ):
        """Test creating a workflow state with actual data."""
        messages = [{"role": "test", "content": "test message"}]

        state = JobEvaluationWorkflowState(
            job_posting_text="Software Engineer at TechCorp",
            extracted_info=mock_pydantic_extraction_result,
            evaluation_result=mock_evaluation_result,
            messages=messages,
            langfuse_handler=None,
            workflow_version="3.0",
            extraction_duration=1.5,
            evaluation_duration=0.8,
        )

        assert state["job_posting_text"] == "Software Engineer at TechCorp"
        assert state["extracted_info"] == mock_pydantic_extraction_result
        assert state["evaluation_result"] == mock_evaluation_result
        assert state["messages"] == messages
        assert state["extraction_duration"] == 1.5
        assert state["evaluation_duration"] == 0.8

    def test_workflow_state_field_access(self, workflow_state_factory):
        """Test accessing workflow state fields."""
        state = workflow_state_factory(
            job_posting_text="Test job", workflow_version="3.0"
        )

        # Test dict-like access
        assert state["job_posting_text"] == "Test job"
        assert state["workflow_version"] == "3.0"

        # Test get method
        assert state.get("job_posting_text") == "Test job"
        assert state.get("nonexistent_field") is None
        assert state.get("nonexistent_field", "default") == "default"

    def test_workflow_state_update(self, workflow_state_factory):
        """Test updating workflow state fields."""
        state = workflow_state_factory()

        # Update a field
        updated_state = {**state, "workflow_version": "2.1"}

        assert updated_state["workflow_version"] == "2.1"
        # Original state should be unchanged
        assert state["workflow_version"] == "3.0"
