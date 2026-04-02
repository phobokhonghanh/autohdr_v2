"""Tests for the custom logger module."""

import logging
import pytest

from core.logger import StepFormatter, get_logger, log


class TestStepFormatter:
    """Tests for StepFormatter class."""

    def test_format_info(self):
        """Should format INFO level correctly."""
        formatter = StepFormatter()
        record = logging.LogRecord(
            name="test", level=logging.INFO, pathname="",
            lineno=0, msg="Test message", args=(), exc_info=None,
        )
        record.step = 1
        result = formatter.format(record)
        assert result == "<INFO: 1: Test message>"

    def test_format_error(self):
        """Should format ERROR level correctly."""
        formatter = StepFormatter()
        record = logging.LogRecord(
            name="test", level=logging.ERROR, pathname="",
            lineno=0, msg="Error occurred", args=(), exc_info=None,
        )
        record.step = 3
        result = formatter.format(record)
        assert result == "<ERROR: 3: Error occurred>"

    def test_format_debug(self):
        """Should format DEBUG level correctly."""
        formatter = StepFormatter()
        record = logging.LogRecord(
            name="test", level=logging.DEBUG, pathname="",
            lineno=0, msg="Debug info", args=(), exc_info=None,
        )
        record.step = 5
        result = formatter.format(record)
        assert result == "<DEBUG: 5: Debug info>"


class TestLogFunction:
    """Tests for the convenience log function."""

    def test_log_info(self, capfd):
        """Should log INFO message with correct format."""
        test_logger = logging.getLogger("test_log_info")
        test_logger.handlers.clear()
        handler = logging.StreamHandler()
        handler.setFormatter(StepFormatter())
        test_logger.addHandler(handler)
        test_logger.setLevel(logging.DEBUG)

        log(test_logger, "INFO", 2, "Upload complete")
        captured = capfd.readouterr()
        assert "<INFO: 2: Upload complete>" in captured.err

    def test_log_error(self, capfd):
        """Should log ERROR message with correct format."""
        test_logger = logging.getLogger("test_log_error")
        test_logger.handlers.clear()
        handler = logging.StreamHandler()
        handler.setFormatter(StepFormatter())
        test_logger.addHandler(handler)
        test_logger.setLevel(logging.DEBUG)

        log(test_logger, "ERROR", 7, "Download failed")
        captured = capfd.readouterr()
        assert "<ERROR: 7: Download failed>" in captured.err
