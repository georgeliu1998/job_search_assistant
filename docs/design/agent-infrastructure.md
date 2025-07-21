# Agent Infrastructure Design

[← Back to Documentation](../README.md)

## Overview

The Job Search Assistant uses LangGraph as the foundation for its agent infrastructure, providing a flexible framework for building complex AI-powered workflows. The design separates concerns between agents, tools, and workflows to enable modular, testable, and extensible AI processes.

## Architecture Components

### 1. Agents (`src/agent/agents/`)
**Purpose**: Specialized AI agents that perform specific tasks

Agents are the core AI components that:
- Process natural language inputs
- Make decisions based on context
- Interact with tools to perform actions
- Maintain conversation state and memory

**Current Implementation**:
- Job evaluation agents for specific extraction tasks
- Future: Resume customization agents, interview preparation agents

### 2. Tools (`src/agent/tools/`)
**Purpose**: Reusable functions that agents can call to perform specific actions

Tools provide:
- **Extraction Tools**: Parse unstructured text into structured data
- **Evaluation Tools**: Apply business logic and criteria
- **Utility Tools**: Common operations like data validation, formatting

**Current Tools**:
- `schema_extraction_tool.py`: Extracts job information from text
- Future: Resume parsing tools, LinkedIn integration tools

### 3. Workflows (`src/agent/workflows/`)
**Purpose**: Orchestrate complex multi-step processes using LangGraph

Workflows:
- Coordinate multiple agents and tools
- Manage state transitions
- Handle error conditions and recovery
- Provide end-to-end process management

**Current Workflows**:
- `job_evaluation/`: Complete job evaluation process

### 4. Prompts (`src/agent/prompts/`)
**Purpose**: Centralized prompt management and versioning

Prompts:
- Define the behavior and personality of agents
- Can be versioned and A/B tested
- Support template variables and dynamic content
- Enable prompt engineering without code changes

## Design Rationale

### Why LangGraph?

1. **State Management**: Built-in state management for complex workflows
2. **Error Handling**: Robust error handling and recovery mechanisms
3. **Observability**: Native support for monitoring and debugging
4. **Extensibility**: Easy to add new nodes and modify workflows
5. **Testing**: Excellent support for unit and integration testing

### Separation of Concerns

#### Agents vs. Tools
- **Agents**: Make decisions, maintain context, handle complex logic
- **Tools**: Perform specific, stateless operations

#### Workflows vs. Agents
- **Workflows**: Orchestrate multiple steps, manage state transitions
- **Agents**: Focus on single, well-defined tasks

#### Prompts vs. Code
- **Prompts**: Define behavior and personality
- **Code**: Handle logic, data processing, and integration

## Current Implementation

### Job Evaluation Workflow

The job evaluation process demonstrates the agent infrastructure:

```python
# Workflow definition in src/agent/workflows/job_evaluation/main.py
workflow = StateGraph(JobEvaluationState)

# Add workflow nodes
workflow.add_node("validate", validate_input)
workflow.add_node("extract", extract_job_info)
workflow.add_node("evaluate", evaluate_job)
workflow.add_node("recommend", generate_recommendation)

# Define workflow flow
workflow.add_edge(START, "validate")
workflow.add_edge("validate", "extract")
workflow.add_edge("extract", "evaluate")
workflow.add_edge("evaluate", "recommend")
workflow.add_edge("recommend", END)
```

### State Management

Each workflow uses a Pydantic state model:

```python
# src/agent/workflows/job_evaluation/states.py
class JobEvaluationState(BaseModel):
    job_posting_text: str
    extracted_info: Optional[Dict[str, Any]] = None
    evaluation_result: Optional[Dict[str, Any]] = None
    recommendation: Optional[str] = None
    reasoning: Optional[str] = None
```

### Tool Integration

Tools are called by workflow nodes:

```python
def extract_job_info(state: JobEvaluationState) -> Dict[str, Any]:
    extracted_info = extract_job_posting(job_text)
    is_valid = validate_extraction_result(extracted_info, "job_posting")
    return {"extracted_info": extracted_info}
```

## Benefits of This Design

### 1. Modularity
- Each component has a single responsibility
- Components can be developed and tested independently
- Easy to swap implementations (e.g., different LLM providers)

### 2. Reusability
- Tools can be used by multiple agents and workflows
- Prompts can be shared across different agents
- Common patterns can be abstracted into reusable components

### 3. Testability
- Each component can be unit tested in isolation
- Workflows can be tested with mock tools and agents
- Integration tests can verify end-to-end behavior

### 4. Observability
- Built-in logging and monitoring
- Langfuse integration for LLM interaction tracking
- Clear visibility into workflow execution

### 5. Extensibility
- New agents can be added without modifying existing code
- Workflows can be extended with additional steps
- Tools can be enhanced with new capabilities

## Future Enhancements

### 1. Advanced Agent Types
- **Memory Agents**: Maintain conversation history and context
- **Planning Agents**: Break complex tasks into subtasks
- **Reflection Agents**: Review and improve their own outputs

### 2. Tool Ecosystem
- **External API Tools**: LinkedIn, job boards, resume parsers
- **Data Processing Tools**: Text analysis, sentiment analysis
- **Integration Tools**: Email, calendar, CRM systems

### 3. Workflow Patterns
- **Conditional Workflows**: Different paths based on input
- **Parallel Workflows**: Multiple agents working simultaneously
- **Recursive Workflows**: Self-improving processes

### 4. Prompt Management
- **Version Control**: Track prompt changes and performance
- **A/B Testing**: Compare different prompt strategies
- **Dynamic Prompts**: Context-aware prompt generation

## Best Practices

### 1. Agent Design
- Keep agents focused on single, well-defined tasks
- Use clear, descriptive names for agents
- Document the expected inputs and outputs

### 2. Tool Design
- Make tools stateless and idempotent
- Provide clear error messages and validation
- Use type hints and documentation

### 3. Workflow Design
- Start simple and add complexity gradually
- Handle errors gracefully at each step
- Provide clear feedback on workflow progress

### 4. State Management
- Keep state models simple and focused
- Use optional fields for gradual data accumulation
- Validate state at each transition
