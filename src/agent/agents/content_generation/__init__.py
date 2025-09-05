"""Content generation agents that create new content from scratch.

These agents generate original content like questions, answers, text,
and other creative outputs based on input requirements and context.
"""

from .answer import answer_agent
from .question import question_agent

__all__ = ["question_agent", "answer_agent"]
