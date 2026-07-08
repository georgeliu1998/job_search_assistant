"""
Unit tests for the Pydantic configuration models in src/config/models.py.

Focuses on the pieces added for per-task interview-prep LLM configs, the
interview-prep orchestration knobs, and the global LLM call-resilience
config (retry shape + cross-provider tier-matched fallback mapping, with
optional per-task override).
"""

import pytest
from pydantic import ValidationError

from src.config.models import (
    AppConfig,
    FallbackTarget,
    InterviewPrepConfig,
    LLMConfig,
    LLMResilienceConfig,
    LLMSettingsConfig,
    RetryConfig,
)

# APP_ENV=stage is set globally in tests/conftest.py, which skips both the
# model-catalog and API-key validators. Use real-looking model names anyway
# so these tests still document/exercise realistic values.


class TestFallbackTarget:
    """FallbackTarget validates provider/model like LLMConfig does."""

    def test_valid_provider_and_model(self):
        target = FallbackTarget(provider="ANTHROPIC", model="claude-haiku-4-5")

        assert target.provider == "anthropic"  # normalized to lowercase
        assert target.model == "claude-haiku-4-5"

    def test_invalid_provider_rejected(self):
        with pytest.raises(ValidationError, match="Provider must be one of"):
            FallbackTarget(provider="openai", model="gpt-4")


class TestLLMConfigFallbackField:
    """LLMConfig carries an optional per-task fallback override."""

    def test_fallback_defaults_to_none(self):
        config = LLMConfig(provider="google", model="gemini-2.5-flash-lite")

        assert config.fallback is None

    def test_fallback_can_be_set(self):
        config = LLMConfig(
            provider="google",
            model="gemini-2.5-flash-lite",
            fallback=FallbackTarget(provider="anthropic", model="claude-haiku-4-5"),
        )

        assert config.fallback == FallbackTarget(provider="anthropic", model="claude-haiku-4-5")

    def test_fallback_not_part_of_hash_or_equality(self):
        """Fallback is a resilience-layer concern, not part of the primary
        model's identity, so two otherwise-identical configs with different
        fallbacks are still equal/hash equal."""
        base = LLMConfig(provider="google", model="gemini-2.5-flash-lite")
        with_fallback = LLMConfig(
            provider="google",
            model="gemini-2.5-flash-lite",
            fallback=FallbackTarget(provider="anthropic", model="claude-haiku-4-5"),
        )

        assert base == with_fallback
        assert hash(base) == hash(with_fallback)


class TestRetryConfig:
    """RetryConfig defaults and the exponential_jitter_params() helper."""

    def test_defaults(self):
        retry = RetryConfig()

        assert retry.max_attempts_per_provider == 3
        assert retry.wait_exponential_jitter is True
        assert retry.exponential_jitter_params() is None

    def test_rejects_non_positive_max_attempts(self):
        with pytest.raises(ValidationError):
            RetryConfig(max_attempts_per_provider=0)

    def test_exponential_jitter_params_only_includes_set_fields(self):
        retry = RetryConfig(jitter_initial=1.0, jitter_max=30.0)

        assert retry.exponential_jitter_params() == {"initial": 1.0, "max": 30.0}

    def test_exponential_jitter_params_all_fields(self):
        retry = RetryConfig(jitter_initial=1.0, jitter_max=30.0, jitter_exp_base=2.0)

        assert retry.exponential_jitter_params() == {
            "initial": 1.0,
            "max": 30.0,
            "exp_base": 2.0,
        }


