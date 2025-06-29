"""
Tests for environment check component functionality
"""

from unittest.mock import MagicMock, patch

import pytest

from ui.components.environment_check import check_environment_setup


class TestEnvironmentCheck:
    """Test environment check functionality"""

    def test_environment_check_with_valid_api_keys(self):
        """Test that environment check passes when API keys are present"""
        # Mock config with valid API keys
        mock_config = MagicMock()
        mock_profile = MagicMock()
        mock_profile.api_key = "test-key"
        mock_config.llm_profiles.items.return_value = [("test_profile", mock_profile)]

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
        mock_config.llm_profiles.items.return_value = [("test_profile", mock_profile)]

        with patch("ui.components.environment_check.config", mock_config):
            is_valid, message = check_environment_setup()

            assert is_valid is False
            assert "Missing required API keys: ANTHROPIC_API_KEY" in message

    def test_environment_check_with_multiple_missing_keys(self):
        """Test environment check with multiple missing API keys"""
        # Mock config with multiple profiles missing API keys
        mock_config = MagicMock()

        mock_profile1 = MagicMock()
        mock_profile1.api_key = None
        mock_profile1.provider = "anthropic"

        mock_profile2 = MagicMock()
        mock_profile2.api_key = None
        mock_profile2.provider = "fireworks"

        mock_config.llm_profiles.items.return_value = [
            ("anthropic_profile", mock_profile1),
            ("fireworks_profile", mock_profile2),
        ]

        with patch("ui.components.environment_check.config", mock_config):
            is_valid, message = check_environment_setup()

            assert is_valid is False
            assert "Missing required API keys:" in message
            assert "ANTHROPIC_API_KEY" in message
            assert "FIREWORKS_API_KEY" in message

    def test_environment_check_handles_config_errors(self):
        """Test that environment check handles configuration errors gracefully"""
        # Mock config that raises an exception
        mock_config = MagicMock()
        mock_config.llm_profiles.items.side_effect = Exception("Config error")

        with patch("ui.components.environment_check.config", mock_config):
            is_valid, message = check_environment_setup()

            assert is_valid is False
            assert "Configuration error: Config error" in message
