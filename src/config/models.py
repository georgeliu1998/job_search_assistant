"""
Pydantic models for configuration validation and type safety.

These models define the structure and validation rules for all configuration
sections in the application.
"""

import os
from typing import ClassVar, Dict, List, Optional

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


class AgentConfig(BaseModel):
    """Agent task to LLM profile mappings."""

    job_evaluation_extraction: str = Field(
        ..., description="LLM profile for job information extraction"
    )


class EvaluationCriteriaConfig(BaseModel):
    """Business logic parameters for job evaluation."""

    min_salary: int = Field(..., ge=0, description="Minimum acceptable salary")
    remote_required: bool = Field(..., description="Whether remote work is required")
    ic_title_requirements: List[str] = Field(
        ..., description="Required seniority levels for IC roles"
    )


class LLMProfileConfig(BaseModel):
    """Configuration for a single LLM profile."""

    provider: str = Field(..., description="LLM provider")
    model: str = Field(..., description="Model identifier")
    temperature: float = Field(
        default=0.0, ge=0.0, le=1.0, description="Sampling temperature"
    )
    max_tokens: int = Field(default=512, gt=0, description="Maximum tokens to generate")
    api_key: Optional[str] = Field(
        default=None, description="API key for the provider (from env var)"
    )

    # Valid models for each provider
    VALID_MODELS: ClassVar[Dict[str, set]] = {
        "anthropic": {
            "claude-3-5-haiku-20241022",
            "claude-3-5-haiku-latest",
            "claude-3-haiku-20240307",
            "claude-sonnet-4-20250514",
        }
    }

    @field_validator("provider")
    @classmethod
    def validate_provider(cls, v: str) -> str:
        """Validate that provider is supported."""
        valid_providers = {"anthropic"}
        if v.lower() not in valid_providers:
            raise ValueError(f"Provider must be one of: {', '.join(valid_providers)}")
        return v.lower()

    @field_validator("model")
    @classmethod
    def validate_model(cls, v: str, info) -> str:
        """Validate that model is supported for the provider."""
        # Skip validation in stage environments or for test/stage models
        current_env = os.getenv("APP_ENV", "").lower()
        if (
            current_env == Environment.STAGE.value
            or v.startswith("stage")
            or v.startswith("test")
            or "stage" in v.lower()
            or "test" in v.lower()
        ):
            return v

        provider = info.data.get("provider", "").lower()

        if provider in cls.VALID_MODELS:
            valid_models = cls.VALID_MODELS[provider]
            if v not in valid_models:
                raise ValueError(
                    f"Model '{v}' not supported for provider '{provider}'. "
                    f"Valid models: {', '.join(sorted(valid_models))}"
                )

        return v

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
                f"Please set {provider.upper()}_API_KEY in your environment or .env file."
            )

        return v

    def __hash__(self) -> int:
        """Make LLMProfileConfig hashable for use in singleton pattern."""
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
        """Define equality for LLMProfileConfig objects."""
        if not isinstance(other, LLMProfileConfig):
            return False
        return (
            self.provider == other.provider
            and self.model == other.model
            and self.temperature == other.temperature
            and self.max_tokens == other.max_tokens
            and self.api_key == other.api_key
        )


class LangfuseConfig(BaseModel):
    """Langfuse observability configuration."""

    enabled: bool = Field(default=False, description="Enable Langfuse tracing")
    host: str = Field(
        default="https://us.cloud.langfuse.com", description="Langfuse host URL"
    )
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
    agents: AgentConfig = Field(..., description="Agent configuration")
    evaluation_criteria: EvaluationCriteriaConfig = Field(
        ..., description="Job evaluation criteria"
    )
    llm_profiles: Dict[str, LLMProfileConfig] = Field(
        ..., description="LLM profile configurations"
    )
    observability: ObservabilityConfig = Field(
        ..., description="Observability configuration"
    )

    def get_llm_profile(self, profile_name: str) -> LLMProfileConfig:
        """Get LLM profile by name with validation."""
        if profile_name not in self.llm_profiles:
            available = ", ".join(self.llm_profiles.keys())
            raise ValueError(
                f"LLM profile '{profile_name}' not found. "
                f"Available profiles: {available}"
            )
        return self.llm_profiles[profile_name]

    def get_agent_llm_profile(self, agent_task: str) -> LLMProfileConfig:
        """Get LLM profile for a specific agent task."""
        if not hasattr(self.agents, agent_task):
            raise ValueError(f"Unknown agent task: {agent_task}")

        profile_name = getattr(self.agents, agent_task)
        return self.get_llm_profile(profile_name)
