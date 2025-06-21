"""
Pytest configuration file for the Job Search Assistant tests.
"""

import os
from pathlib import Path

import pytest
import yaml

# Set test environment before any imports
os.environ["APP_ENV"] = "test"


# Define project root directory
@pytest.fixture
def project_root():
    return Path(__file__).parent.parent


# Configuration fixtures
@pytest.fixture
def test_settings():
    """Provide test settings instance"""
    from src.config.settings import settings
    return settings


@pytest.fixture
def mock_api_keys(monkeypatch):
    """Mock API keys for testing"""
    monkeypatch.setenv("ANTHROPIC_API_KEY", "test-anthropic-key")
    monkeypatch.setenv("FIREWORKS_API_KEY", "test-fireworks-key")
    monkeypatch.setenv("LANGFUSE_PUBLIC_KEY", "test-langfuse-public")
    monkeypatch.setenv("LANGFUSE_SECRET_KEY", "test-langfuse-secret")


@pytest.fixture
def reload_settings():
    """Utility to reload settings during tests"""
    def _reload():
        from src.config.settings import reload_settings
        return reload_settings()
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
