"""
Unit tests for the refactored configuration system.

This module tests the new configuration architecture with ConfigLoader,
ConfigManager, and the singleton pattern.
"""

import os
import tempfile
from pathlib import Path
from unittest.mock import patch

import pytest

from src.config import ConfigLoader, ConfigManager, config
from src.config.models import AppConfig
from src.exceptions.config import (
    ConfigError,
    ConfigFileError,
    ConfigValidationError,
    EnvironmentError,
)


class TestConfigLoader:
    """Test the ConfigLoader class."""

    def test_load_raw_config_dev_environment(self, tmp_path):
        """Test loading development configuration."""
        # Create test config files
        base_config = tmp_path / "base.toml"
        base_config.write_text(
            """
[general]
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
"""
        )

        dev_config = tmp_path / "dev.toml"
        dev_config.write_text(
            """
[general]
debug = true

[logging]
level = "DEBUG"
"""
        )

        with patch.dict(os.environ, {"APP_ENV": "dev"}):
            loader = ConfigLoader(config_dir=tmp_path)
            raw_config = loader.load_raw_config()

            assert raw_config["general"]["name"] == "test-app"
            assert raw_config["general"]["debug"] is True  # Overridden by dev.toml
            assert raw_config["logging"]["level"] == "DEBUG"  # Overridden by dev.toml

    def test_environment_detection(self, tmp_path):
        """Test environment detection and normalization."""
        base_config = tmp_path / "base.toml"
        base_config.write_text("""[general]\nname = "test" """)

        loader = ConfigLoader(config_dir=tmp_path)

        with patch.dict(os.environ, {"APP_ENV": "development"}):
            assert loader.get_environment() == "dev"

        with patch.dict(os.environ, {"APP_ENV": "testing"}):
            assert loader.get_environment() == "test"

        with patch.dict(os.environ, {"APP_ENV": "production"}):
            assert loader.get_environment() == "prod"

    def test_missing_app_env_raises_error(self, tmp_path):
        """Test that missing APP_ENV raises appropriate error."""
        base_config = tmp_path / "base.toml"
        base_config.write_text("""[general]\nname = "test" """)

        with patch.dict(os.environ, {}, clear=True):
            loader = ConfigLoader(config_dir=tmp_path)
            with pytest.raises(
                EnvironmentError, match="APP_ENV environment variable is not set"
            ):
                loader.get_environment()

    def test_invalid_app_env_raises_error(self, tmp_path):
        """Test that invalid APP_ENV raises appropriate error."""
        base_config = tmp_path / "base.toml"
        base_config.write_text("""[general]\nname = "test" """)

        with patch.dict(os.environ, {"APP_ENV": "invalid"}):
            loader = ConfigLoader(config_dir=tmp_path)
            with pytest.raises(EnvironmentError, match="Invalid APP_ENV value"):
                loader.get_environment()

    def test_missing_base_config_raises_error(self, tmp_path):
        """Test that missing base.toml raises appropriate error."""
        with pytest.raises(ConfigFileError, match="Base configuration file not found"):
            ConfigLoader(config_dir=tmp_path)

    def test_missing_env_config_raises_error(self, tmp_path):
        """Test that missing environment config raises appropriate error."""
        base_config = tmp_path / "base.toml"
        base_config.write_text("""[general]\nname = "test" """)

        with patch.dict(os.environ, {"APP_ENV": "dev"}):
            loader = ConfigLoader(config_dir=tmp_path)
            with pytest.raises(
                ConfigFileError, match="Environment configuration file not found"
            ):
                loader.load_raw_config()

    def test_secrets_loading(self, tmp_path):
        """Test that secrets are loaded from environment variables."""
        base_config = tmp_path / "base.toml"
        base_config.write_text(
            """
[general]
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
"""
        )

        dev_config = tmp_path / "dev.toml"
        dev_config.write_text("")

        with patch.dict(
            os.environ,
            {
                "APP_ENV": "dev",
                "ANTHROPIC_API_KEY": "test_anthropic_key",
                "LANGFUSE_PUBLIC_KEY": "test_public_key",
                "LANGFUSE_SECRET_KEY": "test_secret_key",
            },
        ):
            loader = ConfigLoader(config_dir=tmp_path)
            raw_config = loader.load_raw_config()

            assert (
                raw_config["llm_profiles"]["anthropic_profile"]["api_key"]
                == "test_anthropic_key"
            )
            assert (
                raw_config["observability"]["langfuse"]["public_key"]
                == "test_public_key"
            )
            assert (
                raw_config["observability"]["langfuse"]["secret_key"]
                == "test_secret_key"
            )

    def test_config_merging(self, tmp_path):
        """Test that configurations are properly merged."""
        base_config = tmp_path / "base.toml"
        base_config.write_text(
            """
[general]
name = "test-app"
debug = false

[logging]
level = "INFO"
format = "basic"

[nested.section]
value1 = "base"
value2 = "base"
"""
        )

        dev_config = tmp_path / "dev.toml"
        dev_config.write_text(
            """
[general]
debug = true

[nested.section]
value1 = "override"
value3 = "new"
"""
        )

        with patch.dict(os.environ, {"APP_ENV": "dev"}):
            loader = ConfigLoader(config_dir=tmp_path)
            raw_config = loader.load_raw_config()

            # Check overrides
            assert raw_config["general"]["debug"] is True
            assert raw_config["general"]["name"] == "test-app"  # Preserved from base

            # Check nested merging
            assert raw_config["nested"]["section"]["value1"] == "override"
            assert raw_config["nested"]["section"]["value2"] == "base"  # Preserved
            assert raw_config["nested"]["section"]["value3"] == "new"  # Added


