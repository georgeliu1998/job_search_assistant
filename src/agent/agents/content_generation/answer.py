"""Answer Agent for multi-agent interview preparation workflow."""

import logging
from typing import Any, Dict, List

from langchain_core.messages import HumanMessage, SystemMessage

from src.agent.prompts.interview.answer_generation import (
    ANSWER_SYSTEM_PROMPT,
    ANSWER_USER_PROMPT_TEMPLATE,
)
from src.agent.workflows.interview_prep.multi_agent_states import (
    AgentStatus,
    MultiAgentInterviewPrepState,
    WorkflowPhase,
)
from src.config import config
from src.llm.common.factory import get_llm_client_by_profile_name
from src.llm.observability import langfuse_manager
from src.models.interview import AnswerItem, AnswerStyle, QAPair, QuestionCategory

logger = logging.getLogger(__name__)


def answer_agent(state: MultiAgentInterviewPrepState) -> Dict[str, Any]:
    """Intelligent Answer Agent that generates personalized interview answers."""
    logger.info("Answer Agent: Starting intelligent answer generation")

    if state.has_errors:
        logger.info("Answer Agent: Skipping due to previous errors")
        return {}

    if not state.qa_pairs:
        logger.warning("Answer Agent: No questions available for answer generation")
        return {"error": "No questions available for answer generation"}

    if not state.answer_strategy:
        logger.warning("Answer Agent: No answer strategy from planner")
        return _fallback_answer_generation(state)

    try:
        state.set_agent_status("answer_agent", AgentStatus.IN_PROGRESS)
        state.current_agent = "answer_agent"
        state.current_phase = WorkflowPhase.ANSWER_GENERATION

        resume_mapping = _create_resume_experience_mapping(state)
        updated_qa_pairs = _generate_personalized_answers(state, resume_mapping)
        answer_analysis = _analyze_answer_quality(updated_qa_pairs, state)

        state.set_agent_status("answer_agent", AgentStatus.COMPLETED)
        state.resume_mapping = resume_mapping

        logger.info(
            f"Answer Agent: Generated personalized answers for {len(updated_qa_pairs)} questions"
        )

        return {
            "qa_pairs": updated_qa_pairs,
            "resume_mapping": resume_mapping,
            "answer_analysis": answer_analysis,
            "agent_status": state.agent_status,
        }

    except Exception as e:
        logger.error(f"Answer Agent failed: {e}", exc_info=True)
        state.set_agent_error("answer_agent", f"Answer generation failed: {str(e)}")
        return _fallback_answer_generation(state)


def _generate_personalized_answers(state, resume_mapping):
    """Generate personalized answers for each question."""
    logger.info("Answer Agent: Generating personalized answers with resume mapping")

    updated_qa_pairs = []
    llm_client = get_llm_client_by_profile_name(
        config.agents.interview_answer_generation
    )
    config_dict = langfuse_manager.get_config()

    # Prepare common context
    research_context = _create_research_context_for_answers(state)
    resume_context = _prepare_resume_context(state)
    job_focus = _extract_job_focus_areas(state.job_description)
    question_insights = (
        _format_question_insights(state.question_analysis)
        if state.question_analysis
        else ""
    )

    for qa_pair in state.qa_pairs:
        try:
            logger.debug(
                f"Answer Agent: Generating personalized answer for: {qa_pair.question.question[:50]}..."
            )

            system_message = SystemMessage(content=ANSWER_SYSTEM_PROMPT)
            user_message = HumanMessage(
                content=ANSWER_USER_PROMPT_TEMPLATE.format(
                    question_text=qa_pair.question.question,
                    question_category=qa_pair.question.category,
                    question_difficulty=qa_pair.question.difficulty,
                    question_rationale=getattr(
                        qa_pair.question, "rationale", "Not specified"
                    ),
                    experience_highlights=resume_mapping.get(
                        "experience_highlights", []
                    ),
                    skill_demonstration_opportunities=resume_mapping.get(
                        "skill_to_experience_map", {}
                    ),
                    storytelling_approach=state.answer_strategy.get(
                        "storytelling_approach", "star_method"
                    ),
                    answer_length_preference=state.answer_strategy.get(
                        "answer_length_preference", "detailed"
                    ),
                    include_metrics=state.answer_strategy.get("include_metrics", True),
                    company_values_integration=state.answer_strategy.get(
                        "company_values_integration", []
                    ),
                    company=state.interview_details.company or "Not specified",
                    role=state.interview_details.role or "Not specified",
                    job_focus=job_focus,
                    research_context=research_context,
                    resume_context=resume_context,
                    question_insights=question_insights,
                )
            )

            response = llm_client.invoke(
                [system_message, user_message], config=config_dict
            )
            answer_text = (
                response.content if hasattr(response, "content") else str(response)
            )

            answer_style = _determine_intelligent_answer_style(
                qa_pair.question.category, state.answer_strategy
            )

            updated_answer = AnswerItem(
                question=qa_pair.question.question,
                answer=answer_text,
                style=answer_style,
            )

            updated_qa_pair = QAPair(
                question=qa_pair.question,
                answer=updated_answer,
            )

            updated_qa_pairs.append(updated_qa_pair)

        except Exception as e:
            logger.error(
                f"Failed to generate answer for question '{qa_pair.question.question[:50]}...': {e}"
            )
            updated_qa_pairs.append(qa_pair)

    return updated_qa_pairs


