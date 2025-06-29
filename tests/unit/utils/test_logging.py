"""Unit tests for utils logging module."""

import logging
import sys
from io import StringIO
from unittest.mock import Mock, patch

import pytest

from src.utils.logging import get_app_logger, get_logger, setup_logging


class TestSetupLogging:
    """Test the setup_logging function."""

    def setup_method(self):
        """Reset logging configuration before each test."""
        # Clear all handlers from root logger
        root_logger = logging.getLogger()
        for handler in root_logger.handlers[:]:
            root_logger.removeHandler(handler)
        # Reset level
        root_logger.setLevel(logging.WARNING)

    def teardown_method(self):
        """Clean up after each test."""
        # Clear all handlers from root logger
        root_logger = logging.getLogger()
        for handler in root_logger.handlers[:]:
            root_logger.removeHandler(handler)
        # Reset level
        root_logger.setLevel(logging.WARNING)

    def test_setup_logging_default_parameters(self):
        """Test setup_logging with default parameters."""
        setup_logging()

        root_logger = logging.getLogger()

        # Check logging level is set to INFO
        assert root_logger.level == logging.INFO

        # Check that a handler was added
        assert len(root_logger.handlers) == 1

        # Check that it's a StreamHandler pointing to stdout
        handler = root_logger.handlers[0]
        assert isinstance(handler, logging.StreamHandler)
        assert handler.stream == sys.stdout

    def test_setup_logging_custom_level(self):
        """Test setup_logging with custom logging level."""
        setup_logging(level="DEBUG")

        root_logger = logging.getLogger()
        assert root_logger.level == logging.DEBUG

    def test_setup_logging_custom_level_case_insensitive(self):
        """Test setup_logging with custom level in different cases."""
        setup_logging(level="debug")
        root_logger = logging.getLogger()
        assert root_logger.level == logging.DEBUG

        # Clean up and test another case
        self.setup_method()
        setup_logging(level="Error")
        assert root_logger.level == logging.ERROR

    def test_setup_logging_custom_format(self):
        """Test setup_logging with custom format string."""
        custom_format = "%(levelname)s - %(message)s"
        setup_logging(format_string=custom_format)

        root_logger = logging.getLogger()
        handler = root_logger.handlers[0]

        # Check that the formatter uses the custom format
        assert handler.formatter._fmt == custom_format

    def test_setup_logging_default_format(self):
        """Test setup_logging uses correct default format."""
        setup_logging()

        root_logger = logging.getLogger()
        handler = root_logger.handlers[0]

        expected_format = "%(asctime)s %(name)s [%(levelname)s] %(message)s"
        assert handler.formatter._fmt == expected_format
        assert handler.formatter.datefmt == "%Y-%m-%d %H:%M:%S"

    def test_setup_logging_removes_existing_handlers(self):
        """Test that setup_logging removes existing handlers."""
        root_logger = logging.getLogger()

        # Record initial handler count (pytest may have added handlers)
        initial_count = len(root_logger.handlers)

        # Add a mock handler
        mock_handler = Mock()
        root_logger.addHandler(mock_handler)
        assert len(root_logger.handlers) == initial_count + 1

        # Setup logging should remove all existing handlers and add one new one
        setup_logging()

        # Should have only the new handler
        assert len(root_logger.handlers) == 1
        assert root_logger.handlers[0] != mock_handler
        assert isinstance(root_logger.handlers[0], logging.StreamHandler)

    def test_setup_logging_third_party_loggers_quieted(self):
        """Test that third-party loggers are set to WARNING level."""
        setup_logging()

        # Check that noisy third-party loggers are quieted
        assert logging.getLogger("httpx").level == logging.WARNING
        assert logging.getLogger("httpcore").level == logging.WARNING
        assert logging.getLogger("urllib3").level == logging.WARNING

    def test_setup_logging_multiple_calls(self):
        """Test that multiple calls to setup_logging work correctly."""
        # First call
        setup_logging(level="DEBUG")
        root_logger = logging.getLogger()
        assert root_logger.level == logging.DEBUG
        assert len(root_logger.handlers) == 1

        # Second call should replace the handler
        setup_logging(level="ERROR", format_string="%(message)s")
        assert root_logger.level == logging.ERROR
        assert len(root_logger.handlers) == 1
        assert root_logger.handlers[0].formatter._fmt == "%(message)s"

    def test_setup_logging_with_all_log_levels(self):
        """Test setup_logging with all valid log levels."""
        levels = ["DEBUG", "INFO", "WARNING", "ERROR", "CRITICAL"]
        expected_levels = [
            logging.DEBUG,
            logging.INFO,
            logging.WARNING,
            logging.ERROR,
            logging.CRITICAL,
        ]

        for level_str, expected_level in zip(levels, expected_levels):
            self.setup_method()  # Reset
            setup_logging(level=level_str)
            root_logger = logging.getLogger()
            assert root_logger.level == expected_level

    def test_setup_logging_output_capture(self):
        """Test that logging output goes to stdout."""
        # Capture stdout
        captured_output = StringIO()

        with patch("sys.stdout", captured_output):
            setup_logging(level="INFO")
            logger = logging.getLogger("test")
            logger.info("Test message")

        output = captured_output.getvalue()
        assert "Test message" in output
        assert "[INFO]" in output

    def test_setup_logging_formatter_datetime_format(self):
        """Test that the formatter uses correct datetime format."""
        setup_logging()

        root_logger = logging.getLogger()
        handler = root_logger.handlers[0]
        formatter = handler.formatter

        # Test that datetime format is applied
        import datetime

        test_time = datetime.datetime(2024, 1, 15, 14, 30, 45)
        formatted_time = formatter.formatTime(
            logging.LogRecord(
                name="test",
                level=logging.INFO,
                pathname="",
                lineno=0,
                msg="",
                args=(),
                exc_info=None,
            ),
            formatter.datefmt,
        )

        # Should format according to the specified format
        assert len(formatted_time) == 19  # YYYY-MM-DD HH:MM:SS format


