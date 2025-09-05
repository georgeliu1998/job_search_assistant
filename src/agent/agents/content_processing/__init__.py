"""Content processing agents that work with existing content.

These agents handle synthesis, validation, formatting, and enhancement
of already generated content rather than creating content from scratch.
"""

from .editor import editor_agent

__all__ = ["editor_agent"]
