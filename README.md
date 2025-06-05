# Job Search Assistant

An AI-powered job search assistant who does the work and get the job for you.

## Features

### Core Features
- **Job Evaluation**: Analyze job descriptions to determine fit based on your preferences and qualifications
- **Resume Customization**: Automatically tailor your resume for specific job applications

### Planned Features
- Integration with LinkedIn and other job search platforms
- Automated job application submission
- Application tracking and management
- Interview preparation assistance

## Architecture

The Job Search Assistant follows a **modular, agent-based architecture** designed for scalability and maintainability:

### Core Architecture Principles
- **Agent-Based Design**: Uses LangGraph agents for orchestrating AI-driven workflows
- **Separation of Concerns**: Clean separation between UI, business logic, and data layers
- **Provider Abstraction**: Pluggable LLM providers for flexibility and future extensibility
- **Configuration-Driven**: TOML for developer settings, YAML for user preferences

### System Components

```
┌─────────────────┐    ┌─────────────────┐    ┌─────────────────┐
│   Streamlit UI  │    │   LangGraph     │    │   LLM Provider  │
│                 │    │    Agents       │    │   (Anthropic)   │
│  ┌─────────────┐│    │                 │    │                 │
│  │   Pages     ││    │ ┌─────────────┐ │    │ ┌─────────────┐ │
│  │ Components  ││───▶│ │ Job Agent   │ │───▶│ │   AI APIs   │ │
│  └─────────────┘│    │ │ Resume Agent│ │    │ │  (Future:   │ │
└─────────────────┘    │ └─────────────┘ │    │ │ Fireworks)  │ │
                       └─────────────────┘    │ └─────────────┘ │
                                              └─────────────────┘
          │                       │                       │
          ▼                       ▼                       ▼
┌─────────────────┐    ┌─────────────────┐    ┌─────────────────┐
│  Core Business  │    │   Data Layer    │    │   Observability │
│     Logic       │    │                 │    │                 │
│                 │    │ ┌─────────────┐ │    │ ┌─────────────┐ │
│ ┌─────────────┐ │    │ │   Models    │ │    │ │  Langfuse   │ │
│ │Job Evaluation│ │    │ │  Storage    │ │    │ │ Monitoring  │ │
│ │Resume Custom │ │───▶│ │ Persistence │ │    │ └─────────────┘ │
│ └─────────────┘ │    │ └─────────────┘ │    └─────────────────┘
└─────────────────┘    └─────────────────┘
```

### Data Flow
1. **User Input** → Streamlit UI captures job descriptions and user preferences
2. **Agent Orchestration** → LangGraph agents process requests using defined workflows
3. **AI Processing** → LLM providers analyze and generate customized content
4. **Core Logic** → Business rules for job evaluation and resume customization
5. **Results** → Processed output returned to user through UI

## Tech Stack

### **Core Language & Runtime**
- **Python 3.11+** - Primary language with modern features
- **uv** - Ultra-fast package and environment management

### **AI & Machine Learning**
- **LangChain** - LLM orchestration and prompt management
- **LangGraph** - Agent workflows and state management
- **Anthropic API** - Primary LLM provider (Claude models)
- **Langfuse** - LLM observability and performance monitoring
- *Future: Fireworks AI for open-source models*

### **Data & Validation**
- **Pydantic** - Data validation, serialization, and configuration management
- **TOML** - Developer-facing configuration (pyproject.toml, settings)
- **YAML** - User-facing configuration (preferences, templates)

### **User Interface**
- **Streamlit** - Interactive web UI with real-time updates
- Component-based architecture for reusability

### **Development & Testing**
- **pytest** - Testing framework with fixtures and coverage
- **Black** - Code formatting
- **isort** - Import sorting
- **mypy** - Static type checking
- **GitHub Actions** - CI/CD pipeline

### **Architecture Patterns**
- **Modular Design** - Separate packages for core, agents, UI, and utilities
- **Provider Pattern** - Abstracted LLM and data storage interfaces
- **Agent Pattern** - LangGraph-based workflow orchestration
- **Configuration Management** - Environment-specific settings

## Configuration Files

The project uses two types of configuration files for clarity and ease of use:

- **TOML**: Used for developer-facing and internal configuration, such as project metadata and core settings. Example: `pyproject.toml` contains dependency and tool configuration for Python tooling.
- **YAML**: Used for user-facing and editable configuration, such as job preferences and resume templates. Example: `examples/job_preferences.yaml` allows you to specify your preferred job titles, locations, and salary expectations.

### Example: User Preferences (YAML)
```yaml
preferred_titles:
  - Data Scientist
  - Machine Learning Engineer
locations:
  - Remote
  - San Francisco, CA
salary_expectation:
  min: 120000
  max: 180000
```

