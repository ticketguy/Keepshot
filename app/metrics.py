"""Prometheus metrics definitions shared across the application"""
from prometheus_client import Counter, Histogram, Gauge

REQUEST_COUNT = Counter(
    "keepshot_http_requests_total",
    "Total HTTP request count",
    ["method", "path", "status_code"],
)

REQUEST_LATENCY = Histogram(
    "keepshot_http_request_duration_seconds",
    "HTTP request latency in seconds",
    ["method", "path"],
)

ACTIVE_WEBSOCKETS = Gauge(
    "keepshot_active_websockets",
    "Number of active WebSocket connections",
)

BOOKMARKS_CREATED = Counter(
    "keepshot_bookmarks_created_total",
    "Total bookmarks created",
)

AI_CALLS = Counter(
    "keepshot_ai_calls_total",
    "Total AI service calls",
    ["operation"],
)
