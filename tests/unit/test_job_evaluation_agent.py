"""
Tests for the job evaluation agent
"""

from unittest.mock import MagicMock, patch

from src.agents.job_evaluation import evaluate_job_posting, parse_extraction_response


def test_parse_extraction_response():
    """Test parsing of LLM extraction response in JSON format"""
    response = """{
  "title": "Senior Machine Learning Engineer",
  "company": "TechCorp",
  "salary_min": 140000,
  "salary_max": 170000,
  "location_policy": "remote",
  "role_type": "ic"
}"""

    result = parse_extraction_response(response)

    assert result["title"] == "Senior Machine Learning Engineer"
    assert result["salary_min"] == 140000
    assert result["salary_max"] == 170000
    assert result["location_policy"] == "remote"
    assert result["role_type"] == "ic"
    assert result["company"] == "TechCorp"


def test_parse_extraction_response_with_extra_text():
    """Test parsing handles JSON with extra text around it"""
    response = """Here is the extracted information:
{
  "title": "Senior Machine Learning Engineer",
  "company": "TechCorp",
  "salary_min": 140000,
  "salary_max": 170000,
  "location_policy": "remote",
  "role_type": "ic"
}
This completes the extraction."""

    result = parse_extraction_response(response)

    assert result["title"] == "Senior Machine Learning Engineer"
    assert result["company"] == "TechCorp"
    assert result["salary_min"] == 140000
    assert result["salary_max"] == 170000


def test_parse_extraction_response_handles_nulls():
    """Test parsing handles null values correctly"""
    response = """{
  "title": "Senior Engineer",
  "company": null,
  "salary_min": null,
  "salary_max": 150000,
  "location_policy": "remote",
  "role_type": "ic"
}"""

    result = parse_extraction_response(response)

    assert result["title"] == "Senior Engineer"
    assert result["company"] is None
    assert result["salary_min"] is None
    assert result["salary_max"] == 150000


def test_parse_extraction_response_invalid_json():
    """Test parsing returns empty dict for invalid JSON"""
    response = "This is not JSON at all"

    result = parse_extraction_response(response)

    assert result == {}


@patch("src.agents.job_evaluation.llm")
def test_job_evaluation_should_apply(mock_llm):
    """Test job that should result in APPLY recommendation"""
    # Mock LLM response for extraction
    mock_response = MagicMock()
    mock_response.content = """{
  "title": "Lead Machine Learning Engineer",
  "company": "TechCorp",
  "salary_min": 160000,
  "salary_max": 180000,
  "location_policy": "remote",
  "role_type": "ic"
}"""
    mock_llm.invoke.return_value = mock_response

    job_posting = """
    Lead Machine Learning Engineer at TechCorp
    Salary: $160k-$180k
    Remote position
    """

    result = evaluate_job_posting(job_posting, enable_tracing=False)

    assert result["recommendation"] == "APPLY"
    assert "All criteria met" in result["reasoning"]


@patch("src.agents.job_evaluation.llm")
def test_job_evaluation_should_not_apply_low_salary(mock_llm):
    """Test job that should result in DO_NOT_APPLY due to low salary"""
    # Mock LLM response for extraction
    mock_response = MagicMock()
    mock_response.content = """{
  "title": "Lead Machine Learning Engineer",
  "company": "TechCorp",
  "salary_min": 120000,
  "salary_max": 140000,
  "location_policy": "remote",
  "role_type": "ic"
}"""
    mock_llm.invoke.return_value = mock_response

    job_posting = """
    Lead Machine Learning Engineer at TechCorp
    Salary: $120k-$140k
    Remote position
    """

    result = evaluate_job_posting(job_posting, enable_tracing=False)

    assert result["recommendation"] == "DO_NOT_APPLY"
    assert "lower than required salary" in result["reasoning"]


@patch("src.agents.job_evaluation.llm")
def test_job_evaluation_should_not_apply_not_remote(mock_llm):
    """Test job that should result in DO_NOT_APPLY due to not being remote"""
    # Mock LLM response for extraction
    mock_response = MagicMock()
    mock_response.content = """{
  "title": "Lead Machine Learning Engineer",
  "company": "TechCorp",
  "salary_min": 160000,
  "salary_max": 180000,
  "location_policy": "onsite",
  "role_type": "ic"
}"""
    mock_llm.invoke.return_value = mock_response

    job_posting = """
    Lead Machine Learning Engineer at TechCorp
    Salary: $160k-$180k
    Onsite position in San Francisco
    """

    result = evaluate_job_posting(job_posting, enable_tracing=False)

    assert result["recommendation"] == "DO_NOT_APPLY"
    assert "Position is not remote" in result["reasoning"]


@patch("src.agents.job_evaluation.llm")
def test_job_evaluation_should_not_apply_junior_ic_role(mock_llm):
    """Test IC job that should result in DO_NOT_APPLY due to junior title"""
    # Mock LLM response for extraction
    mock_response = MagicMock()
    mock_response.content = """{
  "title": "Machine Learning Engineer",
  "company": "TechCorp",
  "salary_min": 160000,
  "salary_max": 180000,
  "location_policy": "remote",
  "role_type": "ic"
}"""
    mock_llm.invoke.return_value = mock_response

    job_posting = """
    Machine Learning Engineer at TechCorp
    Salary: $160k-$180k
    Remote position
    """

    result = evaluate_job_posting(job_posting, enable_tracing=False)

    assert result["recommendation"] == "DO_NOT_APPLY"
    assert "IC role lacks required seniority" in result["reasoning"]
