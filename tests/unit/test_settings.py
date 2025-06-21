"""
Unit tests for the centralized configuration system.
"""

import os
import tempfile
from pathlib import Path
from unittest.mock import patch

import pytest

from src.config.models import Settings
from src.config.settings import (
    ConfigurationError,
    SettingsLoader,
    get_settings,
    reload_settings,
)


class TestSettingsLoader:
    """Test the SettingsLoader class."""

    def test_load_settings_dev_environment(self, tmp_path):
        """Test loading development configuration."""
        # Create test config files
        base_config = tmp_path / "base.toml"
        base_config.write_text("""
[app]
name = "test-app"
version = "1.0.0"
debug = false

[logging]
level = "INFO"

[agents]
job_evaluation_extraction = "test_profile"
job_evaluation_reasoning = "test_profile"

[evaluation_criteria]
min_salary = 100000
remote_required = true
ic_title_requirements = ["senior"]

[llm_profiles.test_profile]
provider = "anthropic"
model = "test-model"
temperature = 0.0
max_tokens = 100

[observability.langfuse]
enabled = false
""")
        
        dev_config = tmp_path / "dev.toml"
        dev_config.write_text("""
[app]
debug = true

[logging]
level = "DEBUG"
""")
        
        with patch.dict(os.environ, {"APP_ENV": "dev"}):
            loader = SettingsLoader(config_dir=tmp_path)
            settings = loader.load_settings()
            
            assert settings.app.name == "test-app"
            assert settings.app.debug is True  # Overridden by dev.toml
            assert settings.logging.level == "DEBUG"  # Overridden by dev.toml
            assert settings.evaluation_criteria.min_salary == 100000

    def test_load_settings_test_environment(self, tmp_path):
        """Test loading test configuration."""
        # Create test config files
        base_config = tmp_path / "base.toml"
        base_config.write_text("""
[app]
name = "test-app"
version = "1.0.0"
debug = false

[logging]
level = "INFO"

[agents]
job_evaluation_extraction = "test_profile"
job_evaluation_reasoning = "test_profile"

[evaluation_criteria]
min_salary = 100000
remote_required = true
ic_title_requirements = ["senior"]

[llm_profiles.test_profile]
provider = "anthropic"
model = "test-model"

[observability.langfuse]
enabled = true
""")
        
        test_config = tmp_path / "test.toml"
        test_config.write_text("""
[logging]
level = "WARNING"

[observability.langfuse]
enabled = false
""")
        
        with patch.dict(os.environ, {"APP_ENV": "test"}):
            loader = SettingsLoader(config_dir=tmp_path)
            settings = loader.load_settings()
            
            assert settings.app.debug is False  # From base.toml
            assert settings.logging.level == "WARNING"  # Overridden by test.toml
            assert settings.observability.langfuse.enabled is False  # Overridden

    def test_missing_app_env_raises_error(self, tmp_path):
        """Test that missing APP_ENV raises appropriate error."""
        base_config = tmp_path / "base.toml"
        base_config.write_text("""
[app]
name = "test"
""")
        
        with patch.dict(os.environ, {}, clear=True):
            loader = SettingsLoader(config_dir=tmp_path)
            with pytest.raises(ConfigurationError, match="APP_ENV environment variable is not set"):
                loader.load_settings()

    def test_invalid_app_env_raises_error(self, tmp_path):
        """Test that invalid APP_ENV raises appropriate error."""
        base_config = tmp_path / "base.toml"
        base_config.write_text("""
[app]
name = "test"
""")
        
        with patch.dict(os.environ, {"APP_ENV": "invalid"}):
            loader = SettingsLoader(config_dir=tmp_path)
            with pytest.raises(ConfigurationError, match="Invalid APP_ENV value"):
                loader.load_settings()

    def test_missing_base_config_raises_error(self, tmp_path):
        """Test that missing base.toml raises appropriate error."""
        with pytest.raises(ConfigurationError, match="Base configuration file not found"):
            SettingsLoader(config_dir=tmp_path)

    def test_missing_env_config_raises_error(self, tmp_path):
        """Test that missing environment config raises appropriate error."""
        base_config = tmp_path / "base.toml"
        base_config.write_text("""
[app]
name = "test"
""")
        
        with patch.dict(os.environ, {"APP_ENV": "dev"}):
            loader = SettingsLoader(config_dir=tmp_path)
            with pytest.raises(ConfigurationError, match="Environment configuration file not found"):
                loader.load_settings()

    def test_secrets_loading(self, tmp_path):
        """Test that secrets are loaded from environment variables."""
        base_config = tmp_path / "base.toml"
        base_config.write_text("""
[app]
name = "test"
version = "1.0.0"

[logging]
level = "INFO"

[agents]
job_evaluation_extraction = "anthropic_profile"
job_evaluation_reasoning = "anthropic_profile"

[evaluation_criteria]
min_salary = 100000
remote_required = true
ic_title_requirements = ["senior"]

[llm_profiles.anthropic_profile]
provider = "anthropic"
model = "test-model"

[observability.langfuse]
enabled = true
""")
        
        dev_config = tmp_path / "dev.toml"
        dev_config.write_text("")
        
        with patch.dict(os.environ, {
            "APP_ENV": "dev",
            "ANTHROPIC_API_KEY": "test_anthropic_key",
            "LANGFUSE_PUBLIC_KEY": "test_public_key",
            "LANGFUSE_SECRET_KEY": "test_secret_key",
        }):
            loader = SettingsLoader(config_dir=tmp_path)
            settings = loader.load_settings()
            
            assert settings.llm_profiles["anthropic_profile"].api_key == "test_anthropic_key"
            assert settings.observability.langfuse.public_key == "test_public_key"
            assert settings.observability.langfuse.secret_key == "test_secret_key"

    def test_config_validation_error(self, tmp_path):
        """Test that invalid configuration raises validation error."""
        base_config = tmp_path / "base.toml"
        base_config.write_text("""
[app]
name = "test"

[logging]
level = "INVALID_LEVEL"  # This should cause validation error
""")
        
        dev_config = tmp_path / "dev.toml"
        dev_config.write_text("")
        
        with patch.dict(os.environ, {"APP_ENV": "dev"}):
            loader = SettingsLoader(config_dir=tmp_path)
            with pytest.raises(ConfigurationError, match="Configuration validation failed"):
                loader.load_settings()


