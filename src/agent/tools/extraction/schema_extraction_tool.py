"""
Generalized schema-based extraction tools.

This module provides @tool decorated functions for extracting structured
data from text based on different schemas. These tools can be used by
LangGraph agents for tool calling.
"""

from typing import Any, Dict, Optional, Type

from langchain_core.messages import HumanMessage
from langchain_core.tools import tool

from src.agent.prompts.extraction.job_posting import JOB_POSTING_EXTRACTION_PROMPT
from src.config import config
from src.llm.clients.anthropic import AnthropicClient
from src.models.job import JobPostingExtractionSchema
from src.utils.logging import get_logger

logger = get_logger(__name__)

# Registry of available schemas
SCHEMA_REGISTRY = {
    "job_posting": JobPostingExtractionSchema,
    # Future schemas can be added here:
    # "resume": ResumeExtractionSchema,
    # "company": CompanyExtractionSchema,
}

# Registry of prompts for different schemas
PROMPT_REGISTRY = {
    "job_posting": JOB_POSTING_EXTRACTION_PROMPT,
    # Future prompts can be added here
}


def _get_extraction_client() -> AnthropicClient:
    """Get the LLM client for extraction operations."""
    profile_name = config.agents.job_evaluation_extraction
    profile = config.get_llm_profile(profile_name)
    return AnthropicClient(profile)


def _extract_with_schema(
    text: str,
    schema_class: Type,
    prompt_template,
    langfuse_handler: Optional[object] = None,
) -> Dict[str, Any]:
    """
    Internal function to extract data using a specific schema.

    Args:
        text: Text to extract from
        schema_class: Pydantic schema class to use
        prompt_template: Prompt template for extraction
        langfuse_handler: Optional Langfuse handler for tracing

    Returns:
        Dict containing extracted data
    """
    # Get client and create structured LLM
    client = _get_extraction_client()
    structured_llm = client._get_client().with_structured_output(schema_class)

    # Format prompt
    prompt_content = prompt_template.format(job_text=text)
    messages = [HumanMessage(content=prompt_content)]

    # Configure with Langfuse if available
    config_dict = {}
    if langfuse_handler:
        config_dict = {"callbacks": [langfuse_handler]}

    # Extract structured information
    logger.info(f"Extracting structured data using schema: {schema_class.__name__}")

    if config_dict:
        result = structured_llm.invoke(messages, config=config_dict)
    else:
        result = structured_llm.invoke(messages)

    # Convert to dict for tool return
    result_dict = result.model_dump() if hasattr(result, "model_dump") else dict(result)

    logger.info(f"Successfully extracted data: {result_dict}")
    return result_dict


def extract_structured_data_fn(text: str, schema_name: str) -> Dict[str, Any]:
    """
    Extract structured data from text based on a specified schema.

    This is the direct function implementation that can be called without
    the tool decorator interfering.

    Args:
        text: The text to extract information from
        schema_name: Name of the schema to use (e.g., 'job_posting', 'resume', etc.)

    Returns:
        Dict containing extracted structured data matching the schema

    Raises:
        ValueError: If schema_name is not supported
    """
    if not text or not text.strip():
        logger.warning("Empty text provided for extraction")
        return {}

    if schema_name not in SCHEMA_REGISTRY:
        available_schemas = list(SCHEMA_REGISTRY.keys())
        raise ValueError(
            f"Schema '{schema_name}' not supported. Available schemas: {available_schemas}"
        )

    if schema_name not in PROMPT_REGISTRY:
        raise ValueError(f"No prompt template found for schema '{schema_name}'")

    schema_class = SCHEMA_REGISTRY[schema_name]
    prompt_template = PROMPT_REGISTRY[schema_name]

    logger.info(f"Starting structured extraction with schema: {schema_name}")

    return _extract_with_schema(text, schema_class, prompt_template)


