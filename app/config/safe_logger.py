"""A safe logging configuration that avoids the 'args' key error."""
import logging
import os
import sys
from logging.handlers import RotatingFileHandler
from typing import Optional


class SafeLogger(logging.Logger):
    """A logger that safely handles the 'args' key in extra parameters."""

    def makeRecord(
        self,
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
        """Create a LogRecord, ensuring no attribute name conflicts."""
        # Create a clean extra dict without any conflicting keys
        clean_extra = {}
        if extra is not None:
            clean_extra = {
                f"_{key}"
                if key in ["message", "asctime"] or hasattr(logging.LogRecord, key)
                else key: value
                for key, value in extra.items()
            }

        # Create the record with the cleaned extra
        rv = logging.LogRecord(
            name=name,
            level=level,
            pathname=fn,
            lineno=lno,
            msg=msg,
            args=args,
            exc_info=exc_info,
            func=func,
            sinfo=sinfo,
        )

        # Add the cleaned extra fields to the record
        for key, value in clean_extra.items():
            setattr(rv, key, value)

        return rv


def setup_logging(
    level: int = logging.INFO, log_file: Optional[str] = None
) -> logging.Logger:
    """Set up basic logging configuration.

    Args:
        level: Logging level (e.g., logging.INFO, logging.DEBUG)
        log_file: Optional path to log file. If None, logs to console only.

    Returns:
        The root logger instance
    """
    # Set up the custom logger class
    logging.setLoggerClass(SafeLogger)

    # Get the root logger
    logger = logging.getLogger()

    # Clear existing handlers
    for handler in logger.handlers[:]:
        logger.removeHandler(handler)

    # Set the logging level
    logger.setLevel(level)

    # Create formatter
    formatter = logging.Formatter(
        "%(asctime)s - %(name)s - %(levelname)s - %(message)s",
        datefmt="%Y-%m-%d %H:%M:%S",
    )

    # Add console handler
    console_handler = logging.StreamHandler(sys.stdout)
    console_handler.setFormatter(formatter)
    logger.addHandler(console_handler)

    # Add file handler if log file is specified
    if log_file:
        # Ensure the log directory exists
        log_dir = os.path.dirname(log_file)
        if log_dir and not os.path.exists(log_dir):
            os.makedirs(log_dir, exist_ok=True)

        # Create a rotating file handler
        # Rotate log file when it reaches 5MB, keep 5 backup files
        file_handler = RotatingFileHandler(
            log_file, maxBytes=5 * 1024 * 1024, backupCount=5, encoding="utf-8"
        )
        file_handler.setFormatter(formatter)
        logger.addHandler(file_handler)

    # Suppress noisy loggers
    for logger_name in ["urllib3", "playwright", "asyncio", "selenium"]:
        logging.getLogger(logger_name).setLevel(logging.WARNING)

    return logger


def get_logger(name: Optional[str] = None) -> logging.Logger:
    """Get a logger with the given name.

    Args:
        name: The name of the logger. If None, returns the root logger.

    Returns:
        A configured logger instance.
    """
    return logging.getLogger(name)


# Set up default logging when module is imported
logger = get_logger(__name__)
logger.info("Safe logger configured")
