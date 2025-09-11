"""Agent registry for managing agent instances."""

from typing import Dict, List, Optional

from src.agent.agents.common.base import BaseAgent


class AgentRegistry:
    """Registry for managing agent instances."""

    _agents: Dict[str, BaseAgent] = {}

    @classmethod
    def register(cls, agent: BaseAgent) -> None:
        """Register an agent.

        Args:
            agent: Agent instance to register
        """
        cls._agents[agent.name] = agent

    @classmethod
    def get(cls, name: str) -> Optional[BaseAgent]:
        """Get agent by name.

        Args:
            name: Name of the agent

        Returns:
            Agent instance if found, None otherwise
        """
        return cls._agents.get(name)

    @classmethod
    def get_required(cls, name: str) -> BaseAgent:
        """Get agent by name, raising error if not found.

        Args:
            name: Name of the agent

        Returns:
            Agent instance

        Raises:
            ValueError: If agent not found
        """
        if name not in cls._agents:
            raise ValueError(f"Agent '{name}' not registered")
        return cls._agents[name]

    @classmethod
    def list_agents(cls) -> List[str]:
        """List all registered agents.

        Returns:
            List of agent names
        """
        return list(cls._agents.keys())

    @classmethod
    def clear(cls) -> None:
        """Clear all registered agents."""
        cls._agents.clear()

    @classmethod
    def is_registered(cls, name: str) -> bool:
        """Check if an agent is registered.

        Args:
            name: Name of the agent

        Returns:
            True if agent is registered, False otherwise
        """
        return name in cls._agents


def register_all_agents():
    """Register all available agents in the registry.

    This function uses lazy imports to avoid circular dependencies.
    Call this function after all agent modules have been imported.
    """
    # Lazy imports to avoid circular dependencies
    from src.agent.agents.content_generation.answer import answer_agent_instance
    from src.agent.agents.content_generation.question import question_agent_instance
    from src.agent.agents.content_processing.editor import editor_agent_instance
    from src.agent.agents.strategy.planner import planner_agent_instance
    from src.agent.agents.strategy.research import research_agent_instance

    # Clear any existing registrations
    AgentRegistry.clear()

    # Register all agents
    AgentRegistry.register(planner_agent_instance)
    AgentRegistry.register(research_agent_instance)
    AgentRegistry.register(question_agent_instance)
    AgentRegistry.register(answer_agent_instance)
    AgentRegistry.register(editor_agent_instance)
