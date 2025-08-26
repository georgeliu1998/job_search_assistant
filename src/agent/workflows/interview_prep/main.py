"""Main workflow for interview preparation with sequential nodes."""

import logging
from typing import Any, Dict, List, Optional

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
from src.llm.observability import langfuse_manager
from src.models.interview import (
    AnswerItem,
    AnswerStyle,
    DifficultyLevel,
    InterviewGuide,
    InterviewQuestions,
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
    """Generate interview questions based on role and interview type using structured output."""
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

        # Create structured LLM with schema
        structured_llm = llm_client._get_client().with_structured_output(
            InterviewQuestions
        )

        # Create system prompt for question generation
        system_prompt = create_question_system_prompt(state)

        # Create user prompt with context
        user_prompt = create_question_user_prompt(state)

        messages = [
            SystemMessage(content=system_prompt),
            HumanMessage(content=user_prompt),
        ]

        # Context-aware tracing configuration
        config_dict = langfuse_manager.get_config()

        # Generate structured questions
        logger.info(
            f"Generating {state.num_questions} interview questions using structured output"
        )
        result = structured_llm.invoke(messages, config=config_dict)
        logger.debug(f"Result: {result}")

        # Extract questions from structured result
        questions = (
            result.questions
            if hasattr(result, "questions")
            else result.get("questions", [])
        )

        logger.info(f"Generated {len(questions)} structured interview questions")

        # Validate we got the expected number of questions
        if len(questions) != state.num_questions:
            logger.warning(
                f"Generated {len(questions)} questions but requested {state.num_questions}. "
                "Adjusting to match request."
            )

            if len(questions) > state.num_questions:
                # Truncate if we got too many
                questions = questions[: state.num_questions]
                logger.info(f"Truncated to {state.num_questions} questions")
            else:
                # Could implement retry logic here if needed, but structured output is typically more reliable
                logger.warning(
                    f"Only got {len(questions)} questions, proceeding with available questions"
                )

        # Convert to QAPair format for workflow state
        qa_pairs = [
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

        logger.info(f"Successfully created {len(qa_pairs)} QA pairs")
        return {"qa_pairs": qa_pairs}

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

        # Context-aware tracing configuration (computed once per batch)
        config_dict = langfuse_manager.get_config()

        for qa_pair in state.qa_pairs:
            # Create prompts for each question
            system_prompt = create_answer_system_prompt(state)
            user_prompt = create_answer_user_prompt(state, qa_pair.question)

            messages = [
                SystemMessage(content=system_prompt),
                HumanMessage(content=user_prompt),
            ]

            response = llm_client.invoke(messages, config=config_dict)

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


def run_interview_prep_workflow(
    initial_state: InterviewPrepState, config: Optional[Dict[str, Any]] = None
) -> Dict[str, Any]:
    """Run the interview preparation workflow with Langfuse tracing.

    Args:
        initial_state: The initial workflow state
        config: Optional additional configuration for workflow execution

    Returns:
        Final workflow state as a dict
    """
    logger.info("Starting interview preparation workflow")

    try:
        workflow = get_interview_prep_workflow()

        # Configure context-aware Langfuse tracing for the workflow
        execution_config = langfuse_manager.get_workflow_config(config)

        # Run workflow
        final_state_dict = workflow.invoke(initial_state, config=execution_config)

        logger.info("Interview preparation workflow completed successfully")
        return final_state_dict

    except Exception as e:
        logger.error(f"Interview preparation workflow failed: {e}")
        return {"error": f"Workflow execution failed: {str(e)}"}
