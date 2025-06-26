"""
Configuration loader for the Job Search Assistant.

This module provides functionality to load, merge, and validate configuration
from multiple sources including TOML files and environment variables.
"""

import os
import tomllib
from pathlib import Path
from typing import Any, Dict, Optional

from src.exceptions.config import ConfigError, ConfigFileError, EnvironmentError
from src.models.enums import Environment


class ConfigLoader:
    """
    Configuration loader that handles loading from multiple sources.

    The loader follows this precedence order:
    1. Base configuration (base.toml)
    2. Environment-specific overrides ({env}.toml)
    3. Environment variables (for secrets)
    """

    def __init__(self, config_dir: Optional[Path] = None):
        """
        Initialize the configuration loader.

        Args:
            config_dir: Directory containing configuration files.
                       Defaults to 'configs' in project root.
        """
        self.config_dir = self._resolve_config_dir(config_dir)
        self._load_dotenv()
        self._validate_config_directory()

    def _resolve_config_dir(self, config_dir: Optional[Path]) -> Path:
        """Resolve the configuration directory path."""
        if config_dir:
            return config_dir.resolve()

        # Default to configs directory in project root
        current_file = Path(__file__).resolve()
        project_root = current_file.parent.parent.parent
        return project_root / "configs"

    def _load_dotenv(self) -> None:
        """
        Load environment variables from .env file in development only.

        This method attempts to load a .env file when running in development
        environments. It gracefully handles cases where python-dotenv is not
        installed or when not running in development.
        """
        try:
            from dotenv import load_dotenv

            # Only load .env in development, never in production
            current_env = os.getenv("APP_ENV", "").lower()
            if current_env in ("dev", "development", ""):
                load_dotenv()
        except ImportError:
            # python-dotenv not available, skip loading .env file
            pass

    def _validate_config_directory(self) -> None:
        """
        Validate that config directory and base.toml exist.

        Raises:
            ConfigError: If config directory or base.toml is missing
        """
        if not self.config_dir.exists():
            raise ConfigError(
                f"Configuration directory not found: {self.config_dir}",
                config_path=str(self.config_dir),
            )

        base_config = self.config_dir / "base.toml"
        if not base_config.exists():
            raise ConfigFileError(
                f"Base configuration file not found: {base_config}",
                config_path=str(base_config),
            )

    def get_environment(self) -> Environment:
        """
        Get and validate current environment from APP_ENV variable.

        Returns:
            Environment enum value

        Raises:
            EnvironmentError: If APP_ENV is not set or invalid
        """
        env_str = os.getenv("APP_ENV", "").lower()

        if not env_str:
            valid_values = ", ".join([e.value for e in Environment])
            raise EnvironmentError(
                f"APP_ENV environment variable is not set. "
                f"Valid values: {valid_values}"
            )

        try:
            return Environment.from_string(env_str)
        except ValueError as e:
            raise EnvironmentError(str(e))

    def load_toml_file(self, file_path: Path) -> Dict[str, Any]:
        """
        Load and parse a TOML file.

        Args:
            file_path: Path to the TOML file

        Returns:
            Parsed TOML data as dictionary

        Raises:
            ConfigFileError: If file cannot be found or parsed
        """
        try:
            with open(file_path, "rb") as f:
                return tomllib.load(f)
        except FileNotFoundError:
            raise ConfigFileError(
                f"Configuration file not found: {file_path}", config_path=str(file_path)
            )
        except Exception as e:
            raise ConfigFileError(
                f"Failed to parse configuration file {file_path}: {e}",
                config_path=str(file_path),
            )

    def merge_configs(
        self, base: Dict[str, Any], override: Dict[str, Any]
    ) -> Dict[str, Any]:
        """
        Recursively merge configuration dictionaries.

        Args:
            base: Base configuration dictionary
            override: Override configuration dictionary

        Returns:
            Merged configuration dictionary
        """
        result = base.copy()

        for key, value in override.items():
            if (
                key in result
                and isinstance(result[key], dict)
                and isinstance(value, dict)
            ):
                result[key] = self.merge_configs(result[key], value)
            else:
                result[key] = value

        return result

    def load_secrets(self, config: Dict[str, Any]) -> Dict[str, Any]:
        """
        Load secrets from environment variables and inject into config.

        Args:
            config: Configuration dictionary to enhance with secrets

        Returns:
            Configuration dictionary with secrets loaded
        """
        # Create a copy to avoid modifying the original
        config = config.copy()

        # Load Langfuse secrets if observability is configured
        if "observability" in config and "langfuse" in config["observability"]:
            langfuse_config = config["observability"]["langfuse"]
            langfuse_config["public_key"] = os.getenv("LANGFUSE_PUBLIC_KEY")
            langfuse_config["secret_key"] = os.getenv("LANGFUSE_SECRET_KEY")

        # Load LLM API keys for each profile
        if "llm_profiles" in config:
            for profile_name, profile_config in config["llm_profiles"].items():
                provider = profile_config.get("provider", "").lower()

                if provider == "anthropic":
                    profile_config["api_key"] = os.getenv("ANTHROPIC_API_KEY")
                elif provider == "fireworks":
                    profile_config["api_key"] = os.getenv("FIREWORKS_API_KEY")

        return config

    def load_raw_config(self) -> Dict[str, Any]:
        """
        Load complete raw configuration from all sources.

        This method orchestrates the loading of configuration from:
        1. Base configuration file (base.toml)
        2. Environment-specific overrides ({env}.toml)
        3. Environment variables (secrets)

        Returns:
            Complete raw configuration dictionary

        Raises:
            ConfigError: If any step of the loading process fails
        """
        try:
            # 1. Get current environment
            env = self.get_environment()

            # 2. Load base configuration
            base_config_path = self.config_dir / "base.toml"
            config = self.load_toml_file(base_config_path)

            # 3. Load environment-specific overrides
            env_config_path = self.config_dir / f"{env.value}.toml"
            if env_config_path.exists():
                env_config = self.load_toml_file(env_config_path)
                config = self.merge_configs(config, env_config)
            else:
                raise ConfigFileError(
                    f"Environment configuration file not found: {env_config_path}",
                    config_path=str(env_config_path),
                )

            # 4. Load secrets from environment variables
            config = self.load_secrets(config)

            return config

        except (ConfigError, ConfigFileError, EnvironmentError):
            raise
        except Exception as e:
            raise ConfigError(f"Unexpected error loading configuration: {e}")
