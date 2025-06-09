"""
Modern observability module for the application.
Handles logging, error tracking, metrics, and monitoring with 2025 best practices.
"""

import functools
import logging
import os
import time
import uuid
from collections.abc import Callable
from typing import Any, Optional, TypeVar, cast

import structlog

from app.config.safe_logger import get_logger, get_structured_logger

# Type variable for generic function wrapping
F = TypeVar("F", bound=Callable[..., Any])

# Get loggers
logger = get_logger(__name__)
struct_logger = get_structured_logger(__name__)


def setup_sentry(
    dsn: Optional[str] = None,
    environment: str = "development",
    release: Optional[str] = None,
) -> None:
    """
    Set up Sentry for error tracking with enhanced configuration.

    Args:
        dsn: Sentry DSN. If None, Sentry will be disabled.
        environment: Environment name (e.g., 'development', 'production')
        release: Release version for tracking
    """
    if not dsn:
        logger.info("Sentry DSN not provided. Sentry will be disabled.")
        return

    try:
        import sentry_sdk
        from sentry_sdk.integrations.logging import LoggingIntegration
        from sentry_sdk.integrations.stdlib import StdlibIntegration

        # Configure logging integration
        sentry_logging = LoggingIntegration(
            level=logging.INFO,  # Capture info and above as breadcrumbs
            event_level=logging.WARNING,  # Send warnings and above as events
        )

        # Initialize Sentry with enhanced configuration
        sentry_sdk.init(
            dsn=dsn,
            environment=environment,
            release=release or os.getenv("APP_VERSION", "0.2.0"),
            integrations=[
                sentry_logging,
                StdlibIntegration(record_sql_params=True),
            ],
            # Performance monitoring
            traces_sample_rate=0.1 if environment == "production" else 1.0,
            profiles_sample_rate=0.1 if environment == "production" else 1.0,
            # Privacy and data handling
            send_default_pii=False,
            attach_stacktrace=True,
            debug=environment == "development",
            # Error filtering
            before_send=_filter_sentry_events,
            # Set max breadcrumbs
            max_breadcrumbs=50,
            # Additional options
            server_name=os.getenv("SERVER_NAME"),
            auto_enabling_integrations=True,
        )

        # Set user context if available
        with sentry_sdk.configure_scope() as scope:
            scope.set_tag("component", "agent-web-scraper")
            scope.set_context(
                "app",
                {
                    "name": "agent-web-scraper",
                    "version": os.getenv("APP_VERSION", "0.2.0"),
                    "environment": environment,
                },
            )

        struct_logger.info(
            "Sentry initialized", environment=environment, release=release
        )

    except ImportError:
        logger.warning("sentry-sdk not installed. Sentry will be disabled.")
    except Exception as e:
        logger.error(f"Failed to initialize Sentry: {e!s}", exc_info=True)


def _filter_sentry_events(
    event: dict[str, Any], hint: dict[str, Any]
) -> Optional[dict[str, Any]]:
    """Filter Sentry events to reduce noise."""
    # Don't send certain types of errors to Sentry
    if "exc_info" in hint:
        exc_type, exc_value, tb = hint["exc_info"]

        # Filter out common non-critical errors
        if exc_type.__name__ in [
            "KeyboardInterrupt",
            "SystemExit",
            "BrokenPipeError",
            "ConnectionResetError",
        ]:
            return None

        # Filter out HTTP client errors (4xx) but keep server errors (5xx)
        if hasattr(exc_value, "status_code") and 400 <= exc_value.status_code < 500:
            return None

    return event


class RequestTracer:
    """Context manager for tracing requests with correlation IDs."""

    def __init__(self, operation_name: str, **context: Any):
        self.operation_name = operation_name
        self.context = context
        self.correlation_id = str(uuid.uuid4())
        self.start_time = 0.0

    def __enter__(self) -> "RequestTracer":
        self.start_time = time.time()

        # Add correlation ID to structlog context
        structlog.contextvars.bind_contextvars(
            correlation_id=self.correlation_id,
            operation=self.operation_name,
            **self.context,
        )

        struct_logger.info("Operation started", operation=self.operation_name)
        return self

    def __exit__(self, exc_type: Any, exc_val: Any, exc_tb: Any) -> None:
        duration = time.time() - self.start_time

        if exc_type is None:
            struct_logger.info(
                "Operation completed successfully",
                operation=self.operation_name,
                duration_ms=round(duration * 1000, 2),
            )
        else:
            struct_logger.error(
                "Operation failed",
                operation=self.operation_name,
                duration_ms=round(duration * 1000, 2),
                error=str(exc_val),
                exc_info=True,
            )

        # Clear correlation ID from context
        structlog.contextvars.clear_contextvars()


