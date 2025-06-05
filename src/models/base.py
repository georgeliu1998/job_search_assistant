"""Base model classes for the job search assistant."""

from pydantic import BaseModel, ConfigDict


class BaseJobSearchModel(BaseModel):
    """Base model with common configuration for all job search models."""

    model_config = ConfigDict(
        use_enum_values=True,
        # anystr_strip_whitespace = True  # TODO: Decide if desired
    )
