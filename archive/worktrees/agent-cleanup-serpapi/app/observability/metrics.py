"""
P2 Task: Prometheus Metrics Integration
Real-time metrics for FastAPI application
"""

import time
from collections.abc import Callable
from typing import Optional

from prometheus_client import CollectorRegistry, Counter, Gauge, Histogram
from prometheus_fastapi_instrumentator import Instrumentator

from app.config.logging import get_logger

logger = get_logger(__name__)

# Custom metrics registry
registry = CollectorRegistry()

# Business metrics
llm_calls_total = Counter(
    "llm_calls_total",
    "Total number of LLM API calls",
    ["agent_role", "model", "status"],
    registry=registry,
)

llm_cost_total = Counter(
    "llm_cost_usd_total",
    "Total cost of LLM API calls in USD",
    ["agent_role", "model"],
    registry=registry,
)

llm_latency = Histogram(
    "llm_latency_seconds",
    "LLM API call latency in seconds",
    ["agent_role", "model"],
    registry=registry,
)

job_duration = Histogram(
    "job_duration_seconds",
    "Background job duration in seconds",
    ["job_type", "status"],
    registry=registry,
)

jobs_active = Gauge(
    "jobs_active_count",
    "Number of currently active background jobs",
    ["job_type"],
    registry=registry,
)

revenue_events = Counter(
    "revenue_events_total", "Total revenue events", ["event_type"], registry=registry
)

revenue_amount = Counter(
    "revenue_amount_usd_total",
    "Total revenue amount in USD",
    ["source"],
    registry=registry,
)


def setup_metrics_instrumentation(app):
    """Setup Prometheus instrumentation for FastAPI app"""

    instrumentator = Instrumentator(
        should_group_status_codes=False,
        should_ignore_untemplated=True,
        should_group_untemplated=True,
        should_instrument_requests_inprogress=True,
        should_instrument_requests_body_size=True,
        should_instrument_responses_body_size=True,
        excluded_handlers=["/health", "/metrics"],
        registry=registry,
    )

    # Add custom metrics
    instrumentator.add(lambda: llm_calls_total).add(lambda: llm_cost_total).add(
        lambda: job_duration
    ).add(lambda: revenue_events)

    # Instrument the app
    instrumentator.instrument(app)
    instrumentator.expose(app, endpoint="/metrics", tags=["monitoring"])

    logger.info("📊 Prometheus metrics instrumentation enabled")
    return instrumentator


def track_llm_call(
    agent_role: str, model: str, cost: float, latency: float, success: bool = True
):
    """Track LLM call metrics"""
    status = "success" if success else "error"

    llm_calls_total.labels(agent_role=agent_role, model=model, status=status).inc()

    if success:
        llm_cost_total.labels(agent_role=agent_role, model=model).inc(cost)

        llm_latency.labels(agent_role=agent_role, model=model).observe(latency)


def track_job_completion(job_type: str, duration: float, success: bool = True):
    """Track background job completion"""
    status = "success" if success else "error"

    job_duration.labels(job_type=job_type, status=status).observe(duration)


def track_revenue_event(event_type: str, amount: float = 0, source: str = "unknown"):
    """Track revenue-related events"""
    revenue_events.labels(event_type=event_type).inc()

    if amount > 0:
        revenue_amount.labels(source=source).inc(amount)


def update_active_jobs(job_type: str, count: int):
    """Update active job count gauge"""
    jobs_active.labels(job_type=job_type).set(count)


class MetricsCollector:
    """Context manager for collecting operation metrics"""

    def __init__(self, operation_name: str, labels: Optional[dict] = None):
        self.operation_name = operation_name
        self.labels = labels or {}
        self.start_time: Optional[float] = None

    def __enter__(self):
        self.start_time = time.time()
        return self

    def __exit__(self, exc_type, exc_val, exc_tb):
        duration = time.time() - self.start_time
        success = exc_type is None

        # Track based on operation type
        if self.operation_name.startswith("llm_"):
            track_llm_call(
                agent_role=self.labels.get("agent_role", "unknown"),
                model=self.labels.get("model", "unknown"),
                cost=self.labels.get("cost", 0),
                latency=duration,
                success=success,
            )
        elif self.operation_name.startswith("job_"):
            track_job_completion(
                job_type=self.labels.get("job_type", "unknown"),
                duration=duration,
                success=success,
            )


def metrics_middleware(request_path: str) -> Callable:
    """Middleware function for request metrics"""

    def middleware(request, call_next):
        start_time = time.time()

        response = call_next(request)

        duration = time.time() - start_time

        # Log structured data about the request
        from app.observability.structured_logging import log_api_request

        log_api_request(
            method=request.method,
            endpoint=request_path,
            status_code=response.status_code,
            duration_ms=duration * 1000,
        )

        return response

    return middleware
