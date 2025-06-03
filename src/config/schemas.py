"""
Pydantic models for configuration
"""

from typing import List, Optional

from pydantic import BaseModel, Field


class UserPreferences(BaseModel):
    """User job preferences and criteria"""

    desired_roles: List[str] = Field(
        default_factory=list, description="List of desired job titles/roles"
    )

    required_skills: List[str] = Field(
        default_factory=list,
        description="Skills that are required in the job description",
    )

    preferred_skills: List[str] = Field(
        default_factory=list, description="Skills that are preferred but not required"
    )

    min_years_experience: Optional[int] = Field(
        default=None, description="Minimum years of experience"
    )

    max_years_experience: Optional[int] = Field(
        default=None, description="Maximum years of experience"
    )

    desired_salary_range: Optional[tuple[int, int]] = Field(
        default=None, description="Desired salary range (min, max)"
    )

    preferred_locations: List[str] = Field(
        default_factory=list, description="Preferred job locations"
    )

    remote_preference: Optional[str] = Field(
        default=None,
        description="Remote work preference: 'remote', 'hybrid', 'onsite', or None",
    )

    other_criteria: List[str] = Field(
        default_factory=list, description="Other job criteria or preferences"
    )


class LLMConfig(BaseModel):
    """LLM configuration settings"""

    provider: str = Field(
        default="anthropic", description="LLM provider (anthropic, openai, etc.)"
    )

    model: str = Field(
        default="claude-3-opus-20240229", description="Model name to use"
    )

    temperature: float = Field(default=0.7, description="Temperature for generation")

    max_tokens: int = Field(
        default=512, description="Maximum number of tokens to generate"
    )

    api_key: Optional[str] = Field(
        default=None,
        description="API key (should be loaded from environment in production)",
    )
