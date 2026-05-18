"""
Unit tests for the LLM model factory.

Tests get_chat_model and get_chat_model_by_profile_name functions
including provider creation, error handling, and API key validation.
"""

from unittest.mock import MagicMock, patch

import pytest

from src.config.models import LLMProfileConfig
from src.exceptions.llm import LLMProviderError
from src.llm.factory import (
    _ensure_api_key,
    get_chat_model,
    get_chat_model_by_profile_name,
)


class TestGetChatModel:
    """Test the get_chat_model function."""

    @patch("src.llm.factory._create_anthropic_model")
    def test_creates_anthropic_model(self, mock_create):
        """Test creating an Anthropic chat model."""
        mock_model = MagicMock()
        mock_create.return_value = mock_model

        config = LLMProfileConfig(
            provider="anthropic", model="claude-haiku-4-5", api_key="test-key"
        )

        result = get_chat_model(config)

        assert result is mock_model
        mock_create.assert_called_once_with(config)

    @patch("src.llm.factory._create_google_model")
    def test_creates_google_model(self, mock_create):
        """Test creating a Google chat model."""
        mock_model = MagicMock()
        mock_create.return_value = mock_model

        config = LLMProfileConfig(
            provider="google", model="gemini-2.5-flash", api_key="test-key"
        )

        result = get_chat_model(config)

        assert result is mock_model
        mock_create.assert_called_once_with(config)

    def test_unsupported_provider_raises_error(self):
        """Test that unsupported provider raises LLMProviderError."""
        config = LLMProfileConfig(
            provider="anthropic", model="claude-haiku-4-5", api_key="test-key"
        )
        config.provider = "unsupported"

        with pytest.raises(LLMProviderError, match="Unsupported LLM provider"):
            get_chat_model(config)

    def test_provider_case_insensitive(self):
        """Test that provider names are handled case-insensitively."""
        with patch("src.llm.factory._create_anthropic_model") as mock_create:
            mock_create.return_value = MagicMock()

            config = LLMProfileConfig(
                provider="ANTHROPIC", model="claude-haiku-4-5", api_key="test-key"
            )

            get_chat_model(config)
            mock_create.assert_called_once()

    @patch("src.llm.factory._create_anthropic_model")
    def test_import_error_raises_provider_error(self, mock_create):
        """Test that import errors are wrapped in LLMProviderError."""
        mock_create.side_effect = ImportError("langchain_anthropic not installed")

        config = LLMProfileConfig(
            provider="anthropic", model="claude-haiku-4-5", api_key="test-key"
        )

        with pytest.raises(LLMProviderError, match="Failed to import dependencies"):
            get_chat_model(config)

    @patch("src.llm.factory._create_anthropic_model")
    def test_generic_error_raises_provider_error(self, mock_create):
        """Test that generic errors are wrapped in LLMProviderError."""
        mock_create.side_effect = RuntimeError("Connection failed")

        config = LLMProfileConfig(
            provider="anthropic", model="claude-haiku-4-5", api_key="test-key"
        )

        with pytest.raises(LLMProviderError, match="Failed to create chat model"):
            get_chat_model(config)

    @patch("src.llm.factory._create_anthropic_model")
    def test_llm_provider_error_passthrough(self, mock_create):
        """Test that LLMProviderError from constructor passes through unwrapped."""
        mock_create.side_effect = LLMProviderError("API key not found")

        config = LLMProfileConfig(
            provider="anthropic", model="claude-haiku-4-5", api_key="test-key"
        )

        with pytest.raises(LLMProviderError, match="API key not found"):
            get_chat_model(config)


class TestGetChatModelByProfileName:
    """Test the get_chat_model_by_profile_name function."""

    @patch("src.llm.factory.get_chat_model")
    @patch("src.config.config")
    def test_loads_profile_and_creates_model(self, mock_config, mock_get_model):
        """Test that profile is loaded and model is created."""
        mock_profile = LLMProfileConfig(
            provider="anthropic", model="claude-haiku-4-5", api_key="test-key"
        )
        mock_config.get_llm_profile.return_value = mock_profile
        mock_model = MagicMock()
        mock_get_model.return_value = mock_model

        result = get_chat_model_by_profile_name("test_profile")

        assert result is mock_model
        mock_config.get_llm_profile.assert_called_once_with("test_profile")
        mock_get_model.assert_called_once_with(mock_profile)


class TestProviderConstructors:
    """Test the actual provider constructor functions."""

    @patch("langchain_anthropic.ChatAnthropic")
    def test_anthropic_model_creation(self, mock_chat_class):
        """Test that Anthropic model is created with correct parameters."""
        mock_instance = MagicMock()
        mock_chat_class.return_value = mock_instance

        config = LLMProfileConfig(
            provider="anthropic",
            model="claude-haiku-4-5",
            temperature=0.7,
            max_tokens=1000,
            api_key="test-key",
        )

        from src.llm.factory import _create_anthropic_model

        result = _create_anthropic_model(config)

        assert result is mock_instance
        mock_chat_class.assert_called_once_with(
            model="claude-haiku-4-5",
            temperature=0.7,
            max_tokens=1000,
            api_key="test-key",
        )

    @patch("langchain_google_genai.ChatGoogleGenerativeAI")
    def test_google_model_creation(self, mock_chat_class):
        """Test that Google model is created with correct parameters."""
        mock_instance = MagicMock()
        mock_chat_class.return_value = mock_instance

        config = LLMProfileConfig(
            provider="google",
            model="gemini-2.5-flash",
            temperature=0.2,
            max_tokens=512,
            api_key="test-key",
        )

        from src.llm.factory import _create_google_model

        result = _create_google_model(config)

        assert result is mock_instance
        mock_chat_class.assert_called_once_with(
            model="gemini-2.5-flash",
            temperature=0.2,
            max_tokens=512,
            google_api_key="test-key",
        )


class TestEnsureApiKey:
    """Test the _ensure_api_key utility."""

    def test_returns_key_from_config(self):
        """Test that API key from config is returned."""
        config = LLMProfileConfig(
            provider="anthropic", model="claude-haiku-4-5", api_key="config-key"
        )

        result = _ensure_api_key(config, "ANTHROPIC_API_KEY")
        assert result == "config-key"

    @patch.dict("os.environ", {"TEST_KEY": "env-key"})
    def test_returns_key_from_environment(self):
        """Test that API key from environment is returned when config has none."""
        config = LLMProfileConfig(provider="anthropic", model="claude-haiku-4-5")

        result = _ensure_api_key(config, "TEST_KEY")
        assert result == "env-key"

    @patch.dict("os.environ", {"TEST_KEY": "env-key"})
    def test_config_key_takes_precedence(self):
        """Test that config key takes precedence over environment."""
        config = LLMProfileConfig(
            provider="anthropic", model="claude-haiku-4-5", api_key="config-key"
        )

        result = _ensure_api_key(config, "TEST_KEY")
        assert result == "config-key"

    @patch.dict("os.environ", {}, clear=True)
    def test_missing_key_raises_error(self):
        """Test that missing API key raises LLMProviderError."""
        config = LLMProfileConfig(provider="anthropic", model="claude-haiku-4-5")

        with pytest.raises(LLMProviderError, match="API key not found"):
            _ensure_api_key(config, "MISSING_KEY")

    @patch.dict("os.environ", {}, clear=True)
    def test_error_message_contains_env_var_name(self):
        """Test that error message includes the environment variable name."""
        config = LLMProfileConfig(provider="anthropic", model="claude-haiku-4-5")

        with pytest.raises(LLMProviderError, match="MY_API_KEY"):
            _ensure_api_key(config, "MY_API_KEY")
