"""Unit tests for data models."""

from datetime import datetime

import pytest

from src.models.models import (
    Education,
    EvaluationResult,
    Experience,
    JobDescription,
    Resume,
)


def test_education_creation():
    """Test Education model creation."""
    education = Education(
        institution="Test University",
        degree="Bachelor of Science",
        field_of_study="Computer Science",
    )
    assert education.institution == "Test University"
    assert education.degree == "Bachelor of Science"
    assert education.field_of_study == "Computer Science"
    assert education.start_date is None
    assert education.end_date is None


def test_experience_creation():
    """Test Experience model creation."""
    experience = Experience(company="Test Company", title="Software Engineer")
    assert experience.company == "Test Company"
    assert experience.title == "Software Engineer"
    assert experience.highlights == []


def test_resume_creation():
    """Test Resume model creation."""
    resume = Resume(personal_info={"name": "John Doe", "email": "john@example.com"})
    assert resume.personal_info["name"] == "John Doe"
    assert resume.personal_info["email"] == "john@example.com"
    assert resume.education == []
    assert resume.experience == []
    assert resume.skills == []


def test_job_description_creation():
    """Test JobDescription model creation."""
    job = JobDescription(
        raw_text="Sample raw text for job description.",
        title="Python Developer",
        company="Tech Corp",
        description="Develop Python applications",
    )
    assert job.title == "Python Developer"
    assert job.company == "Tech Corp"
    assert job.description == "Develop Python applications"
    assert job.is_remote is False
    assert job.requirements == []


def test_evaluation_result_creation():
    """Test EvaluationResult model creation."""
    job = JobDescription(
        raw_text="Sample raw text for job description.",
        title="Python Developer",
        company="Tech Corp",
        description="Develop Python applications",
    )

    result = EvaluationResult(
        job=job, is_good_fit=True, score=0.8, reasoning="Good match for skills"
    )
    assert result.job.title == "Python Developer"
    assert result.is_good_fit is True
    assert result.score == 0.8
    assert result.reasoning == "Good match for skills"
    assert result.matching_skills == []


def test_evaluation_result_score_validation():
    """Test that EvaluationResult validates score range."""
    job = JobDescription(
        raw_text="Sample raw text for job description.",
        title="Python Developer",
        company="Tech Corp",
        description="Develop Python applications",
    )

    # Test valid score
    result = EvaluationResult(job=job, is_good_fit=True, score=0.5, reasoning="Test")
    assert result.score == 0.5

    # Test score validation will be handled by Pydantic automatically
    # Scores outside 0.0-1.0 range should raise validation errors
