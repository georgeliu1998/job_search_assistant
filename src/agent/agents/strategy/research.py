"""Research Agent for multi-agent interview preparation workflow.

The Research Agent conducts intelligent research using AI-generated search queries
instead of hardcoded topics, making research more targeted and relevant.
"""

import logging
from datetime import datetime
from typing import Any, Dict, List

from langchain_core.messages import HumanMessage, SystemMessage

from src.agent.prompts.interview.research import (
    RESEARCH_SYSTEM_PROMPT,
    RESEARCH_USER_PROMPT_TEMPLATE,
)
from src.agent.tools.research import research_tool
from src.agent.workflows.interview_prep.multi_agent_states import (
    AgentStatus,
    MultiAgentInterviewPrepState,
    WorkflowPhase,
)
from src.config import config
from src.llm.common.factory import get_llm_client_by_profile_name
from src.llm.observability import langfuse_manager
from src.models.interview import ResearchCitation

logger = logging.getLogger(__name__)


def research_agent(state: MultiAgentInterviewPrepState) -> Dict[str, Any]:
    """
    Intelligent Research Agent that generates dynamic search queries.

    Instead of using hardcoded research topics, this agent analyzes the context
    and generates targeted search queries that will yield more relevant results.

    Args:
        state: Current multi-agent workflow state

    Returns:
        Dict containing research results and analysis
    """
    logger.info(
        "Research Agent: Starting intelligent research with dynamic query generation"
    )

    # Skip if previous error
    if state.has_errors:
        logger.info("Research Agent: Skipping due to previous errors")
        return {}

    # Check if we have research strategy from planner
    if not state.research_strategy:
        logger.warning("Research Agent: No research strategy provided by planner")
        # Fallback to original research approach
        return _fallback_research(state)

    try:
        # Update agent status
        state.set_agent_status("research_agent", AgentStatus.IN_PROGRESS)
        state.current_agent = "research_agent"
        state.current_phase = WorkflowPhase.RESEARCH

        # Generate dynamic search queries using LLM
        dynamic_queries = _generate_dynamic_search_queries(state)

        # Store the generated queries for debugging/transparency
        state.dynamic_research_queries = dynamic_queries

        # Conduct research using the generated queries
        research_results = _conduct_intelligent_research(dynamic_queries, state)

        # Analyze research results
        research_analysis = _analyze_research_results(research_results, state)

        # Update state
        state.set_agent_status("research_agent", AgentStatus.COMPLETED)
        state.research_analysis = research_analysis

        logger.info(
            f"Research Agent: Completed with {len(research_results)} citations using {len(dynamic_queries)} dynamic queries"
        )

        return {
            "research_results": research_results,
            "dynamic_research_queries": dynamic_queries,
            "research_analysis": research_analysis,
            "agent_status": state.agent_status,
        }

    except Exception as e:
        logger.error(f"Research Agent failed: {e}", exc_info=True)
        state.set_agent_error("research_agent", f"Research failed: {str(e)}")

        # Try fallback research if main approach fails
        logger.info("Research Agent: Attempting fallback research approach")
        return _fallback_research(state)


def _generate_dynamic_search_queries(state: MultiAgentInterviewPrepState) -> List[str]:
    """Generate intelligent, targeted search queries using LLM analysis."""

    logger.info("Research Agent: Generating dynamic search queries")

    try:
        # Get LLM client for query generation
        llm_client = get_llm_client_by_profile_name(
            config.agents.interview_question_generation  # Reuse existing config
        )

        # Prepare context
        resume_context = _prepare_resume_context(state)
        research_strategy = state.research_strategy

        # Create prompts
        system_message = SystemMessage(content=RESEARCH_SYSTEM_PROMPT)
        user_message = HumanMessage(
            content=RESEARCH_USER_PROMPT_TEMPLATE.format(
                job_description=state.job_description,
                company=state.interview_details.company or "Not specified",
                role=state.interview_details.role or "Not specified",
                interview_type=state.interview_details.type,
                primary_queries=research_strategy.get("primary_queries", []),
                focus_areas=research_strategy.get("focus_areas", []),
                role_specific_topics=research_strategy.get("role_specific_topics", []),
                company_specific_topics=research_strategy.get(
                    "company_specific_topics", []
                ),
                priority_level=research_strategy.get("priority_level", "standard"),
                resume_context=resume_context,
            )
        )

        messages = [system_message, user_message]

        # Get tracing config
        config_dict = langfuse_manager.get_config()

        # Generate queries
        response = llm_client.invoke(messages, config=config_dict)
        query_content = (
            response.content if hasattr(response, "content") else str(response)
        )

        # Parse queries from response
        queries = _parse_search_queries(query_content)

        logger.info(f"Research Agent: Generated {len(queries)} dynamic search queries")
        logger.debug(f"Generated queries: {queries}")

        return queries

    except Exception as e:
        logger.error(f"Failed to generate dynamic search queries: {e}")
        # Fallback to planner's primary queries
        return state.research_strategy.get("primary_queries", [])


