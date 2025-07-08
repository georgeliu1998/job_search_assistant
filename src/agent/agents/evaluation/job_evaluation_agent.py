"""
Job evaluation agent implementation.

This agent specializes in evaluating job postings against predefined criteria
and can be reused across different workflows.
"""

from typing import Any, Dict

from pydantic import BaseModel, Field

from src.agent.agents.base import Agent, AgentResult
from src.core.job_evaluation import evaluate_job_against_criteria
from src.models.job import JobPostingExtractionSchema
from src.utils.logging import get_logger

logger = get_logger(__name__)


class JobEvaluationInput(BaseModel):
    """Input for job evaluation agent."""

    extracted_info: JobPostingExtractionSchema = Field(
        ..., description="Structured job information to evaluate"
    )
    # Future: Could add custom criteria here
    # custom_criteria: Optional[Dict[str, Any]] = Field(None, description="Custom evaluation criteria")


class JobEvaluationOutput(BaseModel):
    """Output from job evaluation agent."""

    evaluation_result: Dict[str, Any] = Field(
        ..., description="Detailed evaluation results for each criterion"
    )
    recommendation: str = Field(
        ..., description="Final recommendation (APPLY/DO_NOT_APPLY)"
    )
    reasoning: str = Field(
        ..., description="Human-readable explanation of the recommendation"
    )
    passed_criteria: int = Field(..., description="Number of criteria that passed")
    total_criteria: int = Field(..., description="Total number of criteria evaluated")


class JobEvaluationAgent(Agent[JobEvaluationInput, JobEvaluationOutput]):
    """Specialized agent for evaluating job postings against criteria."""

    def __init__(self):
        super().__init__(
            name="job_evaluation_agent",
            description="Evaluates job postings against predefined criteria to generate recommendations",
        )

    async def execute(
        self, input_data: JobEvaluationInput
    ) -> AgentResult[JobEvaluationOutput]:
        """
        Execute job evaluation against predefined criteria.

        Args:
            input_data: Job evaluation input containing extracted job info

        Returns:
            AgentResult with evaluation results and recommendation
        """
        logger.info(f"Agent {self.name}: Starting job evaluation")

        try:
            # Convert extracted info to dict format for the core evaluation function
            extracted_info_dict = input_data.extracted_info.model_dump()
            logger.debug(f"Evaluating job info: {extracted_info_dict}")

            # Evaluate against criteria using core logic
            evaluation_result = evaluate_job_against_criteria(extracted_info_dict)
            logger.info(f"Job evaluation completed: {evaluation_result}")

            # Generate recommendation and reasoning
            recommendation, reasoning, passed_count, total_count = (
                self._generate_recommendation(evaluation_result)
            )

            # Create output
            output = JobEvaluationOutput(
                evaluation_result=evaluation_result,
                recommendation=recommendation,
                reasoning=reasoning,
                passed_criteria=passed_count,
                total_criteria=total_count,
            )

            return AgentResult[JobEvaluationOutput](
                success=True,
                data=output,
                metadata={
                    "agent": self.name,
                    "passed_criteria": passed_count,
                    "total_criteria": total_count,
                    "recommendation": recommendation,
                },
            )

        except Exception as e:
            logger.error(f"Agent {self.name}: Failed to evaluate job: {e}")
            return AgentResult[JobEvaluationOutput](
                success=False,
                error=str(e),
                metadata={
                    "agent": self.name,
                    "error_type": type(e).__name__,
                },
            )

    def _generate_recommendation(
        self, evaluation_results: Dict[str, Any]
    ) -> tuple[str, str, int, int]:
        """
        Generate recommendation and reasoning from evaluation results.

        Args:
            evaluation_results: Dictionary with evaluation results for each criteria

        Returns:
            tuple: (recommendation, reasoning, passed_count, total_count)
        """
        if not evaluation_results or "error" in evaluation_results:
            return (
                "DO_NOT_APPLY",
                "Unable to evaluate job posting due to evaluation errors",
                0,
                0,
            )

        # Count passed and total criteria
        passed_criteria = []
        failed_criteria = []

        for criterion, result in evaluation_results.items():
            if isinstance(result, dict):
                if result.get("pass", False):
                    passed_criteria.append(f"{criterion}: {result['reason']}")
                else:
                    failed_criteria.append(f"{criterion}: {result['reason']}")

        passed_count = len(passed_criteria)
        total_count = len(passed_criteria) + len(failed_criteria)

        # Generate recommendation
        if passed_count == total_count:
            recommendation = "APPLY"
            reasoning = f"All {total_count} criteria passed: " + "; ".join(
                passed_criteria
            )
        else:
            recommendation = "DO_NOT_APPLY"
            if failed_criteria:
                reasoning = (
                    f"Failed {len(failed_criteria)} of {total_count} criteria: "
                    + "; ".join(failed_criteria)
                )
            else:
                reasoning = f"Only {passed_count} of {total_count} criteria passed"

        return recommendation, reasoning, passed_count, total_count
