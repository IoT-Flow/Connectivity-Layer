"""
HTTP metrics middleware for Prometheus.
Tracks HTTP request metrics including count, duration, and size.
"""
import logging
import time
import functools
from flask import request, g
from typing import Callable

from src.metrics import (
    HTTP_REQUEST_COUNT,
    HTTP_REQUEST_LATENCY,
    HTTP_REQUESTS_IN_PROGRESS,
    HTTP_REQUEST_SIZE_BYTES,
    HTTP_RESPONSE_SIZE_BYTES,
    HTTP_REQUEST_COUNT_ALL,
)

logger = logging.getLogger(__name__)


def track_request_metrics(func: Callable) -> Callable:
    """
    Decorator to track HTTP request metrics.

    This decorator should be applied to Flask route functions to automatically
    track request count, duration, and other metrics.
    """

    @functools.wraps(func)
    def wrapper(*args, **kwargs):
        # Record request start time
        start_time = time.time()

        # Increment in-progress requests
        HTTP_REQUESTS_IN_PROGRESS.inc()

        # Get request information
        method = request.method
        endpoint = request.endpoint or "unknown"

        # Track request size
        request_size = _get_request_size()
        if request_size > 0:
            HTTP_REQUEST_SIZE_BYTES.labels(method=method, endpoint=endpoint).observe(request_size)

        try:
            # Execute the actual route function
            response = func(*args, **kwargs)

            # Determine status code
            if isinstance(response, tuple):
                status_code = str(response[1]) if len(response) > 1 else "200"
                response_data = response[0]
            else:
                status_code = "200"
                response_data = response

            # Track response size
            response_size = _get_response_size(response_data)
            if response_size > 0:
                HTTP_RESPONSE_SIZE_BYTES.labels(method=method, endpoint=endpoint).observe(response_size)

            return response

        except Exception:
            # Track errors as 500 status
            status_code = "500"
            raise

        finally:
            # Calculate request duration
            duration = time.time() - start_time

            # Update metrics
            HTTP_REQUEST_COUNT.labels(method=method, endpoint=endpoint, status=status_code).inc()
            HTTP_REQUEST_LATENCY.labels(method=method, endpoint=endpoint).observe(duration)
            HTTP_REQUEST_COUNT_ALL.inc()

            # Decrement in-progress requests
            HTTP_REQUESTS_IN_PROGRESS.dec()

            # Log slow requests
            if duration > 1.0:  # Log requests taking more than 1 second
                logger.warning(f"Slow request: {method} {endpoint} took {duration:.3f}s (status: {status_code})")

    return wrapper


def setup_request_metrics_middleware(app):
    """
    Set up request metrics middleware for the Flask app.

    This function should be called during app initialization to set up
    automatic request tracking for all routes.
    """

    @app.before_request
    def before_request():
        """Record request start time and increment in-progress counter."""
        g.start_time = time.time()
        HTTP_REQUESTS_IN_PROGRESS.inc()

        # Track request size
        method = request.method
        endpoint = request.endpoint or "unknown"
        request_size = _get_request_size()

        if request_size > 0:
            HTTP_REQUEST_SIZE_BYTES.labels(method=method, endpoint=endpoint).observe(request_size)

    @app.after_request
    def after_request(response):
        """Record request completion metrics."""
        try:
            # Get request information
            method = request.method
            endpoint = request.endpoint or "unknown"
            status_code = str(response.status_code)

            # Calculate duration
            if hasattr(g, "start_time"):
                duration = time.time() - g.start_time
                HTTP_REQUEST_LATENCY.labels(method=method, endpoint=endpoint).observe(duration)

                # Log slow requests (> 1 second)
                if duration > 1.0:
                    logger.warning(f"Slow request: {method} {endpoint} took {duration:.3f}s")

            # Update counters
            HTTP_REQUEST_COUNT.labels(method=method, endpoint=endpoint, status=status_code).inc()
            HTTP_REQUEST_COUNT_ALL.inc()

            # Track response size
            response_size = _get_response_size(response.data if hasattr(response, "data") else None)
            if response_size > 0:
                HTTP_RESPONSE_SIZE_BYTES.labels(method=method, endpoint=endpoint).observe(response_size)

        except Exception as e:
            logger.error(f"Error recording request metrics: {e}")

        finally:
            # Always decrement in-progress counter
            HTTP_REQUESTS_IN_PROGRESS.dec()

        return response

    @app.teardown_request
    def teardown_request(exception):
        """Ensure in-progress counter is decremented even on exceptions."""
        try:
            # This is a safety net in case after_request doesn't run
            if HTTP_REQUESTS_IN_PROGRESS._value._value > 0:
                HTTP_REQUESTS_IN_PROGRESS.dec()
        except Exception as e:
            logger.error(f"Error in request teardown: {e}")

    logger.info("HTTP metrics middleware configured")


def _get_request_size() -> int:
    """Get the size of the current request in bytes."""
    try:
        # Get content length from headers
        content_length = request.content_length
        if content_length:
            return content_length

        # Try to get size from request data
        if hasattr(request, "data") and request.data:
            return len(request.data)

        # Try to get size from form data
        if request.form:
            return len(str(request.form).encode("utf-8"))

        # Try to get size from JSON data
        if request.is_json and request.json:
            import json

            return len(json.dumps(request.json).encode("utf-8"))

        return 0

    except Exception as e:
        logger.debug(f"Error getting request size: {e}")
        return 0


def _get_response_size(response_data) -> int:
    """Get the size of the response in bytes."""
    try:
        if response_data is None:
            return 0

        if isinstance(response_data, bytes):
            return len(response_data)

        if isinstance(response_data, str):
            return len(response_data.encode("utf-8"))

        # For other types, try to convert to string
        return len(str(response_data).encode("utf-8"))

    except Exception as e:
        logger.debug(f"Error getting response size: {e}")
        return 0


def increment_telemetry_counter():
    """Increment telemetry message counter (called by telemetry routes)."""
    try:
        from src.metrics import IOTFLOW_TELEMETRY_MESSAGES

        IOTFLOW_TELEMETRY_MESSAGES.inc()

    except Exception as e:
        logger.error(f"Error incrementing telemetry counter: {e}")


def increment_control_command_counter(status: str = "pending"):
    """Increment control command counter (called by control routes)."""
    try:
        from src.metrics import IOTFLOW_CONTROL_COMMANDS

        IOTFLOW_CONTROL_COMMANDS.labels(status=status).inc()

    except Exception as e:
        logger.error(f"Error incrementing control command counter: {e}")


def get_current_request_metrics() -> dict:
    """Get current HTTP request metrics for debugging."""
    try:
        return {
            "requests_in_progress": HTTP_REQUESTS_IN_PROGRESS._value._value,
            "total_requests": HTTP_REQUEST_COUNT_ALL._value._value,
            "request_count_metrics": len(HTTP_REQUEST_COUNT._metrics),
            "latency_metrics": len(HTTP_REQUEST_LATENCY._metrics),
        }
    except Exception as e:
        logger.error(f"Error getting current request metrics: {e}")
        return {}
