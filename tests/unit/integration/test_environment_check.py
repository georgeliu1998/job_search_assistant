"""
Tests for environment check component functionality
"""

from types import SimpleNamespace
from unittest.mock import MagicMock, patch

from ui.components.environment_check import check_environment_setup


class TestEnvironmentCheck:
    """Test environment check functionality"""

    def test_environment_check_with_valid_api_keys(self):
        """Test that environment check passes when API keys are present"""
        # Mock config with valid API keys
        mock_config = MagicMock()
        mock_profile = MagicMock()
        mock_profile.api_key = "test-key"
        mock_config.agent_tasks = SimpleNamespace(job_evaluation_extraction=mock_profile)

        with patch("ui.components.environment_check.config", mock_config):
            is_valid, message = check_environment_setup()

            assert is_valid is True
            assert message == "Environment is properly configured"

    def test_environment_check_with_missing_api_keys(self):
        """Test that environment check fails when API keys are missing"""
        # Mock config with missing API keys
        mock_config = MagicMock()
        mock_profile = MagicMock()
        mock_profile.api_key = None
        mock_profile.provider = "anthropic"
        mock_config.agent_tasks = SimpleNamespace(job_evaluation_extraction=mock_profile)

        with patch("ui.components.environment_check.config", mock_config):
            is_valid, message = check_environment_setup()

            assert is_valid is False
            assert "Missing required API keys: ANTHROPIC_API_KEY" in message

    def test_environment_check_with_multiple_missing_keys(self):
        """Test environment check with multiple missing API keys"""
        # Mock config with multiple tasks missing API keys for different providers
        mock_config = MagicMock()

        mock_profile1 = MagicMock()
        mock_profile1.api_key = None
        mock_profile1.provider = "anthropic"

        mock_profile2 = MagicMock()
        mock_profile2.api_key = None
        mock_profile2.provider = "google"

        mock_config.agent_tasks = SimpleNamespace(
            job_evaluation_extraction=mock_profile1,
            interview_research=mock_profile2,
        )

        with patch("ui.components.environment_check.config", mock_config):
            is_valid, message = check_environment_setup()

            assert is_valid is False
            assert "Missing required API keys:" in message
            assert "ANTHROPIC_API_KEY" in message
            assert "GOOGLE_API_KEY" in message

    def test_environment_check_deduplicates_shared_provider(self):
        """Test that a provider shared by multiple tasks is reported once"""
        mock_config = MagicMock()

        mock_profile1 = MagicMock()
        mock_profile1.api_key = None
        mock_profile1.provider = "google"

        mock_profile2 = MagicMock()
        mock_profile2.api_key = None
        mock_profile2.provider = "google"

        mock_config.agent_tasks = SimpleNamespace(
            interview_research=mock_profile1,
            interview_compilation=mock_profile2,
        )

        with patch("ui.components.environment_check.config", mock_config):
            is_valid, message = check_environment_setup()

            assert is_valid is False
            assert message.count("GOOGLE_API_KEY") == 1

    def test_environment_check_handles_config_errors(self):
        """Test that environment check handles configuration errors gracefully"""

        # Config object whose agent_tasks access raises an exception
        class BadConfig:
            @property
            def agent_tasks(self):
                raise Exception("Config error")

        with patch("ui.components.environment_check.config", BadConfig()):
            is_valid, message = check_environment_setup()

            assert is_valid is False
            assert "Configuration error: Config error" in message
