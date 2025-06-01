"""
Global settings for the Job Search Assistant application.
"""

from pathlib import Path

# Base directory
BASE_DIR = Path(__file__).resolve().parent.parent.parent

# LLM Provider settings
DEFAULT_LLM_PROVIDER = "anthropic"
LLM_MODEL = "claude-3-opus-20240229"
# API key should be loaded from environment variables in production
DEFAULT_API_KEY = ""

# Paths
CONFIG_DIR = BASE_DIR / "src" / "config"
DATA_DIR = BASE_DIR / "src" / "data"
TEMPLATE_DIR = BASE_DIR / "src" / "core" / "resume_customization" / "templates"

# Application settings
DEFAULT_TEMPERATURE = 0.7
MAX_TOKENS = 4000
