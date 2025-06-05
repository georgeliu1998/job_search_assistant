"""User-related models for the job search assistant."""

from typing import List

from pydantic import Field

from src.models.base import BaseJobSearchModel


class UserPreferences(BaseJobSearchModel):
    """Model representing user job search preferences."""

    job_titles: List[str] = Field(..., description="List of desired job titles.")
    # TODO: Add more preferences like salary, location, company size, etc.
    # TODO: Add weights to preferences
    # TODO: Add must-have vs. nice-to-have preferences
    # TODO: Add ability to specify how to evaluate each preference
