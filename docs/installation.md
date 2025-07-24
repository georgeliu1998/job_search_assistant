# Installation Guide

[← Back to Documentation](README.md)

## Prerequisites

### System Requirements
- **Python 3.11+**: The application requires Python 3.11 or higher
- **uv**: Modern Python package manager for dependency management
- **Git**: For cloning the repository

### Required API Keys
- **Anthropic API Key**: Required for AI functionality
- **Langfuse Keys** (Optional): For LLM observability and monitoring

## Quick Installation

### 1. Clone the Repository
```bash
git clone https://github.com/georgeliu1998/job_search_assistant.git
cd job_search_assistant
```

### 2. Install Dependencies
```bash
# Install uv if you haven't already
curl -LsSf https://astral.sh/uv/install.sh | sh

# Install Python 3.11 and all dependencies
uv sync
```

### 3. Set Up Environment Variables
```bash
# Create a .env file in the project root (see Detailed Setup section for template)
nano .env
```

Add your API keys using the template shown in the [Detailed Setup](#environment-configuration) section below.

### 4. Run the Application
```bash
uv run streamlit run ui/app.py
```

### 5. Open Your Browser
Navigate to `http://localhost:8501` to access the application.

## Detailed Setup

### Environment Configuration

Create a `.env` file in the project root with the following variables:

```bash
# Required: Anthropic API key for AI functionality
ANTHROPIC_API_KEY=your_anthropic_api_key_here

# Optional: Application environment (dev, stage, prod)
APP_ENV=dev

# Optional: Fireworks AI API key (alternative LLM provider)
FIREWORKS_API_KEY=your_fireworks_api_key_here

# Optional: Langfuse observability (for monitoring LLM interactions)
LANGFUSE_PUBLIC_KEY=your_langfuse_public_key
LANGFUSE_SECRET_KEY=your_langfuse_secret_key
```

### Getting API Keys

#### Anthropic API Key
1. Visit [Anthropic Console](https://console.anthropic.com/)
2. Create an account and generate an API key
3. Copy the key to your `.env` file

#### Langfuse Keys (Optional)
1. Sign up at [Langfuse](https://langfuse.com/)
2. Create a new project
3. Get your public and secret keys from the project settings
4. Add them to your `.env` file

### Development Setup

For development work, install additional dependencies:

```bash
# Install with development dependencies
uv sync --extra dev

# Install pre-commit hooks for code quality
uv run pre-commit install
```

## Configuration

### Environment-Specific Settings

The application uses TOML configuration files in the `configs/` directory:

- `base.toml`: Complete configuration with all defaults
- `dev.toml`: Development environment overrides
- `stage.toml`: Staging environment overrides
- `prod.toml`: Production environment settings

### Key Configuration Areas

#### LLM Settings
```toml
[llm_profiles.anthropic_extraction]
provider = "anthropic"
model = "claude-3-5-haiku-20241022"
temperature = 0.0
max_tokens = 512
```

#### Evaluation Criteria
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

## Verification

### 1. Check Installation
```bash
# Verify Python version
python --version  # Should be 3.11+

# Verify uv installation
uv --version

# Check if dependencies are installed
uv run python -c "import streamlit, langgraph, anthropic; print('All dependencies installed!')"
```

### 2. Test Configuration
```bash
# Test configuration loading
uv run python -c "from src.config.manager import config; print(f'Configuration loaded successfully! App: {config.general.name}')"
```

### 3. Test LLM Connection
```bash
# Test Anthropic API connection
uv run python -c "from src.llm import get_supported_providers; print(f'LLM factory ready with providers: {get_supported_providers()}')"
```

## Troubleshooting

### Common Issues

#### 1. Python Version Issues
**Problem**: `python --version` shows version < 3.11
**Solution**:
```bash
# Install Python 3.11 with uv
uv python install 3.11
uv sync
```

#### 2. API Key Errors
**Problem**: `ANTHROPIC_API_KEY not found` error
**Solution**:
```bash
# Check if .env file exists
ls -la .env

# Verify API key is set
grep ANTHROPIC_API_KEY .env
```

#### 3. Dependency Issues
**Problem**: Import errors or missing packages
**Solution**:
```bash
# Clean and reinstall dependencies
uv sync --reinstall
```

#### 4. Streamlit Issues
**Problem**: Streamlit won't start or shows errors
**Solution**:
```bash
# Check if port 8501 is available
lsof -i :8501

# Try different port
uv run streamlit run ui/app.py --server.port 8502
```

### Debug Mode

Enable debug mode for more detailed error messages:

```bash
# Set debug environment variable
export DEBUG=true

# Run with debug logging
uv run streamlit run ui/app.py --logger.level debug
```

### Logs and Monitoring

#### Application Logs
```bash
# View application logs
tail -f logs/app.log

# Check for errors
grep ERROR logs/app.log
```

#### Langfuse Monitoring (if enabled)
1. Visit your Langfuse dashboard
2. Check the "Traces" section for LLM interactions
3. Monitor performance and error rates

## Production Deployment

### Docker Deployment
```bash
# Build the Docker image
docker build -t job-search-assistant .

# Run the container
docker run -p 8501:8501 \
  -e ANTHROPIC_API_KEY=your_key \
  -e APP_ENV=prod \
  job-search-assistant
```

### Environment Variables for Production
```bash
# Required
ANTHROPIC_API_KEY=your_production_key
APP_ENV=prod

# Optional but recommended
LANGFUSE_PUBLIC_KEY=your_production_langfuse_key
LANGFUSE_SECRET_KEY=your_production_langfuse_secret
```
