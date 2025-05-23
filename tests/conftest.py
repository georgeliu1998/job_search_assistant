"""
Pytest configuration file for the Job Search Assistant tests.
"""
import os
from pathlib import Path
import pytest
import yaml


# Define project root directory
@pytest.fixture
def project_root():
    return Path(__file__).parent.parent


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


# Fixture for job preferences
@pytest.fixture
def sample_job_preferences(project_root):
    preferences_file = project_root / "examples" / "job_preferences.yaml"
    with open(preferences_file, "r") as f:
        return yaml.safe_load(f) 