class TestGetLogger:
    """Test the get_logger function."""

    def test_get_logger_returns_logger_instance(self):
        """Test that get_logger returns a Logger instance."""
        logger = get_logger("test.module")
        assert isinstance(logger, logging.Logger)

    def test_get_logger_with_different_names(self):
        """Test get_logger with different logger names."""
        logger1 = get_logger("module1")
        logger2 = get_logger("module2")

        assert logger1.name == "module1"
        assert logger2.name == "module2"
        assert logger1 != logger2

    def test_get_logger_same_name_returns_same_instance(self):
        """Test that get_logger returns the same instance for the same name."""
        logger1 = get_logger("same.module")
        logger2 = get_logger("same.module")

        assert logger1 is logger2

    def test_get_logger_hierarchical_names(self):
        """Test get_logger with hierarchical logger names."""
        parent_logger = get_logger("parent")
        child_logger = get_logger("parent.child")

        assert parent_logger.name == "parent"
        assert child_logger.name == "parent.child"
        assert child_logger.parent == parent_logger

    def test_get_logger_empty_string(self):
        """Test get_logger with empty string returns root logger."""
        logger = get_logger("")
        root_logger = logging.getLogger()

        assert logger is root_logger

    def test_get_logger_with_special_characters(self):
        """Test get_logger with special characters in name."""
        special_names = ["test-module", "test_module", "test.module.submodule"]

        for name in special_names:
            logger = get_logger(name)
            assert logger.name == name
            assert isinstance(logger, logging.Logger)


class TestGetAppLogger:
    """Test the get_app_logger function."""

    def test_get_app_logger_returns_correct_logger(self):
        """Test that get_app_logger returns the correct application logger."""
        app_logger = get_app_logger()
        expected_logger = logging.getLogger("job_search_assistant")

        assert app_logger is expected_logger
        assert app_logger.name == "job_search_assistant"

    def test_get_app_logger_consistent_returns(self):
        """Test that get_app_logger consistently returns the same instance."""
        logger1 = get_app_logger()
        logger2 = get_app_logger()

        assert logger1 is logger2

    def test_get_app_logger_is_logger_instance(self):
        """Test that get_app_logger returns a Logger instance."""
        app_logger = get_app_logger()
        assert isinstance(app_logger, logging.Logger)


