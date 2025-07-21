# Job Evaluation Design

[← Back to Documentation](../README.md)

## Overview

The job evaluation feature is implemented as a LangGraph workflow with deterministic business logic functions rather than autonomous agents. This design choice enables complex multi-step processing, robust error handling, and future extensibility while maintaining clear separation of concerns.

## Why a Workflow Instead of a Simple Agent?

### 1. Multi-Step Process Requirements

Job evaluation involves several distinct steps that benefit from explicit orchestration:

1. **Input Validation**: Check job posting text for validity
2. **Information Extraction**: Parse unstructured text into structured data
3. **Criteria Evaluation**: Apply business logic against user preferences
4. **Recommendation Generation**: Synthesize results into actionable advice

Each step has different requirements:
- **Extraction**: Uses LLM for structured data extraction
- **Evaluation**: Uses business logic against configuration criteria
- **Recommendation**: Uses business logic to synthesize results
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
- Calls `evaluate_job_against_criteria` from core business logic
- Checks salary against minimum requirements (from config)
- Validates remote work policy requirements
- Evaluates title seniority level for IC roles
- Generates detailed pass/fail results for each criterion

#### 4. Recommendation Generation (`generate_recommendation`)
- Calls `generate_recommendation_from_evaluation` from core business logic
- Analyzes pass/fail results from evaluation step
- Returns "APPLY" if all criteria pass, "DO_NOT_APPLY" if any fail
- Provides detailed reasoning explaining which criteria passed/failed
- Formats output for user consumption

### Current Evaluation Criteria

The evaluation step (`evaluate_job_against_criteria`) implements these specific business rules:

1. **Salary Check**:
   - Compares `salary_max` from extracted info against `config.evaluation_criteria.min_salary`
   - Fails if salary is not specified or below minimum threshold

2. **Remote Work Policy**:
   - Checks if `location_policy` contains "remote"
   - Passes only if position explicitly allows remote work

3. **IC Title Level** (for Individual Contributor roles):
   - For roles identified as IC/Individual Contributor
   - Checks if job title contains required seniority levels from `config.evaluation_criteria.ic_title_requirements`
   - Typical requirements: ["lead", "staff", "principal", "senior staff"]

Each criterion returns a pass/fail result with detailed reasoning, enabling transparent decision-making.

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
