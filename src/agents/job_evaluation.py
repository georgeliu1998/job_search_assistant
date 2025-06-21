"""
Job Evaluation Agent using LangGraph

This agent evaluates job postings against user criteria using a structured
approach:
1. Extract key information from job posting
2. Evaluate against specific criteria
3. Generate recommendation with reasoning
"""

from typing import Any, Dict, List, Optional, TypedDict

from langchain_core.messages import HumanMessage
from langgraph.graph import END, START, StateGraph

from src.config.settings import settings
from src.core.job_evaluation import evaluate_job_against_criteria
from src.llm.clients.anthropic import AnthropicClient
from src.llm.langfuse_handler import get_langfuse_handler
from src.llm.prompts.job_evaluation.extraction import JOB_INFO_EXTRACTION_PROMPT
from src.utils.logging import get_logger

logger = get_logger(__name__)


class JobEvaluationState(TypedDict):
    """State for job evaluation workflow"""

    # Input
    job_posting_text: str  # Raw job posting text

    # Processing
    extracted_info: Optional[Dict[str, Any]]  # Parsed job details
    evaluation_results: Optional[Dict[str, Any]]  # Pass/fail for each criteria

    # Output
    recommendation: Optional[str]  # "APPLY" or "DO_NOT_APPLY"
    reasoning: Optional[str]  # Detailed reasoning

    # Tracking
    messages: List[Dict[str, Any]]  # LLM conversation tracking


def get_extraction_client():
    """Initialize LLM client for job information extraction using centralized settings"""
    profile_name = settings.agents.job_evaluation_extraction
    profile = settings.get_llm_profile(profile_name)
    
    if profile.provider == "anthropic":
        # Convert to legacy format for compatibility with existing client
        from src.config.llm.anthropic import AnthropicConfig, AnthropicModel
        legacy_config = AnthropicConfig()
        legacy_config.model = AnthropicModel(profile.model)
        legacy_config.temperature = profile.temperature
        legacy_config.max_tokens = profile.max_tokens
        if profile.api_key:
            legacy_config.api_key = profile.api_key
        return AnthropicClient(legacy_config)
    else:
        raise ValueError(f"Unsupported provider for extraction: {profile.provider}")


def get_reasoning_client():
    """Initialize LLM client for job evaluation reasoning using centralized settings"""
    profile_name = settings.agents.job_evaluation_reasoning
    profile = settings.get_llm_profile(profile_name)
    
    if profile.provider == "anthropic":
        # Convert to legacy format for compatibility with existing client
        from src.config.llm.anthropic import AnthropicConfig, AnthropicModel
        legacy_config = AnthropicConfig()
        legacy_config.model = AnthropicModel(profile.model)
        legacy_config.temperature = profile.temperature
        legacy_config.max_tokens = profile.max_tokens
        if profile.api_key:
            legacy_config.api_key = profile.api_key
        return AnthropicClient(legacy_config)
    else:
        raise ValueError(f"Unsupported provider for reasoning: {profile.provider}")


# LLM clients will be initialized when needed
extraction_llm = None
reasoning_llm = None


def extract_job_info(state: JobEvaluationState) -> Dict[str, Any]:
    """Extract key information from job posting using LLM"""
    global extraction_llm
    if extraction_llm is None:
        extraction_llm = get_extraction_client()

    job_text = state["job_posting_text"]

    prompt_content = JOB_INFO_EXTRACTION_PROMPT.format(job_text=job_text)

    messages = [HumanMessage(content=prompt_content)]

    try:
        response = extraction_llm.invoke(messages)
        response_text = response.content
        extracted_info = parse_extraction_response(response_text)

        return {"extracted_info": extracted_info}
    except Exception as e:
        logger.error(f"Error extracting job info: {e}")
        return {"extracted_info": {}}


