"""
Job Evaluation Agent using LangGraph

This agent evaluates job postings against user criteria using a structured approach:
1. Extract key information from job posting
2. Evaluate against specific criteria
3. Generate recommendation with reasoning
"""

import os
from typing import Any, Dict, List, Optional, TypedDict

from langchain_anthropic import ChatAnthropic
from langchain_core.messages import HumanMessage
from langfuse.callback import CallbackHandler
from langgraph.graph import END, START, StateGraph

from src.core.job_evaluation.criteria import EVALUATION_CRITERIA


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
    """Initialize Anthropic client with API key"""
    api_key = os.environ.get("ANTHROPIC_API_KEY")
    if not api_key:
        import getpass

        api_key = getpass.getpass("ANTHROPIC_API_KEY: ")
        os.environ["ANTHROPIC_API_KEY"] = api_key

    return ChatAnthropic(model="claude-3-5-haiku-latest", temperature=0)


def get_langfuse_handler():
    """Initialize Langfuse callback handler with API keys"""
    # Check if tracing is explicitly disabled
    langfuse_enabled = os.environ.get("LANGFUSE_ENABLED", "false").lower() == "true"

    if not langfuse_enabled:
        print("⚠️  Langfuse tracing disabled via LANGFUSE_ENABLED environment variable")
        print("    To enable: set LANGFUSE_ENABLED=true")
        print(
            "    Note: Currently disabled due to compatibility issues with Anthropic SDK"
        )
        print("    See: https://github.com/langfuse/langfuse/issues/6882")
        return None

    # Check if Langfuse keys are available
    public_key = os.environ.get("LANGFUSE_PUBLIC_KEY")
    secret_key = os.environ.get("LANGFUSE_SECRET_KEY")
    host = os.environ.get("LANGFUSE_HOST", "https://cloud.langfuse.com")

    if not public_key or not secret_key:
        print("⚠️  Langfuse keys not found. Tracing will be disabled.")
        print("To enable tracing, set these environment variables:")
        print("- LANGFUSE_PUBLIC_KEY")
        print("- LANGFUSE_SECRET_KEY")
        print("- LANGFUSE_HOST (optional, defaults to https://cloud.langfuse.com)")
        return None

    try:
        return CallbackHandler(public_key=public_key, secret_key=secret_key, host=host)
    except Exception as e:
        print(f"⚠️  Failed to initialize Langfuse: {e}")
        return None


# LLM client will be initialized when needed
llm = None


def extract_job_info(state: JobEvaluationState) -> Dict[str, Any]:
    """Extract structured information from job posting text"""
    global llm
    if llm is None:
        llm = get_anthropic_client()

    job_text = state["job_posting_text"]

    prompt = f"""
    Extract the following information from this job posting. Be precise and conservative in your extraction.

    Job Posting:
    {job_text}

    Please extract:
    1. Job Title (exact title as written)
    2. Salary Range (if mentioned, extract min and max as numbers, if only one number mentioned, use it as max)
    3. Location/Remote Policy (remote, hybrid, onsite, or unclear)
    4. Role Type (IC - Individual Contributor, Manager, or unclear)
    5. Company Name (if mentioned)

    Format your response as:
    Job Title: [exact title]
    Salary Min: [number or "not specified"]
    Salary Max: [number or "not specified"]
    Location Policy: [remote/hybrid/onsite/unclear]
    Role Type: [IC/Manager/unclear]
    Company: [name or "not specified"]
    """

    messages = [HumanMessage(content=prompt)]
    response = llm.invoke(messages)

    # Parse the LLM response into structured data
    extracted_info = parse_extraction_response(response.content)

    # Update tracking
    new_messages = state.get("messages", []) + [
        {"role": "user", "content": prompt},
        {"role": "assistant", "content": response.content},
    ]

    return {"extracted_info": extracted_info, "messages": new_messages}


def parse_extraction_response(response_text: str) -> Dict[str, Any]:
    """Parse LLM extraction response into structured data"""
    lines = response_text.strip().split("\n")
    extracted = {}

    for line in lines:
        if ":" in line:
            key, value = line.split(":", 1)
            key = key.strip().lower().replace(" ", "_")
            value = value.strip()

            if key == "job_title":
                extracted["title"] = value
            elif key == "salary_min":
                extracted["salary_min"] = parse_salary(value)
            elif key == "salary_max":
                extracted["salary_max"] = parse_salary(value)
            elif key == "location_policy":
                extracted["location_policy"] = value.lower()
            elif key == "role_type":
                extracted["role_type"] = value.lower()
            elif key == "company":
                extracted["company"] = value

    return extracted


def parse_salary(salary_str: str) -> Optional[int]:
    """Extract numeric salary from string"""
    if "not specified" in salary_str.lower():
        return None

    # Remove common salary formatting
    import re

    numbers = re.findall(r"\d+", salary_str.replace(",", ""))
    if numbers:
        # If it's a number like "150" assume it's in thousands
        num = int(numbers[0])
        if num < 1000:
            return num * 1000
        return num
    return None


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
        results["salary"] = {
            "pass": False,
            "reason": f"Highest salary (${salary_max:,}) is lower than required salary (${EVALUATION_CRITERIA['min_salary']:,})",
        }
    else:
        results["salary"] = {
            "pass": True,
            "reason": f"Salary (${salary_max:,}) meets minimum requirement (${EVALUATION_CRITERIA['min_salary']:,})",
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
        has_required_level = any(
            level in title for level in EVALUATION_CRITERIA["ic_title_requirements"]
        )
        if has_required_level:
            results["title_level"] = {
                "pass": True,
                "reason": "IC role has appropriate seniority level",
            }
        else:
            results["title_level"] = {
                "pass": False,
                "reason": f"IC role lacks required seniority (needs: {', '.join(EVALUATION_CRITERIA['ic_title_requirements'])})",
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
            "reasoning": "Unable to evaluate job posting due to extraction errors",
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
    # Create the graph
    graph = create_job_evaluation_graph()

    # Initialize Langfuse handler if tracing is enabled
    config = {}
    if enable_tracing:
        langfuse_handler = get_langfuse_handler()
        if langfuse_handler:
            config = {"callbacks": [langfuse_handler]}
            print("🔌 Langfuse tracing enabled")

    # Run the evaluation with optional tracing
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

    return {
        "recommendation": result["recommendation"],
        "reasoning": result["reasoning"],
        "extracted_info": result["extracted_info"],
        "evaluation_results": result["evaluation_results"],
    }


# Example usage
if __name__ == "__main__":
    # Test with a sample job posting
    sample_job = """
    Senior Machine Learning Engineer - Remote

    TechCorp is looking for a Senior Machine Learning Engineer to join our AI team.

    Responsibilities:
    - Design and implement ML models
    - Work with large datasets
    - Collaborate with cross-functional teams

    Requirements:
    - 5+ years of ML experience
    - Python, SQL, TensorFlow
    - Strong analytical skills

    Compensation: $140,000 - $170,000
    Location: Fully Remote
    """

    print("🚀 Job Evaluation Agent with Langfuse Observability")
    print("📋 Set LANGFUSE_PUBLIC_KEY and LANGFUSE_SECRET_KEY for tracing")

    result = evaluate_job_posting(sample_job, enable_tracing=True)
    print(f"\n📊 Results:")
    print(f"Recommendation: {result['recommendation']}")
    print(f"Reasoning: {result['reasoning']}")

    if result["extracted_info"]:
        print(f"\n🔍 Extracted Information:")
        for key, value in result["extracted_info"].items():
            print(f"  {key}: {value}")
