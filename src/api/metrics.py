"""
Prometheus metrics for the LLM Safety Layer API.
"""

from prometheus_client import Counter, Histogram, Gauge, Info, generate_latest, CONTENT_TYPE_LATEST
from fastapi import APIRouter, Response
import time

# Create metrics router
metrics_router = APIRouter()

# Application info
APP_INFO = Info("safety_layer", "LLM Safety Layer application information")
APP_INFO.info(
    {
        "version": "0.1.0",
        "name": "llm-safety-layer",
    }
)

# Request metrics
REQUEST_COUNT = Counter(
    "safety_layer_requests_total", "Total number of requests", ["endpoint", "method", "status"]
)

REQUEST_LATENCY = Histogram(
    "safety_layer_request_duration_seconds",
    "Request latency in seconds",
    ["endpoint", "method"],
    buckets=(0.005, 0.01, 0.025, 0.05, 0.1, 0.25, 0.5, 1.0, 2.5, 5.0, 10.0),
)

# Safety metrics
VALIDATION_COUNT = Counter(
    "safety_layer_validations_total",
    "Total number of input validations",
    ["result", "safety_level"],
)

SAFETY_SCORE = Histogram(
    "safety_layer_safety_score",
    "Distribution of safety scores",
    ["dimension"],
    buckets=(0.0, 0.1, 0.2, 0.3, 0.4, 0.5, 0.6, 0.7, 0.8, 0.9, 1.0),
)

CONTENT_FLAGGED = Counter(
    "safety_layer_content_flagged_total", "Total number of flagged content", ["category"]
)

INJECTION_DETECTED = Counter(
    "safety_layer_injection_detected_total",
    "Total number of prompt injection attempts detected",
    ["type"],
)

RATE_LIMITED = Counter(
    "safety_layer_rate_limited_total", "Total number of rate-limited requests", ["user_id"]
)

# Current state gauges
ACTIVE_USERS = Gauge("safety_layer_active_users", "Number of active users")

SAFETY_LAYER_STATUS = Gauge("safety_layer_status", "Safety layer status (1=healthy, 0=unhealthy)")


class MetricsCollector:
    """Collector class for recording metrics."""

    def __init__(self):
        """Initialize the metrics collector."""
        SAFETY_LAYER_STATUS.set(1)

    def record_request(self, endpoint: str, method: str, status: int, duration: float):
        """Record a request metric."""
        REQUEST_COUNT.labels(endpoint=endpoint, method=method, status=str(status)).inc()
        REQUEST_LATENCY.labels(endpoint=endpoint, method=method).observe(duration)

    def record_validation(self, is_safe: bool, safety_level: str):
        """Record a validation result."""
        result = "safe" if is_safe else "unsafe"
        VALIDATION_COUNT.labels(result=result, safety_level=safety_level).inc()

    def record_safety_scores(
        self,
        violence: float,
        hate_speech: float,
        bias: float,
        privacy: float,
        factual: float,
        overall: float,
    ):
        """Record safety score distributions."""
        SAFETY_SCORE.labels(dimension="violence").observe(violence)
        SAFETY_SCORE.labels(dimension="hate_speech").observe(hate_speech)
        SAFETY_SCORE.labels(dimension="bias").observe(bias)
        SAFETY_SCORE.labels(dimension="privacy").observe(privacy)
        SAFETY_SCORE.labels(dimension="factual").observe(factual)
        SAFETY_SCORE.labels(dimension="overall").observe(overall)

    def record_flagged_content(self, category: str):
        """Record flagged content by category."""
        CONTENT_FLAGGED.labels(category=category).inc()

    def record_injection_detected(self, injection_type: str):
        """Record a detected prompt injection."""
        INJECTION_DETECTED.labels(type=injection_type).inc()

    def record_rate_limited(self, user_id: str = "anonymous"):
        """Record a rate-limited request."""
        RATE_LIMITED.labels(user_id=user_id).inc()

    def set_active_users(self, count: int):
        """Set the number of active users."""
        ACTIVE_USERS.set(count)

    def set_status(self, healthy: bool):
        """Set the safety layer status."""
        SAFETY_LAYER_STATUS.set(1 if healthy else 0)


# Global metrics collector instance
metrics_collector = MetricsCollector()


@metrics_router.get(
    "/metrics",
    summary="Prometheus metrics",
    description="Returns Prometheus metrics for monitoring.",
    tags=["Monitoring"],
    include_in_schema=False,
)
async def get_metrics():
    """
    Prometheus metrics endpoint.

    Returns metrics in Prometheus exposition format.
    """
    return Response(
        content=generate_latest(),
        media_type=CONTENT_TYPE_LATEST,
    )


class MetricsMiddleware:
    """Middleware for automatically collecting request metrics."""

    def __init__(self, app):
        self.app = app

    async def __call__(self, scope, receive, send):
        if scope["type"] != "http":
            await self.app(scope, receive, send)
            return

        start_time = time.time()
        status_code = 500

        async def send_wrapper(message):
            nonlocal status_code
            if message["type"] == "http.response.start":
                status_code = message["status"]
            await send(message)

        try:
            await self.app(scope, receive, send_wrapper)
        finally:
            duration = time.time() - start_time
            path = scope.get("path", "unknown")
            method = scope.get("method", "unknown")

            # Skip metrics endpoint itself
            if not path.endswith("/metrics"):
                metrics_collector.record_request(path, method, status_code, duration)