def _conduct_intelligent_research(
    queries: List[str], state: MultiAgentInterviewPrepState
) -> List[ResearchCitation]:
    """Conduct research using the generated queries."""

    logger.info(f"Research Agent: Conducting research with {len(queries)} queries")

    all_citations = []

    for query in queries:
        try:
            logger.debug(f"Researching query: {query}")

            # Use the research tool's search functionality directly
            search_response = research_tool.search.invoke(query)
            results = search_response.get("results", [])

            for result in results:
                try:
                    # Check URL accessibility
                    is_accessible = research_tool._check_url_accessibility(
                        result.get("url", "")
                    )

                    citation = ResearchCitation(
                        url=result.get("url", ""),
                        title=result.get("title", ""),
                        accessed_at=datetime.now(),
                        content_snippet=result.get("content", "")[
                            :300
                        ],  # Longer snippet for intelligent analysis
                        is_accessible=is_accessible,
                    )
                    all_citations.append(citation)

                except Exception as e:
                    logger.warning(f"Failed to process result for query '{query}': {e}")
                    continue

        except Exception as e:
            logger.warning(f"Search failed for query '{query}': {e}")
            continue

    # Remove duplicates based on URL
    seen_urls = set()
    unique_citations = []
    for citation in all_citations:
        if citation.url not in seen_urls:
            unique_citations.append(citation)
            seen_urls.add(citation.url)

    logger.info(
        f"Research Agent: Found {len(unique_citations)} unique citations from {len(queries)} queries"
    )

    return unique_citations


def _analyze_research_results(
    citations: List[ResearchCitation], state: MultiAgentInterviewPrepState
) -> Dict[str, Any]:
    """Analyze research results to provide insights for other agents."""

    accessible_citations = [c for c in citations if c.is_accessible]

    analysis = {
        "total_citations": len(citations),
        "accessible_citations": len(accessible_citations),
        "coverage_quality": (
            "high"
            if len(accessible_citations) >= 5
            else "medium" if len(accessible_citations) >= 2 else "low"
        ),
        "key_findings": [],
        "gaps_identified": [],
        "recommendations_for_questions": [],
        "recommendations_for_answers": [],
    }

    # Extract key findings from top citations
    for citation in accessible_citations[:5]:
        if len(citation.content_snippet) > 50:
            analysis["key_findings"].append(
                {
                    "source": citation.title,
                    "insight": citation.content_snippet[:150] + "...",
                }
            )

    # Provide recommendations based on research quality
    if analysis["coverage_quality"] == "low":
        analysis["gaps_identified"].append(
            "Limited research results - may need broader search queries"
        )
        analysis["recommendations_for_questions"].append(
            "Focus on general role competencies rather than company-specific details"
        )

    if analysis["coverage_quality"] == "high":
        analysis["recommendations_for_questions"].append(
            "Can include company-specific situational questions"
        )
        analysis["recommendations_for_answers"].append(
            "Reference specific company initiatives or values found in research"
        )

    return analysis


def _fallback_research(state: MultiAgentInterviewPrepState) -> Dict[str, Any]:
    """Fallback to original research approach if intelligent research fails."""

    logger.info("Research Agent: Using fallback research approach")

    # Import and use original research function
    from src.agent.workflows.interview_prep.main import research_with_citations

    result = research_with_citations(state)

    # Still mark as completed
    state.set_agent_status("research_agent", AgentStatus.COMPLETED)
    result["agent_status"] = state.agent_status

    return result


def _prepare_resume_context(state: MultiAgentInterviewPrepState) -> str:
    """Prepare resume context for research query generation."""
    if state.pii_redaction_result:
        return state.pii_redaction_result.redacted_resume_text[
            :500
        ]  # Truncate for query generation
    return state.resume_text[:500]


def _parse_search_queries(content: str) -> List[str]:
    """Parse search queries from LLM response."""

    import json
    import re

    queries = []

    try:
        # Try to parse as JSON
        json_match = re.search(r"\[.*\]", content, re.DOTALL)
        if json_match:
            queries_list = json.loads(json_match.group(0))
            queries.extend([str(q).strip('"') for q in queries_list])
    except:
        pass

    if not queries:
        # Fallback: extract lines that look like queries
        lines = content.split("\n")
        for line in lines:
            line = line.strip()
            if line and (
                line.startswith("- ") or line.startswith("* ") or line.startswith('"')
            ):
                query = line.lstrip("- *").strip('"').strip()
                if len(query) > 10:  # Reasonable query length
                    queries.append(query)

    # Ensure we have at least some queries
    if not queries:
        queries = [
            f"{state.interview_details.company or 'company'} {state.interview_details.role or 'role'} interview",
            f"{state.interview_details.role or 'role'} interview questions",
            f"{state.interview_details.company or 'company'} culture values",
        ]

    return queries[:8]  # Limit to 8 queries to avoid overwhelming research tool
