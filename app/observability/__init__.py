"""
Observability module for the application.
Handles logging, error tracking, and monitoring.
"""

import os
import logging
import functools
import time
from typing import Optional, Dict, Any, Callable, TypeVar, cast

# Import our safe logger
from app.config.safe_logger import get_logger, setup_logging

# Set up logging
logger = get_logger(__name__)

# Type variable for generic function wrapping
F = TypeVar('F', bound=Callable[..., Any])

def setup_sentry(dsn: Optional[str] = None, environment: str = 'development') -> None:
    """
    Set up Sentry for error tracking and logging.
    
    Args:
        dsn: Sentry DSN. If None, Sentry will be disabled.
        environment: Environment name (e.g., 'development', 'production')
    """
    if not dsn:
        logger.info("Sentry DSN not provided. Sentry will be disabled.")
        return
    
    try:
        import sentry_sdk
        from sentry_sdk.integrations.logging import LoggingIntegration
        
        # Configure logging integration
        sentry_logging = LoggingIntegration(
            level=logging.INFO,  # Capture info and above as breadcrumbs
            event_level=logging.WARNING  # Send warnings and above as events
        )
        
        # Initialize Sentry with essential configuration
        sentry_sdk.init(
            dsn=dsn,
            environment=environment,
            integrations=[sentry_logging],
            traces_sample_rate=1.0,
            send_default_pii=True,
            release=os.getenv('APP_VERSION', '0.0.0'),
            debug=environment == 'development',
            attach_stacktrace=True
        )
        
        logger.info(f"Sentry initialized in {environment} environment")
        
    except ImportError:
        logger.warning("sentry-sdk not installed. Sentry will be disabled.")
    except Exception as e:
        logger.error(f"Failed to initialize Sentry: {str(e)}")

def track_metrics(name: str, tags: Optional[Dict[str, str]] = None) -> Callable[[F], F]:
    """
    Decorator to track function execution time and success/failure.
    
    Args:
        name: Name of the metric
        tags: Additional tags for the metric
    """
    def decorator(func: F) -> F:
        @functools.wraps(func)
        def wrapper(*args, **kwargs):
            start_time = time.time()
            success = False
            
            try:
                result = func(*args, **kwargs)
                success = True
                return result
            except Exception as e:
                # Log the error
                logger.error(
                    f"Error in {name}",
                    extra={
                        'function_name': func.__name__,
                        'error_message': str(e),
                        'metric_tags': tags or {}
                    },
                    exc_info=True
                )
                raise
            finally:
                # Calculate duration
                duration = (time.time() - start_time) * 1000  # in milliseconds
                
                # Log the metric
                logger.info(
                    f"Function {name} completed",
                    extra={
                        'metric_name': name,
                        'metric_duration_ms': duration,
                        'metric_success': success,
                        'metric_tags': tags or {}
                    }
                )
        
        return cast(F, wrapper)
    return decorator

def log_exceptions(func: F) -> F:
    """Decorator to log exceptions with context."""
    @functools.wraps(func)
    def wrapper(*args, **kwargs):
        try:
            return func(*args, **kwargs)
        except Exception as e:
            # Use _args and _kwargs to avoid conflict with LogRecord's args attribute
            logger.error(
                f"Exception in {func.__name__}",
                extra={
                    'function_name': func.__name__,
                    'error_message': str(e),
                    'function_args': str(args),
                    'function_kwargs': str(kwargs)
                },
                exc_info=True
            )
            raise
    return cast(F, wrapper)

# Initialize logging
setup_logging()

# Initialize Sentry if DSN is provided
sentry_dsn = os.getenv('SENTRY_DSN')
if sentry_dsn:
    setup_sentry(
        dsn=sentry_dsn,
        environment=os.getenv('ENVIRONMENT', 'development')
    )
