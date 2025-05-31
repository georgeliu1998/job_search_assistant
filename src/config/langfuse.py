"""
Langfuse configuration settings.

This module manages configuration for Langfuse tracing and observability.
"""

import os
from typing import Optional
from urllib.parse import urlparse


class LangfuseConfig:
    """Configuration for Langfuse tracing setup."""

    def __init__(
        self,
        public_key: Optional[str] = None,
        secret_key: Optional[str] = None,
        host: Optional[str] = None,
        enabled: Optional[bool] = None,
    ):
        """
        Initialize Langfuse configuration.

        Args:
            public_key: Langfuse public key (defaults to env var)
            secret_key: Langfuse secret key (defaults to env var)
            host: Langfuse host URL (defaults to env var or cloud.langfuse.com)
            enabled: Whether tracing is enabled (defaults to env var)
        """
        self.public_key = public_key or os.environ.get("LANGFUSE_PUBLIC_KEY")
        self.secret_key = secret_key or os.environ.get("LANGFUSE_SECRET_KEY")
        self.host = host or os.environ.get(
            "LANGFUSE_HOST", "https://cloud.langfuse.com"
        )

        # Parse enabled flag with proper boolean conversion
        if enabled is not None:
            self.enabled = enabled
        else:
            env_enabled = os.environ.get("LANGFUSE_ENABLED", "false").lower()
            self.enabled = env_enabled in ("true", "1", "yes", "on")

    def is_valid(self) -> bool:
        """Check if the configuration is valid for creating a handler."""
        return bool(self.enabled and self.public_key and self.secret_key)

    def validate_host(self) -> bool:
        """Validate that the host URL is properly formatted."""
        try:
            parsed = urlparse(self.host)
            return bool(parsed.scheme and parsed.netloc)
        except Exception:
            return False


def get_langfuse_config(
    public_key: Optional[str] = None,
    secret_key: Optional[str] = None,
    host: Optional[str] = None,
    enabled: Optional[bool] = None,
) -> LangfuseConfig:
    """
    Get Langfuse configuration.

    Args:
        public_key: Override public key
        secret_key: Override secret key
        host: Override host URL
        enabled: Override enabled flag

    Returns:
        LangfuseConfig instance
    """
    return LangfuseConfig(
        public_key=public_key,
        secret_key=secret_key,
        host=host,
        enabled=enabled,
    )
