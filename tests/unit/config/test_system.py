"""
Unit tests for the refactored configuration system.

This module tests the new configuration architecture with ConfigLoader,
ConfigManager, and the singleton pattern.
"""

import os
from unittest.mock import patch

import pytest

from src.config import ConfigLoader, ConfigManager
from src.config.models import AppConfig
from src.exceptions.config import (
    ConfigFileError,
    ConfigValidationError,
    EnvironmentError,
)
from src.models.enums import Environment

# Full set of agent task LLM configs required by AppConfig.agent_tasks.
# Uses a "stage-test-model" name so model validation is skipped, and the
# anthropic provider so the local ANTHROPIC_API_KEY (from .env) satisfies
# api-key validation when a fixture runs under the dev environment.
AGENT_TASKS_TOML = """
[agent_tasks.job_evaluation_extraction]
provider = "anthropic"
model = "stage-test-model"
temperature = 0.0
max_tokens = 100

[agent_tasks.job_evaluation_fit]
provider = "anthropic"
model = "stage-test-model"

[agent_tasks.interview_research]
provider = "anthropic"
model = "stage-test-model"

[agent_tasks.interview_question_generation]
provider = "anthropic"
model = "stage-test-model"

[agent_tasks.interview_answer_generation]
provider = "anthropic"
model = "stage-test-model"

[agent_tasks.interview_compilation]
provider = "anthropic"
model = "stage-test-model"
"""


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
tagline = "Test dev application"
version = "1.0.0"
debug = false

[logging]
level = "INFO"
"""
            + AGENT_TASKS_TOML
            + """
[observability.langfuse]
enabled = false
"""
        )

        dev_config = tmp_path / "dev.toml"
        dev_config.write_text("""
[general]
debug = true

[logging]
level = "DEBUG"
""")

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
            assert loader.get_environment() == Environment.DEV

        with patch.dict(os.environ, {"APP_ENV": "staging"}):
            assert loader.get_environment() == Environment.STAGE

        with patch.dict(os.environ, {"APP_ENV": "production"}):
            assert loader.get_environment() == Environment.PROD

    def test_missing_app_env_raises_error(self, tmp_path):
        """Test that missing APP_ENV raises appropriate error."""
        base_config = tmp_path / "base.toml"
        base_config.write_text("""[general]\nname = "test" """)

        with patch.dict(os.environ, {}, clear=True):
            loader = ConfigLoader(config_dir=tmp_path)
            with pytest.raises(EnvironmentError, match="APP_ENV environment variable is not set"):
                loader.get_environment()

    def test_invalid_app_env_raises_error(self, tmp_path):
        """Test that invalid APP_ENV raises appropriate error."""
        base_config = tmp_path / "base.toml"
        base_config.write_text("""[general]\nname = "test" """)

        with patch.dict(os.environ, {"APP_ENV": "invalid"}):
            loader = ConfigLoader(config_dir=tmp_path)
            with pytest.raises(EnvironmentError, match="Invalid environment"):
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
            with pytest.raises(ConfigFileError, match="Environment configuration file not found"):
                loader.load_raw_config()

    def test_secrets_loading(self, tmp_path):
        """Test that secrets are loaded from environment variables."""
        base_config = tmp_path / "base.toml"
        base_config.write_text(
            """
[general]
name = "test"
tagline = "Test secrets application"
version = "1.0.0"

[logging]
level = "INFO"
"""
            + AGENT_TASKS_TOML
            + """
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
                raw_config["agent_tasks"]["job_evaluation_extraction"]["api_key"]
                == "test_anthropic_key"
            )
            assert raw_config["observability"]["langfuse"]["public_key"] == "test_public_key"
            assert raw_config["observability"]["langfuse"]["secret_key"] == "test_secret_key"

    def test_config_merging(self, tmp_path):
        """Test that configurations are properly merged."""
        base_config = tmp_path / "base.toml"
        base_config.write_text("""
[general]
name = "test-app"
tagline = "Test merge application"
debug = false

[logging]
level = "INFO"
format = "basic"

[nested.section]
value1 = "base"
value2 = "base"
""")

        dev_config = tmp_path / "dev.toml"
        dev_config.write_text("""
[general]
debug = true

[nested.section]
value1 = "override"
value3 = "new"
""")

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
tagline = "Test application"
version = "1.0.0"

[logging]
level = "INFO"
"""
            + AGENT_TASKS_TOML
            + """
[observability.langfuse]
enabled = false
"""
        )

        stage_config = tmp_path / "stage.toml"
        stage_config.write_text("")

        with patch.dict(os.environ, {"APP_ENV": "stage"}):
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
tagline = "Test application"
version = "1.0.0"

[logging]
level = "INFO"
"""
            + AGENT_TASKS_TOML
            + """
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
            assert manager1 is not manager3  # Different instances due to different params

    def test_reload_functionality(self, tmp_path):
        """Test that configuration can be reloaded."""
        # Create initial config
        base_config = tmp_path / "base.toml"
        base_config.write_text(
            """
[general]
name = "original-app"
tagline = "Original application"
version = "1.0.0"

[logging]
level = "INFO"
"""
            + AGENT_TASKS_TOML
            + """
[observability.langfuse]
enabled = false
"""
        )

        stage_config = tmp_path / "stage.toml"
        stage_config.write_text("")

        with patch.dict(os.environ, {"APP_ENV": "stage"}):
            manager = ConfigManager(config_dir=tmp_path)
            initial_config = manager.load()

            assert initial_config.general.name == "original-app"

            # Modify the config file
            base_config.write_text(
                """