def _create_resume_experience_mapping(state):
    """Create intelligent mapping of resume experiences to skill areas."""
    resume_text = (
        state.pii_redaction_result.redacted_resume_text
        if state.pii_redaction_result
        else state.resume_text
    )
    answer_strategy = state.answer_strategy

    mapping = {
        "technical_experiences": [],
        "leadership_experiences": [],
        "problem_solving_experiences": [],
        "collaboration_experiences": [],
        "achievement_metrics": [],
        "skill_to_experience_map": answer_strategy.get(
            "skill_demonstration_opportunities", {}
        ),
        "experience_highlights": answer_strategy.get("experience_highlights", []),
    }

    if not mapping["experience_highlights"]:
        mapping["experience_highlights"] = _extract_experiences_from_resume(resume_text)

    mapping["achievement_metrics"] = _extract_metrics_from_resume(resume_text)
    return mapping


def _analyze_answer_quality(qa_pairs, state):
    """Analyze the quality of generated answers."""
    analysis = {
        "total_answers": len(qa_pairs),
        "personalization_score": 0,
        "company_integration_score": 0,
        "metrics_inclusion_score": 0,
        "star_method_usage": 0,
        "quality_insights": [],
        "needs_better_questions": False,
    }

    company_name = state.interview_details.company or ""
    metrics_count = 0
    star_usage = 0
    personalization_indicators = 0

    for qa_pair in qa_pairs:
        if not qa_pair.answer or not qa_pair.answer.answer:
            continue

        answer_text = qa_pair.answer.answer.lower()

        if company_name.lower() in answer_text:
            analysis["company_integration_score"] += 1

        import re

        if re.search(r"\d+%|\d+\+|\$\d+|increased|improved|reduced|grew", answer_text):
            metrics_count += 1

        if any(
            indicator in answer_text
            for indicator in [
                "situation",
                "task",
                "action",
                "result",
                "when",
                "then",
                "outcome",
            ]
        ):
            star_usage += 1

        if any(
            indicator in answer_text
            for indicator in [
                "i",
                "my experience",
                "in my role",
                "at my previous",
                "i worked",
            ]
        ):
            personalization_indicators += 1

    total_answers = max(len(qa_pairs), 1)
    analysis["company_integration_score"] = min(
        100, (analysis["company_integration_score"] / total_answers) * 100
    )
    analysis["metrics_inclusion_score"] = min(
        100, (metrics_count / total_answers) * 100
    )
    analysis["star_method_usage"] = min(100, (star_usage / total_answers) * 100)
    analysis["personalization_score"] = min(
        100, (personalization_indicators / total_answers) * 100
    )

    if analysis["personalization_score"] > 80:
        analysis["quality_insights"].append(
            "Strong personalization with specific experience references"
        )
    elif analysis["personalization_score"] < 50:
        analysis["quality_insights"].append(
            "Answers could be more personalized with specific examples"
        )

    if analysis["company_integration_score"] > 60:
        analysis["quality_insights"].append(
            "Good integration of company-specific context"
        )

    if analysis["metrics_inclusion_score"] > 70:
        analysis["quality_insights"].append(
            "Excellent use of quantifiable achievements"
        )

    if (
        analysis["personalization_score"] < 40
        and analysis["company_integration_score"] < 30
    ):
        analysis["needs_better_questions"] = True

    return analysis


