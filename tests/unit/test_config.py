"""Unit tests for config module."""

import pytest

from src.config import settings
from src.config.schemas import LLMConfig, UserPreferences


def test_settings_constants():
    """Test that settings module has expected constants."""
    assert hasattr(settings, "DEFAULT_LLM_PROVIDER")
    assert hasattr(settings, "LLM_MODEL")
    assert hasattr(settings, "DEFAULT_TEMPERATURE")
    assert hasattr(settings, "MAX_TOKENS")
    assert settings.DEFAULT_LLM_PROVIDER == "anthropic"
    assert settings.DEFAULT_TEMPERATURE == 0.7


def test_user_preferences_creation():
    """Test that UserPreferences can be instantiated."""
    prefs = UserPreferences()
    assert prefs is not None
    assert prefs.desired_roles == []
    assert prefs.required_skills == []
    assert prefs.remote_preference is None


def test_user_preferences_with_data():
    """Test UserPreferences with actual data."""
    prefs = UserPreferences(
        desired_roles=["Software Engineer", "Developer"],
        required_skills=["Python", "Git"],
        min_years_experience=2,
        remote_preference="remote",
    )
    assert prefs.desired_roles == ["Software Engineer", "Developer"]
    assert prefs.required_skills == ["Python", "Git"]
    assert prefs.min_years_experience == 2
    assert prefs.remote_preference == "remote"


def test_llm_config_creation():
    """Test that LLMConfig can be instantiated."""
    config = LLMConfig()
    assert config is not None
    assert config.provider == "anthropic"
    assert config.model == "claude-3-opus-20240229"
    assert config.temperature == 0.7
    assert config.max_tokens == 512


def test_llm_config_custom():
    """Test LLMConfig with custom values."""
    config = LLMConfig(
        provider="openai", model="gpt-4", temperature=0.5, max_tokens=2000
    )
    assert config.provider == "openai"
    assert config.model == "gpt-4"
    assert config.temperature == 0.5
    assert config.max_tokens == 2000