@tool
def extract_structured_data(text: str, schema_name: str) -> Dict[str, Any]:
    """
    Extract structured data from text based on a specified schema.

    This is a generalized extraction tool that can handle different types
    of structured data extraction based on the schema name provided.

    Args:
        text: The text to extract information from
        schema_name: Name of the schema to use (e.g., 'job_posting', 'resume', etc.)

    Returns:
        Dict containing extracted structured data matching the schema

    Raises:
        ValueError: If schema_name is not supported
    """
    return extract_structured_data_fn(text, schema_name)


def extract_job_posting_fn(job_text: str) -> Dict[str, Any]:
    """
    Extract job posting information from text.

    This is the direct function implementation that can be called without
    the tool decorator interfering.

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
    # Call the underlying function directly to avoid tool-calling issues
    schema_class = SCHEMA_REGISTRY["job_posting"]
    prompt_template = PROMPT_REGISTRY["job_posting"]
    return _extract_with_schema(job_text, schema_class, prompt_template)


@tool
def extract_job_posting(job_text: str) -> Dict[str, Any]:
    """
    Extract job posting information from text.

    This is a convenience tool that specifically extracts job posting
    information using the job_posting schema. It's equivalent to calling
    extract_structured_data(job_text, "job_posting").

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
    return extract_job_posting_fn(job_text)


def validate_extraction_result_fn(
    extraction_result: Dict[str, Any], schema_name: str
) -> bool:
    """
    Validate that an extraction result contains meaningful data.

    This is the direct function implementation that can be called without
    the tool decorator interfering.

    Args:
        extraction_result: The extraction result to validate
        schema_name: Name of the schema used for extraction

    Returns:
        bool: True if the result contains meaningful data
    """
    if not extraction_result:
        return False

    if schema_name == "job_posting":
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

    # For other schemas, just check if we have any non-empty values
    return any(
        value is not None and str(value).strip() for value in extraction_result.values()
    )


@tool
def validate_extraction_result(
    extraction_result: Dict[str, Any], schema_name: str
) -> bool:
    """
    Validate that an extraction result contains meaningful data.

    Args:
        extraction_result: The extraction result to validate
        schema_name: Name of the schema used for extraction

    Returns:
        bool: True if the result contains meaningful data
    """
    return validate_extraction_result_fn(extraction_result, schema_name)


def get_extraction_summary_fn(
    extraction_result: Dict[str, Any], schema_name: str
) -> str:
    """
    Get a human-readable summary of the extraction result.

    This is the direct function implementation that can be called without
    the tool decorator interfering.

    Args:
        extraction_result: The extraction result to summarize
        schema_name: Name of the schema used for extraction

    Returns:
        str: Human-readable summary of the extraction
    """
    if not extraction_result:
        return "No data extracted"

    if schema_name == "job_posting":
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

    # For other schemas, provide a generic summary
    non_empty_fields = {
        k: v for k, v in extraction_result.items() if v is not None and str(v).strip()
    }
    if not non_empty_fields:
        return "No meaningful information extracted"

    return f"Extracted {len(non_empty_fields)} fields: {', '.join(non_empty_fields.keys())}"


@tool
def get_extraction_summary(extraction_result: Dict[str, Any], schema_name: str) -> str:
    """
    Get a human-readable summary of the extraction result.

    Args:
        extraction_result: The extraction result to summarize
        schema_name: Name of the schema used for extraction

    Returns:
        str: Human-readable summary of the extraction
    """
    return get_extraction_summary_fn(extraction_result, schema_name)


def get_available_schemas() -> list[str]:
    """Get list of available extraction schemas."""
    return list(SCHEMA_REGISTRY.keys())


def register_schema(name: str, schema_class: Type, prompt_template) -> None:
    """
    Register a new schema for extraction.

    Args:
        name: Name of the schema
        schema_class: Pydantic schema class
        prompt_template: Prompt template for extraction
    """
    SCHEMA_REGISTRY[name] = schema_class
    PROMPT_REGISTRY[name] = prompt_template
    logger.info(f"Registered new extraction schema: {name}")
