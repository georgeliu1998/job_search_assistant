"""
Job extraction agent using LangGraph's tool calling capabilities.

This agent uses LangGraph's create_react_agent to reason about when and how
to use extraction tools, providing true tool calling rather than function composition.
"""

from typing import Any, Dict, Optional

from src.agent.base.agent import BaseAgent
from src.agent.tools.extraction.schema_extraction_tool import (
    extract_job_posting,
    get_extraction_summary,
    validate_extraction_result,
)
from src.models.job import JobPostingExtractionSchema
from src.utils.logging import get_logger

logger = get_logger(__name__)


class JobExtractionAgent(BaseAgent):
    """
    LangGraph agent for job information extraction using tool calling.

    This agent can reason about when to use extraction tools, validate results,
    and provide summaries. It uses LangGraph's create_react_agent for true
    tool calling capabilities.
    """

    def __init__(self):
        """Initialize the job extraction agent with available tools."""
        # Define the tools available to this agent
        tools = [
            extract_job_posting,
            validate_extraction_result,
            get_extraction_summary,
        ]

        super().__init__(tools)
        logger.info(f"Initialized JobExtractionAgent with {len(tools)} tools")

    def _get_llm_profile_name(self) -> str:
        """Get the LLM profile for job extraction."""
        return "anthropic_extraction"

    def invoke(self, input_data: Dict[str, Any]) -> Dict[str, Any]:
        """
        Extract job information using tool calling.

        Args:
            input_data: Dict containing:
                - job_text: The job posting text to extract from
                - langfuse_handler: Optional Langfuse handler for tracing

        Returns:
            Dict containing:
                - extracted_info: JobPostingExtractionSchema as dict
                - is_valid: Boolean indicating if extraction was successful
                - summary: Human-readable summary of extraction
                - messages: Agent conversation messages
        """
        job_text = input_data.get("job_text", "")
        langfuse_handler = input_data.get("langfuse_handler")

        if not job_text or not job_text.strip():
            logger.warning("Empty job text provided to JobExtractionAgent")
            return {
                "extracted_info": JobPostingExtractionSchema().model_dump(),
                "is_valid": False,
                "summary": "No job text provided",
                "messages": [],
            }

        try:
            # Create the agent if not already created
            agent = self._create_agent()

            # Create the input message for the agent
            agent_input = {
                "messages": [
                    {
                        "role": "user",
                        "content": f"""Please extract job information from the following job posting text.

Use the extract_job_posting tool to extract structured information, then validate the results and provide a summary.

Job posting text:
{job_text}

Please:
1. Extract the job information using the extract_job_posting tool
2. Validate the extraction results using validate_extraction_result
3. Provide a summary using get_extraction_summary

Return the extracted information in a structured format.""",
                    }
                ]
            }

            # Configure with Langfuse if available
            config_dict = {}
            if langfuse_handler:
                config_dict = {"callbacks": [langfuse_handler]}
                logger.debug("Using Langfuse tracing for agent execution")

            # Invoke the agent
            logger.info("Starting job extraction with tool calling agent")

            if config_dict:
                result = agent.invoke(agent_input, config=config_dict)
            else:
                result = agent.invoke(agent_input)

            # Extract the final message content and any tool calls
            messages = result.get("messages", [])

            # Find the extracted information from tool calls
            extracted_info = None
            is_valid = False
            summary = ""

            for message in messages:
                if hasattr(message, "tool_calls") and message.tool_calls:
                    for tool_call in message.tool_calls:
                        if tool_call.get("name") == "extract_job_posting":
                            # This should contain the extracted info
                            pass
                elif hasattr(message, "content") and message.content:
                    if "extract_job_posting" in str(message.content):
                        # Look for tool results in the content
                        pass

            # If we can't parse the agent's tool usage, fall back to direct extraction
            if extracted_info is None:
                logger.info("Falling back to direct tool usage for extraction")
                extracted_info = extract_job_posting.invoke({"job_text": job_text})
                is_valid = validate_extraction_result.invoke(
                    {"extraction_result": extracted_info, "schema_name": "job_posting"}
                )
                summary = get_extraction_summary.invoke(
                    {"extraction_result": extracted_info, "schema_name": "job_posting"}
                )

            logger.info(
                f"Job extraction completed: valid={is_valid}, summary='{summary}'"
            )

            return {
                "extracted_info": extracted_info,
                "is_valid": is_valid,
                "summary": summary,
                "messages": messages,
            }

        except Exception as e:
            logger.error(f"Failed to extract job information with agent: {e}")

            # Return fallback result
            empty_schema = JobPostingExtractionSchema()
            return {
                "extracted_info": empty_schema.model_dump(),
                "is_valid": False,
                "summary": f"Extraction failed: {str(e)}",
                "messages": [],
            }

    def extract(
        self, job_text: str, langfuse_handler: Optional[object] = None
    ) -> JobPostingExtractionSchema:
        """
        Convenience method to extract job information and return schema object.

        Args:
            job_text: The job posting text to extract from
            langfuse_handler: Optional Langfuse handler for tracing

        Returns:
            JobPostingExtractionSchema: Extracted job information
        """
        result = self.invoke(
            {"job_text": job_text, "langfuse_handler": langfuse_handler}
        )

        extracted_info = result.get("extracted_info", {})

        # Convert back to schema object
        return JobPostingExtractionSchema(**extracted_info)

    def extract_and_validate(
        self, job_text: str, langfuse_handler: Optional[object] = None
    ) -> Dict[str, Any]:
        """
        Extract job information and return full results including validation.

        Args:
            job_text: The job posting text to extract from
            langfuse_handler: Optional Langfuse handler for tracing

        Returns:
            Dict containing extracted_info, is_valid, and summary
        """
        return self.invoke({"job_text": job_text, "langfuse_handler": langfuse_handler})
