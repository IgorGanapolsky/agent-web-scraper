"""Modern structured logging configuration for 2025 best practices."""

import json
import logging
import os
import sys
from datetime import datetime
from logging.handlers import RotatingFileHandler
from typing import Any, Optional

import structlog


class JSONFormatter(logging.Formatter):
    """JSON formatter for structured logging."""

    def format(self, record: logging.LogRecord) -> str:
        """Format log record as JSON."""
        log_data = {
            "timestamp": datetime.fromtimestamp(record.created).isoformat(),
            "level": record.levelname,
            "logger": record.name,
            "message": record.getMessage(),
            "module": record.module,
            "function": record.funcName,
            "line": record.lineno,
        }

        # Add extra fields from the record
        reserved_attrs = {
            "name",
            "msg",
            "args",
            "levelname",
            "levelno",
            "pathname",
            "filename",
            "module",
            "lineno",
            "funcName",
            "created",
            "msecs",
            "relativeCreated",
            "thread",
            "threadName",
            "processName",
            "process",
            "message",
            "exc_info",
            "exc_text",
            "stack_info",
            "getMessage",
        }
        log_data.update(
            {
                key: value
                for key, value in record.__dict__.items()
                if key not in reserved_attrs
            }
        )

        # Add exception info if present
        if record.exc_info:
            log_data["exception"] = self.formatException(record.exc_info)

        return json.dumps(log_data, default=str, ensure_ascii=False)


class SafeLogger(logging.Logger):
    """Enhanced logger with safe extra parameter handling."""

    def makeRecord(
        self,
        name: str,
        level: int,
        fn: str,
        lno: int,
        msg: Any,
        args: tuple,
        exc_info: Optional[tuple] = None,
        func: Optional[str] = None,
        extra: Optional[dict[str, Any]] = None,
        sinfo: Optional[str] = None,
        **kwargs: Any,
    ) -> logging.LogRecord:
        """Create a LogRecord with safe extra parameter handling."""
        # Clean extra parameters to avoid conflicts
        clean_extra = {}
        if extra:
            reserved_attrs = {
                "name",
                "msg",
                "args",
                "levelname",
                "levelno",
                "pathname",
                "filename",
                "module",
                "lineno",
                "funcName",
                "created",
                "msecs",
                "relativeCreated",
                "thread",
                "threadName",
                "processName",
                "process",
                "message",
                "exc_info",
                "exc_text",
                "stack_info",
            }

            for key, value in extra.items():
                if key in reserved_attrs:
                    clean_extra[f"extra_{key}"] = value
                else:
                    clean_extra[key] = value

        # Create the record
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

        # Add cleaned extra fields
        for key, value in clean_extra.items():
            setattr(rv, key, value)

        return rv


def setup_logging(
    level: int = logging.INFO,
    log_file: Optional[str] = None,
    use_json: bool = True,
    app_name: str = "agent-web-scraper",
) -> logging.Logger:
    """Set up modern structured logging configuration.

    Args:
        level: Logging level (e.g., logging.INFO, logging.DEBUG)
        log_file: Optional path to log file. If None, logs to console only.
        use_json: Whether to use JSON formatting for structured logs
        app_name: Application name for context

    Returns:
        The root logger instance
    """
    # Set up the custom logger class
    logging.setLoggerClass(SafeLogger)

    # Configure structlog
    structlog.configure(
        processors=[
            structlog.contextvars.merge_contextvars,
            structlog.processors.add_log_level,
            structlog.processors.StackInfoRenderer(),
            structlog.dev.set_exc_info,
            structlog.processors.TimeStamper(fmt="iso"),
            (
                structlog.dev.ConsoleRenderer()
                if not use_json
                else structlog.processors.JSONRenderer()
            ),
        ],
        wrapper_class=structlog.make_filtering_bound_logger(level),
        logger_factory=structlog.PrintLoggerFactory(),
        cache_logger_on_first_use=True,
    )

    # Get the root logger
    logger = logging.getLogger()

    # Clear existing handlers
    for handler in logger.handlers[:]:
        logger.removeHandler(handler)

    # Set the logging level
    logger.setLevel(level)

    # Choose formatter based on configuration
    if use_json:
        formatter = JSONFormatter()
    else:
        formatter = logging.Formatter(
            "%(asctime)s | %(levelname)-8s | %(name)s:%(lineno)d | %(message)s",
            datefmt="%Y-%m-%d %H:%M:%S",
        )

    # Add console handler
    console_handler = logging.StreamHandler(sys.stdout)
    console_handler.setFormatter(formatter)
    console_handler.setLevel(level)
    logger.addHandler(console_handler)

    # Add file handler if log file is specified
    if log_file:
        # Ensure the log directory exists
        log_dir = os.path.dirname(log_file)
        if log_dir and not os.path.exists(log_dir):
            os.makedirs(log_dir, exist_ok=True)

        # Create a rotating file handler (10MB max, 10 backup files)
        file_handler = RotatingFileHandler(
            log_file,
            maxBytes=10 * 1024 * 1024,  # 10MB
            backupCount=10,
            encoding="utf-8",
        )
        file_handler.setFormatter(formatter)
        file_handler.setLevel(level)
        logger.addHandler(file_handler)

    # Suppress noisy third-party loggers
    noisy_loggers = [
        "urllib3.connectionpool",
        "urllib3.util.retry",
        "playwright",
        "asyncio",
        "selenium",
        "httpx",
        "httpcore",
        "requests.packages.urllib3",
    ]

    for logger_name in noisy_loggers:
        logging.getLogger(logger_name).setLevel(logging.WARNING)

    # Add application context
    structlog.contextvars.clear_contextvars()
    structlog.contextvars.bind_contextvars(
        app_name=app_name,
        environment=os.getenv("ENVIRONMENT", "development"),
        version=os.getenv("APP_VERSION", "0.2.0"),
    )

    return logger


def get_logger(name: Optional[str] = None) -> logging.Logger:
    """Get a logger with the given name.

    Args:
        name: The name of the logger. If None, returns the root logger.

    Returns:
        A configured logger instance.
    """
    return logging.getLogger(name)


def get_structured_logger(name: Optional[str] = None) -> structlog.BoundLogger:
    """Get a structured logger with the given name.

    Args:
        name: The name of the logger. If None, uses the module name.

    Returns:
        A configured structured logger instance.
    """
    return structlog.get_logger(name)


# Environment-based configuration
def configure_logging_from_env() -> None:
    """Configure logging based on environment variables."""
    log_level_str = os.getenv("LOG_LEVEL", "INFO").upper()
    log_level = getattr(logging, log_level_str, logging.INFO)

    log_file = os.getenv("LOG_FILE", "logs/app.log")
    use_json = os.getenv("LOG_FORMAT", "json").lower() == "json"
    app_name = os.getenv("APP_NAME", "agent-web-scraper")

    setup_logging(
        level=log_level,
        log_file=log_file,
        use_json=use_json,
        app_name=app_name,
    )


# Auto-configure if running as module
if __name__ != "__main__":
    configure_logging_from_env()
    logger = get_logger(__name__)
    logger.info("Modern structured logging configured")