### Example: Project Settings (TOML)
```toml
[tool.job_search_assistant]
llm_provider = "anthropic"
log_level = "INFO"
```

- **Developers** should edit TOML files for project setup and internal settings.
- **End-users** can safely edit YAML files to customize their experience.

## Getting Started

### Prerequisites
- **Python 3.11+** (automatically managed by uv)
- **uv** package manager ([installation guide](https://docs.astral.sh/uv/getting-started/installation/))
- Git

### Installation

1. **Clone the repository**
```bash
git clone https://github.com/georgeliu1998/job_search_assistant.git
cd job_search_assistant
```

2. **Set up Python environment** (uv handles everything automatically)
```bash
# uv will automatically:
# - Install Python 3.11 if needed
# - Create virtual environment
# - Install all dependencies
uv sync
```

### Usage

**Option 1: Using uv commands (recommended)**
```bash
# Run Python scripts
uv run python your_script.py

# Start the Streamlit UI
uv run streamlit run ui/app.py

# Run tests
uv run pytest

# Run with specific Python version
uv run --python 3.11 python your_script.py
```

**Option 2: Traditional virtual environment activation**
```bash
# Activate virtual environment manually
source .venv/bin/activate  # On Windows: .venv\Scripts\activate

# Then run commands normally
python your_script.py
streamlit run ui/app.py
pytest
```

### Development Setup

Install development dependencies:
```bash
# Install dev dependencies (already included in project)
uv sync --extra dev
```

#### Code Formatting and Quality (Automated)

This project uses **pre-commit hooks** to automatically format and check code quality. After setting up your environment, install the hooks:

```bash
uv run pre-commit install
```

Now, every time you commit, the code will be automatically:
- Formatted with **Black**
- Import-sorted with **isort**
- Type-checked with **mypy**
- Checked for basic issues (trailing whitespace, large files, etc.)

#### Manual Formatting (Optional)

You can also run formatting manually:

```bash
# Quick format script
./scripts/format.sh

# Or run individual tools
uv run black src tests ui
uv run isort src tests ui
uv run mypy src

# Run tests with coverage
uv run pytest --cov=src
```

### Environment Information

- **Python Version**: 3.11.12 (pinned in `.python-version`)
- **Virtual Environment**: `.venv/` (automatically created by uv)
- **Dependencies**: Locked in `uv.lock` for reproducible builds
- **Configuration**: `pyproject.toml` with project metadata and tool settings

## How to Run the App

### 🚀 Quick Start (Recommended)

1. **Set up your environment:**
```bash
# Copy the environment template
cp env.example .env

# Edit .env and add your Anthropic API key
# ANTHROPIC_API_KEY=your_actual_api_key_here
```

2. **Run the app:**
```bash
# Easy way - using the provided script
uv run python run_app.py

# Or manually
uv run streamlit run ui/app.py
```

3. **Open your browser** to `http://localhost:8501` and start evaluating jobs!

### 📋 Environment Setup

The app requires an Anthropic API key to function. Here's how to set it up:

1. **Get an Anthropic API key:**
   - Visit [Anthropic Console](https://console.anthropic.com/)
   - Create an account and generate an API key

2. **Configure your environment:**
```bash
# Copy the example file
cp env.example .env

# Edit .env with your actual keys
ANTHROPIC_API_KEY=your_anthropic_api_key_here

# Optional: Add Langfuse for observability
LANGFUSE_PUBLIC_KEY=your_key
LANGFUSE_SECRET_KEY=your_secret
LANGFUSE_ENABLED=true
```

### 🎯 Current Features

- **Job Evaluation**: Paste a job description and get AI-powered analysis
  - Salary range analysis ($160,000+ preferred)
  - Remote work compatibility
  - Experience level matching
  - Skills alignment assessment

- **Coming Soon**: Resume customization and user preferences

### 🛠️ Alternative Running Methods

**Using uv (recommended):**
```bash
uv run streamlit run ui/app.py
```

**Using traditional Python:**
```bash
# Activate virtual environment
source .venv/bin/activate  # Windows: .venv\Scripts\activate

# Run the app
streamlit run ui/app.py
```

**For development:**
```bash
# Run with automatic reloading
uv run streamlit run ui/app.py --server.runOnSave true
```

## Contributing

1. Fork the repository
2. Create a feature branch: `git checkout -b feature-name`
3. Set up pre-commit hooks: `uv run pre-commit install`
4. Make your changes and ensure tests pass: `uv run pytest`
5. Commit your changes (pre-commit will automatically format and check your code)
6. Submit a pull request

**Note**: Pre-commit hooks will automatically format your code with Black and isort, so you don't need to run them manually!

## License
This project is licensed under the MIT License - see the LICENSE file for details.
