"""
Job evaluation workflow implementation using the new agent architecture.

This workflow uses the new structured extraction system while maintaining
compatibility with existing business logic and UI expectations.
"""

import time
from typing import Any, Dict

from langgraph.graph import END, START, StateGraph

from src.agent.agents.extraction.job_extraction_agent import JobExtractionAgent
from src.agent.workflows.job_evaluation.states import (
    JobEvaluationWorkflowState,
    add_message,
    create_initial_state,
    get_extracted_info_as_dict,
    is_extraction_successful,
)
from src.core.job_evaluation import evaluate_job_against_criteria
from src.llm.langfuse_handler import get_langfuse_handler
from src.utils.logging import get_logger

logger = get_logger(__name__)


class JobEvaluationWorkflow:
    """
    Job evaluation workflow using the new agent architecture.

    This workflow replaces the old manual JSON parsing approach with
    structured outputs while maintaining all existing business logic.
    """

    def __init__(self):
        """Initialize the workflow."""
        self._extraction_agent = None
        self._workflow = None

    def _get_extraction_agent(self) -> JobExtractionAgent:
        """Get or create the extraction agent."""
        if self._extraction_agent is None:
            self._extraction_agent = JobExtractionAgent()
            logger.debug("Initialized JobExtractionAgent")
        return self._extraction_agent

    def extract_job_info(
        self, state: JobEvaluationWorkflowState
    ) -> JobEvaluationWorkflowState:
        """
        Extract job information using the new tool-calling agent.

        Args:
            state: Current workflow state

        Returns:
            JobEvaluationWorkflowState: Updated state with extraction results
        """
        start_time = time.time()
        job_text = state["job_posting_text"]
        langfuse_handler = state.get("langfuse_handler")

        logger.info("Starting job information extraction with tool-calling agent")

        try:
            # Use the new extraction agent with tool calling
            extraction_agent = self._get_extraction_agent()
            extracted_info = extraction_agent.extract(job_text, langfuse_handler)

            extraction_duration = time.time() - start_time

            logger.info(
                f"Successfully extracted job information in {extraction_duration:.2f}s: {extracted_info}"
            )

            # Add success message
            updated_state = add_message(
                state,
                role="extraction",
                content="Tool-calling extraction completed successfully",
                metadata={
                    "extraction_agent": "JobExtractionAgent",
                    "duration": extraction_duration,
                    "schema_version": "JobPostingExtractionSchema",
                    "tools_used": extraction_agent.get_available_tools(),
                },
            )

            return {
                **updated_state,
                "extracted_info": extracted_info,
                "extraction_duration": extraction_duration,
            }

        except Exception as e:
            extraction_duration = time.time() - start_time
            logger.error(f"Failed to extract job information: {e}")

            # Add error message
            updated_state = add_message(
                state,
                role="extraction",
                error=str(e),
                metadata={
                    "extraction_agent": "JobExtractionAgent",
                    "duration": extraction_duration,
                },
            )

            return {
                **updated_state,
                "extracted_info": None,
                "extraction_duration": extraction_duration,
            }

    def evaluate_job(
        self, state: JobEvaluationWorkflowState
    ) -> JobEvaluationWorkflowState:
        """
        Evaluate job against criteria using existing business logic.

        Args:
            state: Current workflow state

        Returns:
            JobEvaluationWorkflowState: Updated state with evaluation results
        """
        start_time = time.time()

        if not is_extraction_successful(state):
            logger.error("Cannot evaluate job: extraction failed")

            # Add error message
            updated_state = add_message(
                state,
                role="evaluation",
                error="Failed to extract job information",
                metadata={"evaluator": "evaluate_job_against_criteria"},
            )

            return {
                **updated_state,
                "evaluation_result": {"error": "Failed to extract job information"},
                "evaluation_duration": time.time() - start_time,
            }

        try:
            # Convert extracted info to dictionary format for backward compatibility
            extracted_info_dict = get_extracted_info_as_dict(state)

            logger.info("Starting job evaluation against criteria")

            # Use existing core business logic - no changes needed!
            evaluation_result = evaluate_job_against_criteria(extracted_info_dict)

            evaluation_duration = time.time() - start_time

            logger.info(
                f"Job evaluation completed in {evaluation_duration:.2f}s: {evaluation_result}"
            )

            # Add success message
            updated_state = add_message(
                state,
                role="evaluation",
                content="Job evaluation completed successfully",
                metadata={
                    "evaluator": "evaluate_job_against_criteria",
                    "duration": evaluation_duration,
                    "criteria_count": len(evaluation_result),
                },
            )

            return {
                **updated_state,
                "evaluation_result": evaluation_result,
                "evaluation_duration": evaluation_duration,
            }

        except Exception as e:
            evaluation_duration = time.time() - start_time
            logger.error(f"Failed to evaluate job: {e}")

            # Add error message
            updated_state = add_message(
                state,
                role="evaluation",
                error=str(e),
                metadata={
                    "evaluator": "evaluate_job_against_criteria",
                    "duration": evaluation_duration,
                },
            )

            return {
                **updated_state,
                "evaluation_result": {"error": f"Evaluation failed: {str(e)}"},
                "evaluation_duration": evaluation_duration,
            }

    def _create_workflow(self) -> StateGraph:
        """Create the LangGraph workflow."""
        if self._workflow is None:
            # Initialize workflow with new state
            workflow = StateGraph(JobEvaluationWorkflowState)

            # Add nodes - same structure as before but with new implementations
            workflow.add_node("extract_info", self.extract_job_info)
            workflow.add_node("evaluate", self.evaluate_job)

            # Add edges - same flow as before
            workflow.add_edge(START, "extract_info")
            workflow.add_edge("extract_info", "evaluate")
            workflow.add_edge("evaluate", END)

            # Compile the graph
            self._workflow = workflow.compile()

            logger.info("Compiled job evaluation workflow with new agent architecture")

        return self._workflow

    def run(
        self, job_posting_text: str, langfuse_handler: Any = None
    ) -> JobEvaluationWorkflowState:
        """
        Run the complete job evaluation workflow.

        Args:
            job_posting_text: Raw job posting text to evaluate
            langfuse_handler: Optional Langfuse handler for tracing

        Returns:
            JobEvaluationWorkflowState: Final workflow state with results
        """
        logger.info("Starting job evaluation workflow")

        # Create initial state
        initial_state = create_initial_state(job_posting_text, langfuse_handler)

        # Get workflow
        workflow = self._create_workflow()

        try:
            # Run the workflow
            final_state = workflow.invoke(initial_state)

            logger.info("Job evaluation workflow completed successfully")
            return final_state

        except Exception as e:
            logger.error(f"Job evaluation workflow failed: {e}")

            # Return state with error
            error_state = add_message(
                initial_state,
                role="workflow",
                error=str(e),
                metadata={"workflow_version": "2.0"},
            )

            return {
                **error_state,
                "evaluation_result": {"error": f"Workflow failed: {str(e)}"},
            }


