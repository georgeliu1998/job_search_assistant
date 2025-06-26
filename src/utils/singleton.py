"""
Thread-safe singleton decorator with reload capability.

Provides a reusable singleton pattern that creates one instance per unique
set of initialization parameters, with reload functionality for testing.

Example:
    @singleton
    class ConfigManager:
        def __init__(self, config_dir=None):
            self.config_dir = config_dir

    # Same parameters return same instance
    manager1 = ConfigManager(config_dir="/path/to/config")
    manager2 = ConfigManager(config_dir="/path/to/config")
    assert manager1 is manager2  # True

    # Different parameters create different instances
    manager3 = ConfigManager()
    assert manager1 is not manager3  # True

    # Reload for testing
    new_manager = manager1.reload_singleton(config_dir="/new/path")
    assert new_manager is not manager1  # True
"""

import threading
from typing import Any, Dict, TypeVar

T = TypeVar("T")


def singleton(cls: type[T]) -> type[T]:
    """
    Thread-safe singleton decorator with reload capability.

    Ensures only one instance exists per unique set of initialization parameters.
    Adds a `reload_singleton` method for creating new instances during testing.

    Args:
        cls: The class to make singleton

    Returns:
        The singleton-wrapped class
    """
    instances: Dict[tuple, Any] = {}
    lock = threading.Lock()

    def _make_key(*args, **kwargs):
        """Create a hashable key from args and kwargs."""
        # Convert kwargs to sorted tuple for consistent hashing
        kwargs_items = tuple(sorted(kwargs.items()))
        return (args, kwargs_items)

    def __new__(cls_ref, *args, **kwargs):
        """Override __new__ to return singleton instance."""
        # Check for internal reload flag
        _reload = kwargs.pop("_singleton_reload", False)

        # Create key for this set of parameters
        key = _make_key(*args, **kwargs)

        if key not in instances or _reload:
            with lock:
                # Double-check locking pattern
                if key not in instances or _reload:
                    # Create instance normally
                    instance = object.__new__(cls)
                    instances[key] = instance

        return instances[key]

    def reload_singleton(self, *args, **kwargs):
        """
        Reload the singleton instance with new parameters.

        This creates a new instance of the singleton class, replacing the
        existing one. Useful for testing and dynamic configuration updates.

        Args:
            *args, **kwargs: Arguments to pass to the class constructor

        Returns:
            The new singleton instance
        """
        # If no args provided, use the same parameters that created this instance
        if not args and not kwargs and hasattr(self, "_singleton_key"):
            original_args, original_kwargs_items = self._singleton_key
            kwargs = dict(original_kwargs_items)
            args = original_args

        # Force reload by setting the flag
        reload_kwargs = kwargs.copy()
        reload_kwargs["_singleton_reload"] = True

        # Create new instance using __new__ and then initialize it
        new_instance = cls.__new__(cls, *args, **reload_kwargs)
        if hasattr(new_instance, "__init__"):
            new_instance.__init__(*args, **kwargs)

        # Store the key for future reloads
        new_instance._singleton_key = _make_key(*args, **kwargs)

        return new_instance

    # Store original __new__ and add our version
    cls.__new__ = __new__
    cls.reload_singleton = reload_singleton

    return cls
