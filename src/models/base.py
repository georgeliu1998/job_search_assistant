"""Base model classes for the job search assistant."""

from pydantic import BaseModel, ConfigDict


class BaseDataModel(BaseModel):
    """Base model with common configuration for all data models."""

    model_config = ConfigDict(
        use_enum_values=True,
        # anystr_strip_whitespace = True  # TODO: Decide if desired
    )
