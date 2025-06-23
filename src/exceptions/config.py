"""
Configuration-related exceptions.

This module contains all exceptions related to configuration loading,
validation, and management.
"""

from src.exceptions.base import JobSearchAssistantError


class ConfigError(JobSearchAssistantError):
    """
    Base exception for configuration-related errors.

    Raised when configuration loading, validation, or access fails.
    This includes issues with:
    - Missing or invalid configuration files
    - Environment variable problems
    - Configuration validation failures
    - Configuration directory issues
    """

    def __init__(self, message: str, config_path: str = None):
        """
        Initialize configuration error.

        Args:
            message: Human-readable error description
            config_path: Optional path to the problematic configuration file/directory
        """
        super().__init__(message)
        self.config_path = config_path


class ConfigFileError(ConfigError):
    """Raised when configuration file operations fail."""

    pass


class ConfigValidationError(ConfigError):
    """Raised when configuration validation fails."""

    pass


class EnvironmentError(ConfigError):
    """Raised when environment-related configuration issues occur."""

    pass