def parse_extraction_response(response_text: str) -> Dict[str, Any]:
    """Parse LLM extraction response from JSON format into structured data"""
    import json

    # Clean and extract JSON from response
    response_text = response_text.strip()

    # Handle case where response might have extra text around JSON
    # Look for JSON object boundaries
    start_idx = response_text.find("{")
    end_idx = response_text.rfind("}")

    if start_idx == -1 or end_idx == -1:
        logger.error("No JSON object found in LLM response")
        return {}

    try:
        json_str = response_text[start_idx : end_idx + 1]
        json_data = json.loads(json_str)

        # Since the prompt now returns the exact internal format,
        # we can return it directly after validation
        return json_data

    except (json.JSONDecodeError, KeyError, TypeError) as e:
        logger.error(f"Failed to parse JSON response: {e}")
        logger.debug(f"Raw response: {response_text}")
        return {}


def evaluate_criteria(state: JobEvaluationState) -> Dict[str, Any]:
    """
    LangGraph node function that evaluates job criteria.

    This is a thin wrapper around the core evaluation logic that adapts
    the LangGraph state to the core function interface.
    """
    extracted = state["extracted_info"]
    evaluation_results = evaluate_job_against_criteria(extracted)
    return {"evaluation_results": evaluation_results}


def generate_recommendation(state: JobEvaluationState) -> Dict[str, Any]:
    """Generate final recommendation based on evaluation results"""
    results = state["evaluation_results"]
    if not results:
        return {
            "recommendation": "DO_NOT_APPLY",
            "reasoning": ("Unable to evaluate job posting due to extraction errors"),
        }

    # Check if all criteria pass
    all_pass = all(
        result.get("pass", False)
        for result in results.values()
        if isinstance(result, dict)
    )

    if all_pass:
        recommendation = "APPLY"
        reasoning = "All criteria met: " + "; ".join(
            [
                result["reason"]
                for result in results.values()
                if isinstance(result, dict) and result.get("pass")
            ]
        )
    else:
        recommendation = "DO_NOT_APPLY"
        failed_reasons = [
            result["reason"]
            for result in results.values()
            if isinstance(result, dict) and not result.get("pass")
        ]
        reasoning = "Failed criteria: " + "; ".join(failed_reasons)

    return {"recommendation": recommendation, "reasoning": reasoning}


def create_job_evaluation_graph():
    """Create and compile the job evaluation graph"""
    # Create the graph
    graph = StateGraph(JobEvaluationState)

    # Add nodes
    graph.add_node("extract_job_info", extract_job_info)
    graph.add_node("evaluate_criteria", evaluate_criteria)
    graph.add_node("generate_recommendation", generate_recommendation)

    # Define the flow
    graph.add_edge(START, "extract_job_info")
    graph.add_edge("extract_job_info", "evaluate_criteria")
    graph.add_edge("evaluate_criteria", "generate_recommendation")
    graph.add_edge("generate_recommendation", END)

    # Compile the graph
    return graph.compile()


def evaluate_job_posting(
    job_posting_text: str, enable_tracing: bool = True
) -> Dict[str, Any]:
    """
    Main function to evaluate a job posting

    Args:
        job_posting_text: Raw text of the job posting
        enable_tracing: Whether to enable Langfuse tracing (default: True)

    Returns:
        Dict containing recommendation and reasoning
    """
    logger.info("Starting job posting evaluation")
    logger.debug(f"Tracing enabled: {enable_tracing}")

    # Create the graph
    graph = create_job_evaluation_graph()

    # Initialize Langfuse handler if tracing is enabled
    config = {}
    if enable_tracing:
        langfuse_handler = get_langfuse_handler()
        if langfuse_handler:
            config = {"callbacks": [langfuse_handler]}
            logger.info("Langfuse tracing enabled for this evaluation")
        else:
            logger.debug("Langfuse handler not available, continuing without tracing")

    # Run the evaluation with optional tracing
    logger.debug("Executing job evaluation graph")
    result = graph.invoke(
        {
            "job_posting_text": job_posting_text,
            "extracted_info": None,
            "evaluation_results": None,
            "recommendation": None,
            "reasoning": None,
            "messages": [],
        },
        config=config,
    )

    recommendation = result["recommendation"]
    logger.info(f"Job evaluation completed with recommendation: {recommendation}")
    return {
        "recommendation": result["recommendation"],
        "reasoning": result["reasoning"],
        "extracted_info": result["extracted_info"],
        "evaluation_results": result["evaluation_results"],
    }
