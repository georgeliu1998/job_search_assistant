"""
Job posting extraction prompt for structured outputs.

This prompt is optimized for use with LangChain's structured outputs feature,
focusing on clear instructions without JSON formatting requirements.
"""

from langchain_core.prompts import PromptTemplate

JOB_POSTING_EXTRACTION_RAW_TEMPLATE = """
Extract structured information from this job posting:

{job_text}
"""

JOB_POSTING_EXTRACTION_PROMPT = PromptTemplate.from_template(
    JOB_POSTING_EXTRACTION_RAW_TEMPLATE
)
