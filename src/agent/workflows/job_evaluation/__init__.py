"""
Job evaluation workflow implementation.

This module contains the workflow for evaluating job postings against
user criteria, including extraction and evaluation steps using specialized agents.

## Design Note: Non-Standard Agent/Tool Pattern

⚠️ **Important**: This workflow uses a non-standard agent/tool design pattern that deviates
from typical LangGraph/LangChain conventions. This was an intentional design choice for
this specific use case.

### Current Design (Job Evaluation Workflow):
- **Tools** contain LLM logic for specialized extraction tasks
- **Agents** orchestrate workflows and coordinate tool usage
- Justified for domain-specific job search extraction and evaluation

### Future Workflows:
Future workflows should likely follow the standard LangGraph pattern:
- **Tools** should be simple functions or API calls (no LLM decision-making)
- **Agents** should be LLMs with reasoning that decide when/how to use tools

### Rationale for This Deviation:
This workflow was designed before establishing standard patterns and focuses on:
1. Specialized job posting extraction and validation
2. Workflow orchestration rather than general AI reasoning
3. Type-safe, reusable extraction utilities

**Reminder**: When implementing new workflows, consider using the standard agent/tool
separation pattern unless there's a specific justification for deviation.
"""

from src.agent.workflows.job_evaluation.main import (
    JobEvaluationWorkflow,
    create_job_evaluation_workflow,
    evaluate_job_posting,
)
from src.agent.workflows.job_evaluation.states import (
    JobEvaluationWorkflowState,
    add_message,
    create_initial_state,
    get_extracted_info_as_dict,
    is_evaluation_successful,
    is_extraction_successful,
)

__all__ = [
    # Public API
    "evaluate_job_posting",
    # State management
    "JobEvaluationWorkflowState",
    "create_initial_state",
    "is_extraction_successful",
    "is_evaluation_successful",
    "get_extracted_info_as_dict",
    "add_message",
    # Workflow
    "JobEvaluationWorkflow",
    "create_job_evaluation_workflow",
]
