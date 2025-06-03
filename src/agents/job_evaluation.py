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

from src.config.llm import get_anthropic_config
from src.core.job_evaluation.criteria import EVALUATION_CRITERIA
from src.llm.anthropic import AnthropicClient
from src.llm.langfuse_handler import get_langfuse_handler
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


def get_anthropic_client():
    """Initialize Anthropic client using the new LLM client architecture"""
    config = get_anthropic_config()
    return AnthropicClient(config)


# LLM client will be initialized when needed
llm = None


def extract_job_info(state: JobEvaluationState) -> Dict[str, Any]:
    """Extract key information from job posting using LLM"""
    global llm
    if llm is None:
        llm = get_anthropic_client()

    job_text = state["job_posting_text"]

    prompt = f"""
You are tasked with extracting specific job information from a given job posting and presenting it in a structured JSON format. Here's the job posting you need to analyze:

<job_posting>
{job_text}
</job_posting>

Please extract the following information from the job posting:

1. Job Title: Extract the exact job title as written in the posting.

2. Company Name: Extract the company name if mentioned in the posting.

3. Salary Range: If mentioned, extract the minimum and maximum salary as numbers. If only one number is mentioned, use it as the maximum. If no salary information is provided, use null values.

4. Location/Remote Policy: Determine if the job is remote, hybrid, onsite, or if the policy is unclear based on the information provided.

5. Role Type: Identify if the role is for an Individual Contributor (IC), Manager, or if it's unclear based on the job description.

After analyzing the job posting, present the extracted information in the following JSON format:

{{
  "title": "Exact title as written",
  "company": "Company name or null if not provided",
  "salary_min": minimum salary (number or null if not provided),
  "salary_max": maximum salary (number or null if not provided),
  "location_policy": "remote/hybrid/onsite/unclear",
  "role_type": "ic/manager/unclear"
}}

Important guidelines:
- Base your extraction solely on the information provided in the job posting.
- If any information is not explicitly mentioned or is ambiguous, use "unclear" or null values as appropriate.
- For salary values, use null if not provided. If only one number is mentioned, use it as the maximum and set the minimum to null.
- For location_policy and role_type, use lowercase values: "remote", "hybrid", "onsite", "unclear", "ic", "manager"
- Be precise in your extraction, avoiding any assumptions or inferences not directly supported by the text.

Please provide your final output in the specified JSON format without any explanations.
    """

    messages = [HumanMessage(content=prompt)]

    try:
        response = llm.invoke(messages)
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
    """Evaluate extracted job info against criteria"""
    extracted = state["extracted_info"]
    if not extracted:
        return {"evaluation_results": {"error": "No extracted information available"}}

    results = {}

    # 1. Salary check
    salary_max = extracted.get("salary_max")
    if salary_max is None:
        results["salary"] = {"pass": False, "reason": "Salary not specified"}
    elif salary_max < EVALUATION_CRITERIA["min_salary"]:
        min_salary = EVALUATION_CRITERIA["min_salary"]
        results["salary"] = {
            "pass": False,
            "reason": (
                f"Highest salary (${salary_max:,}) is lower than required "
                f"salary (${min_salary:,})"
            ),
        }
    else:
        min_salary = EVALUATION_CRITERIA["min_salary"]
        results["salary"] = {
            "pass": True,
            "reason": (
                f"Salary (${salary_max:,}) meets minimum requirement "
                f"(${min_salary:,})"
            ),
        }

    # 2. Remote policy check
    location_policy = extracted.get("location_policy", "").lower()
    if "remote" in location_policy:
        results["remote"] = {"pass": True, "reason": "Position is remote"}
    else:
        results["remote"] = {
            "pass": False,
            "reason": f"Position is not remote (location policy: {location_policy})",
        }

    # 3. IC title level check (only for IC roles)
    role_type = extracted.get("role_type", "").lower()
    title = extracted.get("title", "").lower()

    if "ic" in role_type or "individual contributor" in role_type:
        # Check if title contains required seniority level
        ic_requirements = EVALUATION_CRITERIA["ic_title_requirements"]
        has_required_level = any(level in title for level in ic_requirements)
        if has_required_level:
            results["title_level"] = {
                "pass": True,
                "reason": "IC role has appropriate seniority level",
            }
        else:
            required_levels = ", ".join(ic_requirements)
            results["title_level"] = {
                "pass": False,
                "reason": (
                    f"IC role lacks required seniority (needs: {required_levels})"
                ),
            }
    else:
        # Not an IC role, so title level requirement doesn't apply
        results["title_level"] = {
            "pass": True,
            "reason": "Title level requirement not applicable (not IC role)",
        }

    return {"evaluation_results": results}


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
