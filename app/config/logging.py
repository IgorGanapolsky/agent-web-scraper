"""Minimal logging configuration for the application.

This module provides a basic logging configuration that avoids the 'args' key error
by using a custom LogRecord class that handles the 'args' key properly.
"""
import logging
import sys
from typing import Any, Dict, Optional, Union

# Type alias for log levels
LogLevel = Union[int, str]  # Can be either logging.XXX or string name


class SafeLogRecord(logging.LogRecord):
    """A LogRecord that safely handles the 'args' key."""

    def __init__(self, *args, **kwargs):
        # Remove 'args' from kwargs to prevent the 'args' key error
        kwargs.pop("args", None)
        super().__init__(*args, **kwargs)


def safe_make_record(
    name,
    level,
    fn,
    lno,
    msg,
    args,
    exc_info,
    func=None,
    extra=None,
    sinfo=None,
    **kwargs,
):
    """Create a log record safely, avoiding the 'args' key error."""
    # Ensure extra doesn't contain 'args' key
    safe_extra = {}
    if extra is not None:
        for key, value in extra.items():
            if key != "args":
                safe_extra[key] = value

    # Create the record with safe extra data
    record = SafeLogRecord(name, level, fn, lno, msg, args, exc_info, func, sinfo)

    # Add extra fields
    for key, value in safe_extra.items():
        setattr(record, key, value)

    return record


def setup_logging(log_level: Optional[LogLevel] = None, log_to_console: Optional[bool] = None) -> None:
    """Configure basic logging for the application.

    Args:
        log_level: The log level as a string (DEBUG, INFO, WARNING, ERROR, CRITICAL) or logging constant.
                  If None, defaults to INFO.
        log_to_console: Whether to log to console. If None, defaults to True.
    """
    effective_log_level: Union[int, str]
    # Set default log level if not provided
    if log_level is None:
        effective_log_level = logging.INFO  # Default to INFO if not set
    else:
        effective_log_level = log_level

    # Convert string log level to int if needed
    numeric_log_level: int
    if isinstance(effective_log_level, str):
        numeric_log_level = getattr(logging, effective_log_level.upper(), logging.INFO)
    else: # it's an int
        numeric_log_level = effective_log_level

    # Default to True if not specified
    effective_log_to_console: bool = True if log_to_console is None else log_to_console

    # Clear any existing handlers
    root_logger = logging.getLogger()
    for handler in root_logger.handlers[:]:
        root_logger.removeHandler(handler)

    # Set up the root logger with our custom record factory
    logging.setLogRecordFactory(safe_make_record)

    # Set the root logger level
    root_logger.setLevel(numeric_log_level)

    # Add console handler if requested
    if effective_log_to_console:
        console_handler = logging.StreamHandler(sys.stdout)
        console_handler.setLevel(numeric_log_level)
        formatter = logging.Formatter(
            "%(asctime)s - %(name)s - %(levelname)s - %(message)s",
            datefmt="%Y-%m-%d %H:%M:%S",
        )
        console_handler.setFormatter(formatter)
        root_logger.addHandler(console_handler)

    # Suppress noisy loggers
    for logger_name in ["urllib3", "playwright", "asyncio"]:
        logging.getLogger(logger_name).setLevel(logging.WARNING)

    # Log that logging is configured
    logger = logging.getLogger(__name__)
    logger.info("Logging configured at level %s", logging.getLevelName(numeric_log_level))


def get_logger(name: Optional[str] = None) -> logging.Logger:
    """Get a logger with the given name.

    Args:
        name: The name of the logger. If None, returns the root logger.

    Returns:
        A configured logger instance.
    """
    return logging.getLogger(name)


# Set up default logging when module is imported
setup_logging()
