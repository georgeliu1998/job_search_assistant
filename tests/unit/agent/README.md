# Agent Tests

This directory contains comprehensive unit and integration tests for the agent infrastructure.

## Test Structure

```
tests/
├── unit/agent/
│   ├── test_extraction_agent.py      # Unit tests for agent nodes
│   ├── test_schema_extraction_tools.py  # Unit tests for extraction tools
│   └── test_workflow_states.py       # Unit tests for state management
└── integration/agent/
    └── test_workflow_integration.py  # End-to-end workflow tests
```

## Test Coverage

### Unit Tests

**`test_extraction_agent.py`**
- Tests for individual agent nodes (`extraction_node`, `validation_node`, `evaluation_node`)
- Success scenarios, error handling, and edge cases
- Mocked LLM calls and tool interactions

**`test_schema_extraction_tools.py`**
- Tests for schema-based extraction tools
- Validation logic and summary generation
- Registry management and error handling

**`test_workflow_states.py`**
- Tests for workflow state management functions
- State creation, message handling, and type conversions
- Pydantic model integration

### Integration Tests

**`test_workflow_integration.py`**
- End-to-end workflow testing
- Complete job evaluation scenarios
- Real data integration with mocked LLM calls

## Running Tests

### Run All Agent Tests
```bash
# From project root
pytest tests/unit/agent/ tests/integration/agent/ -v
```

### Run Specific Test Categories
```bash
# Unit tests only
pytest tests/unit/agent/ -v

# Integration tests only
pytest tests/integration/agent/ -v

# Specific test file
pytest tests/unit/agent/test_extraction_agent.py -v

# Specific test class
pytest tests/unit/agent/test_extraction_agent.py::TestExtractionNode -v

# Specific test method
pytest tests/unit/agent/test_extraction_agent.py::TestExtractionNode::test_extraction_node_success -v
```

### Run with Coverage
```bash
# Generate coverage report
pytest tests/unit/agent/ tests/integration/agent/ --cov=src.agent --cov-report=html --cov-report=term-missing
```

### Run with Markers
```bash
# Run only slow tests (if marked)
pytest tests/ -m slow

# Skip slow tests
pytest tests/ -m "not slow"
```

## Test Fixtures

The tests use various fixtures defined in `tests/conftest.py`:

- `mock_extraction_result`: Complete successful extraction
- `mock_partial_extraction_result`: Partial extraction data
- `mock_evaluation_result`: Successful evaluation results
- `mock_failed_evaluation_result`: Failed evaluation results
- `mock_llm_client`: Mock LLM client for testing
- `sample_job_posting_texts`: Various job posting scenarios
- `workflow_state_factory`: Factory for creating test states

## Test Scenarios Covered

### Success Scenarios
- Complete workflow with all criteria passing
- Partial extraction with meaningful data
- Mixed evaluation results (some pass, some fail)

### Error Scenarios
- LLM API failures
- Empty or invalid input
- Schema validation failures
- Tool calling errors

### Edge Cases
- Very long job postings
- Malformed text
- Partial data extraction
- Missing fields

## Best Practices

1. **Use Fixtures**: Leverage the comprehensive fixtures for consistent test data
2. **Mock External Calls**: All LLM calls are mocked to avoid API costs
3. **Test Both Success and Failure**: Each function tests both happy path and error cases
4. **Clear Test Names**: Test method names clearly describe the scenario
5. **Isolated Tests**: Each test is independent and can run in any order

## Adding New Tests

When adding new agent functionality:

1. **Unit Tests**: Add tests for individual components in the appropriate file
2. **Integration Tests**: Add end-to-end tests in `test_workflow_integration.py`
3. **Fixtures**: Add reusable test data to `conftest.py`
4. **Documentation**: Update this README with new test scenarios

## Performance Considerations

- Tests use mocking to avoid actual LLM API calls
- Fixtures are session-scoped where appropriate to improve performance
- Large test data is generated dynamically rather than stored

## Debugging Tests

### Verbose Output
```bash
pytest tests/unit/agent/ -v -s
```

### Debug Specific Test
```bash
pytest tests/unit/agent/test_extraction_agent.py::TestExtractionNode::test_extraction_node_success -v -s --pdb
```

### View Coverage Details
```bash
pytest tests/unit/agent/ --cov=src.agent --cov-report=html
# Open htmlcov/index.html in browser
```
