"""Main workflow for interview preparation with sequential nodes."""

import logging
from typing import Any, Dict, List

from langchain_core.messages import HumanMessage, SystemMessage
from langgraph.graph import END, START, StateGraph

from src.agent.prompts.interview.answers import (
    create_answer_system_prompt,
    create_answer_user_prompt,
)
from src.agent.prompts.interview.questions import (
    create_question_system_prompt,
    create_question_user_prompt,
)
from src.agent.tools.interview.pii_redaction import pii_pipeline
from src.agent.tools.interview.research import research_tool
from src.agent.workflows.interview_prep.states import InterviewPrepState
from src.config import config
from src.llm.common.factory import get_llm_client_by_profile_name
from src.models.interview import (
    AnswerItem,
    AnswerStyle,
    DifficultyLevel,
    InterviewGuide,
    QAPair,
    QuestionCategory,
    QuestionItem,
)

logger = logging.getLogger(__name__)


def get_interview_prep_workflow() -> StateGraph:
    """Create the interview preparation workflow."""
    workflow = StateGraph(InterviewPrepState)

    # Sequential nodes (no supervisor initially)
    workflow.add_node("validate_and_redact", validate_and_redact_input)
    workflow.add_node("research", research_with_citations)
    workflow.add_node("questions", generate_questions)
    workflow.add_node("answers", generate_answers)
    workflow.add_node("compile", compile_guide)

    # Sequential edges (like job_evaluation)
    workflow.add_edge(START, "validate_and_redact")
    workflow.add_edge("validate_and_redact", "research")
    workflow.add_edge("research", "questions")
    workflow.add_edge("questions", "answers")
    workflow.add_edge("answers", "compile")
    workflow.add_edge("compile", END)

    return workflow.compile()


def validate_and_redact_input(state: InterviewPrepState) -> Dict[str, Any]:
    """Validate input and perform PII redaction with guardrails."""
    logger.info("Validating input and performing PII redaction")

    # CRITICAL: Skip if previous error (workflow short-circuiting)
    if state.error:
        logger.info("Skipping validation due to previous error")
        return {}

    # Validate required inputs
    if not state.job_description or not state.resume_text:
        logger.warning("Missing required inputs")
        return {"error": "Job description and resume text are required"}

    # PII redaction with validation
    try:
        redaction_result = pii_pipeline.redact_resume(state.resume_text)

        # CRITICAL: Block workflow if PII redaction incomplete
        if not redaction_result.complete:
            logger.warning("PII redaction incomplete")
            return {
                "error": "PII redaction incomplete - manual review required",
                "pii_redaction_result": redaction_result,
            }

        logger.info("PII redaction completed successfully")
        return {"pii_redaction_result": redaction_result}

    except Exception as e:
        logger.error(f"PII redaction failed: {e}")
        return {"error": f"PII redaction failed: {str(e)}"}


def research_with_citations(state: InterviewPrepState) -> Dict[str, Any]:
    """Conduct research with verifiable citations."""
    logger.info("Starting research phase")

    # Skip if previous error
    if state.error:
        logger.info("Skipping research due to previous error")
        return {}

    try:
        company = state.interview_details.company
        role = state.interview_details.role

        # Conduct research
        research_results = research_tool.research_company_and_role(company, role)

        # Add role-specific research topics
        role_topics = _get_role_specific_topics(role)
        if role_topics:
            topic_research = research_tool.research_specific_topics(role_topics)
            research_results.extend(topic_research)

        logger.info(f"Research completed with {len(research_results)} citations")
        return {"research_results": research_results}

    except Exception as e:
        logger.error(f"Research failed: {e}")
        return {"error": f"Research failed: {str(e)}"}


def generate_questions(state: InterviewPrepState) -> Dict[str, Any]:
    """Generate interview questions based on role and interview type."""
    logger.info("Generating interview questions")

    # Skip if previous error
    if state.error:
        logger.info("Skipping question generation due to previous error")
        return {}

    try:
        # Get LLM client for question generation
        llm_client = get_llm_client_by_profile_name(
            config.agents.interview_question_generation
        )

        # Create system prompt for question generation
        system_prompt = create_question_system_prompt(state)

        # Create user prompt with context
        user_prompt = create_question_user_prompt(state)

        # Generate questions with retry logic
        questions = []
        max_retries = 2

        for attempt in range(max_retries + 1):
            # Generate questions using LLM
            messages = [
                SystemMessage(content=system_prompt),
                HumanMessage(content=user_prompt),
            ]

            response = llm_client.invoke(messages)

            # Log the raw LLM response for debugging
            logger.info(
                f"Attempt {attempt + 1}: LLM response length: {len(response.content)} characters"
            )
            logger.debug(f"Raw LLM response:\n{response.content}")

            # Parse response into structured questions
            questions = _parse_questions_response(response.content, state)

            logger.info(
                f"Attempt {attempt + 1}: Generated {len(questions)} interview questions (requested: {state.num_questions})"
            )

            # Check if we got the right number of questions
            if len(questions) == state.num_questions:
                logger.info(
                    f"Successfully generated exactly {state.num_questions} questions on attempt {attempt + 1}"
                )
                break
            elif len(questions) > state.num_questions:
                # If we got too many, truncate to the requested number
                logger.warning(
                    f"Got {len(questions)} questions, truncating to {state.num_questions}"
                )
                questions = questions[: state.num_questions]
                break
            elif attempt < max_retries:
                logger.warning(
                    f"Got only {len(questions)} questions, retrying... (attempt {attempt + 1}/{max_retries + 1})"
                )
            else:
                logger.error(
                    f"Failed to generate {state.num_questions} questions after {max_retries + 1} attempts. Got {len(questions)} questions."
                )
        return {
            "qa_pairs": [
                QAPair(
                    question=q,
                    answer=AnswerItem(
                        question=q.question,
                        answer="",
                        style=AnswerStyle.DETAILED,
                        key_points=[],
                        examples=[],
                    ),
                )
                for q in questions
            ]
        }

    except Exception as e:
        logger.error(f"Question generation failed: {e}")
        return {"error": f"Question generation failed: {str(e)}"}


