from fastapi import APIRouter
from prometheus_client import CONTENT_TYPE_LATEST, Counter, Histogram, generate_latest
from starlette.responses import Response

router = APIRouter(tags=["monitoring"])

# Prometheus metrics registry. Defined here so any import of the metrics
# module (including the /metrics endpoint and tests) registers the ces_*
# collectors with the default registry. The observability middleware imports
# these symbols to record request counts and durations.
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


@router.get("/metrics", include_in_schema=False)
def prometheus_metrics() -> Response:
    return Response(generate_latest(), media_type=CONTENT_TYPE_LATEST)
