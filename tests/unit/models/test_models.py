"""Unit tests for data models."""

from datetime import datetime

import pytest
from pydantic import ValidationError

from src.models import (
    BaseDataModel,
    Education,
    Environment,
    EvaluationResult,
    Experience,
    JobDescription,
    JobSource,
    JobStatus,
    Resume,
    UserPreferences,
)


class TestBaseDataModel:
    """Test the BaseDataModel configuration."""

    def test_base_model_configuration(self):
        """Test that BaseDataModel has correct configuration."""

        # Create a simple test model to verify configuration
        class TestModel(BaseDataModel):
            name: str
            value: int

        model = TestModel(name="  test  ", value=42)

        # Test str_strip_whitespace configuration
        assert model.name == "test"  # Whitespace should be stripped
        assert model.value == 42

    def test_enum_values_configuration(self):
        """Test that use_enum_values configuration works."""

        class TestModel(BaseDataModel):
            status: JobStatus

        model = TestModel(status=JobStatus.PENDING_EVALUATION)

        # Should use enum values in serialization
        data = model.model_dump()
        assert data["status"] == "pending_evaluation"  # Enum value, not enum object


class TestEnvironmentEnum:
    """Test the Environment enum functionality."""

    def test_environment_values(self):
        """Test Environment enum values."""
        assert Environment.DEV.value == "dev"
        assert Environment.STAGE.value == "stage"
        assert Environment.PROD.value == "prod"

    def test_environment_full_name_property(self):
        """Test Environment full_name property."""
        assert Environment.DEV.full_name == "development"
        assert Environment.STAGE.full_name == "staging"
        assert Environment.PROD.full_name == "production"

    def test_environment_from_string_short_forms(self):
        """Test Environment.from_string with short forms."""
        assert Environment.from_string("dev") == Environment.DEV
        assert Environment.from_string("stage") == Environment.STAGE
        assert Environment.from_string("prod") == Environment.PROD

    def test_environment_from_string_full_forms(self):
        """Test Environment.from_string with full forms."""
        assert Environment.from_string("development") == Environment.DEV
        assert Environment.from_string("staging") == Environment.STAGE
        assert Environment.from_string("production") == Environment.PROD

    def test_environment_from_string_case_insensitive(self):
        """Test Environment.from_string is case insensitive."""
        assert Environment.from_string("DEV") == Environment.DEV
        assert Environment.from_string("Development") == Environment.DEV
        assert Environment.from_string("STAGING") == Environment.STAGE

    def test_environment_from_string_whitespace_handling(self):
        """Test Environment.from_string handles whitespace."""
        assert Environment.from_string("  dev  ") == Environment.DEV
        assert Environment.from_string("\tdevelopment\n") == Environment.DEV

    def test_environment_from_string_invalid_value(self):
        """Test Environment.from_string with invalid value."""
        with pytest.raises(ValueError, match="Invalid environment: 'invalid'"):
            Environment.from_string("invalid")

        with pytest.raises(ValueError, match="Valid values: dev, stage, prod"):
            Environment.from_string("test")


class TestJobSourceEnum:
    """Test the JobSource enum."""

    def test_job_source_values(self):
        """Test JobSource enum values."""
        assert JobSource.LINKEDIN.value == "linkedin"
        assert JobSource.INDEED.value == "indeed"
        assert JobSource.ZIPRECRUITER.value == "ziprecruiter"
        assert JobSource.OTHER.value == "other"

    def test_job_source_all_values(self):
        """Test all JobSource values are defined."""
        expected_values = {"linkedin", "indeed", "ziprecruiter", "other"}
        actual_values = {source.value for source in JobSource}
        assert actual_values == expected_values


class TestJobStatusEnum:
    """Test the JobStatus enum."""

    def test_job_status_values(self):
        """Test JobStatus enum values."""
        assert JobStatus.PENDING_EVALUATION.value == "pending_evaluation"
        assert JobStatus.EVALUATING.value == "evaluating"
        assert JobStatus.PASS.value == "pass"
        assert JobStatus.REJECT.value == "reject"
        assert JobStatus.APPLIED.value == "applied"
        assert JobStatus.INTERVIEWING.value == "interviewing"
        assert JobStatus.OFFER.value == "offer"
        assert JobStatus.HIRED.value == "hired"

    def test_job_status_all_values(self):
        """Test all JobStatus values are defined."""
        expected_values = {
            "pending_evaluation",
            "evaluating",
            "pass",
            "reject",
            "applied",
            "interviewing",
            "offer",
            "hired",
        }
        actual_values = {status.value for status in JobStatus}
        assert actual_values == expected_values


