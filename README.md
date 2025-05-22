# Job Search Assistant

A powerful open-source tool designed to streamline the job application process using AI-powered analysis and customization.

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

The Job Search Assistant is built with:
- Python backend with modular components
- Streamlit UI for easy interaction
- LangChain and LangGraph for AI agent orchestration
- Anthropic and other LLM providers for intelligent processing

## Getting Started

### Prerequisites
- Python 3.11
- Git

### Installation
```bash
# Clone the repository
git clone https://github.com/georgeliu1998/job_search_assistant.git
cd job_search_assistant

# Create a virtual environment with uv
uv venv

# Activate the virtual environment
source .venv/bin/activate  # On Windows: .venv\Scripts\activate

# Install dependencies
uv pip install -e .
```

### Usage
```bash
# Start the Streamlit UI
cd ui
streamlit run app.py
```

## Contributing
Contributions are welcome! Please feel free to submit a Pull Request.

## License
This project is licensed under the MIT License - see the LICENSE file for details. 