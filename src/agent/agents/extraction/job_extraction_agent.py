"""
Job extraction agent implementation.

This agent specializes in extracting structured information from job postings
and can be reused across different workflows.
"""

from typing import Optional

from pydantic import BaseModel, Field

from src.agent.agents.base import Agent, AgentResult
from src.agent.tools.extraction.schema_extraction_tool import (
    extract_job_posting,
    validate_extraction_result,
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
            # Extract job information using the tool
            extracted_data = extract_job_posting.invoke(
                {"job_text": input_data.job_text}
            )
            logger.info(f"Successfully extracted job information: {extracted_data}")

            # Validate if requested
            is_valid = True
            validation_details = None

            if input_data.validation_enabled:
                try:
                    is_valid = validate_extraction_result.invoke(
                        {
                            "extraction_result": extracted_data,
                            "schema_name": "job_posting",
                        }
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


# Keep the original node functions for backward compatibility during migration
def extraction_node(state) -> dict:
    """Legacy node function - redirects to new agent."""
    logger.warning(
        "Using legacy extraction_node - consider migrating to JobExtractionAgent"
    )

    agent = JobExtractionAgent()
    agent_input = JobExtractionInput(job_text=state["job_posting_text"])
    result = agent(agent_input)

    if result.success:
        return {
            "extracted_info": result.data.extracted_info,
            "messages": [
                (
                    "extract_node",
                    (
                        result.data.extracted_info.model_dump()
                        if hasattr(result.data.extracted_info, "model_dump")
                        else str(result.data.extracted_info)
                    ),
                )
            ],
        }
    else:
        return {
            "extracted_info": None,
            "messages": [("extract_node", f"Extraction failed: {result.error}")],
        }


def validation_node(state) -> dict:
    """Legacy node function - now handled within JobExtractionAgent."""
    logger.warning(
        "Using legacy validation_node - this is now handled by JobExtractionAgent"
    )

    if not state.get("extracted_info"):
        return {
            "is_valid": False,
            "messages": [("validation_node", "No extracted info to validate")],
        }

    try:
        is_valid = validate_extraction_result.invoke(
            {"extraction_result": state["extracted_info"], "schema_name": "job_posting"}
        )
        return {
            "is_valid": is_valid,
            "messages": [("validation_node", f"is_valid: {is_valid}")],
        }
    except Exception as e:
        return {
            "is_valid": False,
            "messages": [("validation_node", f"Validation failed: {str(e)}")],
        }


def evaluation_node(state) -> dict:
    """Legacy node function - should be moved to JobEvaluationAgent."""
    logger.warning(
        "Using legacy evaluation_node - consider migrating to JobEvaluationAgent"
    )

    from src.core.job_evaluation import evaluate_job_against_criteria

    if not state.get("extracted_info"):
        return {
            "evaluation_result": None,
            "messages": [("evaluation_node", "Skipped due to missing extraction")],
        }

    try:
        extracted_info = state["extracted_info"]
        if hasattr(extracted_info, "model_dump"):
            extracted_info_dict = extracted_info.model_dump()
        elif isinstance(extracted_info, dict):
            extracted_info_dict = extracted_info
        else:
            extracted_info_dict = dict(extracted_info) if extracted_info else {}

        evaluation_result = evaluate_job_against_criteria(extracted_info_dict)

        return {
            "evaluation_result": evaluation_result,
            "messages": [
                (
                    "evaluation_node",
                    f"Evaluation completed with {len(evaluation_result)} criteria",
                )
            ],
        }
    except Exception as e:
        return {
            "evaluation_result": None,
            "messages": [("evaluation_node", f"Evaluation failed: {str(e)}")],
        }