[general]
name = "updated-app"
tagline = "Updated application"
version = "1.0.0"

[logging]
level = "INFO"
"""
                + AGENT_TASKS_TOML
                + """
[observability.langfuse]
enabled = false
"""
            )

            # Reload and verify change
            reloaded_config = manager.reload()
            assert reloaded_config.general.name == "updated-app"

    def test_validation_error_handling(self, tmp_path):
        """Test that validation errors are properly handled."""
        # Create invalid config (missing required fields)
        base_config = tmp_path / "base.toml"
        base_config.write_text("""
[general]
name = "test-app"
# Missing required fields
""")

        dev_config = tmp_path / "dev.toml"
        dev_config.write_text("")

        with patch.dict(os.environ, {"APP_ENV": "dev"}):
            manager = ConfigManager(config_dir=tmp_path)
            with pytest.raises(ConfigValidationError):
                manager.load()


class TestLazyConfigProxy:
    """Test the lazy configuration proxy."""

    def test_lazy_attribute_access(self, tmp_path):
        """Test that config attributes are accessible via lazy proxy."""
        # Create test config
        base_config = tmp_path / "base.toml"
        base_config.write_text(
            """
[general]
name = "proxy-test"
tagline = "Proxy test application"
version = "1.0.0"

[logging]
level = "DEBUG"
"""
            + AGENT_TASKS_TOML
            + """
[observability.langfuse]
enabled = true
"""
        )

        stage_config = tmp_path / "stage.toml"
        stage_config.write_text("")

        with patch.dict(os.environ, {"APP_ENV": "stage"}):
            # Import fresh config proxy
            from src.config import config as test_config

            # Force reload with test directory
            test_config.reload(config_dir=tmp_path)

            # Test attribute access
            assert test_config.general.name == "proxy-test"
            assert test_config.logging.level == "DEBUG"

    def test_proxy_reload(self, tmp_path):
        """Test that proxy reload works correctly."""
        # Create initial config
        base_config = tmp_path / "base.toml"
        base_config.write_text(
            """
[general]
name = "initial"
tagline = "Initial application"
version = "1.0.0"

[logging]
level = "INFO"
"""
            + AGENT_TASKS_TOML
            + """
[observability.langfuse]
enabled = false
"""
        )

        stage_config = tmp_path / "stage.toml"
        stage_config.write_text("")

        with patch.dict(os.environ, {"APP_ENV": "stage"}):
            from src.config import config as test_config

            # Load initial config
            test_config.reload(config_dir=tmp_path)
            assert test_config.general.name == "initial"

            # Modify config file
            base_config.write_text(
                """
[general]
name = "modified"
tagline = "Modified application"
version = "1.0.0"

[logging]
level = "INFO"
"""
                + AGENT_TASKS_TOML
                + """
[observability.langfuse]
enabled = false
"""
            )

            # Reload and verify
            test_config.reload(config_dir=tmp_path)
            assert test_config.general.name == "modified"


class TestConfigIntegration:
    """Integration tests for the complete configuration system."""

    def test_end_to_end_config_loading(self, tmp_path):
        """Test complete end-to-end configuration loading."""
        # Create comprehensive config where each task directly defines its LLM
        base_config = tmp_path / "base.toml"
        base_config.write_text("""
[general]
name = "integration-test"
tagline = "Integration test application"
version = "1.0.0"
debug = false

[logging]
level = "INFO"
format = "%(asctime)s %(name)s [%(levelname)s] %(message)s"

[agent_tasks.job_evaluation_extraction]
provider = "anthropic"
model = "claude-haiku-4-5"
temperature = 0.1
max_tokens = 2048

[agent_tasks.job_evaluation_fit]
provider = "anthropic"
model = "claude-haiku-4-5"
temperature = 0.1
max_tokens = 2048

[agent_tasks.interview_research]
provider = "anthropic"
model = "claude-haiku-4-5"
temperature = 0.1
max_tokens = 2048

[agent_tasks.interview_question_generation]
provider = "anthropic"
model = "claude-haiku-4-5"
temperature = 0.1
max_tokens = 2048

[agent_tasks.interview_answer_generation]
provider = "anthropic"
model = "claude-haiku-4-5"
temperature = 0.1
max_tokens = 2048

[agent_tasks.interview_compilation]
provider = "anthropic"
model = "claude-haiku-4-5"
temperature = 0.1
max_tokens = 2048

[observability.langfuse]
enabled = true
host = "https://us.cloud.langfuse.com"
""")

        dev_config = tmp_path / "dev.toml"
        dev_config.write_text("""
[general]
debug = true

[logging]
level = "DEBUG"

[agent_tasks.job_evaluation_extraction]
temperature = 0.0
""")

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

            # Per-task LLM config, with a surgical override applied to one task
            extraction = settings.agent_tasks.job_evaluation_extraction
            assert extraction.temperature == 0.0  # Overridden by dev.toml
            assert extraction.api_key == "test-key"  # From env
            assert extraction.provider == "anthropic"
            assert extraction.model == "claude-haiku-4-5"

            # Other tasks keep the base temperature (override was surgical)
            assert settings.agent_tasks.interview_research.temperature == 0.1

            assert settings.observability.langfuse.public_key == "test-public"  # From env
