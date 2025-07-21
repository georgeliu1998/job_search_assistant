# Job Search Assistant

AI-powered job search assistant who does the heavy lifting and gets the job for you.

## Features

### ✅ Available Now
- **Job Evaluation**: AI-powered analysis of job descriptions against your criteria
  - Salary range evaluation ($100,000+ minimum)
  - Remote work compatibility check
  - Experience level matching
  - Skills alignment assessment

### 🚧 Coming Soon
- Resume customization and optimization
- User preference configuration
- LinkedIn integration and job discovery
- Automated job application submission
- Job application tracking
- Interview preparation assistance

## Quick Start

### Prerequisites
- **Python 3.11+** (automatically managed by uv)
- **uv** package manager ([installation guide](https://docs.astral.sh/uv/getting-started/installation/))
- **Anthropic API Key** (required for AI functionality)

### Installation & Setup

1. **Clone and install**
```bash
git clone https://github.com/georgeliu1998/job_search_assistant.git
cd job_search_assistant
uv sync  # Installs Python 3.11 + all dependencies automatically
```

2. **Set up environment variables**

Create a `.env` file in the project root:
```bash
# Required: Anthropic API key for AI functionality
ANTHROPIC_API_KEY=your_anthropic_api_key_here

# Optional: Application environment (dev, stage, prod)
APP_ENV=dev
```

For complete setup including optional services (Langfuse, Fireworks), see the [detailed installation guide](docs/installation.md).

3. **Run the application**
```bash
uv run streamlit run ui/app.py
```

4. **Open your browser** to `http://localhost:8501` and start evaluating jobs!

## Configuration

The application uses TOML configuration files in the `configs/` directory:
- `base.toml` - Default settings and complete configuration structure
- `dev.toml` - Development environment overrides
- `stage.toml` - Staging environment overrides
- `prod.toml` - Production environment settings

Key configuration areas:
- **LLM Settings**: Model selection, temperature, token limits
- **Evaluation Criteria**: Salary thresholds, remote work requirements
- **Observability**: Langfuse integration for monitoring

For detailed configuration information, see the [configuration management design](docs/design/configuration.md).

## Development

### Setup Development Environment
```bash
# Install with development dependencies
uv sync --extra dev

# Install pre-commit hooks for code quality
uv run pre-commit install
```

### Code Quality (Automated)
Pre-commit hooks automatically handle:
- **Black** code formatting
- **isort** import sorting
- **mypy** type checking
- Basic file checks

### Manual Commands
```bash
# Run tests
uv run pytest

# Run tests with coverage
uv run pytest --cov=src

# Manual formatting
./scripts/format.sh

# Type checking
uv run mypy src
```

## Project Structure

```
job_search_assistant/
├── src/                    # Main application code
│   ├── agents/            # LangGraph agents (job evaluation)
│   ├── config/            # Configuration management
│   ├── core/              # Business logic
│   ├── llm/               # LLM clients and prompts
│   ├── models/            # Pydantic data models
│   └── utils/             # Utilities and logging
├── ui/                    # Streamlit web interface
│   ├── components/        # Reusable UI components
│   ├── pages/             # Application pages
│   └── utils/             # UI utilities
├── configs/               # TOML configuration files
├── tests/                 # Test suite
└── docs/                  # Documentation
```

## Contributing

1. Fork the repository
2. Create a feature branch: `git checkout -b feature-name`
3. Install pre-commit hooks: `uv run pre-commit install`
4. Make your changes and ensure tests pass: `uv run pytest`
5. Commit your changes (pre-commit will automatically format your code)
6. Submit a pull request

## License

This project is licensed under the MIT License - see the [LICENSE](LICENSE) file for details.
