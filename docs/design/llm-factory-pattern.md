# LLM Factory Pattern Design

## Overview

The Job Search Assistant uses a **Factory Pattern** to manage multiple LLM providers, enabling seamless switching between different AI services (Anthropic, Google, OpenAI, etc.) without code changes. This design provides flexibility, extensibility, and clean separation of concerns.

## Architecture

### Core Components

```
src/llm/
├── common/
│   ├── factory.py          # LLMClientFactory and registration logic
│   └── base.py             # BaseLLMClient abstract base class
├── clients/
│   ├── anthropic.py        # Anthropic client implementation
│   ├── google.py           # Google client implementation
│   └── [future providers]  # New providers go here
└── __init__.py             # Public factory interface
```

### Class Hierarchy

```mermaid
graph TD
    A[LLMClientFactory] --> B[AnthropicClient]
    A --> C[GoogleClient]
    A --> D[OpenAIClient]
    A --> E[Future Providers...]

    B --> F[BaseLLMClient]
    C --> F
    D --> F
    E --> F

    F --> G[@singleton decorator]

    H[get_llm_client] --> A
    I[get_llm_client_by_profile_name] --> A
```

## Factory Pattern Benefits

### ✅ **Extensibility**
- Add new providers without modifying existing code
- Plugin-like architecture for third-party integrations
- Runtime provider registration

### ✅ **Consistency**
- Unified interface across all providers
- Standardized configuration and error handling
- Common logging and observability

### ✅ **Flexibility**
- Switch providers via configuration
- Multiple factory instances with different provider sets
- Environment-specific provider configurations

### ✅ **Resource Efficiency**
- Singleton pattern prevents duplicate client instances
- Lazy loading of provider-specific dependencies
- Connection reuse and pooling

## Usage Patterns

### Basic Client Creation

```python
from src.llm import get_llm_client
from src.config.models import LLMProfileConfig

# Create client via factory
config = LLMProfileConfig(
    provider="anthropic",
    model="claude-3-5-haiku-20241022",
    api_key="your-api-key"
)
client = get_llm_client(config)

# Use the client
response = client.invoke([{"role": "user", "content": "Hello!"}])
```

### Configuration-Based Creation

```python
from src.llm import get_llm_client_by_profile_name

# Uses profile from configs/base.toml
client = get_llm_client_by_profile_name("anthropic_extraction")
```

### Direct Factory Usage

```python
from src.llm import LLMClientFactory

factory = LLMClientFactory()
client = factory.create_client(config)
```

## Provider Registration

The factory supports two types of provider registration with different persistence behaviors:

### 1. Code-Level Registration (Persistent)

**When to Use**: For core, production-ready providers that should always be available.

**How**: Modify `_DEFAULT_PROVIDERS` in `src/llm/common/factory.py`

```python
# src/llm/common/factory.py
_DEFAULT_PROVIDERS: Dict[str, str] = {
    "anthropic": "src.llm.clients.anthropic.AnthropicClient",
    "google": "src.llm.clients.google.GoogleClient",
    "openai": "src.llm.clients.openai.OpenAIClient",  # ← Added permanently
}
```

**Benefits**:
- ✅ Available across all application instances
- ✅ Persists across Python process restarts
- ✅ Part of the stable, tested codebase
- ✅ Included in version control

### 2. Runtime Registration (Session-Level)

**When to Use**: For plugins, testing, experimentation, or conditional providers.

**How**: Use `register_provider()` function

```python
from src.llm import register_provider

# Global registration (affects convenience functions)
register_provider("openai", "src.llm.clients.openai.OpenAIClient")

# Instance-specific registration
factory = LLMClientFactory()
factory.register_provider("custom", "plugins.custom.CustomClient")
```

**Benefits**:
- ✅ Runtime flexibility
- ✅ No code changes required
- ✅ Perfect for plugins and extensions
- ✅ Isolated testing environments

### Registration Persistence Comparison

| Method | Scope | Persistence | Use Case |
|--------|--------|-------------|----------|
| `_DEFAULT_PROVIDERS` | Global/Code | ✅ Persistent | Core providers, production |
| `register_provider()` | Instance/Session | ❌ Not persistent | Runtime, testing, plugins |

## Implementation Guide

### Adding a New Core Provider

**Step 1**: Implement the client class

```python
# src/llm/clients/openai.py
from src.llm.common.base import BaseLLMClient
from src.utils.singleton import singleton

@singleton
class OpenAIClient(BaseLLMClient):
    """OpenAI LLM client implementation."""

    def __init__(self, config: LLMProfileConfig):
        super().__init__(config)

        if config.provider != "openai":
            raise LLMProviderError(f"Expected openai provider, got: {config.provider}")

        self._ensure_api_key("OPENAI_API_KEY", "Enter your OpenAI API key: ")

    def _initialize_client(self):
        # Initialize OpenAI client
        pass

    def invoke(self, messages: List[Any], config: dict = None) -> Any:
        # Implement OpenAI-specific invocation
        pass

    def get_model_name(self) -> str:
        return self.config.model
```

**Step 2**: Add to default providers

```python
# src/llm/common/factory.py
_DEFAULT_PROVIDERS: Dict[str, str] = {
    "anthropic": "src.llm.clients.anthropic.AnthropicClient",
    "google": "src.llm.clients.google.GoogleClient",
    "openai": "src.llm.clients.openai.OpenAIClient",  # ← Add here
}
```

**Step 3**: Update configuration validation