class TestLLMResilienceConfig:
    """Fallback-tier validation and tier-matched resolution."""

    def _resilience_config(self) -> LLMResilienceConfig:
        return LLMResilienceConfig(
            fallback_tiers={
                "cheap": {"google": "gemini-2.5-flash-lite", "anthropic": "claude-haiku-4-5"},
                "standard": {"google": "gemini-2.5-flash", "anthropic": "claude-sonnet-4-6"},
            }
        )

    def test_defaults_to_empty_tiers_and_default_retry(self):
        resilience = LLMResilienceConfig()

        assert resilience.fallback_tiers == {}
        assert resilience.retry == RetryConfig()

    def test_fallback_tiers_normalizes_provider_case(self):
        resilience = LLMResilienceConfig(
            fallback_tiers={"cheap": {"GOOGLE": "gemini-2.5-flash-lite"}}
        )

        assert resilience.fallback_tiers == {"cheap": {"google": "gemini-2.5-flash-lite"}}

    def test_fallback_tiers_rejects_invalid_provider(self):
        with pytest.raises(ValidationError, match="Provider must be one of"):
            LLMResilienceConfig(fallback_tiers={"cheap": {"openai": "gpt-4"}})

    def test_resolve_fallback_matches_tier(self):
        resilience = self._resilience_config()
        primary = LLMConfig(provider="google", model="gemini-2.5-flash-lite")

        fallback = resilience.resolve_fallback(primary)

        assert fallback == FallbackTarget(provider="anthropic", model="claude-haiku-4-5")

    def test_resolve_fallback_is_tier_matched_not_cross_tier(self):
        """A 'standard'-tier google task must not fall back to the 'cheap'
        anthropic model, even though both tiers reference anthropic."""
        resilience = self._resilience_config()
        primary = LLMConfig(provider="google", model="gemini-2.5-flash")

        fallback = resilience.resolve_fallback(primary)

        assert fallback == FallbackTarget(provider="anthropic", model="claude-sonnet-4-6")

    def test_resolve_fallback_returns_none_when_no_tier_matches(self):
        resilience = self._resilience_config()
        primary = LLMConfig(provider="google", model="gemini-2.5-pro")  # premium, no tier defined

        assert resilience.resolve_fallback(primary) is None

    def test_resolve_fallback_returns_none_with_no_tiers_configured(self):
        resilience = LLMResilienceConfig()
        primary = LLMConfig(provider="google", model="gemini-2.5-flash-lite")

        assert resilience.resolve_fallback(primary) is None

    def test_per_task_override_wins_over_tier_lookup(self):
        resilience = self._resilience_config()
        primary = LLMConfig(
            provider="google",
            model="gemini-2.5-flash-lite",
            fallback=FallbackTarget(provider="anthropic", model="claude-opus-4-7"),
        )

        fallback = resilience.resolve_fallback(primary)

        assert fallback == FallbackTarget(provider="anthropic", model="claude-opus-4-7")


class TestInterviewPrepConfig:
    """Orchestration knob defaults."""

    def test_defaults(self):
        cfg = InterviewPrepConfig()

        assert cfg.max_research_attempts == 2
        assert cfg.max_question_attempts == 2
        assert cfg.enable_research_critic is True
        assert cfg.enable_question_critic is True

    def test_gates_can_be_disabled(self):
        cfg = InterviewPrepConfig(enable_research_critic=False, enable_question_critic=False)

        assert cfg.enable_research_critic is False
        assert cfg.enable_question_critic is False

    @pytest.mark.parametrize("field", ["max_research_attempts", "max_question_attempts"])
    def test_rejects_non_positive_attempts(self, field):
        with pytest.raises(ValidationError):
            InterviewPrepConfig(**{field: 0})


class TestAppConfigDefaults:
    """AppConfig fills in llm/interview_prep with defaults when omitted,
    so configs predating this feature still validate."""

    def _minimal_kwargs(self):
        from src.config.models import AgentTasksConfig, ObservabilityConfig

        task = LLMConfig(provider="google", model="gemini-2.5-flash-lite")
        agent_tasks = AgentTasksConfig(
            job_evaluation_extraction=task,
            job_evaluation_fit=task,
            interview_research=task,
            interview_question_generation=task,
            interview_answer_generation=task,
            interview_compilation=task,
            interview_research_planning=task,
            interview_research_critic=task,
            interview_question_critic=task,
            interview_guide_synthesis=task,
        )
        return {
            "general": {"name": "test", "tagline": "test", "version": "0.0.0"},
            "logging": {},
            "agent_tasks": agent_tasks,
            "observability": ObservabilityConfig(),
        }

    def test_llm_and_interview_prep_default_when_omitted(self):
        app_config = AppConfig(**self._minimal_kwargs())

        assert isinstance(app_config.llm, LLMSettingsConfig)
        assert app_config.llm.resilience.fallback_tiers == {}
        assert isinstance(app_config.interview_prep, InterviewPrepConfig)
        assert app_config.interview_prep.max_research_attempts == 2