def track_metrics(
    name: str,
    tags: Optional[dict[str, str]] = None,
    track_timing: bool = True,
) -> Callable[[F], F]:
    """
    Enhanced decorator to track function execution metrics.

    Args:
        name: Name of the metric
        tags: Additional tags for the metric
        track_timing: Whether to track execution time
    """

    def decorator(func: F) -> F:
        @functools.wraps(func)
        def wrapper(*args: Any, **kwargs: Any) -> Any:
            correlation_id = str(uuid.uuid4())
            start_time = time.time() if track_timing else 0

            # Create structured context
            context = {
                "function_name": func.__name__,
                "metric_name": name,
                "correlation_id": correlation_id,
                "tags": tags or {},
            }

            struct_logger.info("Function execution started", **context)

            try:
                result = func(*args, **kwargs)

                if track_timing:
                    duration = (time.time() - start_time) * 1000  # milliseconds
                    context["duration_ms"] = round(duration, 2)

                context["success"] = True
                struct_logger.info("Function execution completed", **context)

                return result

            except Exception as e:
                if track_timing:
                    duration = (time.time() - start_time) * 1000
                    context["duration_ms"] = round(duration, 2)

                context.update(
                    {
                        "success": False,
                        "error_type": type(e).__name__,
                        "error_message": str(e),
                    }
                )

                struct_logger.error(
                    "Function execution failed", **context, exc_info=True
                )
                raise

        return cast("F", wrapper)

    return decorator


def log_exceptions(func: F) -> F:
    """Enhanced decorator to log exceptions with structured context."""

    @functools.wraps(func)
    def wrapper(*args: Any, **kwargs: Any) -> Any:
        try:
            return func(*args, **kwargs)
        except Exception as e:
            # Create rich context for error logging
            context = {
                "function_name": func.__name__,
                "function_module": func.__module__,
                "error_type": type(e).__name__,
                "error_message": str(e),
                "args_count": len(args),
                "kwargs_keys": list(kwargs.keys()),
            }

            struct_logger.error(
                "Unhandled exception in function", **context, exc_info=True
            )
            raise

    return cast("F", wrapper)


def measure_time(operation: str) -> Callable[[F], F]:
    """Decorator to measure and log function execution time."""

    def decorator(func: F) -> F:
        @functools.wraps(func)
        def wrapper(*args: Any, **kwargs: Any) -> Any:
            start_time = time.perf_counter()

            try:
                result = func(*args, **kwargs)
                duration = time.perf_counter() - start_time

                struct_logger.info(
                    "Performance measurement",
                    operation=operation,
                    function=func.__name__,
                    duration_seconds=round(duration, 4),
                    duration_ms=round(duration * 1000, 2),
                )

                return result

            except Exception:
                duration = time.perf_counter() - start_time
                struct_logger.warning(
                    "Performance measurement (with error)",
                    operation=operation,
                    function=func.__name__,
                    duration_seconds=round(duration, 4),
                    duration_ms=round(duration * 1000, 2),
                )
                raise

        return cast("F", wrapper)

    return decorator


def health_check() -> dict[str, Any]:
    """Perform basic application health checks."""
    health_status = {
        "status": "healthy",
        "timestamp": time.time(),
        "version": os.getenv("APP_VERSION", "0.2.0"),
        "environment": os.getenv("ENVIRONMENT", "development"),
        "checks": {},
    }

    # Check logging
    try:
        logger.info("Health check - logging test")
        health_status["checks"]["logging"] = "ok"
    except Exception as e:
        health_status["checks"]["logging"] = f"error: {e}"
        health_status["status"] = "degraded"

    # Check Sentry (if configured)
    try:
        import sentry_sdk

        if sentry_sdk.Hub.current.client:
            health_status["checks"]["sentry"] = "ok"
        else:
            health_status["checks"]["sentry"] = "not_configured"
    except ImportError:
        health_status["checks"]["sentry"] = "not_installed"
    except Exception as e:
        health_status["checks"]["sentry"] = f"error: {e}"

    return health_status


# Initialize observability based on environment
def init_observability() -> None:
    """Initialize observability components based on environment configuration."""
    sentry_dsn = os.getenv("SENTRY_DSN")
    environment = os.getenv("ENVIRONMENT", "development")
    release = os.getenv("APP_VERSION", "0.2.0")

    if sentry_dsn:
        setup_sentry(dsn=sentry_dsn, environment=environment, release=release)

    struct_logger.info(
        "Observability initialized",
        sentry_enabled=bool(sentry_dsn),
        environment=environment,
        release=release,
    )


# Auto-initialize when module is imported
if __name__ != "__main__":
    init_observability()
