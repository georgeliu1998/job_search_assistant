"""Question Agent for multi-agent interview preparation workflow."""

import logging
from typing import Any, Dict, List

from langchain_core.messages import HumanMessage, SystemMessage

from src.agent.prompts.interview.question_generation import (
    QUESTION_SYSTEM_PROMPT,
    QUESTION_USER_PROMPT_TEMPLATE,
)
from src.agent.workflows.interview_prep.multi_agent_states import (
    AgentStatus,
    MultiAgentInterviewPrepState,
    WorkflowPhase,
)
from src.config import config
from src.llm.common.factory import get_llm_client_by_profile_name
from src.llm.observability import langfuse_manager
from src.models.interview import AnswerItem, AnswerStyle, InterviewQuestions, QAPair

logger = logging.getLogger(__name__)


def question_agent(state: MultiAgentInterviewPrepState) -> Dict[str, Any]:
    """Intelligent Question Agent that generates research-informed interview questions."""
    logger.info("Question Agent: Starting intelligent question generation")

    if state.has_errors:
        logger.info("Question Agent: Skipping due to previous errors")
        return {}

    if not state.question_strategy:
        logger.warning("Question Agent: No question strategy from planner")
        return _fallback_question_generation(state)

    try:
        state.set_agent_status("question_agent", AgentStatus.IN_PROGRESS)
        state.current_agent = "question_agent"
        state.current_phase = WorkflowPhase.QUESTION_GENERATION

        research_summary = _create_research_summary(state.research_results or [])
        research_insights = _extract_research_insights(state)
        questions = _generate_research_informed_questions(
            state, research_summary, research_insights
        )
        question_analysis = _analyze_generated_questions(questions, state)

        qa_pairs = [
            QAPair(
                question=q,
                answer=AnswerItem(
                    question=q.question,
                    answer="",
                    style=_determine_answer_style(q.category),
                ),
            )
            for q in questions
        ]

        state.set_agent_status("question_agent", AgentStatus.COMPLETED)
        state.question_analysis = question_analysis

        logger.info(
            f"Question Agent: Generated {len(qa_pairs)} research-informed questions"
        )

        return {
            "qa_pairs": qa_pairs,
            "question_analysis": question_analysis,
            "agent_status": state.agent_status,
        }

    except Exception as e:
        logger.error(f"Question Agent failed: {e}", exc_info=True)
        state.set_agent_error("question_agent", f"Question generation failed: {str(e)}")
        return _fallback_question_generation(state)


def _generate_research_informed_questions(state, research_summary, research_insights):
    """Generate questions using research context and planner strategy."""
    llm_client = get_llm_client_by_profile_name(
        config.agents.interview_question_generation
    )
    structured_llm = llm_client._get_client().with_structured_output(InterviewQuestions)

    question_strategy = state.question_strategy
    resume_context = _prepare_resume_context(state)
    question_mix_str = _format_question_mix(state.interview_details.question_mix)

    system_message = SystemMessage(content=QUESTION_SYSTEM_PROMPT)
    user_message = HumanMessage(
        content=QUESTION_USER_PROMPT_TEMPLATE.format(
            job_description=state.job_description,
            company=state.interview_details.company or "Not specified",
            role=state.interview_details.role or "Not specified",
            interview_type=state.interview_details.type,
            focus_areas=question_strategy.get("focus_areas", []),
            difficulty_distribution=question_strategy.get(
                "difficulty_distribution", {}
            ),
            resume_focus_points=question_strategy.get("resume_focus_points", []),
            company_alignment_points=question_strategy.get(
                "company_alignment_points", []
            ),
            avoid_generic_questions=question_strategy.get(
                "avoid_generic_questions", True
            ),
            emphasize_practical_scenarios=question_strategy.get(
                "emphasize_practical_scenarios", False
            ),
            research_summary=research_summary,
            research_insights=_format_research_insights(research_insights),
            resume_context=resume_context,
            question_mix=question_mix_str,
            num_questions=state.num_questions,
        )
    )

    config_dict = langfuse_manager.get_config()
    result = structured_llm.invoke([system_message, user_message], config=config_dict)

    questions = (
        result.questions
        if hasattr(result, "questions")
        else result.get("questions", [])
    )
    logger.info(f"Question Agent: Generated {len(questions)} intelligent questions")

    if len(questions) != state.num_questions:
        logger.warning(
            f"Generated {len(questions)} questions but requested {state.num_questions}"
        )
        if len(questions) > state.num_questions:
            questions = questions[: state.num_questions]

    return questions


def _fallback_question_generation(state):
    """Fallback to original question generation."""
    from src.agent.workflows.interview_prep.main import generate_questions

    result = generate_questions(state)
    state.set_agent_status("question_agent", AgentStatus.COMPLETED)
    result["agent_status"] = state.agent_status
    return result


