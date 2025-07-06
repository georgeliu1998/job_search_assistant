"""
Job evaluation agent using LangGraph for structured workflow.

This agent extracts key information from job postings and evaluates them
against predefined criteria using a multi-step workflow.

UPDATED: Now uses the new agent architecture with structured outputs
while maintaining backward compatibility.
"""

import json
from typing import Any, Dict, List, Optional, TypedDict

from langchain_core.messages import HumanMessage
from langgraph.graph import END, START, StateGraph

from src.agent.workflows.job_evaluation.workflow import (
    JobEvaluationWorkflow,
    generate_recommendation_from_results,
)
from src.config import config
from src.core.job_evaluation import evaluate_job_against_criteria
from src.llm.clients.anthropic import AnthropicClient
from src.llm.langfuse_handler import get_langfuse_handler
from src.llm.prompts.job_evaluation.extraction import JOB_INFO_EXTRACTION_PROMPT
from src.models.evaluation import EvaluationResult
from src.models.job import JobPostingExtractionSchema
from src.utils.logging import get_logger

logger = get_logger(__name__)


# Legacy state definition - kept for backward compatibility
class JobEvaluationState(TypedDict):
    """State for the job evaluation agent workflow."""

    # Input
    job_posting_text: str

    # Intermediate results
    extracted_info: Optional[Dict[str, Any]]
    evaluation_result: Optional[Dict[str, Any]]

    # Metadata
    messages: List[Dict[str, Any]]  # LLM conversation tracking
    langfuse_handler: Optional[Any]  # Langfuse callback handler


def evaluate_job_posting(job_posting_text: str) -> Dict[str, Any]:
    """
    Evaluate a job posting using the new agent workflow.

    This function now uses the new structured extraction system while
    maintaining exact backward compatibility with the existing API.

    Args:
        job_posting_text: The raw job posting text to evaluate

    Returns:
        Dictionary with evaluation results in the format expected by UI
    """
    logger.info("Starting job evaluation with new agent architecture")

    # Get Langfuse handler for tracing
    langfuse_handler = get_langfuse_handler()
    if langfuse_handler:
        logger.info("Langfuse tracing enabled for job evaluation")

    try:
        # Use the new workflow
        workflow = JobEvaluationWorkflow()
        final_state = workflow.run(job_posting_text, langfuse_handler)

        # Extract result
        result = final_state["evaluation_result"]
        if result is None:
            logger.error("New workflow completed but no result was generated")
            return {
                "recommendation": "DO_NOT_APPLY",
                "reasoning": "Workflow failed to generate result",
                "extracted_info": {},
                "evaluation_result": {},
            }

        # Convert extracted_info back to dictionary format for UI compatibility
        extracted_info_dict = {}
        if final_state["extracted_info"] is not None:
            schema = final_state["extracted_info"]
            extracted_info_dict = {
                "title": schema.title,
                "company": schema.company,
                "salary_min": schema.salary_min,
                "salary_max": schema.salary_max,
                "location_policy": schema.location_policy,
                "role_type": schema.role_type,
                # Additional fields for UI compatibility
                "job_title": schema.title,
                "company_name": schema.company,
            }

        # Generate recommendation and reasoning from evaluation results
        recommendation, reasoning = generate_recommendation_from_results(result)

        logger.info(
            f"Job evaluation completed successfully with recommendation: {recommendation}"
        )

        return {
            "recommendation": recommendation,
            "reasoning": reasoning,
            "extracted_info": extracted_info_dict,
            "evaluation_result": result,
        }

    except Exception as e:
        logger.error(f"New agent workflow failed: {e}")
        return {
            "recommendation": "DO_NOT_APPLY",
            "reasoning": f"Agent workflow error: {str(e)}",
            "extracted_info": {},
            "evaluation_result": {},
        }


# Legacy functions - kept for backward compatibility but deprecated
def get_extraction_client():
    """Initialize LLM client for job information extraction."""
    logger.warning("get_extraction_client() is deprecated - use new agent architecture")
    profile_name = config.agents.job_evaluation_extraction
    profile = config.get_llm_profile(profile_name)
    return AnthropicClient(profile)


# LLM client will be initialized when needed
extraction_llm = None


