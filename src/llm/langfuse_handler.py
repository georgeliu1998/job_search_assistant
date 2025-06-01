"""
Langfuse callback handler for LLM tracing and observability.

This module provides a clean interface for initializing Langfuse
tracing capabilities, with proper error handling and logging.
"""

from typing import Optional

from langfuse.callback import CallbackHandler

from src.config.langfuse import get_langfuse_config
from src.utils.logging import get_logger

logger = get_logger(__name__)

# Global handler instance - initialized once and reused
_langfuse_handler: Optional[CallbackHandler] = None
_handler_initialized: bool = False


def _initialize_langfuse_handler(
    public_key: Optional[str] = None,
    secret_key: Optional[str] = None,
    host: Optional[str] = None,
    enabled: Optional[bool] = None,
) -> Optional[CallbackHandler]:
    """
    Internal function to initialize Langfuse callback handler with API keys.

    This should only be called once per application lifecycle.

    Args:
        public_key: Langfuse public key (optional, uses env var if not provided)
        secret_key: Langfuse secret key (optional, uses env var if not provided)
        host: Langfuse host URL (optional, uses env var or default if not provided)
        enabled: Whether to enable tracing (optional, uses env var if not provided)

    Returns:
        CallbackHandler instance if successful, None if disabled or failed
    """
    # Get configuration
    config = get_langfuse_config(
        public_key=public_key,
        secret_key=secret_key,
        host=host,
        enabled=enabled,
    )

    # Check if tracing is explicitly disabled
    if not config.enabled:
        logger.info("Langfuse tracing disabled via configuration")
        logger.debug("To enable tracing, set LANGFUSE_ENABLED=true")
        logger.debug(
            "Note: Currently disabled due to compatibility issues with Anthropic SDK"
        )
        logger.debug("See: https://github.com/langfuse/langfuse/issues/6882")
        return None

    # Validate configuration
    if not config.is_valid():
        logger.warning("Langfuse configuration incomplete - tracing will be disabled")
        if not config.public_key:
            logger.debug("Missing LANGFUSE_PUBLIC_KEY environment variable")
        if not config.secret_key:
            logger.debug("Missing LANGFUSE_SECRET_KEY environment variable")
        logger.info("To enable tracing, set these environment variables:")
        logger.info("- LANGFUSE_PUBLIC_KEY")
        logger.info("- LANGFUSE_SECRET_KEY")
        logger.info(
            "- LANGFUSE_HOST (optional, defaults to https://cloud.langfuse.com)"
        )
        logger.info("- LANGFUSE_ENABLED=true")
        return None

    # Validate host URL
    if not config.validate_host():
        logger.error(f"Invalid Langfuse host URL: {config.host}")
        return None

    # Attempt to create handler
    try:
        logger.info(f"Initializing Langfuse handler with host: {config.host}")
        handler = CallbackHandler(
            public_key=config.public_key,
            secret_key=config.secret_key,
            host=config.host,
        )

        logger.info("Langfuse handler initialized successfully")
        return handler

    except Exception as e:
        logger.error(f"Failed to initialize Langfuse handler: {e}")
        logger.debug("This could be due to:")
        logger.debug("- Invalid API keys")
        logger.debug("- Network connectivity issues")
        logger.debug("- Langfuse service unavailability")
        return None


def get_langfuse_handler(
    public_key: Optional[str] = None,
    secret_key: Optional[str] = None,
    host: Optional[str] = None,
    enabled: Optional[bool] = None,
) -> Optional[CallbackHandler]:
    """
    Get the global Langfuse callback handler instance.

    The handler is initialized once on first call and reused for subsequent calls.
    This avoids the overhead of reinitializing the handler for every LLM call.

    Args:
        public_key: Langfuse public key (optional, uses env var if not provided)
        secret_key: Langfuse secret key (optional, uses env var if not provided)
        host: Langfuse host URL (optional, uses env var or default if not provided)
        enabled: Whether to enable tracing (optional, uses env var if not provided)

    Returns:
        CallbackHandler instance if successful, None if disabled or failed

    Note:
        Parameters are only used on the first call. Subsequent calls return the
        same handler instance regardless of parameters passed.
    """
    global _langfuse_handler, _handler_initialized

    # Initialize handler only once
    if not _handler_initialized:
        logger.debug(
            "First call to get_langfuse_handler - initializing global instance"
        )
        _langfuse_handler = _initialize_langfuse_handler(
            public_key=public_key,
            secret_key=secret_key,
            host=host,
            enabled=enabled,
        )
        _handler_initialized = True

        if _langfuse_handler:
            logger.debug("Global Langfuse handler instance created successfully")
        else:
            logger.debug(
                "Global Langfuse handler instance not created (disabled or failed)"
            )
    else:
        logger.debug("Reusing existing global Langfuse handler instance")

        # Warn if parameters are passed on subsequent calls
        if any([public_key, secret_key, host, enabled is not None]):
            logger.warning(
                "Parameters passed to get_langfuse_handler are ignored after first initialization. "
                "To change configuration, restart the application."
            )

    return _langfuse_handler


def reset_langfuse_handler() -> None:
    """
    Reset the global Langfuse handler instance.

    This is primarily useful for testing purposes or if you need to
    reinitialize with different configuration.
    """
    global _langfuse_handler, _handler_initialized

    logger.debug("Resetting global Langfuse handler instance")
    _langfuse_handler = None
    _handler_initialized = False


def is_langfuse_enabled() -> bool:
    """Check if Langfuse tracing is enabled based on current configuration."""
    config = get_langfuse_config()
    return config.enabled and config.is_valid()
