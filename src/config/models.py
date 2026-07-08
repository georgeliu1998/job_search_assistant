"""
Pydantic models for configuration validation and type safety.

These models define the structure and validation rules for all configuration
sections in the application.
"""

import os
from typing import ClassVar, Dict, Optional

from pydantic import BaseModel, Field, field_validator

from src.models.enums import Environment


class GeneralConfig(BaseModel):
    """Application metadata and general settings."""

    name: str = Field(..., description="Application name")
    tagline: str = Field(..., description="Application tagline")
    version: str = Field(..., description="Application version")
    debug: bool = Field(default=False, description="Enable debug mode")


class LoggingConfig(BaseModel):
    """Logging configuration settings."""

    level: str = Field(default="INFO", description="Logging level")
    format: str = Field(
        default="%(asctime)s %(name)s [%(levelname)s] %(message)s",
        description="Log message format string",
    )

    @field_validator("level")
    @classmethod
    def validate_log_level(cls, v: str) -> str:
        """Validate that log level is one of the standard levels."""
        valid_levels = {"DEBUG", "INFO", "WARNING", "ERROR", "CRITICAL"}
        if v.upper() not in valid_levels:
            raise ValueError(f"Log level must be one of: {', '.join(valid_levels)}")
        return v.upper()


# Shared by LLMConfig and FallbackTarget so both validate providers/models
# identically without one class depending on the other's definition order.
_VALID_PROVIDERS: frozenset = frozenset({"anthropic", "google"})

_VALID_MODELS_BY_PROVIDER: Dict[str, set] = {
    "anthropic": {
        "claude-haiku-4-5",
        "claude-haiku-4-5-20251001",
        "claude-sonnet-4-6",
        "claude-sonnet-4-20250514",
        "claude-opus-4-7",
    },
    "google": {
        "gemini-3.5-flash",
        "gemini-2.5-pro",
        "gemini-2.5-flash",
        "gemini-2.5-flash-lite",
    },
}


def _validate_provider_name(v: str) -> str:
    """Validate that a provider name is supported, normalizing to lowercase."""
    if v.lower() not in _VALID_PROVIDERS:
        raise ValueError(f"Provider must be one of: {', '.join(sorted(_VALID_PROVIDERS))}")
    return v.lower()


def _validate_model_name(v: str, provider: str) -> str:
    """Validate that a model is supported for the given provider.

    Skipped for stage environments or test/stage-style model names, so
    fixtures and integration stubs don't need to name a real model.
    """
    current_env = os.getenv("APP_ENV", "").lower()
    if (
        current_env == Environment.STAGE.value
        or v.startswith("stage")
        or v.startswith("test")
        or "stage" in v.lower()
        or "test" in v.lower()
    ):
        return v

    provider = provider.lower()
    if provider in _VALID_MODELS_BY_PROVIDER:
        valid_models = _VALID_MODELS_BY_PROVIDER[provider]
        if v not in valid_models:
            raise ValueError(
                f"Model '{v}' not supported for provider '{provider}'. "
                f"Valid models: {', '.join(sorted(valid_models))}"
            )

    return v


class FallbackTarget(BaseModel):
    """A provider+model pair identifying an LLM call-resilience fallback target.

    Used both for the global tier-matched fallback map
    (``LLMResilienceConfig.fallback_tiers``) and for a per-task override
    (``LLMConfig.fallback``). Sampling settings aren't part of this: when a
    fallback is actually built, it borrows ``temperature``/``max_tokens``
    from the primary task's own config - only the provider/model differ.
    """

    provider: str = Field(..., description="Fallback provider")
    model: str = Field(..., description="Fallback model identifier")

    @field_validator("provider")
    @classmethod
    def validate_provider(cls, v: str) -> str:
        """Validate that provider is supported."""
        return _validate_provider_name(v)

    @field_validator("model")
    @classmethod
    def validate_model(cls, v: str, info) -> str:
        """Validate that model is supported for the provider."""
        return _validate_model_name(v, info.data.get("provider", ""))


