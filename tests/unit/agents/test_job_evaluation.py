"""
Tests for the job evaluation agent
"""

from unittest.mock import MagicMock, patch

from src.agent.workflows.job_evaluation import evaluate_job_posting


@patch("src.agent.agents.extraction.job_extraction_agent.extract_job_posting_fn")
def test_job_evaluation_should_apply(mock_extract_job_posting):
    """Test job that should result in successful evaluation"""
    # Mock the extraction tool response
    mock_extract_job_posting.return_value = {
        "title": "Lead Machine Learning Engineer",
        "company": "TechCorp",
        "salary_min": 100000,
        "salary_max": 180000,
        "location_policy": "remote",
        "role_type": "ic",
    }

    job_posting = """
    Lead Machine Learning Engineer at TechCorp
    Salary: $160k-$180k
    Remote position
    """

    result = evaluate_job_posting(job_posting)

    assert "evaluation_result" in result
    assert "extracted_info" in result
    assert result["recommendation"] == "APPLY"

    # Check that all criteria pass
    eval_result = result["evaluation_result"]
    assert eval_result["salary"]["pass"] is True
    assert eval_result["remote"]["pass"] is True
    assert eval_result["title_level"]["pass"] is True


@patch("src.agent.agents.extraction.job_extraction_agent.extract_job_posting_fn")
def test_job_evaluation_should_not_apply_low_salary(mock_extract_job_posting):
    """Test job that should fail due to low salary"""
    # Mock the extraction tool response
    mock_extract_job_posting.return_value = {
        "title": "Lead Machine Learning Engineer",
        "company": "TechCorp",
        "salary_min": 70000,
        "salary_max": 90000,
        "location_policy": "remote",
        "role_type": "ic",
    }

    job_posting = """
    Lead Machine Learning Engineer at TechCorp
    Salary: $70k-$90k
    Remote position
    """

    result = evaluate_job_posting(job_posting)

    assert "evaluation_result" in result
    assert result["recommendation"] == "DO_NOT_APPLY"

    # Check that salary criteria fails
    eval_result = result["evaluation_result"]
    assert eval_result["salary"]["pass"] is False


@patch("src.agent.agents.extraction.job_extraction_agent.extract_job_posting_fn")
def test_job_evaluation_should_not_apply_not_remote(mock_extract_job_posting):
    """Test job that should fail due to not being remote"""
    # Mock the extraction tool response
    mock_extract_job_posting.return_value = {
        "title": "Lead Machine Learning Engineer",
        "company": "TechCorp",
        "salary_min": 100000,
        "salary_max": 180000,
        "location_policy": "onsite",
        "role_type": "ic",
    }

    job_posting = """
    Lead Machine Learning Engineer at TechCorp
    Salary: $160k-$180k
    Onsite position in San Francisco
    """

    result = evaluate_job_posting(job_posting)

    assert "evaluation_result" in result
    assert result["recommendation"] == "DO_NOT_APPLY"

    # Check that remote criteria fails
    eval_result = result["evaluation_result"]
    assert eval_result["remote"]["pass"] is False


@patch("src.agent.agents.extraction.job_extraction_agent.extract_job_posting_fn")
def test_job_evaluation_should_not_apply_junior_ic_role(mock_extract_job_posting):
    """Test IC job that should fail due to junior title"""
    # Mock the extraction tool response
    mock_extract_job_posting.return_value = {
        "title": "Machine Learning Engineer",
        "company": "TechCorp",
        "salary_min": 100000,
        "salary_max": 180000,
        "location_policy": "remote",
        "role_type": "ic",
    }

    job_posting = """
    Machine Learning Engineer at TechCorp
    Salary: $160k-$180k
    Remote position
    """

    result = evaluate_job_posting(job_posting)

    assert "evaluation_result" in result
    assert result["recommendation"] == "DO_NOT_APPLY"

    # Check that title level criteria fails
    eval_result = result["evaluation_result"]
    assert eval_result["title_level"]["pass"] is False


@patch("src.agent.agents.extraction.job_extraction_agent.extract_job_posting_fn")
def test_job_evaluation_handles_extraction_failure(mock_extract_job_posting):
    """Test job evaluation handles extraction failures gracefully"""
    # Mock the extraction tool to raise an exception
    mock_extract_job_posting.side_effect = Exception("Extraction failed")

    job_posting = """
    Some job posting text
    """

    result = evaluate_job_posting(job_posting)

    assert "evaluation_result" in result
    # When extraction fails, the system returns ERROR
    assert result["recommendation"] == "ERROR"
    assert result["extracted_info"] is None  # Changed from {} to None
    assert result["evaluation_result"] is None  # Changed from {} to None


def test_job_evaluation_handles_empty_text():
    """Test job evaluation handles empty job posting text"""
    result = evaluate_job_posting("")

    assert result["recommendation"] == "ERROR"
    assert "empty" in result["reasoning"].lower()
    assert result["extracted_info"] == {}
    assert result["evaluation_result"] == {}


def test_job_evaluation_handles_none_text():
    """Test job evaluation handles None job posting text"""
    result = evaluate_job_posting(None)

    assert result["recommendation"] == "ERROR"
    assert "empty" in result["reasoning"].lower()
    assert result["extracted_info"] == {}
    assert result["evaluation_result"] == {}
