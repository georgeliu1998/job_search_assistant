"""
Interview question generation prompts.

These prompts are designed for generating relevant interview questions
based on job descriptions, interview types, and company research.
"""

from langchain_core.prompts import PromptTemplate

from src.agent.workflows.interview_prep.states import InterviewPrepState

QUESTION_GENERATION_SYSTEM_TEMPLATE = """You are an expert interview preparation assistant. Your task is to generate relevant interview questions based on the job description, interview type, and company information.

Interview Type: {interview_type}
Interview Format: {interview_format}
Company: {company}
Role: {role}

CRITICAL REQUIREMENT: You MUST generate EXACTLY {num_questions} interview questions. No more, no less. Count your questions to ensure you have exactly {num_questions}.

Generate exactly {num_questions} interview questions that are:
1. Relevant to the specific interview type and role
2. Appropriate for the experience level indicated in the resume
3. Mix of behavioral, technical, and situational questions
4. Include rationale for why each question is relevant

Format each question EXACTLY as shown below:
Question: [The actual question]
Category: [general/behavioral/technical/culture/situational]
Difficulty: [easy/medium/hard]
Rationale: [Why this question is relevant]

REMEMBER: You must provide exactly {num_questions} questions in the format above. Double-check your count before submitting your response.

---"""


QUESTION_GENERATION_USER_TEMPLATE = """Job Description:
{job_description}

Redacted Resume Context:
{redacted_resume}

{research_context}Please generate interview questions for this {interview_type} interview."""


QUESTION_GENERATION_SYSTEM_PROMPT = PromptTemplate.from_template(
    QUESTION_GENERATION_SYSTEM_TEMPLATE
)

QUESTION_GENERATION_USER_PROMPT = PromptTemplate.from_template(
    QUESTION_GENERATION_USER_TEMPLATE
)


def create_question_system_prompt(state: InterviewPrepState) -> str:
    """Create system prompt for question generation."""
    # Use the values directly since Pydantic converts enums to strings
    interview_type = state.interview_details.type
    interview_format = state.interview_details.format

    # Handle format enum that might not be converted yet
    if hasattr(interview_format, "value"):
        interview_format = interview_format.value

    return QUESTION_GENERATION_SYSTEM_PROMPT.format(
        interview_type=interview_type,
        interview_format=interview_format,
        company=state.interview_details.company or "Not specified",
        role=state.interview_details.role or "Not specified",
        num_questions=state.num_questions,
    )


def create_question_user_prompt(state: InterviewPrepState) -> str:
    """Create user prompt for question generation with context."""
    research_context = ""
    if state.research_results:
        research_snippets = [r.content_snippet for r in state.research_results[:3]]
        research_context = f"Research findings:\n{' '.join(research_snippets)}\n\n"

    # Use the value directly since Pydantic converts enum to string
    interview_type = state.interview_details.type

    return QUESTION_GENERATION_USER_PROMPT.format(
        job_description=state.job_description,
        redacted_resume=(
            state.pii_redaction_result.redacted_resume_text
            if state.pii_redaction_result
            else "Resume not available"
        ),
        research_context=research_context,
        interview_type=interview_type,
    )
