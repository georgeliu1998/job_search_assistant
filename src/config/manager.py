"""
Configuration manager for high-level configuration orchestration.

This module provides the main interface for configuration management,
handling validation, instantiation, and providing a clean API for
accessing configuration throughout the application.
"""

from pathlib import Path
from typing import Optional

from pydantic import ValidationError

from src.config.loader import ConfigLoader
from src.config.models import AppConfig
from src.exceptions.config import ConfigError, ConfigValidationError
from src.utils.singleton import singleton


@singleton
class ConfigManager:
    """
    High-level configuration manager with singleton pattern.

    This class orchestrates the configuration loading process and provides
    a validated AppConfig object for use throughout the application.
    """

    def __init__(self, config_dir: Optional[Path] = None):
        """
        Initialize configuration manager.

        Args:
            config_dir: Optional override for configuration directory
        """
        self.config_dir = config_dir
        self._config: Optional[AppConfig] = None
        self._loader: Optional[ConfigLoader] = None

    def _get_loader(self) -> ConfigLoader:
        """Get or create configuration loader."""
        if self._loader is None or self._loader.config_dir != self.config_dir:
            self._loader = ConfigLoader(config_dir=self.config_dir)
        return self._loader

    def load(self) -> AppConfig:
        """
        Load and validate configuration.

        Returns:
            Validated AppConfig object

        Raises:
            ConfigError: If loading fails
            ConfigValidationError: If validation fails
        """
        if self._config is None:
            try:
                # Load raw configuration
                loader = self._get_loader()
                raw_config = loader.load_raw_config()

                # Validate with Pydantic
                self._config = AppConfig(**raw_config)

            except ValidationError as e:
                raise ConfigValidationError(f"Configuration validation failed: {e}")
            except ConfigError:
                raise
            except Exception as e:
                raise ConfigError(f"Unexpected error during configuration loading: {e}")

        return self._config

    def get_config(self) -> AppConfig:
        """
        Get validated configuration (alias for load).

        Returns:
            Validated AppConfig object
        """
        return self.load()

    def reload(self, config_dir: Optional[Path] = None) -> AppConfig:
        """
        Reload configuration with optional directory override.

        Args:
            config_dir: Optional override for configuration directory

        Returns:
            Newly loaded AppConfig object
        """
        # Update config directory if provided
        if config_dir is not None:
            self.config_dir = config_dir

        # Clear cached instances to force reload
        self._config = None
        self._loader = None

        # Load fresh configuration
        return self.load()


class LazyConfigProxy:
    """
    Lazy-loading proxy for configuration access.

    This class provides attribute access to configuration data
    without triggering configuration loading at import time.
    """

    def __init__(self):
        """Initialize lazy config proxy."""
        self._current_config_dir: Optional[Path] = None

    def _get_manager(self) -> ConfigManager:
        """Get the appropriate config manager (singleton based on config_dir)."""
        if self._current_config_dir is not None:
            return ConfigManager(config_dir=self._current_config_dir)
        else:
            return ConfigManager()

    def __getattr__(self, name: str):
        """
        Lazy attribute access to configuration data.

        Args:
            name: Attribute name to access

        Returns:
            Configuration attribute value
        """
        manager = self._get_manager()
        config = manager.load()
        return getattr(config, name)

    def reload(self, config_dir: Optional[Path] = None) -> AppConfig:
        """
        Reload configuration through the proxy.

        Args:
            config_dir: Optional override for configuration directory

        Returns:
            Newly loaded AppConfig object
        """
        if config_dir is not None:
            # Update the tracked config_dir and create/get manager for it
            self._current_config_dir = config_dir
            manager = ConfigManager(config_dir=config_dir)
            return manager.load()
        else:
            # Reload current manager
            manager = self._get_manager()
            return manager.reload()


# Create global proxy instance for application use
configs = LazyConfigProxy()
