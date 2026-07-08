"""
Tests for environment check component functionality
"""

from typing import Optional
from unittest.mock import MagicMock, patch

from src.config.models import AgentTasksConfig, LLMConfig
from ui.components.environment_check import (
    build_setup_instructions,
    check_environment_setup,
)


def _make_llm_config(provider: str, api_key: Optional[str]) -> LLMConfig:
    """Build an LLMConfig for tests. APP_ENV=stage in conftest.py disables
    model/api-key validators so api_key=None is allowed here."""
    return LLMConfig(
        provider=provider,
        model="stage-test-model",
        api_key=api_key,
    )


def _make_agent_tasks(**overrides: LLMConfig) -> AgentTasksConfig:
    """Build a real AgentTasksConfig. Defaults to anthropic+valid key for
    every task; tests override only the tasks they care about so a real
    Pydantic model is exercised in every code path."""
    default = _make_llm_config("anthropic", "default-key")
    fields = {
        "job_evaluation_extraction": default,
        "job_evaluation_fit": default,
        "interview_research": default,
        "interview_question_generation": default,
        "interview_answer_generation": default,
        "interview_compilation": default,
        "interview_research_planning": default,
        "interview_research_critic": default,
        "interview_question_critic": default,
        "interview_guide_synthesis": default,
    }
    fields.update(overrides)
    return AgentTasksConfig(**fields)


class TestEnvironmentCheck:
    """Test environment check functionality"""

    def test_environment_check_with_valid_api_keys(self):
        """All tasks have api_key set → environment reports as valid"""
        mock_config = MagicMock()
        mock_config.agent_tasks = _make_agent_tasks()

        with patch("ui.components.environment_check.config", mock_config):
            is_valid, message = check_environment_setup()

            assert is_valid is True
            assert message == "Environment is properly configured"

    def test_environment_check_with_missing_api_keys(self):
        """One task missing its api_key → that provider's env var is reported"""
        mock_config = MagicMock()
        mock_config.agent_tasks = _make_agent_tasks(
            job_evaluation_extraction=_make_llm_config("anthropic", None),
        )

        with patch("ui.components.environment_check.config", mock_config):
            is_valid, message = check_environment_setup()

            assert is_valid is False
            assert "Missing required API keys: ANTHROPIC_API_KEY" in message

    def test_environment_check_with_multiple_missing_keys(self):
        """Tasks missing keys for different providers → all are reported"""
        mock_config = MagicMock()
        mock_config.agent_tasks = _make_agent_tasks(
            job_evaluation_extraction=_make_llm_config("anthropic", None),
            interview_research=_make_llm_config("google", None),
        )

        with patch("ui.components.environment_check.config", mock_config):
            is_valid, message = check_environment_setup()

            assert is_valid is False
            assert "Missing required API keys:" in message
            assert "ANTHROPIC_API_KEY" in message
            assert "GOOGLE_API_KEY" in message

    def test_environment_check_deduplicates_shared_provider(self):
        """Multiple tasks sharing one provider → env var is reported once"""
        mock_config = MagicMock()
        mock_config.agent_tasks = _make_agent_tasks(
            interview_research=_make_llm_config("google", None),
            interview_compilation=_make_llm_config("google", None),
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


class TestBuildSetupInstructions:
    """Test setup-instruction rendering stays in sync with detected
    missing keys, so the UI does not contradict the warning banner."""

    def test_instructions_reference_each_missing_key(self):
        """When the detector reports a key, instructions must mention it."""
        instructions = build_setup_instructions({"GOOGLE_API_KEY"})

        assert "GOOGLE_API_KEY" in instructions
        # And do not invent a different key the detector did not report
        assert "ANTHROPIC_API_KEY" not in instructions

    def test_instructions_list_multiple_missing_keys(self):
        instructions = build_setup_instructions({"ANTHROPIC_API_KEY", "GOOGLE_API_KEY"})

        assert "ANTHROPIC_API_KEY" in instructions
        assert "GOOGLE_API_KEY" in instructions

    def test_instructions_have_generic_fallback_when_no_keys_known(self):
        """If the detector could not enumerate keys (e.g. config error),
        instructions still render without naming the wrong provider."""
        instructions = build_setup_instructions(set())

        assert "ANTHROPIC_API_KEY" not in instructions
        assert "GOOGLE_API_KEY" not in instructions
        assert ".env" in instructions

    def test_instructions_keep_langfuse_optional_section(self):
        instructions = build_setup_instructions({"GOOGLE_API_KEY"})

        assert "LANGFUSE_PUBLIC_KEY" in instructions
        assert "LANGFUSE_SECRET_KEY" in instructions