def extract_job_info(state: JobEvaluationState) -> Dict[str, Any]:
    """Extract key information from job posting using LLM"""
    logger.warning("extract_job_info() is deprecated - use new agent architecture")
    global extraction_llm
    if extraction_llm is None:
        extraction_llm = get_extraction_client()

    job_text = state["job_posting_text"]
    langfuse_handler = state.get("langfuse_handler")

    # Get extraction prompt
    prompt_content = JOB_INFO_EXTRACTION_PROMPT.format(job_text=job_text)
    messages = [HumanMessage(content=prompt_content)]

    try:
        # Pass Langfuse callback to LLM call
        config = {}
        if langfuse_handler:
            config = {"callbacks": [langfuse_handler]}

        response = extraction_llm.invoke(messages, config=config)
        response_text = response.content
        extracted_info = parse_extraction_response(response_text)

        logger.info(f"Successfully extracted job information: {extracted_info}")

        return {
            **state,
            "extracted_info": extracted_info,
            "messages": state.get("messages", [])
            + [{"role": "extraction", "content": response_text}],
        }

    except Exception as e:
        logger.error(f"Failed to extract job information: {e}")
        # Return state with None extracted_info to indicate failure
        return {
            **state,
            "extracted_info": None,
            "messages": state.get("messages", [])
            + [{"role": "extraction", "error": str(e)}],
        }


def evaluate_job(state: JobEvaluationState) -> Dict[str, Any]:
    """Evaluate job against criteria using core business logic"""
    logger.warning("evaluate_job() is deprecated - use new agent architecture")
    extracted_info = state["extracted_info"]

    if extracted_info is None:
        logger.error("Cannot evaluate job: extraction failed")
        return {
            **state,
            "evaluation_result": {"error": "Failed to extract job information"},
        }

    try:
        # Use core business logic for evaluation
        evaluation_result = evaluate_job_against_criteria(extracted_info)

        logger.info(f"Job evaluation completed: {evaluation_result}")

        return {
            **state,
            "evaluation_result": evaluation_result,
        }

    except Exception as e:
        logger.error(f"Failed to evaluate job: {e}")
        return {
            **state,
            "evaluation_result": {"error": f"Evaluation failed: {str(e)}"},
        }


def parse_extraction_response(response_text: str) -> Dict[str, Any]:
    """
    Parse LLM response into structured job information.

    DEPRECATED: This function is no longer needed with structured outputs.
    Kept for backward compatibility only.
    """
    logger.warning(
        "parse_extraction_response() is deprecated - structured outputs eliminate the need for manual parsing"
    )

    try:
        # First, try to find JSON in the response
        response_text = response_text.strip()

        # Look for JSON object boundaries
        start_idx = response_text.find("{")
        end_idx = response_text.rfind("}")

        if start_idx != -1 and end_idx != -1 and end_idx > start_idx:
            # Extract the JSON part
            json_str = response_text[start_idx : end_idx + 1]
            try:
                data = json.loads(json_str)
                return data
            except json.JSONDecodeError:
                pass

        # If JSON parsing failed, try simple line parsing
        lines = response_text.split("\n")
        info = {}

        for line in lines:
            if ":" in line:
                key, value = line.split(":", 1)
                key = key.strip().lower().replace(" ", "_")
                value = value.strip()

                # Handle boolean values
                if value.lower() in ["true", "yes", "y"]:
                    value = True
                elif value.lower() in ["false", "no", "n"]:
                    value = False
                # Handle numeric values
                elif value.isdigit():
                    value = int(value)

                info[key] = value

        # Return the parsed info if we got anything, otherwise return default
        if info:
            return info

    except Exception as e:
        logger.error(f"Failed to parse extraction response: {e}")
        logger.debug(f"Response text: {response_text}")

    # Return minimal job information as fallback
    return {
        "title": "Unknown",
        "company": "Unknown",
        "salary_max": None,
        "location_policy": "unclear",
        "role_type": "unclear",
    }


def create_job_evaluation_agent():
    """
    Create the job evaluation agent workflow.

    DEPRECATED: Use JobEvaluationWorkflow instead.
    Kept for backward compatibility only.
    """
    logger.warning(
        "create_job_evaluation_agent() is deprecated - use JobEvaluationWorkflow instead"
    )

    # Initialize workflow
    workflow = StateGraph(JobEvaluationState)

    # Add nodes
    workflow.add_node("extract_info", extract_job_info)
    workflow.add_node("evaluate", evaluate_job)

    # Add edges
    workflow.add_edge(START, "extract_info")
    workflow.add_edge("extract_info", "evaluate")
    workflow.add_edge("evaluate", END)

    # Compile the graph
    agent = workflow.compile()

    # Add Langfuse tracing if enabled
    langfuse_handler = get_langfuse_handler()
    if langfuse_handler:
        logger.info("Langfuse tracing enabled for job evaluation agent")
        # Note: LangGraph tracing integration would go here
        # This is a placeholder for actual tracing setup

    return agent