class TestEducationModel:
    """Test the Education model."""

    def test_education_creation_required_fields(self):
        """Test Education model creation with required fields."""
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

    def test_education_creation_with_dates(self):
        """Test Education model creation with optional dates."""
        education = Education(
            institution="MIT",
            degree="PhD",
            field_of_study="Artificial Intelligence",
            start_date="2020-09-01",
            end_date="2024-05-15",
        )
        assert education.start_date == "2020-09-01"
        assert education.end_date == "2024-05-15"

    def test_education_missing_required_fields(self):
        """Test Education model validation with missing required fields."""
        with pytest.raises(ValidationError) as exc_info:
            Education(institution="Test University")

        errors = exc_info.value.errors()
        missing_fields = {error["loc"][0] for error in errors}
        assert "degree" in missing_fields
        assert "field_of_study" in missing_fields

    def test_education_serialization(self):
        """Test Education model serialization."""
        education = Education(
            institution="Stanford",
            degree="MS",
            field_of_study="Data Science",
            start_date="2022-09-01",
        )

        data = education.model_dump()
        expected = {
            "institution": "Stanford",
            "degree": "MS",
            "field_of_study": "Data Science",
            "start_date": "2022-09-01",
            "end_date": None,
        }
        assert data == expected

    def test_education_whitespace_stripping(self):
        """Test that Education strips whitespace from string fields."""
        education = Education(
            institution="  Harvard University  ",
            degree="  MBA  ",
            field_of_study="  Business Administration  ",
        )
        assert education.institution == "Harvard University"
        assert education.degree == "MBA"
        assert education.field_of_study == "Business Administration"


class TestExperienceModel:
    """Test the Experience model."""

    def test_experience_creation_required_fields(self):
        """Test Experience model creation with required fields."""
        experience = Experience(company="Test Company", title="Software Engineer")
        assert experience.company == "Test Company"
        assert experience.title == "Software Engineer"
        assert experience.start_date is None
        assert experience.end_date is None
        assert experience.highlights == []

    def test_experience_creation_with_all_fields(self):
        """Test Experience model creation with all fields."""
        highlights = ["Led team of 5 developers", "Increased performance by 40%"]
        experience = Experience(
            company="Google",
            title="Senior Software Engineer",
            start_date="2020-01-15",
            end_date="2023-12-31",
            highlights=highlights,
        )
        assert experience.company == "Google"
        assert experience.title == "Senior Software Engineer"
        assert experience.start_date == "2020-01-15"
        assert experience.end_date == "2023-12-31"
        assert experience.highlights == highlights

    def test_experience_missing_required_fields(self):
        """Test Experience model validation with missing required fields."""
        with pytest.raises(ValidationError) as exc_info:
            Experience(company="Test Company")

        errors = exc_info.value.errors()
        missing_fields = {error["loc"][0] for error in errors}
        assert "title" in missing_fields

        with pytest.raises(ValidationError) as exc_info:
            Experience(title="Developer")

        errors = exc_info.value.errors()
        missing_fields = {error["loc"][0] for error in errors}
        assert "company" in missing_fields

    def test_experience_empty_highlights_default(self):
        """Test that highlights defaults to empty list."""
        experience = Experience(company="Company", title="Title")
        assert experience.highlights == []

        # Test that we can add to highlights
        experience.highlights.append("Achievement")
        assert experience.highlights == ["Achievement"]

    def test_experience_serialization(self):
        """Test Experience model serialization."""
        experience = Experience(
            company="Apple",
            title="iOS Developer",
            start_date="2021-06-01",
            highlights=["Published 3 apps", "Won hackathon"],
        )

        data = experience.model_dump()
        expected = {
            "company": "Apple",
            "title": "iOS Developer",
            "start_date": "2021-06-01",
            "end_date": None,
            "highlights": ["Published 3 apps", "Won hackathon"],
        }
        assert data == expected


