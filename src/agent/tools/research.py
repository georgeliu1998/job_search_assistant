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
                    is_accessible = self._check_url_accessibility(result.get("url", ""))

                    citation = ResearchCitation(
                        url=result.get("url", ""),
                        title=result.get("title", ""),
                        accessed_at=datetime.now(),
                        content_snippet=result.get("content", "")[:200],
                        is_accessible=is_accessible,
                    )
                    citations.append(citation)
                    logger.info(
                        f"Added citation: {result.get('title', 'No title')} (accessible: {is_accessible})"
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
                        is_accessible = self._check_url_accessibility(
                            result.get("url", "")
                        )

                        citation = ResearchCitation(
                            url=result.get("url", ""),
                            title=result.get("title", ""),
                            accessed_at=datetime.now(),
                            content_snippet=result.get("content", "")[:200],
                            is_accessible=is_accessible,
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

    def _check_url_accessibility(self, url: str) -> bool:
        """Verify URL accessibility."""
        # Return False for empty URLs
        if not url or not url.strip():
            return False

        try:
            # Perform HEAD request to check if URL is accessible
            response = self.client.head(url, timeout=5.0, follow_redirects=True)
            return response.status_code == 200

        except httpx.TimeoutException:
            logger.warning(f"Timeout checking URL: {url}")
            return False

        except Exception as e:
            logger.warning(f"Error checking URL {url}: {e}")
            return False

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
