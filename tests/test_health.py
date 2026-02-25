"""Tests for health, metrics, and root endpoints"""
from fastapi.testclient import TestClient


def test_root(client: TestClient):
    resp = client.get("/")
    assert resp.status_code == 200
    body = resp.json()
    assert body["service"] == "KeepShot"
    assert "docs" in body
    assert "health" in body


def test_health_check(client: TestClient):
    resp = client.get("/health")
    assert resp.status_code == 200
    body = resp.json()
    assert body["status"] == "healthy"
    assert body["service"] == "keepshot"


def test_metrics_endpoint_returns_prometheus_format(client: TestClient):
    """
    /metrics must return text/plain content in Prometheus exposition format.
    After at least one request, the keepshot_http_requests_total counter
    should appear in the output.
    """
    # Make a request so there's at least one sample
    client.get("/health")

    resp = client.get("/metrics")
    assert resp.status_code == 200
    assert "text/plain" in resp.headers["content-type"]

    text = resp.text
    assert "keepshot_http_requests_total" in text
    assert "keepshot_http_request_duration_seconds" in text


def test_metrics_active_websockets_gauge(client: TestClient):
    """Gauge for active WebSockets should be present even with zero connections."""
    resp = client.get("/metrics")
    assert "keepshot_active_websockets" in resp.text


def test_docs_available(client: TestClient):
    """OpenAPI docs should be accessible."""
    assert client.get("/docs").status_code == 200


def test_redoc_available(client: TestClient):
    assert client.get("/redoc").status_code == 200