class TestResumeModel:
    """Test the Resume model."""

    def test_resume_creation_minimal(self):
        """Test Resume model creation with minimal required fields."""
        personal_info = {"name": "John Doe", "email": "john@example.com"}
        resume = Resume(personal_info=personal_info)

        assert resume.personal_info == personal_info
        assert resume.summary is None
        assert resume.education == []
        assert resume.experience == []
        assert resume.skills == []

    def test_resume_creation_complete(self):
        """Test Resume model creation with all fields."""
        personal_info = {
            "name": "Jane Smith",
            "email": "jane@example.com",
            "phone": "+1-555-0123",
            "address": "123 Main St, City, State 12345",
        }

        education = [
            Education(institution="MIT", degree="BS", field_of_study="Computer Science")
        ]

        experience = [
            Experience(
                company="Google",
                title="Software Engineer",
                highlights=["Built scalable systems"],
            )
        ]

        skills = ["Python", "JavaScript", "Machine Learning"]
        summary = "Experienced software engineer with 5+ years in tech"

        resume = Resume(
            personal_info=personal_info,
            summary=summary,
            education=education,
            experience=experience,
            skills=skills,
        )

        assert resume.personal_info == personal_info
        assert resume.summary == summary
        assert resume.education == education
        assert resume.experience == experience
        assert resume.skills == skills

    def test_resume_missing_personal_info(self):
        """Test Resume model validation with missing personal_info."""
        with pytest.raises(ValidationError) as exc_info:
            Resume()

        errors = exc_info.value.errors()
        missing_fields = {error["loc"][0] for error in errors}
        assert "personal_info" in missing_fields

    def test_resume_personal_info_types(self):
        """Test Resume personal_info accepts various data types."""
        # Test with different value types
        personal_info = {
            "name": "John Doe",
            "age": 30,
            "is_citizen": True,
            "salary_expectation": 100000.50,
            "languages": ["English", "Spanish"],
        }

        resume = Resume(personal_info=personal_info)
        assert resume.personal_info == personal_info

    def test_resume_serialization(self):
        """Test Resume model serialization."""
        personal_info = {"name": "Test User", "email": "test@example.com"}
        skills = ["Python", "SQL"]

        resume = Resume(personal_info=personal_info, skills=skills)

        data = resume.model_dump()
        expected = {
            "personal_info": personal_info,
            "summary": None,
            "education": [],
            "experience": [],
            "skills": skills,
        }
        assert data == expected


class TestUserPreferencesModel:
    """Test the UserPreferences model."""

    def test_user_preferences_creation(self):
        """Test UserPreferences model creation."""
        job_titles = ["Software Engineer", "Data Scientist", "Product Manager"]
        preferences = UserPreferences(job_titles=job_titles)

        assert preferences.job_titles == job_titles

    def test_user_preferences_missing_job_titles(self):
        """Test UserPreferences validation with missing job_titles."""
        with pytest.raises(ValidationError) as exc_info:
            UserPreferences()

        errors = exc_info.value.errors()
        missing_fields = {error["loc"][0] for error in errors}
        assert "job_titles" in missing_fields

    def test_user_preferences_empty_job_titles(self):
        """Test UserPreferences with empty job_titles list."""
        preferences = UserPreferences(job_titles=[])
        assert preferences.job_titles == []

    def test_user_preferences_serialization(self):
        """Test UserPreferences model serialization."""
        job_titles = ["Backend Developer", "DevOps Engineer"]
        preferences = UserPreferences(job_titles=job_titles)

        data = preferences.model_dump()
        expected = {"job_titles": job_titles}
        assert data == expected


