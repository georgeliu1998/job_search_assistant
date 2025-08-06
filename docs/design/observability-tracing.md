# Observability & Tracing Design

[← Back to Design Documents](README.md)

This document explains the observability and tracing infrastructure of the Job Search Assistant, with a focus on the context-aware Langfuse integration for monitoring AI workflows.

## Overview

The Job Search Assistant includes built-in observability capabilities to monitor LLM calls, workflow execution, and system performance. The tracing system is designed to provide clean, actionable insights without overwhelming developers with duplicate or noisy traces.

## Architecture

### Core Components

```mermaid
graph TB
    A[LangfuseManager] --> B[Context-Aware Tracing]
    A --> C[Handler Management]
    A --> D[Configuration]

    B --> E[Workflow Context]
    B --> F[Individual LLM Calls]

    E --> G[get_workflow_config()]
    F --> H[get_config()]

    I[LangGraph Workflow] --> G
    J[Schema Extraction] --> H
    K[Anthropic Client] --> H
```

### Key Classes

- **`LangfuseManager`**: Core manager for tracing operations
- **`GlobalLangfuseManager`**: Singleton wrapper for application-wide access
- **Context Variables**: Thread-safe workflow state tracking

## Context-Aware Tracing

### The Problem

Traditional tracing approaches often result in duplicate traces:
- **Workflow Level**: LangGraph creates a trace for the entire workflow
- **Individual Calls**: Each LLM call creates its own trace
- **Result**: Messy dashboard with redundant information

### The Solution

Our context-aware system eliminates duplicates through intelligent trace management:

```python
# Workflow level - always traces
execution_config = langfuse_manager.get_workflow_config(config)
workflow.invoke(state, config=execution_config)

# Individual calls - context-aware
config_dict = langfuse_manager.get_config()  # Skips if in workflow
llm.invoke(messages, config=config_dict)
```

### Context Management

The system uses Python's `contextvars` for thread-safe context tracking:

```python
import contextvars

_workflow_context: contextvars.ContextVar[bool] = contextvars.ContextVar(
    "workflow_context", default=False
)
```

## API Reference

### LangfuseManager Methods

#### `get_handler() -> Optional[CallbackHandler]`

Returns the Langfuse callback handler for LangChain integration.

```python
handler = langfuse_manager.get_handler()
if handler:
    # Tracing is available
    pass
```

#### `get_config(additional_config=None, force_tracing=False) -> dict`

Gets execution config with context-aware tracing.

**Parameters:**
- `additional_config`: Optional dict to merge with tracing config
- `force_tracing`: If True, includes tracing even in workflow context

**Returns:** Configuration dict ready for LangChain runnable methods

```python
# Context-aware (recommended for individual calls)
config = langfuse_manager.get_config()

# Force tracing even in workflow context
config = langfuse_manager.get_config(force_tracing=True)

# With additional configuration
config = langfuse_manager.get_config({"temperature": 0.5})
```

#### `get_workflow_config(additional_config=None) -> dict`

Gets execution config specifically for workflow-level tracing.

**Parameters:**
- `additional_config`: Optional dict to merge with tracing config

**Returns:** Configuration dict with workflow context set

```python
# For LangGraph workflows (recommended)
execution_config = langfuse_manager.get_workflow_config()
workflow.invoke(state, config=execution_config)
```

#### `is_enabled() -> bool`

Checks if Langfuse tracing is enabled and properly configured.

```python
if langfuse_manager.is_enabled():
    print("Tracing is active")
```

#### `reset() -> None`

Resets the handler and context (useful for testing).

```python
langfuse_manager.reset()
```

## Configuration

### Environment Variables

The system supports both direct environment variables and `.env` files:

#### Option 1: Direct Environment Variables
```bash
# Required for tracing
export LANGFUSE_PUBLIC_KEY=pk-lf-your-public-key
export LANGFUSE_SECRET_KEY=sk-lf-your-secret-key

# Optional (defaults to US cloud)
export LANGFUSE_HOST=https://cloud.langfuse.com
```

#### Option 2: .env File (Recommended for Development)
Create a `.env` file in your project root:

```bash
# .env file
APP_ENV=dev
LANGFUSE_PUBLIC_KEY=pk-lf-your-public-key
LANGFUSE_SECRET_KEY=sk-lf-your-secret-key
LANGFUSE_HOST=https://cloud.langfuse.com
```

**Note**: The configuration system automatically loads `.env` files when `APP_ENV` is set to `dev` or `development`. This uses the `python-dotenv` package which is included in the project dependencies.

### Configuration Files

```toml
# configs/base.toml or environment-specific files
[observability.langfuse]
enabled = false  # Set to true to enable tracing
host = "https://cloud.langfuse.com"
# public_key and secret_key loaded from environment variables
```

### Environment-Specific Settings

```toml
# configs/dev.toml
[observability.langfuse]
enabled = true  # Enable in development

# configs/prod.toml
[observability.langfuse]
enabled = true  # Enable in production

# configs/stage.toml
[observability.langfuse]
enabled = false  # Disabled for testing
```

## Usage Patterns

### Workflow Tracing

For LangGraph workflows, use `get_workflow_config()`:

```python
from src.llm.observability import langfuse_manager

def run_job_evaluation_workflow(job_text: str, config: Optional[dict] = None):
    workflow = get_job_evaluation_workflow()
    initial_state = JobEvaluationState(job_posting_text=job_text)

    # Use workflow config - sets context and enables tracing
    execution_config = langfuse_manager.get_workflow_config(config)

    return workflow.invoke(initial_state, config=execution_config)
```