class TestSettingsFunctions:
    """Test the module-level functions."""

    def test_get_settings_singleton(self):
        """Test that get_settings returns the same instance in normal usage."""
        # Test the actual singleton behavior without custom config_dir
        # This tests the production behavior
        
        with patch.dict(os.environ, {"APP_ENV": "dev"}):
            # Clear any existing settings to start fresh
            from src.config.settings import _settings, _loader
            import src.config.settings
            src.config.settings._settings = None
            src.config.settings._loader = None
            
            settings1 = get_settings()
            settings2 = get_settings()
            
            # Should be the same instance
            assert settings1 is settings2

    def test_reload_settings(self, tmp_path):
        """Test that reload_settings forces a new instance."""
        # Create minimal config
        base_config = tmp_path / "base.toml"
        base_config.write_text("""
[app]
name = "test"
version = "1.0.0"

[logging]
level = "INFO"

[agents]
job_evaluation_extraction = "test_profile"
job_evaluation_reasoning = "test_profile"

[evaluation_criteria]
min_salary = 100000
remote_required = true
ic_title_requirements = ["senior"]

[llm_profiles.test_profile]
provider = "anthropic"
model = "test"

[observability.langfuse]
enabled = false
""")
        
        dev_config = tmp_path / "dev.toml"
        dev_config.write_text("")
        
        with patch.dict(os.environ, {"APP_ENV": "dev"}):
            settings1 = get_settings(config_dir=tmp_path)
            settings2 = reload_settings(config_dir=tmp_path)
            
            # Should be different instances
            assert settings1 is not settings2
            # But should have the same values
            assert settings1.app.name == settings2.app.name


class TestSettingsModel:
    """Test the Settings model methods."""

    def test_get_llm_profile(self):
        """Test getting LLM profile by name."""
        settings_data = {
            "app": {"name": "test", "version": "1.0.0"},
            "logging": {"level": "INFO"},
            "agents": {
                "job_evaluation_extraction": "test_profile",
                "job_evaluation_reasoning": "test_profile"
            },
            "evaluation_criteria": {
                "min_salary": 100000,
                "remote_required": True,
                "ic_title_requirements": ["senior"]
            },
            "llm_profiles": {
                "test_profile": {
                    "provider": "anthropic",
                    "model": "test-model"
                }
            },
            "observability": {"langfuse": {"enabled": False}}
        }
        
        settings = Settings(**settings_data)
        profile = settings.get_llm_profile("test_profile")
        
        assert profile.provider == "anthropic"
        assert profile.model == "test-model"

    def test_get_llm_profile_not_found(self):
        """Test getting non-existent LLM profile raises error."""
        settings_data = {
            "app": {"name": "test", "version": "1.0.0"},
            "logging": {"level": "INFO"},
            "agents": {
                "job_evaluation_extraction": "test_profile",
                "job_evaluation_reasoning": "test_profile"
            },
            "evaluation_criteria": {
                "min_salary": 100000,
                "remote_required": True,
                "ic_title_requirements": ["senior"]
            },
            "llm_profiles": {
                "test_profile": {
                    "provider": "anthropic",
                    "model": "test-model"
                }
            },
            "observability": {"langfuse": {"enabled": False}}
        }
        
        settings = Settings(**settings_data)
        
        with pytest.raises(ValueError, match="LLM profile 'nonexistent' not found"):
            settings.get_llm_profile("nonexistent")

    def test_get_agent_llm_profile(self):
        """Test getting LLM profile for agent task."""
        settings_data = {
            "app": {"name": "test", "version": "1.0.0"},
            "logging": {"level": "INFO"},
            "agents": {
                "job_evaluation_extraction": "test_profile",
                "job_evaluation_reasoning": "test_profile"
            },
            "evaluation_criteria": {
                "min_salary": 100000,
                "remote_required": True,
                "ic_title_requirements": ["senior"]
            },
            "llm_profiles": {
                "test_profile": {
                    "provider": "anthropic",
                    "model": "test-model"
                }
            },
            "observability": {"langfuse": {"enabled": False}}
        }
        
        settings = Settings(**settings_data)
        profile = settings.get_agent_llm_profile("job_evaluation_extraction")
        
        assert profile.provider == "anthropic"
        assert profile.model == "test-model" 