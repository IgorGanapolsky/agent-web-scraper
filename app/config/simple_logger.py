"""A simple logger configuration that avoids the 'args' key error."""
import logging
import sys
from typing import Optional


class SafeLogger(logging.Logger):
    """A logger that safely handles the 'args' key in extra parameters."""

    def _log(
        self,
        level,
        msg,
        args,
        exc_info=None,
        extra=None,
        stack_info=False,
        stacklevel=1,
    ):
        # Ensure 'args' is not in extra
        if extra and "args" in extra:
            safe_extra = {k: v for k, v in extra.items() if k != "args"}
        else:
            safe_extra = extra

        return super()._log(
            level, msg, args, exc_info, safe_extra, stack_info, stacklevel
        )


# Configure the root logger with a simple formatter
def setup_logging(level=logging.INFO):
    """Set up basic logging configuration."""
    # Configure the root logger
    root_logger = logging.getLogger()
    root_logger.setLevel(level)

    # Clear existing handlers
    for handler in root_logger.handlers[:]:
        root_logger.removeHandler(handler)

    # Add a simple console handler
    console_handler = logging.StreamHandler(sys.stdout)
    formatter = logging.Formatter(
        "%(asctime)s - %(name)s - %(levelname)s - %(message)s",
        datefmt="%Y-%m-%d %H:%M:%S",
    )
    console_handler.setFormatter(formatter)
    root_logger.addHandler(console_handler)

    # Set our custom logger class
    logging.setLoggerClass(SafeLogger)

    # Suppress noisy loggers
    for logger_name in ["urllib3", "playwright", "asyncio"]:
        logging.getLogger(logger_name).setLevel(logging.WARNING)

    # Log that logging is configured
    logger = get_logger(__name__)
    logger.info("Simple logging configured at level %s", logging.getLevelName(level))

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
setup_logging()
