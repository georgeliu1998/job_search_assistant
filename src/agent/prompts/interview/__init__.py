"""Interview preparation prompts."""

from .answer_generation import ANSWER_SYSTEM_PROMPT, ANSWER_USER_PROMPT_TEMPLATE
from .answers import create_answer_system_prompt, create_answer_user_prompt
from .editor import EDITOR_SYSTEM_PROMPT, EDITOR_USER_PROMPT_TEMPLATE
from .planner import PLANNER_SYSTEM_PROMPT, PLANNER_USER_PROMPT_TEMPLATE
from .question_generation import QUESTION_SYSTEM_PROMPT, QUESTION_USER_PROMPT_TEMPLATE
from .questions import create_question_system_prompt, create_question_user_prompt
from .research import RESEARCH_SYSTEM_PROMPT, RESEARCH_USER_PROMPT_TEMPLATE

__all__ = [
    "create_answer_system_prompt",
    "create_answer_user_prompt",
    "create_question_system_prompt",
    "create_question_user_prompt",
    "PLANNER_SYSTEM_PROMPT",
    "PLANNER_USER_PROMPT_TEMPLATE",
    "RESEARCH_SYSTEM_PROMPT",
    "RESEARCH_USER_PROMPT_TEMPLATE",
    "QUESTION_SYSTEM_PROMPT",
    "QUESTION_USER_PROMPT_TEMPLATE",
    "ANSWER_SYSTEM_PROMPT",
    "ANSWER_USER_PROMPT_TEMPLATE",
    "EDITOR_SYSTEM_PROMPT",
    "EDITOR_USER_PROMPT_TEMPLATE",
]
