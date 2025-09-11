"""Question Agent for multi-agent interview preparation workflow."""

from typing import Any, Dict, List

from src.agent.agents.common.base import BaseAgent
from src.agent.prompts.interview.question_generation import (
    QUESTION_SYSTEM_PROMPT,
    QUESTION_USER_PROMPT_TEMPLATE,
)
from src.agent.workflows.interview_prep.multi_agent_states import (
    AgentStatus,
    MultiAgentInterviewPrepState,
    WorkflowPhase,
)
from src.models.interview import (
    AnswerItem,
    AnswerStyle,
    InterviewQuestions,
    QAPair,
    QuestionCategory,
)


class QuestionAgent(BaseAgent):
    """Question Agent that generates research-informed interview questions."""

    def __init__(self):
        """Initialize the Question Agent."""
        super().__init__(name="question_agent")

    def check_prerequisites(self, state: MultiAgentInterviewPrepState) -> bool:
        """Check if question generation prerequisites are met.

        Args:
            state: Current multi-agent workflow state

        Returns:
            True if question strategy is available
        """
        return bool(state.question_strategy)

    def handle_missing_prerequisites(
        self, state: MultiAgentInterviewPrepState
    ) -> Dict[str, Any]:
        """Handle missing question strategy by using fallback.

        Args:
            state: Current multi-agent workflow state

        Returns:
            Fallback question generation results
        """
        self.logger.warning("No question strategy from planner, using fallback")
        return self._fallback_question_generation(state)

    def has_fallback(self) -> bool:
        """Question agent has fallback to original approach.

        Returns:
            True
        """
        return True

    def execute_fallback(self, state: MultiAgentInterviewPrepState) -> Dict[str, Any]:
        """Execute fallback question generation.

        Args:
            state: Current multi-agent workflow state

        Returns:
            Fallback question generation results
        """
        return self._fallback_question_generation(state)

    def execute(self, state: MultiAgentInterviewPrepState) -> Dict[str, Any]:
        """Generate research-informed interview questions.

        Args:
            state: Current multi-agent workflow state

        Returns:
            Dict containing QA pairs and question analysis
        """
        state.current_phase = WorkflowPhase.QUESTION_GENERATION

        research_summary = self._create_research_summary(state.research_results or [])
        research_insights = self._extract_research_insights(state)
        questions = self._generate_research_informed_questions(
            state, research_summary, research_insights
        )
        question_analysis = self._analyze_generated_questions(questions, state)

        qa_pairs = [
            QAPair(
                question=q,
                answer=AnswerItem(
                    question=q.question,
                    answer="",
                    style=self._determine_answer_style(q.category),
                ),
            )
            for q in questions
        ]

        state.question_analysis = question_analysis

        self.logger.info(f"Generated {len(qa_pairs)} research-informed questions")

        return {
            "qa_pairs": qa_pairs,
            "question_analysis": question_analysis,
        }

    def _generate_research_informed_questions(
        self, state, research_summary, research_insights
    ):
        """Generate questions using research context and planner strategy.

        Args:
            state: Current multi-agent workflow state
            research_summary: Summary of research findings
            research_insights: Extracted research insights

        Returns:
            List of generated questions
        """
        question_strategy = state.question_strategy
        resume_context = self.prepare_resume_context(state)
        question_mix_str = self._format_question_mix(
            state.interview_details.question_mix
        )

        user_prompt = QUESTION_USER_PROMPT_TEMPLATE.format(
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

        result = self.invoke_llm(
            system_prompt=QUESTION_SYSTEM_PROMPT,
            user_prompt=user_prompt,
            structured_output=InterviewQuestions,
        )

        questions = (
            result.questions
            if hasattr(result, "questions")
            else result.get("questions", [])
        )
        self.logger.info(f"Generated {len(questions)} intelligent questions")

        if len(questions) != state.num_questions:
            self.logger.warning(
                f"Generated {len(questions)} questions but requested {state.num_questions}"
            )
            if len(questions) > state.num_questions:
                questions = questions[: state.num_questions]

        return questions

    def _fallback_question_generation(self, state):
        """Fallback to original question generation.

        Args:
            state: Current multi-agent workflow state

        Returns:
            Fallback question generation results
        """
        from src.agent.workflows.interview_prep.main import generate_questions

        result = generate_questions(state)
        state.set_agent_status("question_agent", AgentStatus.COMPLETED)
        result["agent_status"] = state.agent_status
        return result

    def _create_research_summary(self, research_results):
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

    def _extract_research_insights(self, state):
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

            insights["recommendations"] = analysis.get(
                "recommendations_for_questions", []
            )

        return insights

    def _analyze_generated_questions(self, questions, state):
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
                term in q_text
                for term in ["research", "recent", "specific", "particular"]
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

    def _format_question_mix(self, question_mix):
        """Format question mix for display."""
        return ", ".join(
            [
                f"{category.replace('_', ' ').title()}: {count}"
                for category, count in question_mix.items()
                if count > 0
            ]
        )

    def _format_research_insights(self, insights):
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

    def _determine_answer_style(self, category):
        """Determine answer style based on question category.

        Args:
            category: Question category

        Returns:
            Appropriate answer style
        """
        if category == QuestionCategory.BEHAVIORAL:
            return AnswerStyle.STAR
        elif category in [QuestionCategory.TECHNICAL, QuestionCategory.SITUATIONAL]:
            return AnswerStyle.DETAILED
        else:
            return AnswerStyle.CONCISE


# Create singleton instance for backward compatibility
question_agent_instance = QuestionAgent()


def question_agent(state: MultiAgentInterviewPrepState) -> Dict[str, Any]:
    """
    Backward compatible function interface for question agent.

    Args:
        state: Current multi-agent workflow state

    Returns:
        Dict containing QA pairs and question analysis
    """
    return question_agent_instance(state)
