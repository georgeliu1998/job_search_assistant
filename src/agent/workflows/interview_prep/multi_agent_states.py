"""Enhanced state management for multi-agent interview preparation workflow."""

from enum import Enum
from typing import Any, Dict, List, Optional

from pydantic import ConfigDict, Field

from src.agent.workflows.interview_prep.states import InterviewPrepState
from src.models.base import BaseDataModel
from src.models.interview import QAPair, ResearchCitation


class AgentStatus(str, Enum):
    """Status of individual agents in the workflow."""

    PENDING = "pending"
    PLANNING = "planning"
    IN_PROGRESS = "in_progress"
    COMPLETED = "completed"
    FAILED = "failed"
    SKIPPED = "skipped"


class WorkflowPhase(str, Enum):
    """Current phase of the multi-agent workflow."""

    INITIALIZATION = "initialization"
    PLANNING = "planning"
    RESEARCH = "research"
    QUESTION_GENERATION = "question_generation"
    ANSWER_GENERATION = "answer_generation"
    COMPILATION = "compilation"
    COMPLETED = "completed"


class AgentPlan(BaseDataModel):
    """Plan created by the planner agent for other agents."""

    research_strategy: Dict[str, Any] = Field(default_factory=dict)
    question_strategy: Dict[str, Any] = Field(default_factory=dict)
    answer_strategy: Dict[str, Any] = Field(default_factory=dict)
    compilation_strategy: Dict[str, Any] = Field(default_factory=dict)


class MultiAgentInterviewPrepState(InterviewPrepState):
    """Enhanced state for multi-agent interview preparation workflow."""

    model_config = ConfigDict(
        extra="allow",
        use_enum_values=True,
    )

    # === Multi-Agent Coordination ===

    # Current workflow state
    current_phase: WorkflowPhase = Field(
        default=WorkflowPhase.INITIALIZATION,
        description="Current phase of the workflow",
    )
    current_agent: Optional[str] = Field(
        default=None, description="Currently active agent"
    )

    # Agent status tracking
    agent_status: Dict[str, AgentStatus] = Field(
        default_factory=dict, description="Status of each agent in the workflow"
    )

    # Execution plan and strategies
    execution_plan: Optional[AgentPlan] = Field(
        default=None, description="Execution plan created by planner agent"
    )

    # Iteration control
    iteration_count: int = Field(
        default=0, description="Current iteration count for loop control"
    )
    max_iterations: int = Field(
        default=3, description="Maximum iterations to prevent infinite loops"
    )

    # === Agent-Specific Intermediate Results ===

    # Research Agent outputs
    research_strategy: Optional[Dict[str, Any]] = Field(
        default=None, description="Research strategy determined by planner"
    )
    dynamic_research_queries: Optional[List[str]] = Field(
        default=None, description="AI-generated research queries"
    )
    research_analysis: Optional[Dict[str, Any]] = Field(
        default=None, description="Analysis of research results by research agent"
    )

    # Question Agent outputs
    question_strategy: Optional[Dict[str, Any]] = Field(
        default=None, description="Question generation strategy"
    )
    question_analysis: Optional[Dict[str, Any]] = Field(
        default=None, description="Analysis of generated questions"
    )

    # Answer Agent outputs
    answer_strategy: Optional[Dict[str, Any]] = Field(
        default=None, description="Answer generation strategy"
    )
    resume_mapping: Optional[Dict[str, Any]] = Field(
        default=None, description="Mapping of resume experiences to questions"
    )

    # Editor Agent outputs
    compilation_strategy: Optional[Dict[str, Any]] = Field(
        default=None, description="Guide compilation and formatting strategy"
    )
    quality_assessment: Optional[Dict[str, Any]] = Field(
        default=None, description="Quality assessment of final guide"
    )

    # === Enhanced Error Handling ===

    agent_errors: Dict[str, str] = Field(
        default_factory=dict, description="Errors from specific agents"
    )

    recovery_attempts: Dict[str, int] = Field(
        default_factory=dict, description="Number of recovery attempts per agent"
    )

    # === Progress Tracking ===

    workflow_metrics: Dict[str, Any] = Field(
        default_factory=dict, description="Performance metrics for the workflow"
    )

    @property
    def has_errors(self) -> bool:
        """Check if any agent has errors."""
        return bool(self.error or self.agent_errors)

    @property
    def completed_agents(self) -> List[str]:
        """Get list of completed agents."""
        return [
            agent
            for agent, status in self.agent_status.items()
            if status == AgentStatus.COMPLETED
        ]

    @property
    def failed_agents(self) -> List[str]:
        """Get list of failed agents."""
        return [
            agent
            for agent, status in self.agent_status.items()
            if status == AgentStatus.FAILED
        ]

    def set_agent_status(self, agent_name: str, status: AgentStatus) -> None:
        """Update agent status."""
        self.agent_status[agent_name] = status

    def set_agent_error(self, agent_name: str, error_msg: str) -> None:
        """Set error for specific agent."""
        self.agent_errors[agent_name] = error_msg
        self.set_agent_status(agent_name, AgentStatus.FAILED)

    def can_continue(self) -> bool:
        """Check if workflow can continue based on errors and iterations."""
        return (
            not self.error
            and self.iteration_count < self.max_iterations
            and len(self.failed_agents) == 0
        )

    def advance_phase(self, next_phase: WorkflowPhase) -> None:
        """Advance to the next workflow phase."""
        self.current_phase = next_phase
        self.iteration_count += 1