class TestJobDescriptionModel:
    """Test the JobDescription model."""

    def test_job_description_creation_minimal(self):
        """Test JobDescription model creation with minimal required fields."""
        job = JobDescription(raw_text="Sample raw text for job description.")

        assert job.raw_text == "Sample raw text for job description."
        assert job.title is None
        assert job.company is None
        assert job.description is None
        assert job.is_remote is False
        assert job.requirements == []
        assert job.source is None
        assert job.url is None
        assert job.date_posted is None
        assert job.date_scraped is None
        assert (
            job.status == JobStatus.PENDING_EVALUATION
        )  # Default values remain as enum objects
        assert job.evaluation_score is None
        assert job.evaluation_notes is None

    def test_job_description_creation_complete(self):
        """Test JobDescription model creation with all fields."""
        job = JobDescription(
            raw_text="Complete job description text",
            title="Senior Python Developer",
            company="Tech Corp",
            description="Develop Python applications",
            is_remote=True,
            requirements=["Python", "Django", "5+ years experience"],
            source=JobSource.LINKEDIN,
            url="https://linkedin.com/jobs/123",
            date_posted="2024-01-15",
            date_scraped="2024-01-16",
            status=JobStatus.PASS,
            evaluation_score=0.85,
            evaluation_notes="Strong match for requirements",
        )

        assert job.title == "Senior Python Developer"
        assert job.company == "Tech Corp"
        assert job.description == "Develop Python applications"
        assert job.is_remote is True
        assert job.requirements == ["Python", "Django", "5+ years experience"]
        assert job.source == "linkedin"  # use_enum_values=True converts to string
        assert job.url == "https://linkedin.com/jobs/123"
        assert job.date_posted == "2024-01-15"
        assert job.date_scraped == "2024-01-16"
        assert job.status == "pass"  # use_enum_values=True converts to string
        assert job.evaluation_score == 0.85
        assert job.evaluation_notes == "Strong match for requirements"

    def test_job_description_missing_raw_text(self):
        """Test JobDescription validation with missing raw_text."""
        with pytest.raises(ValidationError) as exc_info:
            JobDescription(title="Developer")

        errors = exc_info.value.errors()
        missing_fields = {error["loc"][0] for error in errors}
        assert "raw_text" in missing_fields

    def test_job_description_evaluation_score_validation(self):
        """Test JobDescription evaluation_score validation."""
        # Valid scores
        job1 = JobDescription(raw_text="test", evaluation_score=0.0)
        assert job1.evaluation_score == 0.0

        job2 = JobDescription(raw_text="test", evaluation_score=1.0)
        assert job2.evaluation_score == 1.0

        job3 = JobDescription(raw_text="test", evaluation_score=0.5)
        assert job3.evaluation_score == 0.5

        # Invalid scores
        with pytest.raises(
            ValidationError, match="Evaluation score must be between 0 and 1"
        ):
            JobDescription(raw_text="test", evaluation_score=-0.1)

        with pytest.raises(
            ValidationError, match="Evaluation score must be between 0 and 1"
        ):
            JobDescription(raw_text="test", evaluation_score=1.1)

    def test_job_description_default_status(self):
        """Test JobDescription default status."""
        job = JobDescription(raw_text="test")
        assert (
            job.status == JobStatus.PENDING_EVALUATION
        )  # Default values remain as enum objects

    def test_job_description_serialization(self):
        """Test JobDescription model serialization."""
        job = JobDescription(
            raw_text="Test job description",
            title="Developer",
            company="Company",
            is_remote=True,
            source=JobSource.INDEED,
            status=JobStatus.EVALUATING,
        )

        data = job.model_dump()

        # Check that enums are serialized as values
        assert data["source"] == "indeed"
        assert data["status"] == "evaluating"
        assert data["is_remote"] is True


class TestEvaluationResultModel:
    """Test the EvaluationResult model."""

    def test_evaluation_result_creation_minimal(self):
        """Test EvaluationResult model creation with minimal fields."""
        job = JobDescription(
            raw_text="Sample job description",
            title="Python Developer",
            company="Tech Corp",
        )

        result = EvaluationResult(
            job=job,
            is_good_fit=True,
            score=0.8,
            reasoning="Good match for skills",
        )

        assert result.job == job
        assert result.is_good_fit is True
        assert result.score == 0.8
        assert result.reasoning == "Good match for skills"
        assert result.matching_skills == []

    def test_evaluation_result_creation_complete(self):
        """Test EvaluationResult model creation with all fields."""
        job = JobDescription(raw_text="test", title="Developer")
        matching_skills = ["Python", "Django", "REST APIs"]

        result = EvaluationResult(
            job=job,
            is_good_fit=False,
            score=0.3,
            reasoning="Missing required experience",
            matching_skills=matching_skills,
        )

        assert result.is_good_fit is False
        assert result.score == 0.3
        assert result.reasoning == "Missing required experience"
        assert result.matching_skills == matching_skills

    def test_evaluation_result_missing_required_fields(self):
        """Test EvaluationResult validation with missing required fields."""
        job = JobDescription(raw_text="test")

        with pytest.raises(ValidationError) as exc_info:
            EvaluationResult(job=job, is_good_fit=True)

        errors = exc_info.value.errors()
        missing_fields = {error["loc"][0] for error in errors}
        assert "score" in missing_fields
        assert "reasoning" in missing_fields

    def test_evaluation_result_score_validation(self):
        """Test EvaluationResult score validation."""
        job = JobDescription(raw_text="test")

        # Valid scores
        result1 = EvaluationResult(
            job=job, is_good_fit=True, score=0.0, reasoning="test"
        )
        assert result1.score == 0.0

        result2 = EvaluationResult(
            job=job, is_good_fit=True, score=1.0, reasoning="test"
        )
        assert result2.score == 1.0

        # Invalid scores
        with pytest.raises(ValidationError, match="Score must be between 0 and 1"):
            EvaluationResult(job=job, is_good_fit=True, score=-0.1, reasoning="test")

        with pytest.raises(ValidationError, match="Score must be between 0 and 1"):
            EvaluationResult(job=job, is_good_fit=True, score=1.1, reasoning="test")

    def test_evaluation_result_serialization(self):
        """Test EvaluationResult model serialization."""
        job = JobDescription(
            raw_text="test job",
            title="Developer",
            status=JobStatus.PASS,
        )

        result = EvaluationResult(
            job=job,
            is_good_fit=True,
            score=0.9,
            reasoning="Excellent match",
            matching_skills=["Python", "SQL"],
        )

        data = result.model_dump()

        # Check that nested job model is properly serialized
        assert "job" in data
        assert data["job"]["title"] == "Developer"
        assert data["job"]["status"] == "pass"  # Enum serialized as value
        assert data["is_good_fit"] is True
        assert data["score"] == 0.9
        assert data["reasoning"] == "Excellent match"
        assert data["matching_skills"] == ["Python", "SQL"]


