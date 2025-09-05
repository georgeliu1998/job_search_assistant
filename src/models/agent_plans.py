"""Pydantic models for agent execution plans and strategies."""

import json
from typing import Any, Dict, List, Optional, Union

from pydantic import BaseModel, Field, field_validator


class ResearchStrategy(BaseModel):
    """Strategy for research agent execution."""

    # AI-generated search queries instead of hardcoded topics
    primary_queries: List[str] = Field(
        description="Primary search queries generated from job analysis"
    )

    secondary_queries: List[str] = Field(
        default_factory=list,
        description="Secondary/follow-up search queries for deeper investigation",
    )

    # Research focus areas
    focus_areas: List[str] = Field(
        description="Key areas that need investigation (e.g., 'company culture', 'technical stack')"
    )

    # Research depth and prioritization
    priority_level: str = Field(
        description="Research intensity: 'light', 'standard', 'deep'",
        default="standard",
    )

    # Role-specific research guidance
    role_specific_topics: List[str] = Field(
        default_factory=list,
        description="Topics specific to the role that should be researched",
    )

    company_specific_topics: List[str] = Field(
        default_factory=list,
        description="Company-specific topics that should be researched",
    )


class QuestionStrategy(BaseModel):
    """Strategy for question generation agent."""

    # Question distribution and focus
    focus_areas: List[str] = Field(
        description="Areas to emphasize in question generation"
    )

    difficulty_distribution: Dict[str, float] = Field(
        description="Percentage distribution of question difficulties as decimal values (e.g., {'easy': 0.2, 'medium': 0.6, 'hard': 0.2})",
        default={"easy": 0.2, "medium": 0.6, "hard": 0.2},
    )

    @field_validator("difficulty_distribution", mode="before")
    @classmethod
    def parse_difficulty_distribution(cls, v):
        """Parse difficulty distribution from string if needed."""
        if isinstance(v, str):
            try:
                # Try to parse as JSON
                return json.loads(v.replace("'", '"'))
            except:
                # Fallback to default
                return {"easy": 0.2, "medium": 0.6, "hard": 0.2}
        return v

    # Question personalization
    resume_focus_points: List[str] = Field(
        default_factory=list,
        description="Key points from resume that should influence questions",
    )

    company_alignment_points: List[str] = Field(
        default_factory=list,
        description="Company values/needs that questions should address",
    )

    # Question quality criteria
    avoid_generic_questions: bool = Field(
        default=True, description="Whether to avoid generic, common interview questions"
    )

    emphasize_practical_scenarios: bool = Field(
        default=False,
        description="Whether to emphasize practical, scenario-based questions",
    )


class AnswerStrategy(BaseModel):
    """Strategy for answer generation agent."""

    # Answer personalization approach
    storytelling_approach: str = Field(
        description="Approach for incorporating personal examples",
        default="star_method",  # or "narrative", "concise_examples"
    )

    # Experience mapping
    experience_highlights: List[str] = Field(
        default_factory=list,
        description="Key experiences from resume to highlight in answers",
    )

    skill_demonstration_opportunities: Dict[str, List[str]] = Field(
        default_factory=dict,
        description="Skills mapped to experiences that demonstrate them (e.g., {'React': ['E-commerce project', 'Team leadership'], 'Leadership': ['Mentored 3 developers']})",
    )

    @field_validator("skill_demonstration_opportunities", mode="before")
    @classmethod
    def parse_skill_opportunities(cls, v):
        """Parse skill demonstration opportunities from string if needed."""
        if isinstance(v, str):
            try:
                # Try to parse as JSON
                parsed = json.loads(v.replace("'", '"'))
                # Ensure values are lists
                result = {}
                for key, value in parsed.items():
                    if isinstance(value, list):
                        result[key] = value
                    else:
                        result[key] = [str(value)]
                return result
            except:
                # Fallback to empty dict
                return {}
        return v

    # Answer style adaptation
    answer_length_preference: str = Field(
        description="Preferred answer length",
        default="detailed",  # or "concise", "moderate"
    )

    include_metrics: bool = Field(
        default=True,
        description="Whether to include quantified achievements where possible",
    )

    company_values_integration: List[str] = Field(
        default_factory=list, description="Company values to weave into answers"
    )


class CompilationStrategy(BaseModel):
    """Strategy for editor agent compilation."""

    # Guide structure and formatting
    guide_format: str = Field(
        description="Overall guide format",
        default="comprehensive",  # or "concise", "executive"
    )

    include_research_summary: bool = Field(
        default=True, description="Whether to include detailed research summary"
    )

    include_preparation_tips: bool = Field(
        default=True, description="Whether to include interview preparation tips"
    )

    # Quality validation criteria
    quality_checks: List[str] = Field(
        default_factory=lambda: [
            "answer_completeness",
            "question_relevance",
            "research_integration",
            "personalization_level",
        ],
        description="Quality checks to perform on final guide",
    )

    # Personalization elements
    personalization_elements: List[str] = Field(
        default_factory=lambda: [
            "resume_integration",
            "company_alignment",
            "role_specificity",
        ],
        description="Elements to personalize in final guide",
    )


class ExecutionPlan(BaseModel):
    """Complete execution plan for all agents."""

    research_strategy: ResearchStrategy = Field(
        description="Strategy for research agent"
    )

    question_strategy: QuestionStrategy = Field(
        description="Strategy for question generation agent"
    )

    answer_strategy: AnswerStrategy = Field(
        description="Strategy for answer generation agent"
    )

    compilation_strategy: CompilationStrategy = Field(
        description="Strategy for editor agent compilation"
    )

    # Overall workflow guidance
    workflow_priorities: List[str] = Field(
        default_factory=list,
        description="Overall priorities for the workflow execution",
    )

    estimated_complexity: str = Field(
        description="Estimated complexity of the interview prep task",
        default="medium",  # or "low", "high"
    )

    special_considerations: List[str] = Field(
        default_factory=list,
        description="Special considerations or requirements for this specific case",
    )
