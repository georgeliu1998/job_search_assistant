# Tracing Quick Reference

[← Back to Documentation](README.md)

Quick reference for using the context-aware Langfuse tracing system in the Job Search Assistant.

## TL;DR

```python
from src.llm.observability import langfuse_manager

# ✅ For LangGraph workflows
config = langfuse_manager.get_workflow_config()
workflow.invoke(state, config=config)

# ✅ For individual LLM calls (context-aware)
config = langfuse_manager.get_config()
llm.invoke(messages, config=config)
```

## Setup

### 1. Environment Variables

**Option A: Direct export**
```bash
export LANGFUSE_PUBLIC_KEY=pk-lf-your-public-key
export LANGFUSE_SECRET_KEY=sk-lf-your-secret-key
export LANGFUSE_HOST=https://cloud.langfuse.com  # Optional
```

**Option B: .env file (recommended)**
```bash
# Copy the example file and edit it
cp env.example .env
# Then edit .env with your actual keys
```

### 2. Enable in Config

```toml
# configs/dev.toml or configs/prod.toml
[observability.langfuse]
enabled = true
```

## Common Patterns

### Workflow Tracing

```python
from src.llm.observability import langfuse_manager

def my_workflow(input_data, user_config=None):
    workflow = get_my_workflow()

    # Sets workflow context, enables tracing
    execution_config = langfuse_manager.get_workflow_config(user_config)

    return workflow.invoke(input_data, config=execution_config)
```

### Individual LLM Calls

```python
from src.llm.observability import langfuse_manager

def call_llm(messages):
    client = get_llm_client()

    # Context-aware: skips tracing if already in workflow
    config = langfuse_manager.get_config()

    return client.invoke(messages, config=config)
```

### Force Tracing

```python
# Force tracing even if in workflow context
config = langfuse_manager.get_config(force_tracing=True)
result = llm.invoke(messages, config=config)
```

## Troubleshooting

### No Traces Appearing

```python
# Check if enabled
print(f"Tracing enabled: {langfuse_manager.is_enabled()}")

# Check handler
handler = langfuse_manager.get_handler()
print(f"Handler available: {handler is not None}")
```

### Duplicate Traces

Make sure you're using the right methods:

```python
# ❌ Wrong - creates duplicate traces
config = langfuse_manager.get_workflow_config()  # Don't use for individual calls
llm.invoke(messages, config=config)

# ✅ Correct - context-aware
config = langfuse_manager.get_config()  # Use for individual calls
llm.invoke(messages, config=config)
```

### Missing Individual Call Traces

If you need individual call traces within a workflow:

```python
# Force tracing for specific calls
config = langfuse_manager.get_config(force_tracing=True)
result = llm.invoke(messages, config=config)
```

## Testing

```python
from src.llm.observability import langfuse_manager

def test_my_function():
    # Reset context for clean test
    langfuse_manager.reset()

    # Your test code here
    pass
```

## API Quick Reference

| Method | Use Case | Context-Aware |
|--------|----------|---------------|
| `get_workflow_config()` | LangGraph workflows | No (always traces) |
| `get_config()` | Individual LLM calls | Yes (skips if in workflow) |
| `get_config(force_tracing=True)` | Force individual tracing | No (always traces) |
| `get_handler()` | Direct handler access | N/A |
| `is_enabled()` | Check if tracing active | N/A |
| `reset()` | Reset for testing | N/A |

## Environment-Specific Behavior

| Environment | Default Enabled | Purpose |
|-------------|----------------|---------|
| `dev` | `true` | Development debugging |
| `prod` | `true` | Production monitoring |
| `stage` | `false` | Testing without noise |

## Example Script

Test your tracing setup with the provided example:

```bash
# Set up environment
export LANGFUSE_PUBLIC_KEY=pk-lf-your-key
export LANGFUSE_SECRET_KEY=sk-lf-your-key
export APP_ENV=dev

# Run the example
python docs/examples/tracing-example.py
```

For detailed documentation, see [Observability & Tracing Design](design/observability-tracing.md).