```python
# src/config/models.py - Add to VALID_MODELS
VALID_MODELS: ClassVar[Dict[str, set]] = {
    "anthropic": {"claude-3-5-haiku-20241022", ...},
    "google": {"gemini-2.5-flash", ...},
    "openai": {"gpt-4", "gpt-3.5-turbo", ...},  # ← Add models
}
```

**Step 4**: Add configuration profile

```toml
# configs/base.toml
[llm_profiles.openai_extraction]
provider = "openai"
model = "gpt-4"
temperature = 0.0
max_tokens = 512
```

### Adding a Plugin Provider

```python
# plugins/custom_ai.py
from src.llm.common.base import BaseLLMClient

class CustomAIClient(BaseLLMClient):
    # Implementation...

# Application startup
def load_plugins():
    from src.llm import register_provider
    register_provider("custom_ai", "plugins.custom_ai.CustomAIClient")
```

## Testing Strategy

### Factory Testing

```python
# Test provider registration
def test_register_new_provider():
    factory = LLMClientFactory()
    factory.register_provider("test", "tests.mocks.TestClient")
    assert factory.is_provider_supported("test")

# Test singleton behavior
def test_singleton_across_factories():
    factory1 = LLMClientFactory()
    factory2 = LLMClientFactory()

    client1 = factory1.create_client(config)
    client2 = factory2.create_client(config)

    assert client1 is client2  # Same singleton instance
```

### Mock Providers for Testing

```python
# tests/mocks/mock_client.py
class MockLLMClient(BaseLLMClient):
    def invoke(self, messages, config=None):
        return {"content": "Mock response"}

    def get_model_name(self):
        return "mock-model"

    def _initialize_client(self):
        return Mock()

# In tests
def test_feature_with_mock_llm():
    factory = LLMClientFactory()
    factory.register_provider("mock", "tests.mocks.mock_client.MockLLMClient")

    config = LLMProfileConfig(provider="mock", model="test", api_key="test")
    client = factory.create_client(config)
    # Test your feature...
```

## Error Handling

### Unsupported Provider

```python
try:
    client = get_llm_client(config)
except LLMProviderError as e:
    # Error: "Unsupported LLM provider: 'unknown'.
    #         Available providers: anthropic, google.
    #         Use register_provider() to add new providers."
```

### Provider Import Failures

```python
# Factory handles import errors gracefully
register_provider("broken", "non.existent.Client")

try:
    client = factory.create_client(config)
except LLMProviderError as e:
    # Error: "Failed to import client for provider 'broken':
    #         No module named 'non.existent'"
```

### Invalid Client Classes

```python
# Factory validates inheritance
class InvalidClient:  # Doesn't inherit from BaseLLMClient
    pass

register_provider("invalid", "path.to.InvalidClient")
# Error: "Client class must inherit from BaseLLMClient"
```

## Configuration Integration

### Profile-Based Usage

```python
# configs/base.toml
[agents]
job_evaluation_extraction = "anthropic_extraction"

[llm_profiles.anthropic_extraction]
provider = "anthropic"
model = "claude-3-5-haiku-20241022"
temperature = 0.0
max_tokens = 512

# Application code
from src.llm import get_llm_client_by_profile_name
client = get_llm_client_by_profile_name("anthropic_extraction")
```

### Environment-Specific Providers

```toml
# configs/dev.toml - Development environment
[llm_profiles.extraction]
provider = "anthropic"  # Use real provider in dev

# configs/stage.toml - Testing environment
[llm_profiles.extraction]
provider = "mock"  # Use mock provider in testing
```

## Best Practices

### ✅ **Do**

- Use `get_llm_client()` for most client creation
- Register core providers in `_DEFAULT_PROVIDERS`
- Use `register_provider()` for plugins and testing
- Follow the singleton pattern for new provider implementations
- Implement comprehensive error handling
- Use type hints and proper documentation

### ❌ **Don't**

- Import client classes directly (use factory instead)
- Modify `_DEFAULT_PROVIDERS` for experimental providers
- Create multiple factory instances unnecessarily
- Bypass the factory pattern for client creation
- Forget to validate provider-specific configuration
- Mix factory and direct instantiation patterns

## Migration Guide

### From Direct Imports

**Before:**
```python
from src.llm.clients.anthropic import AnthropicClient
client = AnthropicClient(config)
```

**After:**
```python
from src.llm import get_llm_client
client = get_llm_client(config)
```

### From Manual Client Management

**Before:**
```python
if provider == "anthropic":
    client = AnthropicClient(config)
elif provider == "google":
    client = GoogleClient(config)
else:
    raise ValueError(f"Unsupported provider: {provider}")
```

**After:**
```python
from src.llm import get_llm_client
client = get_llm_client(config)  # Factory handles provider selection
```

## Future Enhancements

### Planned Features

- **Auto-discovery**: Automatic provider registration from plugins directory
- **Health checks**: Provider availability and status monitoring
- **Load balancing**: Distribute requests across multiple provider instances
- **Fallback chains**: Automatic failover between providers
- **Rate limiting**: Per-provider request throttling
- **Metrics**: Provider usage statistics and performance monitoring

### Extension Points

- **Custom factories**: Specialized factories for different use cases
- **Provider middleware**: Request/response transformation layers
- **Configuration adapters**: Dynamic configuration from external sources
- **Client decorators**: Cross-cutting concerns (retry, cache, etc.)

---

*This document is part of the Job Search Assistant architecture documentation. For implementation details, see the source code in `src/llm/common/factory.py`.*