class TestConfigManager:
    """Test the ConfigManager class."""

    def test_load_and_validate_config(self, tmp_path):
        """Test loading and validating configuration."""
        # Create minimal valid config
        base_config = tmp_path / "base.toml"
        base_config.write_text(
            """
[general]
name = "test-app"
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
model = "test-model"

[observability.langfuse]
enabled = false
"""
        )

        dev_config = tmp_path / "dev.toml"
        dev_config.write_text("")

        with patch.dict(os.environ, {"APP_ENV": "dev"}):
            manager = ConfigManager(config_dir=tmp_path)
            settings = manager.load()

            assert isinstance(settings, AppConfig)
            assert settings.general.name == "test-app"

    def test_singleton_behavior(self, tmp_path):
        """Test that ConfigManager follows singleton pattern."""
        base_config = tmp_path / "base.toml"
        base_config.write_text(
            """
[general]
name = "test-app"
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
model = "test-model"

[observability.langfuse]
enabled = false
"""
        )

        dev_config = tmp_path / "dev.toml"
        dev_config.write_text("")

        with patch.dict(os.environ, {"APP_ENV": "dev"}):
            # Same parameters should return same instance
            manager1 = ConfigManager(config_dir=tmp_path)
            manager2 = ConfigManager(config_dir=tmp_path)

            assert manager1 is manager2  # Same instance due to singleton

            # Different parameters should create different instances
            manager3 = ConfigManager()  # No config_dir parameter
            assert (
                manager1 is not manager3
            )  # Different instances due to different params

    def test_reload_functionality(self, tmp_path):
        """Test configuration reload functionality."""
        # Create initial config
        base_config = tmp_path / "base.toml"
        base_config.write_text(
            """
[general]
name = "initial-app"
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
model = "test-model"

[observability.langfuse]
enabled = false
"""
        )

        dev_config = tmp_path / "dev.toml"
        dev_config.write_text("")

        with patch.dict(os.environ, {"APP_ENV": "dev"}):
            manager = ConfigManager(config_dir=tmp_path)
            initial_settings = manager.load()
            assert initial_settings.general.name == "initial-app"

            # Update config file
            base_config.write_text(
                """
[general]
name = "updated-app"
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
model = "test-model"

[observability.langfuse]
enabled = false
"""
            )

            # Reload and verify update
            updated_settings = manager.reload()
            assert updated_settings.general.name == "updated-app"

    def test_validation_error_handling(self, tmp_path):
        """Test that validation errors are properly handled."""
        # Create invalid config (missing required fields)
        base_config = tmp_path / "base.toml"
        base_config.write_text(
            """
[general]
name = "test-app"
# Missing required fields
"""
        )

        dev_config = tmp_path / "dev.toml"
        dev_config.write_text("")

        with patch.dict(os.environ, {"APP_ENV": "dev"}):
            manager = ConfigManager(config_dir=tmp_path)
            with pytest.raises(ConfigValidationError):
                manager.load()


