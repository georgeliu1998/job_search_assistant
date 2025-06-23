"""
Job evaluation agent using LangGraph for structured workflow.

This agent extracts key information from job postings and evaluates them
against predefined criteria using a multi-step workflow.
"""

import json
from typing import Any, Dict, List, Optional, TypedDict

from langchain_core.messages import HumanMessage
from langgraph.graph import END, START, StateGraph

from src.config import config
from src.core.job_evaluation import evaluate_job_against_criteria
from src.llm.clients.anthropic import AnthropicClient
from src.llm.langfuse_handler import get_langfuse_handler
from src.llm.prompts.job_evaluation.extraction import JOB_INFO_EXTRACTION_PROMPT
from src.models.evaluation import EvaluationResult
from src.utils.logging import get_logger

logger = get_logger(__name__)


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


def get_extraction_client():
    """Initialize LLM client for job information extraction."""
    profile_name = config.agents.job_evaluation_extraction
    profile = config.get_llm_profile(profile_name)
    return AnthropicClient(profile)


def get_reasoning_client():
    """Initialize LLM client for job evaluation reasoning."""
    profile_name = config.agents.job_evaluation_reasoning
    profile = config.get_llm_profile(profile_name)
    return AnthropicClient(profile)


# LLM clients will be initialized when needed
extraction_llm = None
reasoning_llm = None


def extract_job_info(state: JobEvaluationState) -> Dict[str, Any]:
    """Extract key information from job posting using LLM"""
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
    """Parse LLM response into structured job information"""
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
    """Create the job evaluation agent workflow"""
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
    app = workflow.compile()

    # Add Langfuse tracing if enabled
    langfuse_handler = get_langfuse_handler()
    if langfuse_handler:
        logger.info("Langfuse tracing enabled for job evaluation agent")
        # Note: LangGraph tracing integration would go here
        # This is a placeholder for actual tracing setup

    return app


def generate_recommendation_from_results(
    evaluation_results: Dict[str, Any],
) -> tuple[str, str]:
    """Generate final recommendation and reasoning from evaluation results"""
    if not evaluation_results or "error" in evaluation_results:
        return "DO_NOT_APPLY", "Unable to evaluate job posting due to extraction errors"

    # Check if all criteria pass
    all_pass = all(
        result.get("pass", False)
        for result in evaluation_results.values()
        if isinstance(result, dict)
    )

    if all_pass:
        recommendation = "APPLY"
        reasoning = "All criteria met: " + "; ".join(
            [
                result["reason"]
                for result in evaluation_results.values()
                if isinstance(result, dict) and result.get("pass")
            ]
        )
    else:
        recommendation = "DO_NOT_APPLY"
        failed_reasons = [
            result["reason"]
            for result in evaluation_results.values()
            if isinstance(result, dict) and not result.get("pass")
        ]
        reasoning = "Failed criteria: " + "; ".join(failed_reasons)

    return recommendation, reasoning


def evaluate_job_posting(job_posting_text: str) -> Dict[str, Any]:
    """
    Evaluate a job posting using the agent workflow.

    Args:
        job_posting_text: The raw job posting text to evaluate

    Returns:
        Dictionary with evaluation results in the format expected by UI
    """
    logger.info("Starting job evaluation")

    # Create agent
    agent = create_job_evaluation_agent()

    # Get Langfuse handler for tracing
    langfuse_handler = get_langfuse_handler()
    if langfuse_handler:
        logger.info("Langfuse tracing enabled for job evaluation")

    # Prepare initial state
    initial_state = JobEvaluationState(
        job_posting_text=job_posting_text,
        extracted_info=None,
        evaluation_result=None,
        messages=[],
        langfuse_handler=langfuse_handler,
    )

    try:
        # Run the agent workflow
        final_state = agent.invoke(initial_state)

        # Extract result
        result = final_state["evaluation_result"]
        if result is None:
            logger.error("Agent workflow completed but no result was generated")
            return {
                "recommendation": "DO_NOT_APPLY",
                "reasoning": "Agent workflow failed to generate result",
                "extracted_info": final_state.get("extracted_info", {}),
                "evaluation_result": {},
            }

        # Generate recommendation and reasoning from evaluation results
        recommendation, reasoning = generate_recommendation_from_results(result)

        logger.info(
            f"Job evaluation completed successfully with recommendation: {recommendation}"
        )
        return {
            "recommendation": recommendation,
            "reasoning": reasoning,
            "extracted_info": final_state["extracted_info"],
            "evaluation_result": result,
        }

    except Exception as e:
        logger.error(f"Agent workflow failed: {e}")
        return {
            "recommendation": "DO_NOT_APPLY",
            "reasoning": f"Agent workflow error: {str(e)}",
            "extracted_info": {},
            "evaluation_result": {},
        }
