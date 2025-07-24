"""
Job posting extraction tools.

This module provides functions for extracting structured data from job posting text.
These functions can be used directly by LangGraph workflows and other components.
"""

from typing import Any, Dict, Optional, Type

from langchain_core.messages import HumanMessage

from src.agent.prompts.extraction.job_posting import JOB_POSTING_EXTRACTION_PROMPT
from src.config import config
from src.llm import get_llm_client_by_profile_name
from src.llm.observability import langfuse_manager
from src.models.job import JobPostingExtractionSchema
from src.utils.logging import get_logger

logger = get_logger(__name__)


def _get_extraction_client():
    """
    Get the LLM client for extraction operations using the factory pattern.

    Uses the factory pattern to create the appropriate client based on the
    configured provider. The factory ensures singleton behavior, so multiple
    calls with the same configuration return the same instance, improving
    resource efficiency by reusing connections and avoiding redundant client
    initialization.

    Returns:
        BaseLLMClient: Singleton instance configured for extraction

    Example:
        # This will create an AnthropicClient if the profile is configured for Anthropic,
        # or a GoogleClient if configured for Google, etc.
        client = _get_extraction_client()
    """
    profile_name = config.agents.job_evaluation_extraction
    return get_llm_client_by_profile_name(profile_name)


def _extract_with_schema(
    text: str,
    schema_class: Type,
    prompt_template,
) -> Dict[str, Any]:
    """
    Internal function to extract data using a specific schema.

    Args:
        text: Text to extract from
        schema_class: Pydantic schema class to use
        prompt_template: Prompt template for extraction

    Returns:
        Dict containing extracted data
    """
    # Get client and create structured LLM
    client = _get_extraction_client()
    structured_llm = client._get_client().with_structured_output(schema_class)

    # Format prompt
    prompt_content = prompt_template.format(job_text=text)
    messages = [HumanMessage(content=prompt_content)]

    # Get context-aware tracing configuration
    config_dict = langfuse_manager.get_config()

    # Extract structured information
    logger.info(f"Extracting structured data using schema: {schema_class.__name__}")

    result = structured_llm.invoke(messages, config=config_dict)

    # Convert to dict for tool return
    result_dict = result.model_dump() if hasattr(result, "model_dump") else dict(result)

    logger.info(f"Successfully extracted data: {result_dict}")
    return result_dict


def extract_job_posting(job_text: str) -> Dict[str, Any]:
    """
    Extract job posting information from text.

    Args:
        job_text: The job posting text to extract information from

    Returns:
        Dict containing extracted job posting information with fields:
        - title: Job title
        - company: Company name
        - salary_min: Minimum salary
        - salary_max: Maximum salary
        - location_policy: remote/hybrid/onsite/unclear
        - role_type: ic/manager/unclear
    """
    return _extract_with_schema(
        job_text, JobPostingExtractionSchema, JOB_POSTING_EXTRACTION_PROMPT
    )


def validate_extraction_result(
    extraction_result: Dict[str, Any], schema_name: str
) -> bool:
    """
    Validate that a job posting extraction result contains meaningful data.

    Args:
        extraction_result: The extraction result to validate
        schema_name: Name of the schema used for extraction (must be "job_posting")

    Returns:
        bool: True if the result contains meaningful data

    Raises:
        ValueError: If schema_name is not "job_posting"
    """
    if schema_name != "job_posting":
        raise ValueError(f"Only 'job_posting' schema is supported, got: {schema_name}")

    if not extraction_result:
        return False

    # Check if we have at least some meaningful extracted data
    has_title = extraction_result.get("title") is not None and bool(
        str(extraction_result.get("title")).strip()
    )
    has_company = extraction_result.get("company") is not None and bool(
        str(extraction_result.get("company")).strip()
    )
    has_salary = (
        extraction_result.get("salary_min") is not None
        or extraction_result.get("salary_max") is not None
    )
    has_clear_policy = extraction_result.get("location_policy") != "unclear"
    has_clear_role = extraction_result.get("role_type") != "unclear"

    # Consider it valid if we have at least title or company, plus one other field
    basic_info = has_title or has_company
    additional_info = has_salary or has_clear_policy or has_clear_role

    is_valid = basic_info and additional_info

    logger.debug(
        f"Job posting validation: {is_valid} (title={has_title}, company={has_company}, salary={has_salary}, policy={has_clear_policy}, role={has_clear_role})"
    )

    return bool(is_valid)


def get_extraction_summary(extraction_result: Dict[str, Any], schema_name: str) -> str:
    """
    Get a human-readable summary of the job posting extraction result.

    Args:
        extraction_result: The extraction result to summarize
        schema_name: Name of the schema used for extraction (must be "job_posting")

    Returns:
        str: Human-readable summary of the extraction

    Raises:
        ValueError: If schema_name is not "job_posting"
    """
    if schema_name != "job_posting":
        raise ValueError(f"Only 'job_posting' schema is supported, got: {schema_name}")

    if not extraction_result:
        return "No data extracted"

    parts = []

    if extraction_result.get("title"):
        parts.append(f"Title: {extraction_result['title']}")

    if extraction_result.get("company"):
        parts.append(f"Company: {extraction_result['company']}")

    salary_min = extraction_result.get("salary_min")
    salary_max = extraction_result.get("salary_max")
    if salary_min or salary_max:
        if salary_min and salary_max:
            parts.append(f"Salary: ${salary_min:,} - ${salary_max:,}")
        elif salary_max:
            parts.append(f"Salary: Up to ${salary_max:,}")
        elif salary_min:
            parts.append(f"Salary: From ${salary_min:,}")

    location_policy = extraction_result.get("location_policy")
    if location_policy and location_policy != "unclear":
        parts.append(f"Location: {location_policy.title()}")

    role_type = extraction_result.get("role_type")
    if role_type and role_type != "unclear":
        role_display = "Individual Contributor" if role_type == "ic" else "Manager"
        parts.append(f"Role: {role_display}")

    if not parts:
        return "No meaningful information extracted"

    return " | ".join(parts)
