"""
Pytest configuration file for the Job Search Assistant tests.
"""

import os
from pathlib import Path

import pytest
import yaml

# Set test environment before any imports
os.environ["APP_ENV"] = "test"


@pytest.fixture(autouse=True)
def reset_configs_state():
    """Reset global configs state before each test for proper isolation."""
    # This fixture runs automatically before each test
    yield  # Run the test

    # After the test, reset the global config proxy state
    from src.config import config

    config._current_config_dir = None


# Define project root directory
@pytest.fixture
def project_root():
    return Path(__file__).parent.parent


# Configuration fixtures
@pytest.fixture
def test_config():
    """Provide test config instance"""
    from src.config import config

    return config


@pytest.fixture
def mock_api_keys(monkeypatch):
    """Mock API keys for testing"""
    monkeypatch.setenv("ANTHROPIC_API_KEY", "test-anthropic-key")
    monkeypatch.setenv("FIREWORKS_API_KEY", "test-fireworks-key")
    monkeypatch.setenv("LANGFUSE_PUBLIC_KEY", "test-langfuse-public")
    monkeypatch.setenv("LANGFUSE_SECRET_KEY", "test-langfuse-secret")


@pytest.fixture
def reload_config():
    """Utility to reload config during tests"""

    def _reload(config_dir=None):
        from src.config import config

        return config.reload(config_dir=config_dir)

    return _reload


# Fixture for sample job descriptions
@pytest.fixture
def sample_job_descriptions_dir(project_root):
    return project_root / "tests" / "fixtures" / "sample_job_descriptions"


# Fixture for sample resumes
@pytest.fixture
def sample_resumes_dir(project_root):
    return project_root / "tests" / "fixtures" / "sample_resumes"


# Fixture to load a sample job description
@pytest.fixture
def sample_job_description(sample_job_descriptions_dir):
    job_file = sample_job_descriptions_dir / "software_engineer.txt"
    with open(job_file, "r") as f:
        return f.read()


# Fixture to load a sample resume
@pytest.fixture
def sample_resume(sample_resumes_dir):
    resume_file = sample_resumes_dir / "software_engineer.yaml"
    with open(resume_file, "r") as f:
        return yaml.safe_load(f)
