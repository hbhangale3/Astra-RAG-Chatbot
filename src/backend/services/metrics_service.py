import time
from typing import Callable

from fastapi import Request, Response
from prometheus_client import Counter, Histogram, Gauge, generate_latest, CONTENT_TYPE_LATEST


api_requests_total = Counter(
    "api_requests_total",
    "Total number of API requests received by the FastAPI backend.",
    ["method", "endpoint", "status_code"],
)

api_errors_total = Counter(
    "api_errors_total",
    "Total number of failed API requests returned by the FastAPI backend.",
    ["method", "endpoint", "status_code"],
)

api_request_latency_seconds = Histogram(
    "api_request_latency_seconds",
    "Latency of FastAPI requests in seconds.",
    ["method", "endpoint"],
)


def get_metrics_response() -> Response:
    """
    Returns Prometheus metrics in text exposition format.

    Returns:
        Response: FastAPI response containing all registered Prometheus metrics.
    """
    return Response(
        content=generate_latest(),
        media_type=CONTENT_TYPE_LATEST,
    )


async def prometheus_metrics_middleware(
    request: Request,
    call_next: Callable,
):
    """
    Measures request count, error count, and latency for all FastAPI endpoints.

    Parameters:
        request (Request): Incoming FastAPI request.
        call_next (Callable): Next middleware or route handler.

    Returns:
        Response: API response after recording Prometheus metrics.
    """
    start_time = time.time()

    method = request.method
    endpoint = request.url.path
    if endpoint in ["/metrics", "/favicon.ico"]:
    return await call_next(request)


    try:
        response = await call_next(request)
        status_code = str(response.status_code)

        api_requests_total.labels(
            method=method,
            endpoint=endpoint,
            status_code=status_code,
        ).inc()

        if response.status_code >= 400:
            api_errors_total.labels(
                method=method,
                endpoint=endpoint,
                status_code=status_code,
            ).inc()

        return response

    except Exception:
        status_code = "500"

        api_requests_total.labels(
            method=method,
            endpoint=endpoint,
            status_code=status_code,
        ).inc()

        api_errors_total.labels(
            method=method,
            endpoint=endpoint,
            status_code=status_code,
        ).inc()

        raise

    finally:
        duration = time.time() - start_time

        api_request_latency_seconds.labels(
            method=method,
            endpoint=endpoint,
        ).observe(duration)