class TestLoggingIntegration:
    """Test integration scenarios with logging setup."""

    def setup_method(self):
        """Reset logging configuration before each test."""
        root_logger = logging.getLogger()
        for handler in root_logger.handlers[:]:
            root_logger.removeHandler(handler)
        root_logger.setLevel(logging.WARNING)

    def teardown_method(self):
        """Clean up after each test."""
        root_logger = logging.getLogger()
        for handler in root_logger.handlers[:]:
            root_logger.removeHandler(handler)
        root_logger.setLevel(logging.WARNING)

    def test_logging_after_setup(self):
        """Test that loggers work correctly after setup."""
        # Create a custom handler to capture output
        captured_output = StringIO()
        test_handler = logging.StreamHandler(captured_output)
        test_handler.setFormatter(
            logging.Formatter("%(name)s [%(levelname)s] %(message)s")
        )

        # Setup logging with DEBUG level
        setup_logging(level="DEBUG")

        # Replace the stdout handler with our test handler
        root_logger = logging.getLogger()
        root_logger.removeHandler(root_logger.handlers[0])
        root_logger.addHandler(test_handler)

        # Test different loggers
        app_logger = get_app_logger()
        module_logger = get_logger("test.module")

        # Both should log at appropriate levels
        app_logger.info("App message")
        module_logger.debug("Module debug message")

        output = captured_output.getvalue()
        assert "App message" in output
        assert "Module debug message" in output

    def test_logger_hierarchy_after_setup(self):
        """Test logger hierarchy works after setup."""
        setup_logging(level="INFO")

        parent_logger = get_logger("parent")
        child_logger = get_logger("parent.child")

        # Child should inherit parent's configuration
        assert child_logger.parent == parent_logger
        assert child_logger.level == logging.NOTSET  # Inherits from parent
        assert parent_logger.level == logging.NOTSET  # Inherits from root

    def test_third_party_logger_levels_after_setup(self):
        """Test that third-party loggers maintain their WARNING level."""
        setup_logging(level="DEBUG")

        # Even though root is DEBUG, these should be WARNING
        httpx_logger = logging.getLogger("httpx")
        httpcore_logger = logging.getLogger("httpcore")
        urllib3_logger = logging.getLogger("urllib3")

        assert httpx_logger.level == logging.WARNING
        assert httpcore_logger.level == logging.WARNING
        assert urllib3_logger.level == logging.WARNING

    def test_custom_logger_not_affected_by_third_party_rules(self):
        """Test that custom loggers are not affected by third-party logger rules."""
        setup_logging(level="DEBUG")

        # Custom logger should inherit from root
        custom_logger = get_logger("my.custom.httpx.logger")
        assert custom_logger.level == logging.NOTSET  # Inherits from root (DEBUG)

    def test_logging_with_exception_info(self):
        """Test logging with exception information."""
        # Create a custom handler to capture output
        captured_output = StringIO()
        test_handler = logging.StreamHandler(captured_output)
        test_handler.setFormatter(
            logging.Formatter("%(name)s [%(levelname)s] %(message)s")
        )

        setup_logging(level="ERROR")

        # Replace the stdout handler with our test handler
        root_logger = logging.getLogger()
        root_logger.removeHandler(root_logger.handlers[0])
        root_logger.addHandler(test_handler)

        logger = get_logger("test.exceptions")

        try:
            raise ValueError("Test exception")
        except ValueError:
            logger.error("An error occurred", exc_info=True)

        output = captured_output.getvalue()
        assert "An error occurred" in output
        assert "ValueError: Test exception" in output
        assert "Traceback" in output

    def test_logging_performance_with_disabled_level(self):
        """Test that logging calls are efficient when level is disabled."""
        setup_logging(level="ERROR")

        logger = get_logger("test.performance")

        # Mock an expensive operation
        expensive_operation = Mock(return_value="expensive result")

        # This should not call the expensive operation
        logger.debug("Debug message: %s", expensive_operation())

        # The expensive operation should not have been called
        expensive_operation.assert_called_once()  # Called due to eager evaluation

        # Better test - use lazy evaluation
        expensive_operation.reset_mock()
        if logger.isEnabledFor(logging.DEBUG):
            logger.debug("Debug message: %s", expensive_operation())

        # Now it shouldn't be called
        expensive_operation.assert_not_called()
