"""Research tool with citations for interview preparation."""

import logging
from datetime import datetime
from typing import List, Optional

import httpx
from langchain_tavily import TavilySearch

from src.models.interview import ResearchCitation

logger = logging.getLogger(__name__)


class ResearchWithCitations:
    """Research tool with verifiable citations and link checking."""

    def __init__(self):
        """Initialize the research tool."""
        self.search = TavilySearch(max_results=5)
        self.client = httpx.Client(timeout=10.0)

    def research_company_and_role(
        self, company: Optional[str] = None, role: Optional[str] = None
    ) -> List[ResearchCitation]:
        """Research company and role with verifiable citations."""
        logger.info(f"Starting research for company: {company}, role: {role}")

        # Build search query
        search_terms = []
        if company:
            search_terms.append(company)
        if role:
            search_terms.append(role)

        # Add interview-specific terms
        search_terms.extend(["interview", "questions", "company", "culture"])
        search_query = " ".join(search_terms)

        logger.info(f"Search query: {search_query}")

        citations = []
        try:
            # Perform search with Tavily
            search_response = self.search.invoke(search_query)

            # Extract results from the Tavily response
            # According to Tavily docs, response has structure: {'results': [...], 'query': '...', etc.}
            results = search_response.get("results", [])

            logger.debug(f"Tavily returned {len(results)} results")

            for result in results:
                try:
                    # Verify link accessibility
                    reliability_score = self._check_link_reliability(
                        result.get("url", "")
                    )

                    citation = ResearchCitation(
                        url=result.get("url", ""),
                        title=result.get("title", ""),
                        accessed_at=datetime.now(),
                        reliability_score=reliability_score,
                        content_snippet=result.get("content", "")[:200],
                    )
                    citations.append(citation)
                    logger.info(
                        f"Added citation: {result.get('title', 'No title')} (score: {reliability_score})"
                    )

                except Exception as e:
                    logger.warning(f"Failed to process search result: {e}")
                    continue

        except Exception as e:
            logger.error(f"Search failed: {e}")
            # Return empty citations if search fails
            return []

        logger.info(f"Research completed with {len(citations)} citations")
        return citations

    def research_specific_topics(self, topics: List[str]) -> List[ResearchCitation]:
        """Research specific interview topics."""
        logger.info(f"Researching specific topics: {topics}")

        all_citations = []
        for topic in topics:
            search_query = f"{topic} interview questions preparation tips"

            try:
                # Create a new TavilySearch instance for fewer results per topic
                topic_search = TavilySearch(max_results=3)
                search_response = topic_search.invoke(search_query)

                # Extract results from the Tavily response
                results = search_response.get("results", [])
                logger.debug(
                    f"Topic '{topic}' - Tavily returned {len(results)} results"
                )

                for result in results:
                    try:
                        reliability_score = self._check_link_reliability(
                            result.get("url", "")
                        )

                        citation = ResearchCitation(
                            url=result.get("url", ""),
                            title=result.get("title", ""),
                            accessed_at=datetime.now(),
                            reliability_score=reliability_score,
                            content_snippet=result.get("content", "")[:200],
                        )
                        all_citations.append(citation)

                    except Exception as e:
                        logger.warning(
                            f"Failed to process result for topic {topic}: {e}"
                        )
                        continue

            except Exception as e:
                logger.warning(f"Search failed for topic {topic}: {e}")
                continue

        logger.info(f"Topic research completed with {len(all_citations)} citations")
        return all_citations

    def _check_link_reliability(self, url: str) -> float:
        """Verify URL accessibility and assign reliability score."""
        # Return low score for empty URLs
        if not url or not url.strip():
            return 0.1

        try:
            # Perform HEAD request to check if URL is accessible
            response = self.client.head(url, timeout=5.0, follow_redirects=True)

            if response.status_code == 200:
                # Score based on domain reputation
                domain = url.lower()

                # High reliability domains
                if any(
                    trusted in domain
                    for trusted in [
                        "linkedin.com",
                        "glassdoor.com",
                        "indeed.com",
                        "harvard.edu",
                        "mit.edu",
                        ".edu",
                        "medium.com",
                        "dev.to",
                        "stackoverflow.com",
                        "github.com",
                    ]
                ):
                    return 0.9

                # Medium reliability domains
                elif any(
                    medium in domain
                    for medium in [
                        "forbes.com",
                        "techcrunch.com",
                        "wired.com",
                        "businessinsider.com",
                        "bloomberg.com",
                        "reddit.com",
                        "quora.com",
                    ]
                ):
                    return 0.7

                # Basic reliable response
                else:
                    return 0.6

            elif response.status_code in [301, 302, 303, 307, 308]:
                # Redirects are okay but slightly lower score
                return 0.5

            else:
                # Non-200 response
                return 0.3

        except httpx.TimeoutException:
            logger.warning(f"Timeout checking URL: {url}")
            return 0.2

        except Exception as e:
            logger.warning(f"Error checking URL {url}: {e}")
            return 0.1

    def close(self):
        """Close the HTTP client."""
        if hasattr(self, "client"):
            self.client.close()


# Global instance for use across the application
# Only create when TAVILY_API_KEY is available
_research_tool_instance = None


def get_research_tool():
    """Get a ResearchWithCitations instance (lazy-loaded)."""
    global _research_tool_instance
    if _research_tool_instance is None:
        _research_tool_instance = ResearchWithCitations()
    return _research_tool_instance


# Create a research_tool that can be imported directly
class LazyResearchTool:
    """Lazy-loading wrapper for ResearchWithCitations."""

    def __getattr__(self, name):
        # Delegate all attribute access to the actual research tool
        return getattr(get_research_tool(), name)


research_tool = LazyResearchTool()
