"""Research Agent for multi-agent interview preparation workflow.

The Research Agent conducts intelligent research using AI-generated search queries
instead of hardcoded topics, making research more targeted and relevant.
"""

import json
import re
from datetime import datetime
from typing import Any, Dict, List

from src.agent.agents.common.base import BaseAgent
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
from src.models.interview import ResearchCitation


class ResearchAgent(BaseAgent):
    """Research Agent that conducts intelligent research with dynamic queries."""

    def __init__(self):
        """Initialize the Research Agent."""
        super().__init__(name="research_agent")

    def check_prerequisites(self, state: MultiAgentInterviewPrepState) -> bool:
        """Check if research prerequisites are met.

        Args:
            state: Current multi-agent workflow state

        Returns:
            True if research strategy is available
        """
        return bool(state.research_strategy)

    def handle_missing_prerequisites(
        self, state: MultiAgentInterviewPrepState
    ) -> Dict[str, Any]:
        """Handle missing research strategy by using fallback.

        Args:
            state: Current multi-agent workflow state

        Returns:
            Fallback research results
        """
        self.logger.warning("No research strategy provided by planner, using fallback")
        return self._fallback_research(state)

    def has_fallback(self) -> bool:
        """Research agent has fallback to original approach.

        Returns:
            True
        """
        return True

    def execute_fallback(self, state: MultiAgentInterviewPrepState) -> Dict[str, Any]:
        """Execute fallback research approach.

        Args:
            state: Current multi-agent workflow state

        Returns:
            Fallback research results
        """
        self.logger.info("Attempting fallback research approach")
        return self._fallback_research(state)

    def execute(self, state: MultiAgentInterviewPrepState) -> Dict[str, Any]:
        """Execute intelligent research with dynamic queries.

        Args:
            state: Current multi-agent workflow state

        Returns:
            Dict containing research results and analysis
        """
        state.current_phase = WorkflowPhase.RESEARCH

        # Generate dynamic search queries using LLM
        dynamic_queries = self._generate_dynamic_search_queries(state)

        # Store the generated queries for debugging/transparency
        state.dynamic_research_queries = dynamic_queries

        # Conduct research using the generated queries
        research_results = self._conduct_intelligent_research(dynamic_queries, state)

        # Analyze research results
        research_analysis = self._analyze_research_results(research_results, state)

        # Update state
        state.research_analysis = research_analysis

        self.logger.info(
            f"Completed with {len(research_results)} citations using {len(dynamic_queries)} dynamic queries"
        )

        return {
            "research_results": research_results,
            "dynamic_research_queries": dynamic_queries,
            "research_analysis": research_analysis,
        }

    def _generate_dynamic_search_queries(
        self, state: MultiAgentInterviewPrepState
    ) -> List[str]:
        """Generate intelligent, targeted search queries using LLM analysis.

        Args:
            state: Current multi-agent workflow state

        Returns:
            List of generated search queries
        """
        self.logger.info("Generating dynamic search queries")

        try:
            # Prepare context
            resume_context = self.prepare_resume_context(state, max_length=500)
            research_strategy = state.research_strategy

            # Build the research prompt
            user_prompt = RESEARCH_USER_PROMPT_TEMPLATE.format(
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

            # Generate queries
            response = self.invoke_llm(
                system_prompt=RESEARCH_SYSTEM_PROMPT, user_prompt=user_prompt
            )
            query_content = (
                response.content if hasattr(response, "content") else str(response)
            )

            # Parse queries from response
            queries = self._parse_search_queries(query_content, state)

            self.logger.info(f"Generated {len(queries)} dynamic search queries")
            self.logger.debug(f"Generated queries: {queries}")

            return queries

        except Exception as e:
            self.logger.error(f"Failed to generate dynamic search queries: {e}")
            # Fallback to planner's primary queries
            return state.research_strategy.get("primary_queries", [])

    def _conduct_intelligent_research(
        self, queries: List[str], state: MultiAgentInterviewPrepState
    ) -> List[ResearchCitation]:
        """Conduct research using the generated queries.

        Args:
            queries: List of search queries
            state: Current multi-agent workflow state

        Returns:
            List of unique research citations
        """
        self.logger.info(f"Conducting research with {len(queries)} queries")

        all_citations = []

        for query in queries:
            try:
                self.logger.debug(f"Researching query: {query}")

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
                        self.logger.warning(
                            f"Failed to process result for query '{query}': {e}"
                        )
                        continue

            except Exception as e:
                self.logger.warning(f"Search failed for query '{query}': {e}")
                continue

        # Remove duplicates based on URL
        seen_urls = set()
        unique_citations = []
        for citation in all_citations:
            if citation.url not in seen_urls:
                unique_citations.append(citation)
                seen_urls.add(citation.url)

        self.logger.info(
            f"Found {len(unique_citations)} unique citations from {len(queries)} queries"
        )

        return unique_citations

    def _analyze_research_results(
        self, citations: List[ResearchCitation], state: MultiAgentInterviewPrepState
    ) -> Dict[str, Any]:
        """Analyze research results to provide insights for other agents.

        Args:
            citations: List of research citations
            state: Current multi-agent workflow state

        Returns:
            Dict containing research analysis
        """
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

    def _fallback_research(self, state: MultiAgentInterviewPrepState) -> Dict[str, Any]:
        """Fallback to original research approach if intelligent research fails.

        Args:
            state: Current multi-agent workflow state

        Returns:
            Fallback research results
        """
        self.logger.info("Using fallback research approach")

        # Import and use original research function
        from src.agent.workflows.interview_prep.main import research_with_citations

        result = research_with_citations(state)

        # Still mark as completed
        state.set_agent_status("research_agent", AgentStatus.COMPLETED)
        result["agent_status"] = state.agent_status

        return result

    def _parse_search_queries(
        self, content: str, state: MultiAgentInterviewPrepState
    ) -> List[str]:
        """Parse search queries from LLM response.

        Args:
            content: LLM response content
            state: Current multi-agent workflow state

        Returns:
            List of parsed search queries
        """
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
                    line.startswith("- ")
                    or line.startswith("* ")
                    or line.startswith('"')
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


# Create singleton instance for backward compatibility
research_agent_instance = ResearchAgent()


def research_agent(state: MultiAgentInterviewPrepState) -> Dict[str, Any]:
    """
    Backward compatible function interface for research agent.

    Args:
        state: Current multi-agent workflow state

    Returns:
        Dict containing research results and analysis
    """
    return research_agent_instance(state)
