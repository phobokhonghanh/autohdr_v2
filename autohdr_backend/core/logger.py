"""
Custom logger module for AutoHDR backend.

Log format follows the specification:
    <LEVEL: STEP_NUMBER: MESSAGE>

Levels:
    - INFO: Display information for each step
    - ERROR: Report errors
    - DEBUG: Display debug information without returning results
"""

import os
import logging
from typing import Optional


class StepFormatter(logging.Formatter):
    """
    Custom log formatter that outputs in the format:
        <LEVEL: STEP_NUMBER: MESSAGE>

    Attributes:
        LEVEL_MAP: Mapping from Python logging levels to custom level names.
    """

    LEVEL_MAP = {
        logging.DEBUG: "DEBUG",
        logging.INFO: "INFO",
        logging.WARNING: "INFO",
        logging.ERROR: "ERROR",
        logging.CRITICAL: "ERROR",
    }

    def format(self, record: logging.LogRecord) -> str:
        """
        Format the log record into the custom format.

        Args:
            record: The log record to format.

        Returns:
            Formatted log string in <LEVEL: STEP: MESSAGE> format.
        """
        level_name = self.LEVEL_MAP.get(record.levelno, "INFO")
        step_number = getattr(record, "step", "?")
        message = record.getMessage()
        return f"<{level_name}: {step_number}: {message}>"


def get_logger(name: str, step: Optional[int] = None) -> logging.Logger:
    """
    Get a configured logger with the custom StepFormatter.

    Args:
        name: Logger name (typically module name).
        step: Default step number to include in log messages.

    Returns:
        Configured logging.Logger instance.

    Example:
        >>> logger = get_logger(__name__, step=1)
        >>> logger.info("Presigned URLs generated successfully")
        <INFO: 1: Presigned URLs generated successfully>
    """
    logger = logging.getLogger(name)

    if not logger.handlers:
        handler = logging.StreamHandler()
        handler.setFormatter(StepFormatter())
        logger.addHandler(handler)
        logger.setLevel(logging.DEBUG)

    if step is not None:
        old_factory = logging.getLogRecordFactory()

        def record_factory(*args, **kwargs):
            record = old_factory(*args, **kwargs)
            if not hasattr(record, "step") or record.step == "?":
                record.step = step
            return record

        logging.setLogRecordFactory(record_factory)

    return logger


def log(logger: logging.Logger, level: str, step: int, message: str) -> None:
    """
    Convenience function to log with an explicit step number.

    Args:
        logger: The logger instance to use.
        level: Log level string ("INFO", "ERROR", "DEBUG").
        step: Step number (1-7).
        message: Log message.
    """
    level_map = {
        "INFO": logging.INFO,
        "ERROR": logging.ERROR,
        "DEBUG": logging.DEBUG,
    }
    log_level = level_map.get(level.upper(), logging.INFO)
    logger.log(log_level, message, extra={"step": step})


class LogCollector(logging.Handler):
    """
    Custom logging handler that collects log records in a list.
    Used by the API to return logs for a specific request.
    """

    def __init__(self):
        super().__init__()
        self.records = []
        self.setFormatter(StepFormatter())

    def emit(self, record):
        self.records.append(self.format(record))

    def get_logs(self):
        return self.records


def add_file_handler(logger: logging.Logger, log_path: str, mode: str = "a") -> logging.FileHandler:
    """
    Add a file handler to the logger with the custom StepFormatter.

    Args:
        logger: The logger instance to add the handler to.
        log_path: Path to the log file.
        mode: File open mode ("w" for overwrite, "a" for append).

    Returns:
        The created logging.FileHandler instance.
    """
    os.makedirs(os.path.dirname(log_path), exist_ok=True)
    handler = logging.FileHandler(log_path, mode=mode, encoding="utf-8")
    handler.setFormatter(StepFormatter())
    logger.addHandler(handler)
    return handler
