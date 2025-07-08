"""
Base classes for all agents in the job search assistant.

This module provides the foundation for creating reusable, composable agents
that can be used across different workflows.
"""

from abc import ABC, abstractmethod
from typing import Any, Dict, Generic, List, Optional, TypeVar

from langchain_core.messages import BaseMessage
from pydantic import BaseModel

T = TypeVar("T", bound=BaseModel)  # Input type
U = TypeVar("U", bound=BaseModel)  # Output type


class AgentResult(BaseModel, Generic[U]):
    """Standard result wrapper for all agents."""

    success: bool
    data: Optional[U] = None
    error: Optional[str] = None
    metadata: Dict[str, Any] = {}
    messages: List[BaseMessage] = []

    class Config:
        arbitrary_types_allowed = True


class Agent(ABC, Generic[T, U]):
    """Base class for all agents."""

    def __init__(self, name: str, description: str):
        self.name = name
        self.description = description

    @abstractmethod
    async def execute(self, input_data: T) -> AgentResult[U]:
        """Execute the agent's main functionality."""
        pass

    def __call__(self, input_data: T) -> AgentResult[U]:
        """Sync wrapper for execute."""
        import asyncio

        try:
            return asyncio.run(self.execute(input_data))
        except RuntimeError:
            # Handle case where we're already in an async context
            import nest_asyncio

            nest_asyncio.apply()
            return asyncio.run(self.execute(input_data))

    def __str__(self) -> str:
        return f"Agent(name={self.name}, description={self.description})"

    def __repr__(self) -> str:
        return self.__str__()
