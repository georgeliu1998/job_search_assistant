"""
Interview answer generation prompts.

These prompts are designed for generating personalized, compelling answers
to interview questions based on the candidate's experience and the specific role.
"""

from langchain_core.prompts import PromptTemplate

from src.agent.workflows.interview_prep.states import InterviewPrepState
from src.models.interview import QuestionItem

ANSWER_GENERATION_SYSTEM_TEMPLATE = """You are an expert interview coach. Generate personalized, compelling answers to interview questions based on the candidate's experience and the specific role.

Guidelines:
1. Use specific examples from the candidate's experience
2. Follow STAR method for behavioral questions (Situation, Task, Action, Result)
3. Keep answers concise but comprehensive (2-3 minutes when spoken)
4. Highlight relevant skills and achievements
5. Show enthusiasm and cultural fit

Interview Type: {interview_type}
Company: {company}
Role: {role}"""


ANSWER_GENERATION_USER_TEMPLATE = """Question: {question}
Category: {category}
Difficulty: {difficulty}
Rationale: {rationale}

Candidate's Background (Redacted):
{redacted_resume}

Job Requirements:
{job_description}

Please generate a personalized, compelling answer for this question."""


ANSWER_GENERATION_SYSTEM_PROMPT = PromptTemplate.from_template(
    ANSWER_GENERATION_SYSTEM_TEMPLATE
)

ANSWER_GENERATION_USER_PROMPT = PromptTemplate.from_template(
    ANSWER_GENERATION_USER_TEMPLATE
)


def create_answer_system_prompt(state: InterviewPrepState) -> str:
    """Create system prompt for answer generation."""
    # Use the value directly since Pydantic converts enum to string
    interview_type = state.interview_details.type

    return ANSWER_GENERATION_SYSTEM_PROMPT.format(
        interview_type=interview_type,
        company=state.interview_details.company or "Not specified",
        role=state.interview_details.role or "Not specified",
    )


def create_answer_user_prompt(state: InterviewPrepState, question: QuestionItem) -> str:
    """Create user prompt for answer generation."""
    # Use the values directly since Pydantic converts enum to string
    category = question.category
    difficulty = question.difficulty

    return ANSWER_GENERATION_USER_PROMPT.format(
        question=question.question,
        category=category,
        difficulty=difficulty,
        rationale=question.rationale,
        redacted_resume=(
            state.pii_redaction_result.redacted_resume_text
            if state.pii_redaction_result
            else "Resume not available"
        ),
        job_description=state.job_description,
    )
