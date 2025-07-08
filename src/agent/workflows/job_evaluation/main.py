"""
Defines the job evaluation workflow using a StateGraph.

This module provides the complete job evaluation workflow implementation,
including the public API function that serves as the main entry point.
"""

from typing import Any, Dict, Optional

from langgraph.graph import END, StateGraph

from src.agent.agents.evaluation.job_evaluation_agent import (
    JobEvaluationAgent,
    JobEvaluationInput,
)
from src.agent.agents.extraction.job_extraction_agent import (
    JobExtractionAgent,
    JobExtractionInput,
)
from src.agent.workflows.job_evaluation.states import JobEvaluationWorkflowState
from src.llm.langfuse_handler import get_langfuse_handler
from src.utils.logging import get_logger

logger = get_logger(__name__)


class JobEvaluationWorkflow:
    """
    Manages the job evaluation process as a compiled LangGraph workflow.

    This workflow uses specialized agents for extraction and evaluation,
    providing a clean separation of concerns and reusable components.
    """

    def __init__(self):
        # Initialize the specialized agents
        self.extraction_agent = JobExtractionAgent()
        self.evaluation_agent = JobEvaluationAgent()

        # Build and compile the workflow
        self.workflow = self._build_graph()
        self.app = self.workflow.compile()

    def _build_graph(self) -> StateGraph:
        """Builds the StateGraph for the job evaluation workflow."""
        workflow = StateGraph(JobEvaluationWorkflowState)

        # Add nodes using adapter methods
        workflow.add_node("extract", self._extraction_node)
        workflow.add_node("evaluate", self._evaluation_node)

        # Define edges - simplified flow (extraction includes validation)
        workflow.set_entry_point("extract")
        workflow.add_edge("extract", "evaluate")
        workflow.add_edge("evaluate", END)

        return workflow

    def _extraction_node(self, state: JobEvaluationWorkflowState) -> dict:
        """
        Adapter between workflow state and extraction agent.

        This method bridges the workflow state format with the agent's
        typed input/output interface.
        """
        logger.info("Workflow node: extract - using JobExtractionAgent")

        # Create agent input
        agent_input = JobExtractionInput(
            job_text=state["job_posting_text"], validation_enabled=True
        )

        # Execute the agent
        result = self.extraction_agent(agent_input)

        if result.success:
            logger.info("Extraction successful")
            return {
                "extracted_info": result.data.extracted_info,
                "is_valid": result.data.is_valid,
                "messages": state["messages"]
                + [
                    {
                        "role": "extraction_agent",
                        "content": f"Successfully extracted job info (valid: {result.data.is_valid})",
                        "metadata": result.metadata,
                    }
                ],
            }
        else:
            logger.error(f"Extraction failed: {result.error}")
            return {
                "extracted_info": None,
                "is_valid": False,
                "messages": state["messages"]
                + [
                    {
                        "role": "extraction_agent",
                        "error": result.error,
                        "metadata": result.metadata,
                    }
                ],
            }

    def _evaluation_node(self, state: JobEvaluationWorkflowState) -> dict:
        """
        Adapter between workflow state and evaluation agent.

        This method bridges the workflow state format with the agent's
        typed input/output interface.
        """
        logger.info("Workflow node: evaluate - using JobEvaluationAgent")

        # Check if we have extracted info to evaluate
        if not state.get("extracted_info"):
            logger.warning("No extracted info available for evaluation")
            return {
                "evaluation_result": None,
                "recommendation": "ERROR",
                "reasoning": "No extracted information available for evaluation",
                "messages": state["messages"]
                + [
                    {
                        "role": "evaluation_agent",
                        "error": "No extracted info to evaluate",
                    }
                ],
            }

        # Create agent input
        agent_input = JobEvaluationInput(extracted_info=state["extracted_info"])

        # Execute the agent
        result = self.evaluation_agent(agent_input)

        if result.success:
            logger.info(f"Evaluation successful: {result.data.recommendation}")
            return {
                "evaluation_result": result.data.evaluation_result,
                "recommendation": result.data.recommendation,
                "reasoning": result.data.reasoning,
                "passed_criteria": result.data.passed_criteria,
                "total_criteria": result.data.total_criteria,
                "messages": state["messages"]
                + [
                    {
                        "role": "evaluation_agent",
                        "content": f"Evaluation completed: {result.data.recommendation}",
                        "metadata": result.metadata,
                    }
                ],
            }
        else:
            logger.error(f"Evaluation failed: {result.error}")
            return {
                "evaluation_result": None,
                "recommendation": "ERROR",
                "reasoning": f"Evaluation failed: {result.error}",
                "messages": state["messages"]
                + [
                    {
                        "role": "evaluation_agent",
                        "error": result.error,
                        "metadata": result.metadata,
                    }
                ],
            }

    def run(
        self, job_posting_text: str, langfuse_handler: Optional[Any] = None
    ) -> dict:
        """
        Executes the job evaluation workflow.

        Args:
            job_posting_text: The raw job posting text.
            langfuse_handler: Optional Langfuse handler for tracing.

        Returns:
            The final state of the workflow.
        """
        logger.info("Starting JobEvaluationWorkflow run")
        initial_state = {
            "job_posting_text": job_posting_text,
            "extracted_info": None,
            "evaluation_result": None,
            "messages": [],
            "langfuse_handler": langfuse_handler,
            "workflow_version": "3.0",  # Updated version with new agents
            "extraction_duration": None,
            "evaluation_duration": None,
        }

        config = {}
        if langfuse_handler:
            config = {"callbacks": [langfuse_handler]}

        final_state = self.app.invoke(initial_state, config=config)
        logger.info("JobEvaluationWorkflow run completed")
        return final_state


