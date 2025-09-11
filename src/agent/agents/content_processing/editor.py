"""Editor Agent for multi-agent interview preparation workflow."""

from typing import Any, Dict, List

from src.agent.agents.common.base import BaseAgent
from src.agent.prompts.interview.editor import (
    EDITOR_SYSTEM_PROMPT,
    EDITOR_USER_PROMPT_TEMPLATE,
)
from src.agent.workflows.interview_prep.multi_agent_states import (
    AgentStatus,
    MultiAgentInterviewPrepState,
    WorkflowPhase,
)
from src.models.interview import InterviewGuide


class EditorAgent(BaseAgent):
    """Editor Agent that synthesizes and validates the complete interview guide."""

    def __init__(self):
        """Initialize the Editor Agent."""
        super().__init__(name="editor_agent")

    def check_prerequisites(self, state: MultiAgentInterviewPrepState) -> bool:
        """Check if editor prerequisites are met.

        Args:
            state: Current multi-agent workflow state

        Returns:
            True if QA pairs are available
        """
        return bool(state.qa_pairs)

    def handle_missing_prerequisites(
        self, state: MultiAgentInterviewPrepState
    ) -> Dict[str, Any]:
        """Handle missing QA pairs.

        Args:
            state: Current multi-agent workflow state

        Returns:
            Error result
        """
        self.logger.warning("No QA pairs available for guide compilation")
        return {"error": "No QA pairs available for guide compilation"}

    def has_fallback(self) -> bool:
        """Editor agent has fallback to original approach.

        Returns:
            True
        """
        return True

    def execute_fallback(self, state: MultiAgentInterviewPrepState) -> Dict[str, Any]:
        """Execute fallback guide compilation.

        Args:
            state: Current multi-agent workflow state

        Returns:
            Fallback compilation results
        """
        return self._fallback_guide_compilation(state)

    def execute(self, state: MultiAgentInterviewPrepState) -> Dict[str, Any]:
        """Synthesize and validate the complete interview guide.

        Args:
            state: Current multi-agent workflow state

        Returns:
            Dict containing interview guide and quality assessment
        """
        state.current_phase = WorkflowPhase.COMPILATION

        quality_assessment = self._perform_comprehensive_quality_assessment(state)
        preparation_tips = self._generate_intelligent_preparation_tips(
            state, quality_assessment
        )
        research_summary = self._create_enhanced_research_summary(state)
        interview_guide = self._compile_intelligent_interview_guide(
            state, quality_assessment, preparation_tips, research_summary
        )
        final_quality_check = self._final_quality_validation(interview_guide, state)

        state.quality_assessment = quality_assessment

        self.logger.info("Successfully compiled intelligent interview guide")

        return {
            "interview_guide": interview_guide,
            "quality_assessment": quality_assessment,
            "final_quality_check": final_quality_check,
        }

    def _perform_comprehensive_quality_assessment(self, state):
        """Perform comprehensive assessment of all workflow components.

        Args:
            state: Current multi-agent workflow state

        Returns:
            Dict containing quality assessment
        """
        assessment = {
            "overall_quality_score": 0,
            "component_scores": {
                "research_quality": 0,
                "question_quality": 0,
                "answer_quality": 0,
                "integration_quality": 0,
            },
            "strengths": [],
            "improvement_areas": [],
            "critical_gaps": [],
            "recommendations": [],
        }

        # Assess research quality
        if state.research_analysis:
            coverage = state.research_analysis.get("coverage_quality", "unknown")
            if coverage == "high":
                assessment["component_scores"]["research_quality"] = 85
                assessment["strengths"].append(
                    "Excellent research coverage with accessible sources"
                )
            elif coverage == "medium":
                assessment["component_scores"]["research_quality"] = 65
                assessment["improvement_areas"].append(
                    "Research coverage is adequate but could be enhanced"
                )
            else:
                assessment["component_scores"]["research_quality"] = 40
                assessment["critical_gaps"].append(
                    "Limited research results - may impact question specificity"
                )

        # Assess question quality
        if state.question_analysis:
            company_specificity = state.question_analysis.get(
                "company_specificity_score", 0
            )
            research_integration = state.question_analysis.get(
                "research_integration_score", 0
            )

            question_score = (company_specificity + research_integration) / 2
            assessment["component_scores"]["question_quality"] = question_score

            if question_score > 70:
                assessment["strengths"].append(
                    "Questions show strong company focus and research integration"
                )
            elif question_score > 40:
                assessment["improvement_areas"].append(
                    "Questions are adequate but could be more company-specific"
                )
            else:
                assessment["critical_gaps"].append(
                    "Questions lack company specificity and research context"
                )

        # Assess answer quality
        if hasattr(state, "answer_analysis") and state.answer_analysis:
            personalization = state.answer_analysis.get("personalization_score", 0)
            company_integration = state.answer_analysis.get(
                "company_integration_score", 0
            )

            answer_score = (personalization + company_integration) / 2
            assessment["component_scores"]["answer_quality"] = answer_score

            if answer_score > 75:
                assessment["strengths"].append(
                    "Answers are highly personalized with strong company context"
                )
            elif answer_score > 50:
                assessment["improvement_areas"].append(
                    "Answers show good personalization but could integrate more company context"
                )
            else:
                assessment["critical_gaps"].append(
                    "Answers need better personalization and company context"
                )

        # Calculate overall integration score
        scores = list(assessment["component_scores"].values())
        integration_score = sum(scores) / len(scores) if scores else 0
        assessment["component_scores"]["integration_quality"] = integration_score
        assessment["overall_quality_score"] = integration_score

        # Generate recommendations
        if integration_score > 80:
            assessment["recommendations"].append(
                "Excellent preparation - focus on practice and confidence building"
            )
        elif integration_score > 60:
            assessment["recommendations"].append(
                "Good foundation - refine weak areas and enhance company context"
            )
        else:
            assessment["recommendations"].append(
                "Needs significant improvement - focus on research and personalization"
            )

        return assessment

    def _generate_intelligent_preparation_tips(self, state, quality_assessment):
        """Generate intelligent, context-aware preparation tips.

        Args:
            state: Current multi-agent workflow state
            quality_assessment: Quality assessment results

        Returns:
            List of preparation tips
        """
        self.logger.info("Generating intelligent preparation tips")

        try:
            compilation_strategy = state.compilation_strategy or {}

            user_prompt = EDITOR_USER_PROMPT_TEMPLATE.format(
                guide_format=compilation_strategy.get("guide_format", "comprehensive"),
                include_research_summary=compilation_strategy.get(
                    "include_research_summary", True
                ),
                include_preparation_tips=compilation_strategy.get(
                    "include_preparation_tips", True
                ),
                quality_checks=compilation_strategy.get("quality_checks", []),
                personalization_elements=compilation_strategy.get(
                    "personalization_elements", []
                ),
                company=state.interview_details.company or "Not specified",
                role=state.interview_details.role or "Not specified",
                interview_type=state.interview_details.type,
                duration=state.interview_details.duration,
                research_coverage=(
                    state.research_analysis.get("coverage_quality", "unknown")
                    if state.research_analysis
                    else "unknown"
                ),
                total_citations=len(state.research_results or []),
                research_key_findings=(
                    len(state.research_analysis.get("key_findings", []))
                    if state.research_analysis
                    else 0
                ),
                total_questions=len(state.qa_pairs or []),
                company_specificity_score=(
                    state.question_analysis.get("company_specificity_score", 0)
                    if state.question_analysis
                    else 0
                ),
                research_integration_score=(
                    state.question_analysis.get("research_integration_score", 0)
                    if state.question_analysis
                    else 0
                ),
                personalization_score=getattr(state, "answer_analysis", {}).get(
                    "personalization_score", 0
                ),
                company_integration_score=getattr(state, "answer_analysis", {}).get(
                    "company_integration_score", 0
                ),
                metrics_inclusion_score=getattr(state, "answer_analysis", {}).get(
                    "metrics_inclusion_score", 0
                ),
            )

            response = self.invoke_llm(
                system_prompt=EDITOR_SYSTEM_PROMPT, user_prompt=user_prompt
            )
            tips_content = (
                response.content if hasattr(response, "content") else str(response)
            )
            tips = self._parse_preparation_tips(tips_content)

            self.logger.info(f"Generated {len(tips)} intelligent preparation tips")
            return tips

        except Exception as e:
            self.logger.error(f"Failed to generate intelligent preparation tips: {e}")
            return self._generate_quality_based_tips(state, quality_assessment)

    def _create_enhanced_research_summary(self, state):
        """Create an enhanced research summary with strategic insights.

        Args:
            state: Current multi-agent workflow state

        Returns:
            Research summary string
        """
        if not state.research_results:
            return "No specific research conducted for this interview."

        summary_parts = ["Strategic Research Summary:"]

        if state.research_analysis:
            coverage = state.research_analysis.get("coverage_quality", "unknown")
            summary_parts.append(f"Research Coverage: {coverage.title()}")

        accessible_results = [r for r in state.research_results if r.is_accessible]
        summary_parts.append(
            f"\nKey Findings ({len(accessible_results)} sources verified):"
        )

        for i, citation in enumerate(accessible_results[:5], 1):
            summary_parts.append(f"{i}. {citation.title}")
            summary_parts.append(f"   Strategic insight: {citation.content_snippet}")
            summary_parts.append("")

        if state.research_analysis and state.research_analysis.get(
            "recommendations_for_questions"
        ):
            summary_parts.append("Strategic Application:")
            for rec in state.research_analysis["recommendations_for_questions"]:
                summary_parts.append(f"• {rec}")

        return "\n".join(summary_parts)

    def _compile_intelligent_interview_guide(
        self, state, quality_assessment, preparation_tips, research_summary
    ):
        """Compile the final intelligent interview guide.

        Args:
            state: Current multi-agent workflow state
            quality_assessment: Quality assessment results
            preparation_tips: List of preparation tips
            research_summary: Research summary string

        Returns:
            InterviewGuide object
        """
        return InterviewGuide(
            num_questions=state.num_questions,
            research_summary=research_summary,
            qa_pairs=state.qa_pairs or [],
            preparation_tips=preparation_tips,
            citations=state.research_results or [],
        )

    def _final_quality_validation(self, interview_guide, state):
        """Perform final quality validation on the compiled guide.

        Args:
            interview_guide: Compiled interview guide
            state: Current multi-agent workflow state

        Returns:
            Dict containing validation results
        """
        validation = {
            "completeness_score": 0,
            "quality_score": 0,
            "readiness_assessment": "needs_review",
            "validation_checks": {
                "has_questions": len(interview_guide.qa_pairs) > 0,
                "has_answers": any(
                    qa.answer and qa.answer.answer for qa in interview_guide.qa_pairs
                ),
                "has_research": len(interview_guide.citations) > 0,
                "has_preparation_tips": len(interview_guide.preparation_tips) > 0,
                "research_summary_exists": bool(interview_guide.research_summary),
            },
            "recommendations": [],
        }

        completed_checks = sum(
            1 for check in validation["validation_checks"].values() if check
        )
        validation["completeness_score"] = (
            completed_checks / len(validation["validation_checks"])
        ) * 100

        if validation["completeness_score"] >= 90:
            validation["quality_score"] = 85
            validation["readiness_assessment"] = "excellent"
            validation["recommendations"].append(
                "Guide is comprehensive and ready for use"
            )
        elif validation["completeness_score"] >= 70:
            validation["quality_score"] = 70
            validation["readiness_assessment"] = "good"
            validation["recommendations"].append(
                "Guide is solid with minor areas for enhancement"
            )
        else:
            validation["quality_score"] = 50
            validation["readiness_assessment"] = "needs_improvement"
            validation["recommendations"].append(
                "Guide needs significant improvements before use"
            )

        return validation

    def _fallback_guide_compilation(self, state):
        """Fallback to original guide compilation.

        Args:
            state: Current multi-agent workflow state

        Returns:
            Fallback compilation results
        """
        from src.agent.workflows.interview_prep.main import compile_guide

        result = compile_guide(state)
        state.set_agent_status("editor_agent", AgentStatus.COMPLETED)
        result["agent_status"] = state.agent_status
        return result

    def _parse_preparation_tips(self, content):
        """Parse preparation tips from LLM response.

        Args:
            content: LLM response content

        Returns:
            List of parsed preparation tips
        """
        tips = []
        lines = content.split("\n")

        for line in lines:
            line = line.strip()
            if (
                line.startswith("•")
                or line.startswith("-")
                or line.startswith("*")
                or (len(line) > 20 and line[0].isdigit() and "." in line[:5])
                or (len(line) > 30 and not line.endswith(":"))
            ):

                clean_tip = line.lstrip("•-*0123456789. ").strip()
                if len(clean_tip) > 15:
                    tips.append(clean_tip)

        if not tips:
            tips = [
                "Research the company's recent news, values, and culture thoroughly",
                "Prepare specific examples that demonstrate your key skills and achievements",
                "Practice your responses aloud to build confidence and natural delivery",
                "Prepare thoughtful questions that show your genuine interest in the role",
                "Plan to arrive early and test all technology for virtual interviews",
            ]

        return tips[:8]

    def _generate_quality_based_tips(self, state, quality_assessment):
        """Generate tips based on quality assessment when LLM generation fails.

        Args:
            state: Current multi-agent workflow state
            quality_assessment: Quality assessment results

        Returns:
            List of quality-based tips
        """
        tips = [
            "Research the company's recent news, values, and culture",
            "Prepare specific examples that demonstrate your key skills",
            "Practice your elevator pitch and 'tell me about yourself' response",
        ]

        if "Limited research results" in quality_assessment.get("critical_gaps", []):
            tips.append("Conduct additional company research using multiple sources")

        if (
            "company specificity"
            in str(quality_assessment.get("improvement_areas", [])).lower()
        ):
            tips.append(
                "Reference specific company initiatives and values in your answers"
            )

        interview_type = state.interview_details.type
        if interview_type == "hiring_manager":
            tips.extend(
                [
                    "Prepare to discuss how you'd contribute to team goals and company success",
                    "Think of examples that show leadership potential and cultural fit",
                ]
            )

        return tips


# Create singleton instance for backward compatibility
editor_agent_instance = EditorAgent()


def editor_agent(state: MultiAgentInterviewPrepState) -> Dict[str, Any]:
    """
    Backward compatible function interface for editor agent.

    Args:
        state: Current multi-agent workflow state

    Returns:
        Dict containing interview guide and quality assessment
    """
    return editor_agent_instance(state)
