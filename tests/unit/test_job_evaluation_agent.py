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

    # The new parser tries JSON first, then falls back to line parsing
    # Since this has valid JSON, it should parse the JSON
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
    """Test parsing returns default dict for invalid JSON"""
    response = "This is not JSON at all"

    result = parse_extraction_response(response)

    # The new parser returns a default dict with unknown values
    assert result["title"] == "Unknown"
    assert result["company"] == "Unknown"
    assert result["salary_max"] is None
    assert result["location_policy"] == "unclear"
    assert result["role_type"] == "unclear"


@patch("src.agents.job_evaluation.extraction_llm")
def test_job_evaluation_should_apply(mock_extraction_llm):
    """Test job that should result in successful evaluation"""
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
    mock_extraction_llm.invoke.return_value = mock_response

    job_posting = """
    Lead Machine Learning Engineer at TechCorp
    Salary: $160k-$180k
    Remote position
    """

    result = evaluate_job_posting(job_posting)

    assert "evaluation_result" in result
    assert "extracted_info" in result
    # Check that all criteria pass
    eval_result = result["evaluation_result"]
    assert eval_result["salary"]["pass"] is True
    assert eval_result["remote"]["pass"] is True
    assert eval_result["title_level"]["pass"] is True


@patch("src.agents.job_evaluation.extraction_llm")
def test_job_evaluation_should_not_apply_low_salary(mock_extraction_llm):
    """Test job that should fail due to low salary"""
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
    mock_extraction_llm.invoke.return_value = mock_response

    job_posting = """
    Lead Machine Learning Engineer at TechCorp
    Salary: $120k-$140k
    Remote position
    """

    result = evaluate_job_posting(job_posting)

    assert "evaluation_result" in result
    eval_result = result["evaluation_result"]
    assert eval_result["salary"]["pass"] is False
    assert "lower than required salary" in eval_result["salary"]["reason"]


@patch("src.agents.job_evaluation.extraction_llm")
def test_job_evaluation_should_not_apply_not_remote(mock_extraction_llm):
    """Test job that should fail due to not being remote"""
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
    mock_extraction_llm.invoke.return_value = mock_response

    job_posting = """
    Lead Machine Learning Engineer at TechCorp
    Salary: $160k-$180k
    Onsite position in San Francisco
    """

    result = evaluate_job_posting(job_posting)

    assert "evaluation_result" in result
    eval_result = result["evaluation_result"]
    assert eval_result["remote"]["pass"] is False
    assert "Position is not remote" in eval_result["remote"]["reason"]


@patch("src.agents.job_evaluation.extraction_llm")
def test_job_evaluation_should_not_apply_junior_ic_role(mock_extraction_llm):
    """Test IC job that should fail due to junior title"""
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
    mock_extraction_llm.invoke.return_value = mock_response

    job_posting = """
    Machine Learning Engineer at TechCorp
    Salary: $160k-$180k
    Remote position
    """

    result = evaluate_job_posting(job_posting)

    assert "evaluation_result" in result
    eval_result = result["evaluation_result"]
    assert eval_result["title_level"]["pass"] is False
    assert "IC role lacks required seniority" in eval_result["title_level"]["reason"]
