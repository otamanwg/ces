import json
import logging

from fastapi import FastAPI
from fastapi.testclient import TestClient

from backend.app.core.observability import JsonLogFormatter, observe_http_request


def _make_observed_app() -> FastAPI:
    app = FastAPI()
    app.middleware("http")(observe_http_request)

    @app.get("/ok")
    def ok() -> dict[str, bool]:
        return {"ok": True}

    return app


def test_observe_http_request_reuses_inbound_request_id() -> None:
    client = TestClient(_make_observed_app())

    response = client.get("/ok", headers={"X-Request-ID": "client-request-123"})

    assert response.status_code == 200
    assert response.headers["X-Request-ID"] == "client-request-123"


def test_observe_http_request_generates_request_id_when_missing() -> None:
    client = TestClient(_make_observed_app())

    response = client.get("/ok")

    assert response.status_code == 200
    assert len(response.headers["X-Request-ID"]) == 32


def test_json_log_formatter_includes_request_context_and_extra_fields() -> None:
    record = logging.LogRecord(
        name="CityHTTP",
        level=logging.INFO,
        pathname=__file__,
        lineno=1,
        msg="http_request",
        args=(),
        exc_info=None,
    )
    record.request_id = "request-1"
    record.method = "GET"
    record.path = "/health/live"
    record.status = 200

    payload = json.loads(JsonLogFormatter().format(record))

    assert payload["level"] == "INFO"
    assert payload["logger"] == "CityHTTP"
    assert payload["message"] == "http_request"
    assert payload["request_id"] == "request-1"
    assert payload["method"] == "GET"
    assert payload["path"] == "/health/live"
    assert payload["status"] == 200
