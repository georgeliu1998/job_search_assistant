# Configuration Management Design

[← Back to Documentation](../README.md)

## Overview

The Job Search Assistant uses a TOML-based configuration system that supports environment-specific overrides, type-safe loading, and centralized management of all application settings.

## Design Goals

1. **Environment Separation**: Different settings for development, staging, and production
2. **Type Safety**: Configuration values are validated and typed using Pydantic models
3. **Centralized Management**: All configuration in one place with clear structure
4. **Runtime Flexibility**: Configuration can be updated without code changes
5. **Validation**: Automatic validation of configuration values and relationships

## Configuration Structure

### File Organization

```
configs/
├── base.toml      # Complete configuration with all defaults
├── dev.toml       # Development environment overrides
├── stage.toml     # Staging environment overrides
└── prod.toml      # Production environment overrides
```

### Configuration Sections

#### General Settings
```toml
[general]
name = "job-search-assistant"
tagline = "AI-powered job search assistant"
version = "0.1.0"
debug = false
```

#### Logging Configuration
```toml
[logging]
level = "INFO"
format = "%(asctime)s %(name)s [%(levelname)s] %(message)s"
```

#### Agent LLM Configuration
Each agent task directly defines the LLM it uses (provider, model, and
sampling settings). Two tasks can share the same model with different
settings simply by repeating the model with different values.
```toml
[agent_tasks.job_evaluation_extraction]
provider = "google"
model = "gemini-2.5-flash"
temperature = 0.0
max_tokens = 4096

[agent_tasks.interview_question_generation]
provider = "google"
model = "gemini-2.5-flash-lite"
temperature = 0.7
max_tokens = 4096
```

#### Business Logic Parameters
```toml
[evaluation_criteria]
min_salary = 100000
remote_required = true
ic_title_requirements = ["lead", "staff", "principal", "senior staff"]
```

#### Observability
```toml
[observability.langfuse]
enabled = false
host = "https://us.cloud.langfuse.com"
```

## TOML Structure and Access Patterns

### Understanding TOML-to-Python Mapping

The TOML configuration structure translates to Python data structures in specific ways:

#### 1. Nested Sections → Pydantic Models (Attribute Access)
```toml
[evaluation_criteria]
min_salary = 100000
remote_required = true
```
Becomes a Pydantic model accessible via **attributes**:
```python
config.evaluation_criteria.min_salary        # ✅ Works
config.evaluation_criteria.remote_required   # ✅ Works
```

#### 2. Per-Task LLM Config → Pydantic Models (Attribute Access)
```toml
[agent_tasks.job_evaluation_extraction]
provider = "google"
model = "gemini-2.5-flash"

[agent_tasks.interview_question_generation]
provider = "google"
model = "gemini-2.5-flash-lite"
```
Each task becomes an `LLMConfig` accessible via **attributes** on
`config.agent_tasks`:
```python
config.agent_tasks.job_evaluation_extraction          # ✅ LLMConfig
config.agent_tasks.job_evaluation_extraction.provider  # ✅ Attribute access
config.agent_tasks.job_evaluation_extraction.model     # ✅ Attribute access
```

### Why This Design?

- **Intuitive**: The model a task uses is defined in one place, not via an indirection layer
- **Type Safety**: Each task's LLM settings are validated as an `LLMConfig` Pydantic model
- **Per-task flexibility**: Two tasks can share a model with different settings (e.g. temperature) without inventing distinct profile names, and overrides in `dev.toml`/`prod.toml` apply per task

## Configuration Loading Strategy

### 1. Base Configuration
- `base.toml` contains all possible configuration options with sensible defaults
- Serves as the complete configuration schema
- All other files override specific values

### 2. Environment-Specific Overrides
- Environment is determined by `APP_ENV` environment variable
- Corresponding `.toml` file is loaded and merged with base configuration
- Only changed values need to be specified in environment files

### 3. Environment Variable Overrides
- Sensitive values (API keys) are loaded from environment variables
- Environment variables take precedence over file-based configuration
- Follows the pattern: `LANGFUSE_PUBLIC_KEY`, `ANTHROPIC_API_KEY`

## Implementation Details

### Configuration Manager
The `src/config/manager.py` module provides:

- **Type-safe loading**: Configuration is loaded into Pydantic models
- **Validation**: Automatic validation of configuration values
- **Environment detection**: Automatic detection of current environment
- **Caching**: Configuration is cached after first load

### Configuration Models
Pydantic models in `src/config/models.py` define:

- **Configuration structure**: All configuration sections and their types
- **Validation rules**: Constraints and validation logic
- **Default values**: Sensible defaults for all configuration options

### Usage Pattern
```python
from src.config.manager import config

# Access typed configuration values directly
min_salary = config.evaluation_criteria.min_salary

# The config proxy provides lazy loading - configuration is loaded automatically
# on first access and cached for subsequent uses.
# Each agent task carries its own LLM config (an LLMConfig):
extraction_llm = config.agent_tasks.job_evaluation_extraction
model = get_chat_model(extraction_llm)
```

## Benefits of This Design

### 1. Environment Isolation
- Clear separation between development, staging, and production settings
- No risk of accidentally using production settings in development
- Easy to add new environments (e.g., `test.toml`)

### 2. Type Safety
- Configuration errors are caught at startup
- IDE support for configuration access
- Clear documentation of all available options

### 3. Maintainability
- All configuration in one place
- Easy to understand what can be configured
- Simple to add new configuration options

### 4. Security
- Sensitive values stored in environment variables
- No secrets committed to version control
- Clear separation of sensitive vs. non-sensitive configuration
