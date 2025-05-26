"""
Tests for the job evaluation agent
"""

from unittest.mock import MagicMock, patch

from src.agents.job_evaluation import (
    evaluate_job_posting,
    parse_extraction_response,
    parse_salary,
)


def test_parse_salary():
    """Test salary parsing function"""
    assert parse_salary("150") == 150000  # Assumes thousands
    assert parse_salary("150000") == 150000
    assert parse_salary("$150,000") == 150000
    assert parse_salary("not specified") is None
    assert parse_salary("") is None


def test_parse_extraction_response():
    """Test parsing of LLM extraction response"""
    response = """
    Job Title: Senior Machine Learning Engineer
    Salary Min: 140000
    Salary Max: 170000
    Location Policy: remote
    Role Type: IC
    Company: TechCorp
    """

    result = parse_extraction_response(response)

    assert result["title"] == "Senior Machine Learning Engineer"
    assert result["salary_min"] == 140000
    assert result["salary_max"] == 170000
    assert result["location_policy"] == "remote"
    assert result["role_type"] == "ic"
    assert result["company"] == "TechCorp"


@patch("src.agents.job_evaluation.llm")
def test_job_evaluation_should_apply(mock_llm):
    """Test job that should result in APPLY recommendation"""
    # Mock LLM response for extraction
    mock_response = MagicMock()
    mock_response.content = """
    Job Title: Lead Machine Learning Engineer
    Salary Min: 160000
    Salary Max: 180000
    Location Policy: remote
    Role Type: IC
    Company: TechCorp
    """
    mock_llm.invoke.return_value = mock_response

    job_posting = """
    Lead Machine Learning Engineer - Remote
    TechCorp is hiring a Lead ML Engineer.
    Salary: $160,000 - $180,000
    Location: Fully Remote
    """

    result = evaluate_job_posting(job_posting, enable_tracing=False)

    assert result["recommendation"] == "APPLY"
    assert "All criteria met" in result["reasoning"]


@patch("src.agents.job_evaluation.llm")
def test_job_evaluation_should_not_apply_low_salary(mock_llm):
    """Test job that should result in DO_NOT_APPLY due to low salary"""
    # Mock LLM response for extraction
    mock_response = MagicMock()
    mock_response.content = """
    Job Title: Lead Machine Learning Engineer
    Salary Min: 120000
    Salary Max: 140000
    Location Policy: remote
    Role Type: IC
    Company: TechCorp
    """
    mock_llm.invoke.return_value = mock_response

    job_posting = """
    Lead Machine Learning Engineer - Remote
    TechCorp is hiring a Lead ML Engineer.
    Salary: $120,000 - $140,000
    Location: Fully Remote
    """

    result = evaluate_job_posting(job_posting, enable_tracing=False)

    assert result["recommendation"] == "DO_NOT_APPLY"
    assert "lower than required salary" in result["reasoning"]


@patch("src.agents.job_evaluation.llm")
def test_job_evaluation_should_not_apply_not_remote(mock_llm):
    """Test job that should result in DO_NOT_APPLY due to not being remote"""
    # Mock LLM response for extraction
    mock_response = MagicMock()
    mock_response.content = """
    Job Title: Lead Machine Learning Engineer
    Salary Min: 160000
    Salary Max: 180000
    Location Policy: onsite
    Role Type: IC
    Company: TechCorp
    """
    mock_llm.invoke.return_value = mock_response

    job_posting = """
    Lead Machine Learning Engineer - San Francisco
    TechCorp is hiring a Lead ML Engineer.
    Salary: $160,000 - $180,000
    Location: San Francisco Office
    """

    result = evaluate_job_posting(job_posting, enable_tracing=False)

    assert result["recommendation"] == "DO_NOT_APPLY"
    assert "not remote" in result["reasoning"]


@patch("src.agents.job_evaluation.llm")
def test_job_evaluation_should_not_apply_junior_ic_role(mock_llm):
    """Test IC job that should result in DO_NOT_APPLY due to junior title"""
    # Mock LLM response for extraction
    mock_response = MagicMock()
    mock_response.content = """
    Job Title: Machine Learning Engineer
    Salary Min: 160000
    Salary Max: 180000
    Location Policy: remote
    Role Type: IC
    Company: TechCorp
    """
    mock_llm.invoke.return_value = mock_response

    job_posting = """
    Machine Learning Engineer - Remote
    TechCorp is hiring an ML Engineer.
    Salary: $160,000 - $180,000
    Location: Fully Remote
    """

    result = evaluate_job_posting(job_posting, enable_tracing=False)

    assert result["recommendation"] == "DO_NOT_APPLY"
    assert "lacks required seniority" in result["reasoning"]
