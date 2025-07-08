"""
Agent infrastructure for the job search assistant.

This module provides the foundation for creating specialized, reusable agents
that can be composed into different workflows.
"""

# Import evaluation agents
from src.agent.agents.evaluation.job_evaluation_agent import (
    JobEvaluationAgent,
    JobEvaluationInput,
    JobEvaluationOutput,
)

# Import extraction agents
from src.agent.agents.extraction.job_extraction_agent import (
    JobExtractionAgent,
    JobExtractionInput,
    JobExtractionOutput,
)
from src.agent.common.base import Agent, AgentResult

__all__ = [
    # Base classes
    "Agent",
    "AgentResult",
    # Extraction agents
    "JobExtractionAgent",
    "JobExtractionInput",
    "JobExtractionOutput",
    # Evaluation agents
    "JobEvaluationAgent",
    "JobEvaluationInput",
    "JobEvaluationOutput",
]
