"""User preference persistence.

Loads and saves :class:`JobPreferences` to a local YAML file so the user's job
evaluation preferences persist across sessions.
"""

from pathlib import Path
from typing import Union

import yaml
from pydantic import ValidationError

from src.models.user import JobPreferences
from src.utils.logging import get_logger

logger = get_logger(__name__)

# Default location for the persisted preferences, relative to the project root.
_PROJECT_ROOT = Path(__file__).resolve().parent.parent.parent
DEFAULT_PREFERENCES_PATH = _PROJECT_ROOT / "data" / "user_preferences.yaml"


def load_preferences(
    path: Union[str, Path] = DEFAULT_PREFERENCES_PATH,
) -> JobPreferences:
    """Load preferences from a YAML file.

    Returns default preferences if the file is missing, malformed, or fails
    validation (for example, after a schema change), rather than raising.

    Args:
        path: Path to the YAML preferences file.

    Returns:
        A validated :class:`JobPreferences` instance.
    """
    path = Path(path)

    if not path.exists():
        logger.info("No preferences file at %s; using defaults", path)
        return JobPreferences()

    try:
        with open(path, "r", encoding="utf-8") as f:
            data = yaml.safe_load(f)
        if not data:
            logger.warning("Preferences file %s is empty; using defaults", path)
            return JobPreferences()
        return JobPreferences.model_validate(data)
    except (yaml.YAMLError, ValidationError, OSError) as e:
        logger.warning(
            "Failed to load preferences from %s (%s); using defaults", path, e
        )
        return JobPreferences()


def save_preferences(
    preferences: JobPreferences,
    path: Union[str, Path] = DEFAULT_PREFERENCES_PATH,
) -> None:
    """Persist preferences to a YAML file.

    Uses ``model_dump(mode="json")`` so ``StrEnum`` values are written as plain
    strings rather than Python enum objects.

    Args:
        preferences: The preferences to save.
        path: Destination path for the YAML file.
    """
    path = Path(path)
    path.parent.mkdir(parents=True, exist_ok=True)

    data = preferences.model_dump(mode="json")
    with open(path, "w", encoding="utf-8") as f:
        yaml.safe_dump(data, f, sort_keys=False, default_flow_style=False)

    logger.info("Saved preferences to %s", path)
