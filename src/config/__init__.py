"""
Configuration module for Job Search Assistant.

This module provides centralized configuration management with support for:
- Environment-specific configuration files
- Secret loading from environment variables
- Pydantic validation
- Singleton pattern with reload capability
- Clean, lazy-loaded access patterns

Main exports:
- configs: Main configuration instance for application use
- ConfigManager: Manager class for advanced usage and testing
- ConfigLoader: Loader class for low-level operations
"""

from src.config.loader import ConfigLoader
from src.config.manager import ConfigManager, configs
from src.config.models import ApplicationConfig

# Primary interface - use this throughout the application
__all__ = [
    "configs",  # Main configuration instance
    "ConfigManager",  # For testing and advanced usage
    "ConfigLoader",  # For low-level operations
    "ApplicationConfig",  # Pydantic model for type hints
]
