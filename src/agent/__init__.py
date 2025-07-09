"""
Agent system for job search assistant.

This module contains the redesigned agent infrastructure leveraging
LangGraph's tool calling capabilities with structured outputs for
type-safe, validated extraction and agent reasoning.

## Design Philosophy: Flexible Agent Architecture

This agent system is designed to support different agent/tool patterns depending on
the specific use case:

### Standard LangGraph Pattern (Recommended for new workflows):
- **Tools** are simple functions or API calls (no LLM decision-making)
- **Agents** are LLMs with reasoning that decide when/how to use tools

### Alternative Pattern (Used in some existing workflows):
- **Tools** contain LLM logic for specialized tasks
- **Agents** orchestrate workflows and coordinate tool usage

### Guidelines for New Development:
- **Default**: Use the standard LangGraph pattern unless there's specific justification
- **Domain-Specific**: Consider alternative patterns only for highly specialized use cases
- **Documentation**: Always document deviations from standard patterns

**Note**: The job evaluation workflow uses a non-standard pattern for specific reasons.
See `src/agent/workflows/job_evaluation/` for detailed rationale and design decisions.

The base agent infrastructure supports both patterns and remains extensible for
future job search use cases while maintaining clean separation of concerns and type safety.
"""

__version__ = "2.0.0"  # Updated to reflect tool-calling architecture