class TestLazyConfigProxy:
    """Test the lazy configuration proxy."""

    def test_lazy_attribute_access(self, tmp_path):
        """Test that attributes are lazily loaded through the proxy."""
        # Create valid config
        base_config = tmp_path / "base.toml"
        base_config.write_text(
            """
[general]
name = "proxy-test"
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
model = "test-model"

[observability.langfuse]
enabled = false
"""
        )

        dev_config = tmp_path / "dev.toml"
        dev_config.write_text("")

        with patch.dict(os.environ, {"APP_ENV": "dev"}):
            # Test using a separate proxy instance to avoid global state
            from src.config.manager import LazyConfigProxy

            test_proxy = LazyConfigProxy()

            # Force the proxy to use our test config
            test_proxy.reload(config_dir=tmp_path)

            # Access through proxy should work
            assert test_proxy.general.name == "proxy-test"
            assert test_proxy.logging.level == "INFO"

    def test_proxy_reload(self, tmp_path):
        """Test reloading through the proxy."""
        # Create initial config
        base_config = tmp_path / "base.toml"
        base_config.write_text(
            """
[general]
name = "proxy-initial"
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
model = "test-model"

[observability.langfuse]
enabled = false
"""
        )

        dev_config = tmp_path / "dev.toml"
        dev_config.write_text("")

        with patch.dict(os.environ, {"APP_ENV": "dev"}):
            # Initial load
            config.reload(config_dir=tmp_path)
            assert config.general.name == "proxy-initial"

            # Update config
            base_config.write_text(
                """
[general]
name = "proxy-updated"
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
model = "test-model"

[observability.langfuse]
enabled = false
"""
            )

            # Reload and verify
            config.reload(config_dir=tmp_path)
            assert config.general.name == "proxy-updated"


class TestConfigIntegration:
    """Integration tests for the complete configuration system."""

    def test_end_to_end_config_loading(self, tmp_path):
        """Test complete end-to-end configuration loading."""
        # Create comprehensive config
        base_config = tmp_path / "base.toml"
        base_config.write_text(
            """
[general]
name = "integration-test"
version = "1.0.0"
debug = false

[logging]
level = "INFO"
format = "%(asctime)s %(name)s [%(levelname)s] %(message)s"

[agents]
job_evaluation_extraction = "claude_profile"
job_evaluation_reasoning = "claude_profile"

[evaluation_criteria]
min_salary = 150000
remote_required = true
ic_title_requirements = ["senior", "staff", "principal"]

[llm_profiles.claude_profile]
provider = "anthropic"
model = "claude-3-5-haiku-20241022"
temperature = 0.1
max_tokens = 2048

[observability.langfuse]
enabled = true
host = "https://us.cloud.langfuse.com"
"""
        )

        dev_config = tmp_path / "dev.toml"
        dev_config.write_text(
            """
[general]
debug = true

[logging]
level = "DEBUG"

[llm_profiles.claude_profile]
temperature = 0.0
"""
        )

        with patch.dict(
            os.environ,
            {
                "APP_ENV": "dev",
                "ANTHROPIC_API_KEY": "test-key",
                "LANGFUSE_PUBLIC_KEY": "test-public",
                "LANGFUSE_SECRET_KEY": "test-secret",
            },
        ):
            # Test through ConfigManager
            manager = ConfigManager(config_dir=tmp_path)
            settings = manager.load()

            # Verify all sections loaded correctly
            assert settings.general.name == "integration-test"
            assert settings.general.debug is True  # Overridden by dev.toml
            assert settings.logging.level == "DEBUG"  # Overridden by dev.toml
            assert settings.evaluation_criteria.min_salary == 150000
            assert (
                settings.llm_profiles["claude_profile"].temperature == 0.0
            )  # Overridden
            assert (
                settings.llm_profiles["claude_profile"].api_key == "test-key"
            )  # From env
            assert (
                settings.observability.langfuse.public_key == "test-public"
            )  # From env

            # Test model methods
            profile = settings.get_llm_profile("claude_profile")
            assert profile.provider == "anthropic"

            agent_profile = settings.get_agent_llm_profile("job_evaluation_extraction")
            assert agent_profile.model == "claude-3-5-haiku-20241022"