def generate_answers(state: InterviewPrepState) -> Dict[str, Any]:
    """Generate personalized answers for the interview questions."""
    logger.info("Generating personalized answers")

    # Skip if previous error
    if state.error:
        logger.info("Skipping answer generation due to previous error")
        return {}

    if not state.qa_pairs:
        logger.warning("No questions available for answer generation")
        return {"error": "No questions available for answer generation"}

    try:
        # Get LLM client for answer generation
        llm_client = get_llm_client_by_profile_name(
            config.agents.interview_answer_generation
        )

        updated_qa_pairs = []

        for qa_pair in state.qa_pairs:
            # Create prompts for each question
            system_prompt = create_answer_system_prompt(state)
            user_prompt = create_answer_user_prompt(state, qa_pair.question)

            messages = [
                SystemMessage(content=system_prompt),
                HumanMessage(content=user_prompt),
            ]

            response = llm_client.invoke(messages)

            # Parse and create answer
            answer_content = response.content
            answer = AnswerItem(
                question=qa_pair.question.question,
                answer=answer_content,
                style=_determine_answer_style(qa_pair.question.category),
                key_points=_extract_key_points(answer_content),
                examples=_extract_examples(answer_content),
            )

            updated_qa_pairs.append(QAPair(question=qa_pair.question, answer=answer))

        logger.info(f"Generated answers for {len(updated_qa_pairs)} questions")
        return {"qa_pairs": updated_qa_pairs}

    except Exception as e:
        logger.error(f"Answer generation failed: {e}")
        return {"error": f"Answer generation failed: {str(e)}"}


def compile_guide(state: InterviewPrepState) -> Dict[str, Any]:
    """Compile the complete interview preparation guide."""
    logger.info("Compiling interview preparation guide")

    # Skip if previous error
    if state.error:
        logger.info("Skipping compilation due to previous error")
        return {}

    try:
        # Create research summary
        research_summary = _create_research_summary(state.research_results or [])

        # Generate preparation tips
        preparation_tips = _generate_preparation_tips(state)

        # Create final interview guide
        interview_guide = InterviewGuide(
            num_questions=state.num_questions,
            research_summary=research_summary,
            qa_pairs=state.qa_pairs or [],
            preparation_tips=preparation_tips,
            citations=state.research_results or [],
        )

        logger.info("Interview preparation guide compiled successfully")
        return {"interview_guide": interview_guide}

    except Exception as e:
        logger.error(f"Guide compilation failed: {e}")
        return {"error": f"Guide compilation failed: {str(e)}"}


# Helper functions for the workflow


def _get_role_specific_topics(role: str) -> List[str]:
    """Get research topics specific to the role."""
    if not role:
        return []

    role_lower = role.lower()
    topics = []

    if "engineer" in role_lower or "developer" in role_lower:
        topics.extend(["coding interview", "technical questions", "system design"])
    elif "manager" in role_lower:
        topics.extend(
            ["leadership interview", "team management", "conflict resolution"]
        )
    elif "product" in role_lower:
        topics.extend(["product management", "user experience", "roadmap planning"])
    elif "data" in role_lower:
        topics.extend(["data analysis", "statistical methods", "machine learning"])

    return topics


