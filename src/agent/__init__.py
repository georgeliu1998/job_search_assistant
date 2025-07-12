"""
Agent system for job search assistant.

This module contains the agent infrastructure that focuses on
clean, maintainable workflows using LangGraph for orchestration.

## Design Philosophy: Workflow Architecture

This agent system follows a streamlined approach:

### Current Architecture:
- **Workflows** handle end-to-end processes using LangGraph StateGraph
- **Tools** are simple functions that perform specific tasks (extraction, evaluation)
- **Prompts** are organized by domain for reusability

### Key Components:
- `workflows/` - LangGraph-based process orchestration
- `tools/` - Reusable utility functions
- `prompts/` - Domain-specific prompt templates
- `agents/` - Reserved for future LLM-powered decision-making agents
- `common/` - Reserved for shared utilities

### Current Workflows:
- **Job Evaluation**: Extract job info → Evaluate against criteria → Recommend action

### Future Growth:
The structure is designed to support both:
- **Workflow-as-Agent**: Fixed processes with LangGraph orchestration (current)
- **Traditional Agents**: LLM-powered decision-making entities (future)

This architecture prioritizes simplicity and maintainability while remaining
extensible for future job search use cases.
"""

__version__ = "3.0.0"  # Current workflow-based architecture
