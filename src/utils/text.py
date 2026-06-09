"""Text utilities for the Job Search Assistant.

Provides helpers for bounding user-supplied text before it reaches LLM calls,
preventing runaway cost and context window overflows.
"""

from src.utils.logging import get_logger

logger = get_logger(__name__)

# Character limits for user-supplied inputs sent to LLMs. These are generous
# (~5x the average input) so legitimate text is never truncated, while still
# catching accidental pastes of entire documents or web pages.
MAX_JOB_DESCRIPTION_CHARS = 20_000
MAX_ROLE_DESCRIPTION_CHARS = 2_000

_TRUNCATION_MARKER = "\n[truncated]"


def truncate_text(text: str, max_chars: int, label: str = "input") -> str:
    """Truncate ``text`` to ``max_chars`` characters.

    If truncation occurs, a ``[truncated]`` marker is appended so the LLM knows
    the input is incomplete, and a warning is logged.

    Args:
        text: The text to bound.
        max_chars: Maximum number of characters to keep (before the marker).
        label: Human-readable name of the field, used in the warning log.

    Returns:
        The original text if within the limit, otherwise the truncated text
        with a marker appended.
    """
    if text is None:
        return text

    if len(text) <= max_chars:
        return text

    logger.warning("Truncating %s from %d to %d characters", label, len(text), max_chars)
    return text[:max_chars] + _TRUNCATION_MARKER
