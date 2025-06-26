"""
Pytest configuration file for the Job Search Assistant tests.

This file contains shared fixtures and configuration for all tests.
"""

import os
from pathlib import Path

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
