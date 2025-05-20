"""Minimal logging configuration for the application.

This module provides a basic logging configuration that avoids the 'args' key error
by using a very simple setup.
"""
import logging
import sys
from typing import Optional, Union

# Type alias for log levels
LogLevel = Union[int, str]  # Can be either logging.XXX or string name

def setup_logging(log_level: LogLevel = "INFO", log_to_console: bool = True) -> None:
    """Configure basic logging for the application.
    
    Args:
        log_level: The log level as a string (DEBUG, INFO, WARNING, ERROR, CRITICAL).
        log_to_console: Whether to log to console.
    """
    # Convert string log level to int if needed
    if isinstance(log_level, str):
        log_level = log_level.upper()
        log_level = getattr(logging, log_level, logging.INFO)
    
    # Configure basic logging with minimal settings
    logging.basicConfig(
        level=log_level,
        format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
        datefmt='%Y-%m-%d %H:%M:%S',
        handlers=[logging.StreamHandler(sys.stdout)] if log_to_console else []
    )
    
    # Suppress noisy loggers
    for logger_name in ['urllib3', 'playwright', 'asyncio']:
        logging.getLogger(logger_name).setLevel(logging.WARNING)
    
    # Log that logging is configured
    logger = logging.getLogger(__name__)
    logger.info("Minimal logging configured at level %s", logging.getLevelName(log_level))

def get_logger(name: str = None) -> logging.Logger:
    """Get a logger with the given name.
    
    Args:
        name: The name of the logger. If None, returns the root logger.
        
    Returns:
        A configured logger instance.
    """
    return logging.getLogger(name)

# Set up default logging when module is imported
setup_logging()
