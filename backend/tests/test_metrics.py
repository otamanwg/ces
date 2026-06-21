from prometheus_client import generate_latest

from backend.app.api.metrics import prometheus_metrics


def test_metrics_endpoint_exposes_backend_metrics() -> None:
    response = prometheus_metrics()
    body = bytes(response.body)

    assert response.status_code == 200
    assert b"ces_http_requests_total" in generate_latest()
    assert b"ces_http_request_duration_seconds" in body