def _parse_questions_response(
    response: str, state: InterviewPrepState
) -> List[QuestionItem]:
    """Parse LLM response into structured questions."""
    questions = []
    lines = response.strip().split("\n")
    current_question = {}

    logger.debug(f"Parsing {len(lines)} lines from LLM response")

    for i, line in enumerate(lines):
        line = line.strip()

        # Skip empty lines
        if not line:
            continue

        # Handle both "Question:" and "1. Question:" formats
        if line.startswith("Question:") or (
            line
            and "Question:" in line
            and any(
                line.startswith(str(i) + ".") for i in range(1, 50)
            )  # Increased range for more questions
        ):
            if current_question.get("question"):
                # Save previous question
                questions.append(_create_question_item(current_question))
                logger.debug(
                    f"Parsed question {len(questions)}: {current_question.get('question', '')[:50]}..."
                )

            # Extract question text after "Question:"
            if "Question:" in line:
                question_text = line.split("Question:", 1)[1].strip()
                current_question = {"question": question_text}

        elif line.startswith("Category:") or (
            "Category:" in line and line.strip().startswith("Category:")
        ):
            category_text = line.split("Category:", 1)[1].strip()
            current_question["category"] = category_text

        elif line.startswith("Difficulty:") or (
            "Difficulty:" in line and line.strip().startswith("Difficulty:")
        ):
            difficulty_text = line.split("Difficulty:", 1)[1].strip()
            current_question["difficulty"] = difficulty_text

        elif line.startswith("Rationale:") or (
            "Rationale:" in line and line.strip().startswith("Rationale:")
        ):
            rationale_text = line.split("Rationale:", 1)[1].strip()
            current_question["rationale"] = rationale_text

    # Add last question
    if current_question.get("question"):
        questions.append(_create_question_item(current_question))
        logger.debug(
            f"Parsed final question {len(questions)}: {current_question.get('question', '')[:50]}..."
        )

    logger.info(f"Successfully parsed {len(questions)} questions from LLM response")
    return questions


def _create_question_item(question_data: Dict[str, str]) -> QuestionItem:
    """Create QuestionItem from parsed data."""
    category_map = {
        "general": QuestionCategory.GENERAL,
        "behavioral": QuestionCategory.BEHAVIORAL,
        "technical": QuestionCategory.TECHNICAL,
        "culture": QuestionCategory.CULTURE,
        "situational": QuestionCategory.SITUATIONAL,
    }

    difficulty_map = {
        "easy": DifficultyLevel.EASY,
        "medium": DifficultyLevel.MEDIUM,
        "hard": DifficultyLevel.HARD,
    }

    return QuestionItem(
        question=question_data.get("question", ""),
        category=category_map.get(
            question_data.get("category", "").lower(), QuestionCategory.GENERAL
        ),
        rationale=question_data.get("rationale", ""),
        difficulty=difficulty_map.get(
            question_data.get("difficulty", "").lower(), DifficultyLevel.MEDIUM
        ),
    )


def _determine_answer_style(category: QuestionCategory) -> AnswerStyle:
    """Determine answer style based on question category."""
    if category == QuestionCategory.BEHAVIORAL:
        return AnswerStyle.STAR
    elif category in [QuestionCategory.TECHNICAL, QuestionCategory.SITUATIONAL]:
        return AnswerStyle.DETAILED
    else:
        return AnswerStyle.CONCISE


def _extract_key_points(answer: str) -> List[str]:
    """Extract key points from answer text."""
    # Simple extraction - look for numbered points or bullet points
    lines = answer.split("\n")
    key_points = []

    for line in lines:
        line = line.strip()
        if line.startswith(("1.", "2.", "3.", "4.", "5.", "-", "•")):
            key_points.append(line)

    return key_points[:5]  # Limit to 5 key points


def _extract_examples(answer: str) -> List[str]:
    """Extract specific examples from answer text."""
    # Look for phrases that indicate examples
    examples = []
    sentences = answer.split(".")

    for sentence in sentences:
        if any(
            phrase in sentence.lower()
            for phrase in [
                "for example",
                "for instance",
                "specifically",
                "in my experience at",
                "when I worked on",
                "during my time at",
            ]
        ):
            examples.append(sentence.strip())

    return examples[:3]  # Limit to 3 examples


def _create_research_summary(research_results: List) -> str:
    """Create a summary of research findings."""
    if not research_results:
        return "No specific research conducted for this interview."

    summary_parts = ["Research Summary:"]

    for citation in research_results[:3]:  # Use top 3 citations
        if citation.reliability_score >= 0.6:
            summary_parts.append(f"• {citation.title}: {citation.content_snippet}")

    return "\n".join(summary_parts)


def _generate_preparation_tips(state: InterviewPrepState) -> List[str]:
    """Generate general preparation tips based on interview type."""
    tips = [
        "Research the company's recent news, values, and culture",
        "Prepare specific examples that demonstrate your key skills",
        "Practice your elevator pitch and 'tell me about yourself' response",
        "Prepare thoughtful questions to ask your interviewer",
    ]

    # Add interview type specific tips - use string value directly since Pydantic converts enums
    interview_type = state.interview_details.type
    if interview_type == "technical":
        tips.extend(
            [
                "Review key technical concepts and be ready for coding challenges",
                "Prepare to discuss your technical projects in detail",
            ]
        )
    elif interview_type == "behavioral":
        tips.extend(
            [
                "Use the STAR method (Situation, Task, Action, Result) for behavioral questions",
                "Think of examples that show leadership, problem-solving, and teamwork",
            ]
        )

    return tips
