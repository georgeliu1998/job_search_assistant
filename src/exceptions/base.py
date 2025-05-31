"""
Base exception classes for the Job Search Assistant application.
"""


class JobSearchAssistantError(Exception):
    """
    Base exception class for all Job Search Assistant application errors.

    This serves as the root exception that all other custom exceptions
    in the application should inherit from, enabling consistent error
    handling patterns.
    """

    def __init__(self, message: str, details: dict = None):
        """
        Initialize the base exception.

        Args:
            message: Human-readable error message
            details: Optional dictionary with additional error context
        """
        super().__init__(message)
        self.message = message
        self.details = details or {}

    def __str__(self) -> str:
        """Return string representation of the exception."""
        if self.details:
            return f"{self.message} (Details: {self.details})"
        return self.message