class LLMConfig(BaseModel):
    """Configuration for a single LLM (provider, model, and sampling settings)."""

    provider: str = Field(..., description="LLM provider")
    model: str = Field(..., description="Model identifier")
    temperature: float = Field(default=0.0, ge=0.0, le=1.0, description="Sampling temperature")
    max_tokens: int = Field(default=512, gt=0, description="Maximum tokens to generate")
    api_key: Optional[str] = Field(
        default=None, description="API key for the provider (from env var)"
    )
    fallback: Optional[FallbackTarget] = Field(
        default=None,
        description=(
            "Optional override of the global tier-matched resilience fallback "
            "(AppConfig.llm.resilience.fallback_tiers) for this task only."
        ),
    )

    # Valid models for each provider
    VALID_MODELS: ClassVar[Dict[str, set]] = _VALID_MODELS_BY_PROVIDER

    @field_validator("provider")
    @classmethod
    def validate_provider(cls, v: str) -> str:
        """Validate that provider is supported."""
        return _validate_provider_name(v)

    @field_validator("model")
    @classmethod
    def validate_model(cls, v: str, info) -> str:
        """Validate that model is supported for the provider."""
        return _validate_model_name(v, info.data.get("provider", ""))

    @field_validator("api_key")
    @classmethod
    def validate_api_key(cls, v: Optional[str], info) -> Optional[str]:
        """Validate that API key is provided for non-test environments."""
        current_env = os.getenv("APP_ENV", "").lower()

        # Skip validation in stage environment (used for testing)
        if current_env == Environment.STAGE.value:
            return v

        # In dev and prod environments, require API key
        if not v:
            provider = info.data.get("provider", "unknown")
            raise ValueError(
                f"API key is required for {provider} provider. "
                f"Please set {provider.upper()}_API_KEY in your environment "
                "or .env file."
            )

        return v

    def __hash__(self) -> int:
        """Make LLMConfig hashable for use in singleton pattern."""
        return hash(
            (
                self.provider,
                self.model,
                self.temperature,
                self.max_tokens,
                self.api_key,
            )
        )

    def __eq__(self, other) -> bool:
        """Define equality for LLMConfig objects."""
        if not isinstance(other, LLMConfig):
            return False
        return (
            self.provider == other.provider
            and self.model == other.model
            and self.temperature == other.temperature
            and self.max_tokens == other.max_tokens
            and self.api_key == other.api_key
        )


class AgentTasksConfig(BaseModel):
    """LLM configuration for each agent task.

    Each task directly carries its own provider, model, and sampling settings.
    """

    job_evaluation_extraction: LLMConfig = Field(
        ..., description="LLM config for job information extraction"
    )
    job_evaluation_fit: LLMConfig = Field(..., description="LLM config for the job fit assessment")
    interview_research: LLMConfig = Field(..., description="LLM config for interview research")
    interview_question_generation: LLMConfig = Field(
        ..., description="LLM config for question generation"
    )
    interview_answer_generation: LLMConfig = Field(
        ..., description="LLM config for answer generation"
    )
    interview_compilation: LLMConfig = Field(..., description="LLM config for guide compilation")
    interview_research_planning: LLMConfig = Field(
        ..., description="LLM config for the research-planner node (JD/resume -> query plan)"
    )
    interview_research_critic: LLMConfig = Field(
        ..., description="LLM config for the post-research quality gate"
    )
    interview_question_critic: LLMConfig = Field(
        ..., description="LLM config for the post-question quality gate"
    )
    interview_guide_synthesis: LLMConfig = Field(
        ..., description="LLM config for research-summary and prep-tips synthesis"
    )


class RetryConfig(BaseModel):
    """Same-provider retry/backoff shape for the LLM call-resilience layer.

    Maps onto ``Runnable.with_retry``'s parameters (see
    ``src/llm/resilience.py``): ``jitter_*`` fields are optional overrides
    for Tenacity's ``wait_exponential_jitter``; unset ones fall back to
    Tenacity's own defaults via :meth:`exponential_jitter_params`.
    """

    max_attempts_per_provider: int = Field(
        default=3,
        ge=1,
        description="Same-provider attempts before falling back to another provider (or failing)",
    )
    wait_exponential_jitter: bool = Field(
        default=True,
        description="Use exponential backoff with jitter between same-provider attempts",
    )
    jitter_initial: Optional[float] = Field(
        default=None,
        gt=0,
        description="Tenacity wait_exponential_jitter 'initial' override (seconds)",
    )
    jitter_max: Optional[float] = Field(
        default=None, gt=0, description="Tenacity wait_exponential_jitter 'max' override (seconds)"
    )
    jitter_exp_base: Optional[float] = Field(
        default=None, gt=0, description="Tenacity wait_exponential_jitter 'exp_base' override"
    )

    def exponential_jitter_params(self) -> Optional[Dict[str, float]]:
        """Build kwargs for ``with_retry``'s ``exponential_jitter_params``.

        Returns ``None`` (letting Tenacity use its own defaults) when none of
        the jitter fields have been overridden.
        """
        params = {
            "initial": self.jitter_initial,
            "max": self.jitter_max,
            "exp_base": self.jitter_exp_base,
        }
        set_params = {k: v for k, v in params.items() if v is not None}
        return set_params or None


