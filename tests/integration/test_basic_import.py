"""Basic integration tests to ensure modules import correctly."""

import pytest


def test_config_imports():
    """Test that config modules can be imported."""
    # Only testing the actual config modules that exist
    import src.config

    assert src.config is not None


def test_data_imports():
    """Test that data modules can be imported."""
    from src.models.models import EvaluationResult, JobDescription, Resume

    assert Resume is not None
    assert JobDescription is not None
    assert EvaluationResult is not None


def test_all_main_modules_import():
    """Test that all main application modules can be imported."""
    # These imports should not raise any errors
    try:
        import src.agents
        import src.api
        import src.config
        import src.core
        import src.llm
        import src.models
        import src.utils
    except ImportError as e:
        pytest.fail(f"Failed to import module: {e}")


def test_core_submodules_import():
    """Test that core submodules can be imported."""
    try:
        import src.core.job_evaluation
        import src.core.resume_customization
    except ImportError as e:
        pytest.fail(f"Failed to import core submodule: {e}")
