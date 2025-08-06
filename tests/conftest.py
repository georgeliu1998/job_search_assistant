"""
Pytest configuration file for the Job Search Assistant tests.

This file contains shared fixtures and configuration for all tests.
"""

import os
from pathlib import Path
from unittest.mock import Mock

import pytest

from src.models.enums import Environment

# Set stage environment before any imports
os.environ["APP_ENV"] = Environment.STAGE.value


@pytest.fixture(autouse=True)
def reset_config_state():
    """Reset global configs state before each test for proper isolation."""
    # This fixture runs automatically before each test
    yield  # Run the test

    # After the test, reset the global config proxy state
    from src.config import config
    from src.config.manager import ConfigManager

    # Clear any cached instances
    ConfigManager._instances = {}

    # Reset the lazy config proxy state
    config._current_config_dir = None


@pytest.fixture
def project_root():
    """Return the project root directory."""
    return Path(__file__).parent.parent


@pytest.fixture
def test_config():
    """Provide stage config instance"""
    from src.config import config

    return config


@pytest.fixture
def mock_api_keys(monkeypatch):
    """Mock API keys for testing"""
    monkeypatch.setenv("ANTHROPIC_API_KEY", "test-anthropic-key")
    monkeypatch.setenv("FIREWORKS_API_KEY", "test-fireworks-key")
    monkeypatch.setenv("GOOGLE_API_KEY", "test-google-key")
    monkeypatch.setenv("LANGFUSE_PUBLIC_KEY", "test-langfuse-public")
    monkeypatch.setenv("LANGFUSE_SECRET_KEY", "test-langfuse-secret")


@pytest.fixture
def config_reload_helper():
    """Utility to reload config during tests"""

    def reload_config():
        """Force reload configuration"""
        from src.config.manager import ConfigManager

        # Clear cached instances to force reload
        ConfigManager._instances = {}

        # Import and return fresh config
        from src.config import config

        return config

    return reload_config


@pytest.fixture
def sample_job_descriptions_dir(project_root):
    return project_root / "tests" / "fixtures" / "sample_job_descriptions"


@pytest.fixture
def sample_resumes_dir(project_root):
    return project_root / "tests" / "fixtures" / "sample_resumes"


@pytest.fixture
def sample_job_description(sample_job_descriptions_dir):
    """Load sample software engineer job description."""
    job_file = sample_job_descriptions_dir / "software_engineer.txt"
    if job_file.exists():
        return job_file.read_text()
    return "Sample job description not found"


@pytest.fixture
def sample_resume(sample_resumes_dir):
    """Load sample software engineer resume."""
    resume_file = sample_resumes_dir / "software_engineer.yaml"
    if resume_file.exists():
        return resume_file.read_text()
    return "Sample resume not found"


# Agent-specific fixtures
@pytest.fixture
def mock_extraction_result():
    """Mock successful extraction result for testing."""
    return {
        "title": "Senior Software Engineer",
        "company": "TechCorp",
        "salary_min": 140000,
        "salary_max": 170000,
        "location_policy": "remote",
        "role_type": "ic",
    }


@pytest.fixture
def mock_partial_extraction_result():
    """Mock partial extraction result for testing edge cases."""
    return {
        "title": "Software Engineer",
        "company": None,
        "salary_min": None,
        "salary_max": None,
        "location_policy": "unclear",
        "role_type": "unclear",
    }


@pytest.fixture
def mock_evaluation_result():
    """Mock successful evaluation result for testing."""
    return {
        "salary": {"pass": True, "reason": "Salary meets requirement"},
        "remote": {"pass": True, "reason": "Position is remote"},
        "title_level": {"pass": True, "reason": "IC role has appropriate seniority"},
    }


@pytest.fixture
def mock_failed_evaluation_result():
    """Mock failed evaluation result for testing."""
    return {
        "salary": {"pass": False, "reason": "Salary too low"},
        "remote": {"pass": False, "reason": "Position is not remote"},
        "title_level": {"pass": False, "reason": "IC role lacks required seniority"},
    }


@pytest.fixture
def mock_llm_client():
    """Mock LLM client for testing."""
    client = Mock()
    client.invoke = Mock()
    client._get_client = Mock()

    # Mock structured output
    structured_llm = Mock()
    client._get_client.return_value.with_structured_output.return_value = structured_llm

    return client


@pytest.fixture
def mock_langfuse_handler():
    """Mock Langfuse handler for testing."""
    handler = Mock()
    handler.flush = Mock()
    return handler


@pytest.fixture
def sample_job_posting_texts():
    """Sample job posting texts for testing various scenarios."""
    return {
        "complete": """
        Senior Software Engineer
        TechCorp Inc.
        Remote position
        Salary: $140,000 - $170,000

        We are looking for a senior software engineer to join our team.
        This is a fully remote position with competitive compensation.
        """,
        "minimal": "Software Engineer position available",
        "no_salary": """
        Senior Software Engineer at TechCorp
        Remote position
        No salary information provided
        """,
        "onsite": """
        Senior Software Engineer at TechCorp
        On-site position in San Francisco
        Salary: $140,000 - $170,000
        """,
        "manager": """
        Engineering Manager at TechCorp
        Remote position
        Salary: $160,000 - $200,000
        Leading a team of 8 engineers
        """,
        "junior": """
        Junior Software Engineer at TechCorp
        Remote position
        Salary: $80,000 - $100,000
        Entry level position
        """,
    }


@pytest.fixture
def workflow_state_factory():
    """Factory function for creating workflow states for testing."""
    from src.agent.workflows.job_evaluation.states import JobEvaluationState

    def create_state(
        job_posting_text="Test job posting",
        extracted_info=None,
        evaluation_result=None,
        recommendation=None,
        reasoning=None,
    ):
        return JobEvaluationState(
            job_posting_text=job_posting_text,
            extracted_info=extracted_info,
            evaluation_result=evaluation_result,
            recommendation=recommendation,
            reasoning=reasoning,
        )

    return create_state


@pytest.fixture
def mock_pydantic_extraction_result():
    """Mock Pydantic model extraction result for testing."""
    from src.models.job import JobPostingExtractionSchema

    return JobPostingExtractionSchema(
        title="Senior Software Engineer",
        company="TechCorp",
        salary_min=140000,
        salary_max=170000,
        location_policy="remote",
        role_type="ic",
    )
