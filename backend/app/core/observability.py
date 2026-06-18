import json
import logging
from contextvars import ContextVar
from datetime import UTC, datetime
from time import perf_counter
from uuid import uuid4

from fastapi import Request
from prometheus_client import Counter, Histogram

from backend.app.core.config import settings

request_id_context: ContextVar[str] = ContextVar("request_id", default="-")
logger = logging.getLogger("CityHTTP")

HTTP_REQUESTS = Counter(
    "ces_http_requests_total",
    "HTTP requests handled by the backend.",
    ("method", "path", "status"),
)
HTTP_REQUEST_DURATION = Histogram(
    "ces_http_request_duration_seconds",
    "HTTP request duration in seconds.",
    ("method", "path"),
)

_RESERVED_LOG_RECORD_KEYS = {
    "args",
    "asctime",
    "created",
    "exc_info",
    "exc_text",
    "filename",
    "funcName",
    "levelname",
    "levelno",
    "lineno",
    "message",
    "module",
    "msecs",
    "msg",
    "name",
    "pathname",
    "process",
    "processName",
    "relativeCreated",
    "stack_info",
    "thread",
    "threadName",
}


class RequestIdFilter(logging.Filter):
    def filter(self, record: logging.LogRecord) -> bool:
        record.request_id = request_id_context.get()
        return True


class JsonLogFormatter(logging.Formatter):
    def format(self, record: logging.LogRecord) -> str:
        payload = {
            "timestamp": datetime.fromtimestamp(record.created, UTC).isoformat(),
            "level": record.levelname,
            "logger": record.name,
            "message": record.getMessage(),
            "request_id": getattr(record, "request_id", "-"),
        }

        for key, value in record.__dict__.items():
            if key not in _RESERVED_LOG_RECORD_KEYS and key not in payload:
                payload[key] = value

        if record.exc_info:
            payload["exception"] = self.formatException(record.exc_info)

        return json.dumps(payload, ensure_ascii=False, default=str)


def configure_logging() -> None:
    formatter: logging.Formatter
    if settings.log_format == "json":
        formatter = JsonLogFormatter()
    else:
        formatter = logging.Formatter("%(levelname)s:%(name)s:%(message)s request_id=%(request_id)s")

    root_logger = logging.getLogger()
    root_logger.setLevel(logging.INFO)
    if not root_logger.handlers:
        root_logger.addHandler(logging.StreamHandler())

    for handler in root_logger.handlers:
        handler.setFormatter(formatter)
        if not any(isinstance(log_filter, RequestIdFilter) for log_filter in handler.filters):
            handler.addFilter(RequestIdFilter())


def _resolve_request_id(request: Request) -> str:
    raw_request_id = request.headers.get("X-Request-ID", "").strip()
    if raw_request_id and len(raw_request_id) <= 128:
        return raw_request_id
    return uuid4().hex


async def observe_http_request(request: Request, call_next):
    if request.url.path == "/metrics":
        return await call_next(request)

    request_id = _resolve_request_id(request)
    request.state.request_id = request_id
    request_token = request_id_context.set(request_id)
    started_at = perf_counter()
    status_code = 500
    try:
        response = await call_next(request)
        status_code = response.status_code
        response.headers["X-Request-ID"] = request_id
        return response
    finally:
        route = request.scope.get("route")
        path = getattr(route, "path", request.url.path)
        duration_seconds = perf_counter() - started_at
        HTTP_REQUESTS.labels(request.method, path, str(status_code)).inc()
        HTTP_REQUEST_DURATION.labels(request.method, path).observe(duration_seconds)
        logger.info(
            "http_request",
            extra={
                "method": request.method,
                "path": path,
                "status": status_code,
                "duration_ms": round(duration_seconds * 1000, 3),
            },
        )
        request_id_context.reset(request_token)
