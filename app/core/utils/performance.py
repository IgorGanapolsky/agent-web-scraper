"""Performance monitoring utilities."""
import logging
import time
from contextlib import contextmanager
from typing import Any, Dict, Optional

logger = logging.getLogger("performance")


@contextmanager
def log_performance(operation_name: str, extra_data: Optional[Dict[str, Any]] = None):
    """Context manager to log the performance of a code block.

    Args:
        operation_name: Name of the operation being measured
        extra_data: Additional data to include in the log
    """
    start_time = time.monotonic()
    extra = extra_data or {}

    try:
        yield
        duration = time.monotonic() - start_time

        # Log slow operations
        if duration > 1.0:  # Log if operation takes more than 1 second
            logger.warning(
                "Slow operation: %s took %.2f seconds",
                operation_name,
                duration,
                extra={
                    "data": {
                        "duration_seconds": duration,
                        "operation": operation_name,
                        **extra,
                    }
                },
            )

        logger.debug(
            "Operation completed: %s (%.4fs)",
            operation_name,
            duration,
            extra={
                "data": {
                    "duration_seconds": duration,
                    "operation": operation_name,
                    **extra,
                }
            },
        )

    except Exception as e:
        duration = time.monotonic() - start_time
        logger.error(
            "Operation failed after %.2f seconds: %s - %s",
            duration,
            operation_name,
            str(e),
            exc_info=True,
            extra={
                "data": {
                    "duration_seconds": duration,
                    "operation": operation_name,
                    "error": str(e),
                    **extra,
                }
            },
        )
        raise
