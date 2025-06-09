"""
P1 Task: Structured Logging with structlog
Machine-readable JSON logs for production observability
"""

import logging
import sys
from typing import Any

import structlog

from app.core.api_key_manager import get_api_key_manager


def setup_structured_logging():
    """Configure structlog for production-ready structured logging"""

    # Configure standard library logging
    logging.basicConfig(
        format="%(message)s",
        stream=sys.stdout,
        level=logging.INFO,
    )

    # Configure structlog processors
    shared_processors = [
        structlog.stdlib.filter_by_level,
        structlog.stdlib.add_logger_name,
        structlog.stdlib.add_log_level,
        structlog.stdlib.PositionalArgumentsFormatter(),
        structlog.processors.TimeStamper(fmt="ISO"),
        structlog.processors.StackInfoRenderer(),
        structlog.processors.format_exc_info,
        add_agent_context,
        add_request_context,
    ]

    # JSON formatting for production
    structlog.configure(
        processors=shared_processors + [structlog.processors.JSONRenderer()],
        wrapper_class=structlog.stdlib.BoundLogger,
        logger_factory=structlog.stdlib.LoggerFactory(),
        cache_logger_on_first_use=True,
    )


def add_agent_context(
    logger: Any, method_name: str, event_dict: dict[str, Any]
) -> dict[str, Any]:
    """Add Claude Squad agent context to logs"""
    manager = get_api_key_manager()

    # Add agent role and cost center
    event_dict["agent_role"] = manager.current_role.value
    event_dict["cost_center"] = manager.get_cost_center()
    event_dict["langsmith_project"] = manager.get_langsmith_project()

    return event_dict


def add_request_context(
    logger: Any, method_name: str, event_dict: dict[str, Any]
) -> dict[str, Any]:
    """Add request context to logs (will be enhanced with FastAPI middleware)"""

    # Add basic application context
    event_dict["service"] = "agent-web-scraper"
    event_dict["version"] = "2.0"
    event_dict["environment"] = "production"  # TODO: Make configurable

    return event_dict


# Create structured logger instance
logger = structlog.get_logger()


def log_llm_call(
    agent_role: str,
    model: str,
    prompt_length: int,
    response_length: int,
    tokens_used: int,
    cost: float,
    latency_ms: float,
    success: bool = True,
    error: str | None = None,
):
    """Log LLM API call with structured data"""

    log_data = {
        "event": "llm_call",
        "agent_role": agent_role,
        "model": model,
        "prompt_length": prompt_length,
        "response_length": response_length,
        "tokens_used": tokens_used,
        "cost_usd": cost,
        "latency_ms": latency_ms,
        "success": success,
    }

    if error:
        log_data["error"] = error
        logger.error("LLM call failed", **log_data)
    else:
        logger.info("LLM call completed", **log_data)


def log_job_event(
    event_type: str,
    job_id: str,
    user_id: str | None = None,
    job_type: str | None = None,
    status: str | None = None,
    duration_ms: float | None = None,
    error: str | None = None,
    **kwargs,
):
    """Log job-related events"""

    log_data = {
        "event": event_type,
        "job_id": job_id,
        "user_id": user_id,
        "job_type": job_type,
        "status": status,
    }

    if duration_ms is not None:
        log_data["duration_ms"] = duration_ms

    if error:
        log_data["error"] = error

    # Add any additional context
    log_data.update(kwargs)

    logger.info("Job event", **log_data)


def log_api_request(
    method: str,
    endpoint: str,
    status_code: int,
    duration_ms: float,
    user_id: str | None = None,
    request_size: int | None = None,
    response_size: int | None = None,
):
    """Log API request with performance metrics"""

    logger.info(
        "API request",
        event="api_request",
        method=method,
        endpoint=endpoint,
        status_code=status_code,
        duration_ms=duration_ms,
        user_id=user_id,
        request_size=request_size,
        response_size=response_size,
    )


def log_business_event(
    event_type: str,
    user_id: str | None = None,
    revenue_impact: float | None = None,
    **kwargs,
):
    """Log business-critical events"""

    log_data = {
        "event": event_type,
        "user_id": user_id,
        "category": "business",
    }

    if revenue_impact is not None:
        log_data["revenue_impact_usd"] = revenue_impact

    log_data.update(kwargs)

    logger.info("Business event", **log_data)