def _create_research_summary(research_results):
    """Create research summary for question context."""
    if not research_results:
        return "No specific research findings available."

    summary_parts = ["Key Research Findings:"]
    accessible_results = [r for r in research_results if r.is_accessible]

    for i, citation in enumerate(accessible_results[:5], 1):
        summary_parts.append(f"{i}. {citation.title}")
        summary_parts.append(f"   {citation.content_snippet}")
        summary_parts.append("")

    return "\n".join(summary_parts)


def _extract_research_insights(state):
    """Extract insights from research analysis."""
    insights = {
        "research_quality": "unknown",
        "company_specific_info": [],
        "role_specific_info": [],
        "technical_insights": [],
        "culture_insights": [],
        "recommendations": [],
    }

    if state.research_analysis:
        analysis = state.research_analysis
        insights["research_quality"] = analysis.get("coverage_quality", "unknown")

        key_findings = analysis.get("key_findings", [])
        for finding in key_findings:
            insight_text = finding.get("insight", "")

            if (
                state.interview_details.company
                and state.interview_details.company.lower() in insight_text.lower()
            ):
                insights["company_specific_info"].append(insight_text)
            elif any(
                term in insight_text.lower()
                for term in ["developer", "engineer", "technical"]
            ):
                insights["role_specific_info"].append(insight_text)

        insights["recommendations"] = analysis.get("recommendations_for_questions", [])

    return insights


def _analyze_generated_questions(questions, state):
    """Analyze generated questions for quality."""
    analysis = {
        "total_questions": len(questions),
        "category_distribution": {},
        "difficulty_distribution": {},
        "research_integration_score": 0,
        "company_specificity_score": 0,
        "recommendations_for_answers": [],
        "needs_more_research": False,
    }

    for question in questions:
        category = (
            question.category.value
            if hasattr(question.category, "value")
            else str(question.category)
        )
        analysis["category_distribution"][category] = (
            analysis["category_distribution"].get(category, 0) + 1
        )

        difficulty = (
            question.difficulty.value
            if hasattr(question.difficulty, "value")
            else str(question.difficulty)
        )
        analysis["difficulty_distribution"][difficulty] = (
            analysis["difficulty_distribution"].get(difficulty, 0) + 1
        )

    # Simple heuristic for research integration
    company_mentions = 0
    research_references = 0

    for question in questions:
        q_text = question.question.lower()
        if (
            state.interview_details.company
            and state.interview_details.company.lower() in q_text
        ):
            company_mentions += 1
        if any(
            term in q_text for term in ["research", "recent", "specific", "particular"]
        ):
            research_references += 1

    analysis["research_integration_score"] = (
        min(100, (research_references / len(questions)) * 100) if questions else 0
    )
    analysis["company_specificity_score"] = (
        min(100, (company_mentions / len(questions)) * 100) if questions else 0
    )

    if analysis["company_specificity_score"] > 50:
        analysis["recommendations_for_answers"].append(
            "Reference specific company context in answers"
        )

    if analysis["research_integration_score"] > 30:
        analysis["recommendations_for_answers"].append(
            "Use research findings to demonstrate preparation"
        )

    if (
        analysis["research_integration_score"] < 20
        and analysis["company_specificity_score"] < 30
    ):
        analysis["needs_more_research"] = True

    return analysis


def _prepare_resume_context(state):
    """Prepare resume context for question generation."""
    if state.pii_redaction_result:
        return state.pii_redaction_result.redacted_resume_text
    return state.resume_text


def _format_question_mix(question_mix):
    """Format question mix for display."""
    return ", ".join(
        [
            f"{category.replace('_', ' ').title()}: {count}"
            for category, count in question_mix.items()
            if count > 0
        ]
    )


def _format_research_insights(insights):
    """Format research insights for prompt context."""
    formatted_parts = []

    if insights["research_quality"] != "unknown":
        formatted_parts.append(f"Research Quality: {insights['research_quality']}")

    if insights["company_specific_info"]:
        formatted_parts.append("Company-Specific Information:")
        for info in insights["company_specific_info"][:3]:
            formatted_parts.append(f"- {info}")

    if insights["recommendations"]:
        formatted_parts.append("Research Recommendations:")
        for rec in insights["recommendations"][:3]:
            formatted_parts.append(f"- {rec}")

    return (
        "\n".join(formatted_parts)
        if formatted_parts
        else "No specific research insights available."
    )


def _determine_answer_style(category):
    """Determine answer style based on question category."""
    from src.models.interview import QuestionCategory

    if category == QuestionCategory.BEHAVIORAL:
        return AnswerStyle.STAR
    elif category in [QuestionCategory.TECHNICAL, QuestionCategory.SITUATIONAL]:
        return AnswerStyle.DETAILED
    else:
        return AnswerStyle.CONCISE
