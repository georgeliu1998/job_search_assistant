"""
Centralized configuration management for Job Search Assistant.

This module provides a single entry point for all application configuration,
with support for:
- Environment-specific configuration files
- Secret loading from environment variables
- Pydantic validation
- Singleton pattern with reload capability for testing
"""

import os
import sys
import tomllib
from pathlib import Path
from typing import Any, Dict, Optional

from pydantic import ValidationError

from src.config.models import Settings

# Load environment variables from .env file if it exists (dev only)
try:
    from dotenv import load_dotenv
    # Only load .env in development, never in production
    if os.getenv("APP_ENV", "").lower() in ("dev", "development", ""):
        load_dotenv()
except ImportError:
    # python-dotenv not available, skip loading .env file
    pass


class ConfigurationError(Exception):
    """Raised when configuration loading or validation fails."""
    pass


class SettingsLoader:
    """Handles loading and validation of application settings."""
    
    def __init__(self, config_dir: Optional[Path] = None):
        """
        Initialize settings loader.
        
        Args:
            config_dir: Directory containing config files (defaults to project root/configs)
        """
        if config_dir is None:
            # Default to configs/ directory at project root
            project_root = Path(__file__).parent.parent.parent
            config_dir = project_root / "configs"
        
        self.config_dir = Path(config_dir)
        self._validate_config_directory()
    
    def _validate_config_directory(self) -> None:
        """Validate that config directory and base.toml exist."""
        if not self.config_dir.exists():
            raise ConfigurationError(
                f"Configuration directory not found: {self.config_dir}"
            )
        
        base_config = self.config_dir / "base.toml"
        if not base_config.exists():
            raise ConfigurationError(
                f"Base configuration file not found: {base_config}"
            )
    
    def _get_environment(self) -> str:
        """Get current environment from APP_ENV variable."""
        env = os.getenv("APP_ENV", "").lower()
        
        if not env:
            raise ConfigurationError(
                "APP_ENV environment variable is not set. "
                "Valid values: dev, test, prod"
            )
        
        # Normalize environment names
        env_mapping = {
            "development": "dev",
            "testing": "test",
            "production": "prod",
        }
        env = env_mapping.get(env, env)
        
        valid_environments = {"dev", "test", "prod"}
        if env not in valid_environments:
            raise ConfigurationError(
                f"Invalid APP_ENV value: '{env}'. "
                f"Valid values: {', '.join(valid_environments)}"
            )
        
        return env
    
    def _load_toml_file(self, file_path: Path) -> Dict[str, Any]:
        """Load and parse a TOML file."""
        try:
            with open(file_path, "rb") as f:
                return tomllib.load(f)
        except FileNotFoundError:
            raise ConfigurationError(f"Configuration file not found: {file_path}")
        except Exception as e:
            raise ConfigurationError(
                f"Failed to parse configuration file {file_path}: {e}"
            )
    
    def _merge_configs(self, base: Dict[str, Any], override: Dict[str, Any]) -> Dict[str, Any]:
        """Recursively merge configuration dictionaries."""
        result = base.copy()
        
        for key, value in override.items():
            if key in result and isinstance(result[key], dict) and isinstance(value, dict):
                result[key] = self._merge_configs(result[key], value)
            else:
                result[key] = value
        
        return result
    
    def _load_secrets(self, config: Dict[str, Any]) -> Dict[str, Any]:
        """Load secrets from environment variables."""
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
    
    def load_settings(self) -> Settings:
        """Load and validate application settings."""
        try:
            # 1. Get current environment
            env = self._get_environment()
            
            # 2. Load base configuration
            base_config_path = self.config_dir / "base.toml"
            config = self._load_toml_file(base_config_path)
            
            # 3. Load environment-specific overrides
            env_config_path = self.config_dir / f"{env}.toml"
            if env_config_path.exists():
                env_config = self._load_toml_file(env_config_path)
                config = self._merge_configs(config, env_config)
            else:
                raise ConfigurationError(
                    f"Environment configuration file not found: {env_config_path}"
                )
            
            # 4. Load secrets from environment variables
            config = self._load_secrets(config)
            
            # 5. Validate configuration with Pydantic
            try:
                return Settings(**config)
            except ValidationError as e:
                raise ConfigurationError(f"Configuration validation failed: {e}")
            
        except ConfigurationError:
            raise
        except Exception as e:
            raise ConfigurationError(f"Unexpected error loading configuration: {e}")


# Global settings instance
_settings: Optional[Settings] = None
_loader: Optional[SettingsLoader] = None


def get_settings(reload: bool = False, config_dir: Optional[Path] = None) -> Settings:
    """
    Get application settings (singleton pattern).
    
    Args:
        reload: Force reload of settings (useful for testing)
        config_dir: Override config directory (useful for testing)
    
    Returns:
        Validated Settings instance
    """
    global _settings, _loader
    
    # For testing with custom config_dir, always create new instances
    if config_dir is not None:
        test_loader = SettingsLoader(config_dir=config_dir)
        return test_loader.load_settings()
    
    # Normal singleton behavior for production use
    if _settings is None or reload:
        if _loader is None:
            _loader = SettingsLoader()
        _settings = _loader.load_settings()
    
    return _settings


def reload_settings(config_dir: Optional[Path] = None) -> Settings:
    """
    Force reload of settings (useful for testing).
    
    Args:
        config_dir: Override config directory
    
    Returns:
        Newly loaded Settings instance
    """
    return get_settings(reload=True, config_dir=config_dir)


# Convenience access to settings (lazy-loaded)
def _get_lazy_settings() -> Settings:
    """Lazy-loaded settings to avoid import-time configuration loading."""
    return get_settings()

# Create a property-like access pattern
class LazySettings:
    """Lazy-loading wrapper for settings."""
    
    def __getattr__(self, name: str):
        return getattr(_get_lazy_settings(), name)

settings = LazySettings() 