def create_job_evaluation_workflow() -> JobEvaluationWorkflow:
    """
    Create a new job evaluation workflow instance.

    Returns:
        JobEvaluationWorkflow: New workflow instance
    """
    return JobEvaluationWorkflow()


# Backward compatibility functions for existing code
def generate_recommendation_from_results(
    evaluation_results: Dict[str, Any],
) -> tuple[str, str]:
    """
    Generate final recommendation and reasoning from evaluation results.

    This function maintains backward compatibility with existing code.

    Args:
        evaluation_results: Dictionary with evaluation results for each criteria

    Returns:
        tuple[str, str]: (recommendation, reasoning)
    """
    if not evaluation_results or "error" in evaluation_results:
        return "DO_NOT_APPLY", "Unable to evaluate job posting due to extraction errors"

    # Check if all criteria pass
    all_pass = all(
        result.get("pass", False)
        for result in evaluation_results.values()
        if isinstance(result, dict)
    )

    if all_pass:
        recommendation = "APPLY"
        reasoning = "All criteria met: " + "; ".join(
            [
                result["reason"]
                for result in evaluation_results.values()
                if isinstance(result, dict) and result.get("pass")
            ]
        )
    else:
        recommendation = "DO_NOT_APPLY"
        failed_reasons = [
            result["reason"]
            for result in evaluation_results.values()
            if isinstance(result, dict) and not result.get("pass")
        ]
        reasoning = "Failed criteria: " + "; ".join(failed_reasons)

    return recommendation, reasoning
