"""
Job extraction agent implementation.

This agent specializes in extracting structured information from job postings
and can be reused across different workflows.
"""

from typing import Optional

from pydantic import BaseModel, Field

from src.agent.common.base import Agent, AgentResult
from src.agent.tools.extraction.schema_extraction_tool import (
    extract_job_posting_fn,
    validate_extraction_result_fn,
)
from src.models.job import JobPostingExtractionSchema
from src.utils.logging import get_logger

logger = get_logger(__name__)


class JobExtractionInput(BaseModel):
    """Input for job extraction agent."""

    job_text: str = Field(..., description="Raw job posting text to extract from")
    validation_enabled: bool = Field(
        default=True, description="Whether to validate extraction results"
    )


class JobExtractionOutput(BaseModel):
    """Output from job extraction agent."""

    extracted_info: JobPostingExtractionSchema = Field(
        ..., description="Structured job information"
    )
    is_valid: bool = Field(
        default=True, description="Whether extraction passed validation"
    )
    validation_details: Optional[str] = Field(
        None, description="Details about validation results"
    )


class JobExtractionAgent(Agent[JobExtractionInput, JobExtractionOutput]):
    """Specialized agent for extracting and validating job posting information."""

    def __init__(self):
        super().__init__(
            name="job_extraction_agent",
            description="Extracts structured information from job postings using LLM tools",
        )

    async def execute(
        self, input_data: JobExtractionInput
    ) -> AgentResult[JobExtractionOutput]:
        """
        Execute job extraction with optional validation.

        Args:
            input_data: Job extraction input containing text and options

        Returns:
            AgentResult with extracted job information or error details
        """
        logger.info(f"Agent {self.name}: Starting job extraction")

        try:
            # Extract job information using the direct function
            extracted_data = extract_job_posting_fn(input_data.job_text)
            logger.info(f"Successfully extracted job information: {extracted_data}")

            # Validate if requested
            is_valid = True
            validation_details = None

            if input_data.validation_enabled:
                try:
                    is_valid = validate_extraction_result_fn(
                        extracted_data, "job_posting"
                    )
                    validation_details = (
                        f"Validation {'passed' if is_valid else 'failed'}"
                    )
                    logger.info(f"Validation result: {is_valid}")
                except Exception as validation_error:
                    logger.warning(f"Validation failed: {validation_error}")
                    is_valid = False
                    validation_details = f"Validation error: {str(validation_error)}"

            # Create output
            output = JobExtractionOutput(
                extracted_info=extracted_data,
                is_valid=is_valid,
                validation_details=validation_details,
            )

            return AgentResult[JobExtractionOutput](
                success=True,
                data=output,
                metadata={
                    "agent": self.name,
                    "validation_enabled": input_data.validation_enabled,
                    "validation_passed": is_valid,
                },
            )

        except Exception as e:
            logger.error(f"Agent {self.name}: Failed to extract job information: {e}")
            return AgentResult[JobExtractionOutput](
                success=False,
                error=str(e),
                metadata={
                    "agent": self.name,
                    "error_type": type(e).__name__,
                },
            )