### Individual LLM Calls

For individual LLM calls, use `get_config()` (context-aware):

```python
from src.llm.observability import langfuse_manager

def extract_with_schema(text: str, schema_class: Type):
    client = get_extraction_client()
    structured_llm = client._get_client().with_structured_output(schema_class)

    # Context-aware config - skips tracing if already in workflow
    config_dict = langfuse_manager.get_config()

    return structured_llm.invoke(messages, config=config_dict)
```

### Force Tracing

When you need tracing even within a workflow context:

```python
# Force individual call tracing
config = langfuse_manager.get_config(force_tracing=True)
result = llm.invoke(messages, config=config)
```

## Best Practices

### Do's ✅

1. **Use `get_workflow_config()` for workflows**
   ```python
   config = langfuse_manager.get_workflow_config()
   workflow.invoke(state, config=config)
   ```

2. **Use `get_config()` for individual calls**
   ```python
   config = langfuse_manager.get_config()
   llm.invoke(messages, config=config)
   ```

3. **Check if tracing is enabled before expensive operations**
   ```python
   if langfuse_manager.is_enabled():
       # Perform tracing-specific setup
       pass
   ```

4. **Use environment variables for credentials**
   ```bash
   export LANGFUSE_PUBLIC_KEY=pk-lf-...
   export LANGFUSE_SECRET_KEY=sk-lf-...
   ```

### Don'ts ❌

1. **Don't manually create CallbackHandler instances**
   ```python
   # ❌ Don't do this
   handler = CallbackHandler(public_key=..., secret_key=...)

   # ✅ Do this instead
   handler = langfuse_manager.get_handler()
   ```

2. **Don't use `get_workflow_config()` for individual calls**
   ```python
   # ❌ This creates unnecessary traces
   config = langfuse_manager.get_workflow_config()
   llm.invoke(messages, config=config)

   # ✅ Use context-aware method
   config = langfuse_manager.get_config()
   llm.invoke(messages, config=config)
   ```

3. **Don't hardcode tracing configuration**
   ```python
   # ❌ Don't hardcode
   config = {"callbacks": [some_handler]}

   # ✅ Use manager methods
   config = langfuse_manager.get_config()
   ```

## Troubleshooting

### Common Issues

#### Tracing Not Working

1. **Check configuration**:
   ```python
   print(f"Enabled: {langfuse_manager.is_enabled()}")
   ```

2. **Verify environment variables**:
   ```bash
   echo $LANGFUSE_PUBLIC_KEY
   echo $LANGFUSE_SECRET_KEY
   ```

   **If using .env file**: Ensure `APP_ENV=dev` is set and the file is in the project root.

3. **Check config files**:
   ```toml
   [observability.langfuse]
   enabled = true
   ```

#### Duplicate Traces

If you see duplicate traces, ensure you're using the correct methods:

```python
# ✅ For workflows
config = langfuse_manager.get_workflow_config()

# ✅ For individual calls (context-aware)
config = langfuse_manager.get_config()
```

#### Missing Traces

If traces are missing, check if you're in a workflow context:

```python
# Force tracing if needed
config = langfuse_manager.get_config(force_tracing=True)
```

### Debug Mode

Enable debug logging to troubleshoot tracing issues:

```python
import logging
logging.getLogger('src.llm.observability').setLevel(logging.DEBUG)
```

## Testing

### Unit Tests

The tracing system includes comprehensive tests:

```bash
# Run tracing tests
pytest tests/unit/llm/observability/test_langfuse.py -v

# Run integration tests
pytest tests/integration/agent/test_workflow_integration.py -v
```

### Test Patterns

```python
from src.llm.observability import LangfuseManager

def test_context_aware_tracing():
    manager = LangfuseManager()

    # Test workflow context
    config = manager.get_workflow_config()
    assert "callbacks" in config

    # Test individual call context
    config = manager.get_config()
    # Should be empty if in workflow context
```

## Performance Considerations

### Handler Caching

The system caches handlers to avoid repeated initialization:

```python
# First call initializes and caches
handler1 = langfuse_manager.get_handler()

# Subsequent calls reuse cached handler
handler2 = langfuse_manager.get_handler()
assert handler1 is handler2
```

### Context Variables

Context variables are thread-local and have minimal performance impact:

- **Memory**: Negligible per-thread overhead
- **CPU**: O(1) context lookups
- **Concurrency**: Thread-safe without locks

## Future Enhancements

### Planned Features

1. **Custom Trace Metadata**: Add workflow-specific metadata to traces
2. **Performance Metrics**: Automatic latency and token usage tracking
3. **Error Correlation**: Link errors to specific trace spans
4. **Multi-Provider Support**: Support for other observability platforms

### Extension Points

The system is designed for extensibility:

```python
class CustomObservabilityManager(LangfuseManager):
    def get_config(self, additional_config=None, force_tracing=False):
        # Custom logic here
        return super().get_config(additional_config, force_tracing)
```

## Related Documentation

- [Configuration Management](configuration.md) - How observability settings are managed
- [Agent Infrastructure](agent-infrastructure.md) - How tracing integrates with workflows
- [Architecture Overview](../architecture.md) - System-wide architecture context
