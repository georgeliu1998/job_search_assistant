"""
Interview Preparation Agent

This agent generates comprehensive interview preparation guides by taking
job descriptions, resumes, and other context to provide personalized
interview coaching and preparation materials.
"""

from typing import Optional

from langchain_core.messages import HumanMessage

from src.config.llm import get_gemini_config
from src.llm.clients.gemini import GeminiClient
from src.llm.langfuse_handler import get_langfuse_handler
from src.llm.prompts.interview_preparation import INTERVIEW_PREPARATION_PROMPT
from src.models.interview import InterviewPrepInput, InterviewPrepOutput, InterviewType
from src.utils.logging import get_logger

logger = get_logger(__name__)


class InterviewPreparationAgent:
    """
    Agent for generating personalized interview preparation guides.

    Uses a single comprehensive LLM call to generate detailed interview
    preparation materials including questions, answers, strategy, and tips.
    """

    def __init__(self, gemini_api_key: Optional[str] = None):
        """
        Initialize the interview preparation agent.

        Args:
            gemini_api_key: Optional API key for Gemini. If not provided,
                          will try to get from environment or prompt user.
        """
        config = get_gemini_config()
        if gemini_api_key:
            config.api_key = gemini_api_key

        # Override max_tokens for comprehensive interview guides
        config.max_tokens = 8192  # Allow for very detailed guides

        self.client = GeminiClient(config)
        logger.info("Interview Preparation Agent initialized with extended token limit")

    def generate_interview_guide(
        self, input_data: InterviewPrepInput, enable_tracing: bool = True
    ) -> InterviewPrepOutput:
        """
        Generate comprehensive interview guide with single LLM call.

        Args:
            input_data: Interview preparation input data
            enable_tracing: Whether to enable Langfuse tracing (default: True)

        Returns:
            Complete interview preparation guide

        Raises:
            Exception: If guide generation fails
        """
        logger.info(
            f"Generating interview guide for {input_data.interview_type} interview"
        )
        logger.debug(f"Tracing enabled: {enable_tracing}")

        try:
            # Format interviewer information
            interviewer_info = self._format_interviewer_info(input_data)

            # Format additional context
            additional_context = self._format_additional_context(input_data)

            # Handle interview_type (Pydantic converts str Enums to strings)
            if isinstance(input_data.interview_type, str):
                interview_type_str = input_data.interview_type
            else:
                # Fallback for enum objects
                interview_type_str = input_data.interview_type.value

            # Create comprehensive prompt
            prompt_kwargs = {
                "job_description": input_data.job_description,
                "interview_type": interview_type_str,
                "interviewer_info": interviewer_info,
                "company_website": input_data.company_website or "Not provided",
                "resume_text": input_data.resume_text,
                "additional_context": additional_context,
            }

            prompt_content = INTERVIEW_PREPARATION_PROMPT.format(**prompt_kwargs)

            # Initialize Langfuse handler if tracing is enabled
            config = {}
            if enable_tracing:
                langfuse_handler = get_langfuse_handler()
                if langfuse_handler:
                    config = {"callbacks": [langfuse_handler]}
                    logger.info(
                        "Langfuse tracing enabled for interview guide generation"
                    )
                else:
                    logger.debug(
                        "Langfuse handler not available, continuing without tracing"
                    )

            # Single LLM call to generate complete guide
            messages = [HumanMessage(content=prompt_content)]

            # Call the client with tracing configuration
            response = self.client.invoke(messages, config=config)

            # Extract basic info for metadata
            job_title = self._extract_job_title(input_data.job_description)
            company_name = self._extract_company_name(input_data.job_description)

            # Create output
            result = InterviewPrepOutput(
                guide_content=response.content,
                estimated_prep_time=self._estimate_prep_time(input_data.interview_type),
                interview_type=input_data.interview_type,
                job_title_extracted=job_title,
                company_name_extracted=company_name,
            )

            logger.info(
                f"Successfully generated interview guide ({len(response.content)} characters)"
            )
            return result

        except Exception as e:
            logger.error(f"Failed to generate interview guide: {e}")
            raise Exception(f"Interview guide generation failed: {str(e)}")

    def _format_interviewer_info(self, input_data: InterviewPrepInput) -> str:
        """Format interviewer information for the prompt."""
        parts = []

        if input_data.interviewer_name:
            parts.append(f"Name: {input_data.interviewer_name}")

        if input_data.interviewer_title:
            parts.append(f"Title: {input_data.interviewer_title}")

        if not parts:
            return "Not provided"

        return ", ".join(parts)

    def _format_additional_context(self, input_data: InterviewPrepInput) -> str:
        """Format additional context information."""
        context_parts = []

        if input_data.interviewer_linkedin:
            context_parts.append(
                f"Interviewer LinkedIn Profile/Info:\n{input_data.interviewer_linkedin}"
            )

        if not context_parts:
            return "None provided"

        return "\n\n".join(context_parts)

    def _extract_job_title(self, job_description: str) -> Optional[str]:
        """
        Simple extraction of job title from description.

        This is a basic implementation that looks for common patterns.
        Could be enhanced with more sophisticated NLP in the future.
        """
        lines = job_description.split("\n")

        # Look for title in first few lines
        for line in lines[:5]:
            line = line.strip()
            if line and len(line) < 100:  # Likely a title
                # Clean up common prefixes
                for prefix in ["Position:", "Job Title:", "Role:"]:
                    if line.startswith(prefix):
                        return line[len(prefix) :].strip()
                # If it's a short line at the top, likely the title
                if len(line.split()) <= 6:
                    return line

        return None

    def _extract_company_name(self, job_description: str) -> Optional[str]:
        """
        Simple extraction of company name from description.

        Basic implementation that looks for common patterns.
        """
        lines = job_description.split("\n")

        # Look for company name patterns
        for line in lines[:10]:
            line = line.strip()
            if line:
                # Common patterns
                for prefix in ["Company:", "About ", "At "]:
                    if line.startswith(prefix):
                        return line[len(prefix) :].strip().split()[0]

        return None

    def _estimate_prep_time(self, interview_type) -> str:
        """Estimate preparation time based on interview type."""
        # Handle both enum and string types (Pydantic converts str Enums to strings)
        if isinstance(interview_type, str):
            interview_type_str = interview_type
        else:
            interview_type_str = interview_type.value

        if interview_type_str == "HR pre-screen":
            return "1-2 hours recommended"
        elif interview_type_str == "hiring manager interview":
            return "2-3 hours recommended"
        elif interview_type_str == "technical interview":
            return "3-4 hours recommended"
        else:
            return "2-3 hours recommended"


def create_interview_preparation_agent(
    gemini_api_key: Optional[str] = None,
) -> InterviewPreparationAgent:
    """
    Factory function to create interview preparation agent.

    Args:
        gemini_api_key: Optional Gemini API key

    Returns:
        Configured InterviewPreparationAgent instance
    """
    return InterviewPreparationAgent(gemini_api_key)