class LLMResilienceConfig(BaseModel):
    """Global defaults for the LLM call-resilience layer (see ``src/llm/resilience.py``).

    ``fallback_tiers`` groups equivalent cost/capability models across
    providers (e.g. a "cheap" tier pairing google's flash-lite with
    anthropic's haiku) so a fallback never silently downgrades a task onto a
    much weaker model. Any ``agent_tasks.<task>.fallback`` overrides this
    tier lookup for that one task.
    """

    retry: RetryConfig = Field(
        default_factory=RetryConfig, description="Default retry/backoff shape for every task"
    )
    fallback_tiers: Dict[str, Dict[str, str]] = Field(
        default_factory=dict,
        description="Tier name -> {provider: model}, for cross-provider same-tier fallback",
    )

    @field_validator("fallback_tiers")
    @classmethod
    def validate_fallback_tiers(cls, v: Dict[str, Dict[str, str]]) -> Dict[str, Dict[str, str]]:
        """Validate and normalize every (provider, model) pair in every tier."""
        normalized: Dict[str, Dict[str, str]] = {}
        for tier_name, providers in v.items():
            normalized_providers: Dict[str, str] = {}
            for provider, model in providers.items():
                provider_norm = _validate_provider_name(provider)
                normalized_providers[provider_norm] = _validate_model_name(model, provider_norm)
            normalized[tier_name] = normalized_providers
        return normalized

    def resolve_fallback(self, primary: LLMConfig) -> Optional[FallbackTarget]:
        """Resolve the fallback target for a primary task config.

        A per-task ``primary.fallback`` override always wins. Otherwise, find
        the tier that contains ``primary``'s (provider, model) pair and
        return the *other* provider's model from that same tier. Returns
        ``None`` if there is no override and no tier contains this
        provider/model pairing, so callers can fall back to primary-only
        retries instead of guessing a mismatched-tier fallback.
        """
        if primary.fallback is not None:
            return primary.fallback

        for providers in self.fallback_tiers.values():
            if providers.get(primary.provider) != primary.model:
                continue
            for other_provider, other_model in providers.items():
                if other_provider != primary.provider:
                    return FallbackTarget(provider=other_provider, model=other_model)

        return None


class LLMSettingsConfig(BaseModel):
    """Top-level ``[llm]`` configuration section."""

    resilience: LLMResilienceConfig = Field(
        default_factory=LLMResilienceConfig, description="Global LLM call-resilience configuration"
    )


class InterviewPrepConfig(BaseModel):
    """Orchestration knobs for the interview-prep multi-agent workflow.

    Bound the two bounded critic gates (research and questions) so retries
    are structurally capped, and let each gate be disabled independently
    (e.g. for a future free tier that skips quality gates).
    """

    max_research_attempts: int = Field(
        default=2, ge=1, description="Max research re-plans before proceeding with best effort"
    )
    max_question_attempts: int = Field(
        default=2,
        ge=1,
        description="Max question-regeneration rounds before proceeding with best effort",
    )
    enable_research_critic: bool = Field(
        default=True, description="Toggle the post-research quality gate"
    )
    enable_question_critic: bool = Field(
        default=True, description="Toggle the post-question quality gate"
    )


class LangfuseConfig(BaseModel):
    """Langfuse observability configuration."""

    enabled: bool = Field(default=False, description="Enable Langfuse tracing")
    host: str = Field(default="https://us.cloud.langfuse.com", description="Langfuse host URL")
    public_key: Optional[str] = Field(
        default=None, description="Langfuse public key (from env var)"
    )
    secret_key: Optional[str] = Field(
        default=None, description="Langfuse secret key (from env var)"
    )

    def is_valid(self) -> bool:
        """Check if configuration is valid for creating a handler."""
        return bool(self.enabled and self.public_key and self.secret_key)


class ObservabilityConfig(BaseModel):
    """Observability and monitoring settings."""

    langfuse: LangfuseConfig = Field(
        default_factory=LangfuseConfig, description="Langfuse configuration"
    )


class AppConfig(BaseModel):
    """Root configuration model containing all application configuration."""

    general: GeneralConfig = Field(..., description="General application configuration")
    logging: LoggingConfig = Field(..., description="Logging configuration")
    agent_tasks: AgentTasksConfig = Field(..., description="Per-task LLM configuration")
    llm: LLMSettingsConfig = Field(
        default_factory=LLMSettingsConfig, description="Global LLM configuration (call resilience)"
    )
    interview_prep: InterviewPrepConfig = Field(
        default_factory=InterviewPrepConfig,
        description="Interview-prep workflow orchestration knobs",
    )
    observability: ObservabilityConfig = Field(..., description="Observability configuration")