def create_job_evaluation_workflow() -> JobEvaluationWorkflow:
    """
    Create a new job evaluation workflow instance.

    Returns:
        JobEvaluationWorkflow: New workflow instance
    """
    return JobEvaluationWorkflow()


def evaluate_job_posting(job_posting_text: str) -> Dict[str, Any]:
    """
    Evaluates a job posting using the graph-based agent workflow.

    This is the main public API for the job evaluation system. It provides
    a clean interface to the underlying LangGraph workflow system.

    Args:
        job_posting_text: The raw job posting text to evaluate.

    Returns:
        A dictionary with evaluation results in the format expected by the UI:
        - recommendation: "APPLY", "DO_NOT_APPLY", or "ERROR"
        - reasoning: Human-readable explanation of the recommendation
        - extracted_info: Dictionary with structured job information
        - evaluation_result: Dictionary with detailed evaluation criteria results
    """
    logger.info("Starting job evaluation with graph-based workflow.")

    if not job_posting_text or not job_posting_text.strip():
        logger.warning("Job posting text is empty.")
        return {
            "recommendation": "ERROR",
            "reasoning": "Job posting text was empty.",
            "extracted_info": {},
            "evaluation_result": {},
        }

    langfuse_handler = get_langfuse_handler()

    try:
        workflow = JobEvaluationWorkflow()
        final_state = workflow.run(job_posting_text, langfuse_handler)

        # The new agent-based workflow provides recommendation directly
        recommendation = final_state.get("recommendation", "ERROR")
        reasoning = final_state.get("reasoning", "Unknown error occurred")
        result = final_state.get("evaluation_result", {})

        if recommendation == "ERROR":
            logger.error(f"Workflow completed with error: {reasoning}")
            return {
                "recommendation": "ERROR",
                "reasoning": reasoning,
                "extracted_info": final_state.get("extracted_info", {}),
                "evaluation_result": result,
            }

        # Convert extracted_info to dictionary format for UI compatibility
        extracted_info_dict = {}
        extracted_info = final_state.get("extracted_info")
        if extracted_info:
            if hasattr(extracted_info, "model_dump"):
                extracted_info_dict = extracted_info.model_dump()
            elif isinstance(extracted_info, dict):
                extracted_info_dict = extracted_info
            else:
                extracted_info_dict = dict(extracted_info) if extracted_info else {}

        logger.info(f"Job evaluation completed with recommendation: {recommendation}")

        return {
            "recommendation": recommendation,
            "reasoning": reasoning,
            "extracted_info": extracted_info_dict,
            "evaluation_result": result,
        }

    except Exception as e:
        logger.error(f"Job evaluation workflow failed: {e}", exc_info=True)
        return {
            "recommendation": "ERROR",
            "reasoning": f"An unexpected error occurred during the workflow: {e}",
            "extracted_info": {},
            "evaluation_result": {},
        }
