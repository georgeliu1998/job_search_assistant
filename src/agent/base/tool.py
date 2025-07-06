"""
Base tool class for complex tools.

This module provides a base class for tools that need more structure
than simple @tool decorated functions. Most tools should use @tool
decorators directly, but this is available for complex cases.
"""

from abc import ABC, abstractmethod
from typing import Any, Dict, Optional

from langchain_core.tools import BaseTool as LangChainBaseTool
from pydantic import BaseModel

from src.utils.logging import get_logger

logger = get_logger(__name__)


class BaseTool(LangChainBaseTool, ABC):
    """
    Base class for complex tools that need more structure.

    Most tools should use @tool decorators directly. This class is
    provided for tools that need additional complexity, state management,
    or custom validation logic.
    """

    def __init__(self, **kwargs):
        """Initialize the base tool."""
        super().__init__(**kwargs)
        self._initialized = False

    def _initialize(self) -> None:
        """Initialize the tool if not already initialized."""
        if not self._initialized:
            self._setup()
            self._initialized = True
            logger.debug(f"Initialized tool: {self.name}")

    def _setup(self) -> None:
        """
        Setup method for tool initialization.

        Subclasses can override this to perform setup operations
        like loading models, connecting to services, etc.
        """
        pass

    def _run(self, *args, **kwargs) -> Any:
        """
        Run the tool with automatic initialization.

        This method ensures the tool is initialized before running
        and provides consistent logging.
        """
        self._initialize()

        try:
            logger.debug(f"Running tool: {self.name}")
            result = self._execute(*args, **kwargs)
            logger.debug(f"Tool {self.name} completed successfully")
            return result
        except Exception as e:
            logger.error(f"Tool {self.name} failed: {e}")
            raise

    @abstractmethod
    def _execute(self, *args, **kwargs) -> Any:
        """
        Execute the tool's main logic.

        Subclasses must implement this method with their specific logic.
        """
        pass

    async def _arun(self, *args, **kwargs) -> Any:
        """
        Async version of _run.

        Default implementation just calls _run. Subclasses can override
        for true async behavior.
        """
        return self._run(*args, **kwargs)


class ToolConfig(BaseModel):
    """Configuration model for tools that need complex configuration."""

    name: str
    description: str
    enabled: bool = True
    timeout: Optional[int] = None
    retry_count: int = 0

    class Config:
        """Pydantic configuration."""

        extra = "allow"  # Allow additional fields for tool-specific config
