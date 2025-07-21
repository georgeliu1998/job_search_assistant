# Job Evaluation Design

## Overview

The job evaluation feature is implemented as a LangGraph workflow rather than a simple agent. This design choice enables complex multi-step processing, robust error handling, and future extensibility while maintaining clear separation of concerns.

## Why a Workflow Instead of a Simple Agent?

### 1. Multi-Step Process Requirements

Job evaluation involves several distinct steps that benefit from explicit orchestration:

1. **Input Validation**: Check job posting text for validity
2. **Information Extraction**: Parse unstructured text into structured data
3. **Criteria Evaluation**: Apply business logic against user preferences
4. **Recommendation Generation**: Synthesize results into actionable advice

Each step has different requirements:
- Different LLM models (extraction vs. evaluation)
- Different error handling strategies
- Different validation needs

### 2. State Management Complexity

The process accumulates state across multiple steps:

```python
class JobEvaluationState(BaseModel):
    job_posting_text: str                    # Input
    extracted_info: Optional[Dict] = None    # Step 2 output
    evaluation_result: Optional[Dict] = None # Step 3 output
    recommendation: Optional[str] = None     # Step 4 output
    reasoning: Optional[str] = None          # Step 4 output
```

A simple agent would need to manage this state internally, making it harder to:
- Debug intermediate results
- Test individual steps
- Handle partial failures

### 3. Error Handling and Recovery

Each step can fail for different reasons:

- **Validation**: Empty or malformed input
- **Extraction**: LLM fails to extract meaningful information
- **Evaluation**: Missing required fields or invalid data
- **Recommendation**: Insufficient data for meaningful recommendation

The workflow design allows:
- Graceful degradation (continue with partial data)
- Step-specific error handling
- Clear error messages for each failure point
- Recovery strategies (retry, fallback, etc.)

## Current Workflow Implementation

### Workflow Structure

```python
# src/agent/workflows/job_evaluation/main.py
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

### Step-by-Step Process

#### 1. Input Validation (`validate_input`)
- Checks if job posting text is provided and non-empty
- Returns early error if validation fails
- Sets up initial state for processing

#### 2. Information Extraction (`extract_job_info`)
- Uses specialized extraction tool with structured output
- Validates extraction results
- Handles extraction failures gracefully

#### 3. Criteria Evaluation (`evaluate_job`)
- Applies business logic against extracted information
- Checks salary, remote work, experience level, skills
- Generates detailed evaluation results

#### 4. Recommendation Generation (`generate_recommendation`)
- Synthesizes evaluation results into actionable advice
- Provides reasoning for the recommendation
- Formats output for user consumption

## Design Benefits

### 1. Observability
Each step is logged and monitored independently:
- Input validation results
- Extraction success/failure rates
- Evaluation criteria matches
- Recommendation quality

### 2. Testability
Individual steps can be tested in isolation:
- Mock inputs for each step
- Validate step outputs independently
- Test error conditions for each step

### 3. Extensibility
Easy to add new steps or modify existing ones:
- Add pre-processing steps (text cleaning, formatting)
- Add post-processing steps (result formatting, caching)
- Modify evaluation criteria without changing workflow structure

### 4. Error Resilience
Robust error handling at each step:
- Continue processing with partial data
- Provide meaningful error messages
- Support retry mechanisms

## Comparison: Workflow vs. Simple Agent

### Simple Agent Approach
```python
def evaluate_job_agent(job_text: str) -> Dict:
    # All logic in one function
    # Hard to test individual steps
    # Difficult error handling
    # No intermediate state visibility
    pass
```

**Problems:**
- Monolithic function hard to test
- Error handling mixed with business logic
- No visibility into intermediate steps
- Difficult to extend or modify

### Workflow Approach
```python
# Each step is a separate, testable function
def validate_input(state: JobEvaluationState) -> Dict:
    # Focused on validation only
    pass

def extract_job_info(state: JobEvaluationState) -> Dict:
    # Focused on extraction only
    pass

def evaluate_job(state: JobEvaluationState) -> Dict:
    # Focused on evaluation only
    pass

def generate_recommendation(state: JobEvaluationState) -> Dict:
    # Focused on recommendation only
    pass
```

**Benefits:**
- Each step is focused and testable
- Clear error handling per step
- Full visibility into intermediate state
- Easy to extend and modify

## Future Enhancements

### 1. Conditional Workflows
Add decision points based on job characteristics:
- Different evaluation paths for different job types
- Conditional extraction based on job format
- Adaptive recommendation strategies

### 2. Parallel Processing
Process multiple aspects simultaneously:
- Extract job info and user preferences in parallel
- Evaluate multiple criteria simultaneously
- Generate multiple recommendation types

### 3. Feedback Loops
Add self-improving capabilities:
- Learn from user feedback on recommendations
- Adapt extraction based on success rates
- Refine evaluation criteria based on outcomes

### 4. Integration Points
Connect with external systems:
- LinkedIn job data integration
- Resume matching capabilities
- Application tracking integration

## Best Practices Applied

### 1. Single Responsibility
Each workflow node has one clear purpose:
- `validate_input`: Only validates input
- `extract_job_info`: Only extracts information
- `evaluate_job`: Only applies evaluation criteria
- `generate_recommendation`: Only generates recommendations

### 2. Error Handling
Each step handles its own errors:
- Validation errors don't affect extraction
- Extraction errors don't affect evaluation
- Evaluation errors don't affect recommendation generation

### 3. State Management
Clear state transitions:
- Each step adds to state without modifying previous steps
- State is validated at each transition
- Optional fields allow gradual data accumulation

### 4. Observability
Comprehensive logging and monitoring:
- Each step logs its inputs and outputs
- Error conditions are clearly logged
- Performance metrics are tracked per step