class TestModelInteroperability:
    """Test how models work together."""

    def test_resume_with_education_and_experience(self):
        """Test Resume model with Education and Experience objects."""
        education = Education(
            institution="University of California",
            degree="BS",
            field_of_study="Computer Science",
            start_date="2018-09-01",
            end_date="2022-05-15",
        )

        experience = Experience(
            company="Meta",
            title="Software Engineer",
            start_date="2022-06-01",
            highlights=["Built React components", "Optimized database queries"],
        )

        resume = Resume(
            personal_info={"name": "Alice Johnson", "email": "alice@example.com"},
            summary="Recent CS graduate with internship experience",
            education=[education],
            experience=[experience],
            skills=["Python", "JavaScript", "React", "SQL"],
        )

        assert len(resume.education) == 1
        assert len(resume.experience) == 1
        assert resume.education[0].institution == "University of California"
        assert resume.experience[0].company == "Meta"

    def test_evaluation_result_with_complete_job(self):
        """Test EvaluationResult with a complete JobDescription."""
        job = JobDescription(
            raw_text="Senior Software Engineer position at Google...",
            title="Senior Software Engineer",
            company="Google",
            description="Build scalable systems",
            is_remote=True,
            requirements=["Python", "Distributed Systems", "5+ years"],
            source=JobSource.LINKEDIN,
            status=JobStatus.EVALUATING,
            evaluation_score=0.8,
        )

        result = EvaluationResult(
            job=job,
            is_good_fit=True,
            score=0.85,
            reasoning="Strong technical match with remote option",
            matching_skills=["Python", "Distributed Systems"],
        )

        # Verify the relationship
        assert result.job.title == "Senior Software Engineer"
        assert result.job.company == "Google"
        assert result.job.is_remote is True
        assert result.score == 0.85
        assert "Python" in result.matching_skills

    def test_model_validation_cascading(self):
        """Test that validation errors cascade through nested models."""
        # Create an invalid job (score out of range)
        with pytest.raises(ValidationError):
            invalid_job = JobDescription(
                raw_text="test", evaluation_score=1.5  # Invalid score
            )

        # Create a valid job
        valid_job = JobDescription(raw_text="test")

        # Try to create EvaluationResult with invalid score
        with pytest.raises(ValidationError):
            EvaluationResult(
                job=valid_job,
                is_good_fit=True,
                score=2.0,  # Invalid score
                reasoning="test",
            )

    def test_model_serialization_nested(self):
        """Test serialization of nested models."""
        education = Education(institution="Stanford", degree="MS", field_of_study="AI")

        resume = Resume(
            personal_info={"name": "Bob", "email": "bob@test.com"},
            education=[education],
            skills=["Machine Learning"],
        )

        data = resume.model_dump()

        # Check nested education serialization
        assert len(data["education"]) == 1
        assert data["education"][0]["institution"] == "Stanford"
        assert data["education"][0]["degree"] == "MS"
        assert data["education"][0]["field_of_study"] == "AI"