def _fallback_answer_generation(state):
    """Fallback to original answer generation."""
    from src.agent.workflows.interview_prep.main import generate_answers

    result = generate_answers(state)
    state.set_agent_status("answer_agent", AgentStatus.COMPLETED)
    result["agent_status"] = state.agent_status
    return result


def _extract_experiences_from_resume(resume_text):
    """Extract key experiences from resume text."""
    experiences = []
    lines = resume_text.split("\n")
    for line in lines:
        line = line.strip()
        if len(line) > 30 and (
            "led" in line.lower()
            or "managed" in line.lower()
            or "built" in line.lower()
            or "developed" in line.lower()
            or "implemented" in line.lower()
            or "created" in line.lower()
        ):
            experiences.append(line)
    return experiences[:5]


def _extract_metrics_from_resume(resume_text):
    """Extract quantifiable metrics from resume text."""
    import re

    metrics = []
    patterns = [
        r"\d+%",
        r"\d+\+",
        r"\$\d+",
        r"\d+\s*(users|customers|developers|people|team|members)",
        r"(increased|improved|reduced|grew)\s*\w*\s*by\s*\d+",
    ]

    for pattern in patterns:
        matches = re.findall(pattern, resume_text, re.IGNORECASE)
        metrics.extend(matches[:2])

    return metrics[:5]


def _create_research_context_for_answers(state):
    """Create research context for answer generation."""
    if not state.research_results:
        return "No specific company research available."

    context_parts = ["Relevant Company Information:"]
    accessible_results = [r for r in state.research_results if r.is_accessible]
    for i, citation in enumerate(accessible_results[:3], 1):
        context_parts.append(f"{i}. {citation.title}")
        if len(citation.content_snippet) > 50:
            context_parts.append(f"   Key insight: {citation.content_snippet[:150]}...")

    return "\n".join(context_parts)


def _prepare_resume_context(state):
    """Prepare resume context for answer generation."""
    if state.pii_redaction_result:
        return state.pii_redaction_result.redacted_resume_text
    return state.resume_text


def _extract_job_focus_areas(job_description):
    """Extract key focus areas from job description."""
    focus_areas = []
    lines = job_description.split("\n")

    for line in lines:
        line = line.strip()
        if any(
            keyword in line.lower()
            for keyword in ["require", "must", "should", "need", "responsible"]
        ):
            if len(line) > 20:
                focus_areas.append(line)

    return "; ".join(focus_areas[:3]) if focus_areas else "General role requirements"


def _format_question_insights(question_analysis):
    """Format question analysis insights for answer context."""
    if not question_analysis:
        return "No question analysis available."

    insights = []

    if question_analysis.get("company_specificity_score", 0) > 50:
        insights.append(
            "Questions show strong company focus - reference specific company context"
        )

    if question_analysis.get("research_integration_score", 0) > 30:
        insights.append(
            "Questions incorporate research findings - demonstrate preparation"
        )

    recommendations = question_analysis.get("recommendations_for_answers", [])
    insights.extend(recommendations)

    return (
        "; ".join(insights)
        if insights
        else "General interview questions - focus on clear examples"
    )


def _determine_intelligent_answer_style(category, answer_strategy):
    """Determine answer style based on question category and strategy."""
    storytelling_approach = answer_strategy.get("storytelling_approach", "star_method")

    if category == QuestionCategory.BEHAVIORAL:
        return (
            AnswerStyle.STAR
            if storytelling_approach == "star_method"
            else AnswerStyle.DETAILED
        )
    elif category in [QuestionCategory.TECHNICAL, QuestionCategory.SITUATIONAL]:
        return AnswerStyle.DETAILED
    else:
        return AnswerStyle.CONCISE
