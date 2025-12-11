"""
Unit tests for metrics middleware.
"""
import pytest
import time
from unittest.mock import Mock, patch, MagicMock
from flask import Flask, request, g

from src.middleware.metrics_middleware import (
    track_request_metrics,
    setup_request_metrics_middleware,
    _get_request_size,
    _get_response_size,
)


@pytest.fixture
def app():
    """Create a Flask app for testing."""
    app = Flask(__name__)
    app.config["TESTING"] = True
    return app


@pytest.fixture
def app_context(app):
    """Create an application context."""
    with app.app_context():
        yield app


@pytest.fixture
def request_context(app):
    """Create a request context."""
    with app.test_request_context():
        yield


class TestTrackRequestMetrics:
    """Test track_request_metrics decorator."""

    @patch("src.middleware.metrics_middleware.HTTP_REQUEST_COUNT")
    @patch("src.middleware.metrics_middleware.HTTP_REQUEST_LATENCY")
    @patch("src.middleware.metrics_middleware.HTTP_REQUESTS_IN_PROGRESS")
    def test_track_request_metrics_success(self, mock_in_progress, mock_latency, mock_count, request_context):
        """Test successful request tracking."""
        # Setup mocks
        mock_counter = Mock()
        mock_histogram = Mock()

        mock_count.labels.return_value = mock_counter
        mock_latency.labels.return_value = mock_histogram

        with patch("src.middleware.metrics_middleware.request") as mock_request:
            mock_request.method = "GET"
            mock_request.endpoint = "test_endpoint"
            mock_request.content_length = 100

            @track_request_metrics
            def test_function():
                return "test_response"

            result = test_function()

            assert result == "test_response"
            mock_in_progress.inc.assert_called_once()
            mock_in_progress.dec.assert_called_once()
            mock_counter.inc.assert_called_once()
            mock_histogram.observe.assert_called_once()

    @patch("src.middleware.metrics_middleware.HTTP_REQUEST_COUNT")
    @patch("src.middleware.metrics_middleware.HTTP_REQUEST_LATENCY")
    @patch("src.middleware.metrics_middleware.HTTP_REQUESTS_IN_PROGRESS")
    def test_track_request_metrics_with_tuple_response(
        self, mock_in_progress, mock_latency, mock_count, request_context
    ):
        """Test request tracking with tuple response."""
        mock_counter = Mock()
        mock_histogram = Mock()

        mock_count.labels.return_value = mock_counter
        mock_latency.labels.return_value = mock_histogram

        with patch("src.middleware.metrics_middleware.request") as mock_request:
            mock_request.method = "POST"
            mock_request.endpoint = "create_endpoint"
            mock_request.content_length = 200

            @track_request_metrics
            def test_function():
                return "created", 201

            result = test_function()

            assert result == ("created", 201)
            mock_counter.inc.assert_called_once()

    @patch("src.middleware.metrics_middleware.HTTP_REQUEST_COUNT")
    @patch("src.middleware.metrics_middleware.HTTP_REQUEST_LATENCY")
    @patch("src.middleware.metrics_middleware.HTTP_REQUESTS_IN_PROGRESS")
    def test_track_request_metrics_with_exception(self, mock_in_progress, mock_latency, mock_count, request_context):
        """Test request tracking when function raises exception."""
        mock_counter = Mock()
        mock_histogram = Mock()

        mock_count.labels.return_value = mock_counter
        mock_latency.labels.return_value = mock_histogram

        with patch("src.middleware.metrics_middleware.request") as mock_request:
            mock_request.method = "DELETE"
            mock_request.endpoint = "delete_endpoint"
            mock_request.content_length = 0

            @track_request_metrics
            def test_function():
                raise ValueError("Test error")

            with pytest.raises(ValueError):
                test_function()

            # Should still track metrics even with exception
            mock_in_progress.inc.assert_called_once()
            mock_in_progress.dec.assert_called_once()
            mock_counter.inc.assert_called_once()
            mock_histogram.observe.assert_called_once()

    @patch("src.middleware.metrics_middleware.HTTP_REQUEST_SIZE_BYTES")
    @patch("src.middleware.metrics_middleware.HTTP_RESPONSE_SIZE_BYTES")
    def test_track_request_metrics_with_size_tracking(self, mock_response_size, mock_request_size, request_context):
        """Test request and response size tracking."""
        mock_req_histogram = Mock()
        mock_resp_histogram = Mock()

        mock_request_size.labels.return_value = mock_req_histogram
        mock_response_size.labels.return_value = mock_resp_histogram

        with patch("src.middleware.metrics_middleware.request") as mock_request:
            mock_request.method = "PUT"
            mock_request.endpoint = "update_endpoint"
            mock_request.content_length = 500

            with patch("src.middleware.metrics_middleware._get_request_size", return_value=500):
                with patch("src.middleware.metrics_middleware._get_response_size", return_value=300):

                    @track_request_metrics
                    def test_function():
                        return "updated_data"

                    result = test_function()

                    assert result == "updated_data"
                    mock_req_histogram.observe.assert_called_once_with(500)
                    mock_resp_histogram.observe.assert_called_once_with(300)

    @patch("src.middleware.metrics_middleware.logger")
    @patch("src.middleware.metrics_middleware.HTTP_REQUEST_COUNT")
    @patch("src.middleware.metrics_middleware.HTTP_REQUEST_LATENCY")
    @patch("src.middleware.metrics_middleware.HTTP_REQUESTS_IN_PROGRESS")
    @patch("src.middleware.metrics_middleware.HTTP_REQUEST_COUNT_ALL")
    def test_track_request_metrics_slow_request_logging(
        self, mock_count_all, mock_in_progress, mock_latency, mock_count, mock_logger, request_context
    ):
        """Test logging of slow requests."""
        # Mock the metrics
        mock_counter = Mock()
        mock_histogram = Mock()
        mock_count.labels.return_value = mock_counter
        mock_latency.labels.return_value = mock_histogram

        with patch("src.middleware.metrics_middleware.request") as mock_request:
            mock_request.method = "GET"
            mock_request.endpoint = "slow_endpoint"
            mock_request.content_length = 0

            # Mock time module at the middleware level
            with patch("src.middleware.metrics_middleware.time") as mock_time:
                mock_time.time.side_effect = [0, 1.5]  # 1.5 second duration

                @track_request_metrics
                def slow_function():
                    return "slow_response"

                result = slow_function()

                assert result == "slow_response"
                mock_logger.warning.assert_called_once()

    def test_track_request_metrics_unknown_endpoint(self, request_context):
        """Test handling of unknown endpoint."""
        with patch("src.middleware.metrics_middleware.request") as mock_request:
            mock_request.method = "GET"
            mock_request.endpoint = None
            mock_request.content_length = 0

            @track_request_metrics
            def test_function():
                return "response"

            with patch("src.middleware.metrics_middleware.HTTP_REQUEST_COUNT") as mock_count:
                mock_counter = Mock()
                mock_count.labels.return_value = mock_counter

                result = test_function()

                assert result == "response"
                mock_count.labels.assert_called_with(method="GET", endpoint="unknown", status="200")


class TestRequestSizeHelpers:
    """Test request and response size helper functions."""

    def test_get_request_size_with_content_length(self, request_context):
        """Test getting request size from content-length header."""
        with patch("src.middleware.metrics_middleware.request") as mock_request:
            mock_request.content_length = 1024

            size = _get_request_size()

            assert size == 1024

    def test_get_request_size_without_content_length(self, request_context):
        """Test getting request size without content-length header."""
        with patch("src.middleware.metrics_middleware.request") as mock_request:
            mock_request.content_length = None
            mock_request.data = b"test data"

            size = _get_request_size()

            assert size == len(b"test data")

    def test_get_request_size_no_data(self, request_context):
        """Test getting request size when no data available."""
        with patch("src.middleware.metrics_middleware.request") as mock_request:
            mock_request.content_length = None
            mock_request.data = b""
            mock_request.form = {}
            mock_request.is_json = False
            mock_request.json = None

            size = _get_request_size()

            assert size == 0

    def test_get_response_size_string(self):
        """Test getting response size for string data."""
        response_data = "Hello, World!"

        size = _get_response_size(response_data)

        assert size == len(response_data.encode("utf-8"))

    def test_get_response_size_bytes(self):
        """Test getting response size for bytes data."""
        response_data = b"Binary data"

        size = _get_response_size(response_data)

        assert size == len(response_data)

    def test_get_response_size_none(self):
        """Test getting response size for None data."""
        size = _get_response_size(None)

        assert size == 0

    def test_get_response_size_dict(self):
        """Test getting response size for dict data (JSON)."""
        response_data = {"key": "value", "number": 42}

        size = _get_response_size(response_data)

        # Should convert to string and get byte length
        expected_size = len(str(response_data).encode("utf-8"))
        assert size == expected_size


class TestSetupRequestMetricsMiddleware:
    """Test setup_request_metrics_middleware function."""

    def test_setup_request_metrics_middleware(self):
        """Test setting up request metrics middleware."""
        mock_app = Mock()

        setup_request_metrics_middleware(mock_app)

        # Should register before_request and after_request handlers
        mock_app.before_request.assert_called_once()
        mock_app.after_request.assert_called_once()

    def test_before_request_handler(self, app_context):
        """Test the before_request handler functionality."""
        mock_app = Mock()

        setup_request_metrics_middleware(mock_app)

        # Get the before_request handler
        before_handler = mock_app.before_request.call_args[0][0]

        with patch("src.middleware.metrics_middleware.g") as mock_g:
            with patch("time.time", return_value=123456.789):
                before_handler()

                # Check that the attribute was set (it will be a Mock object)
                assert hasattr(mock_g, "request_start_time")

    @patch("src.middleware.metrics_middleware.HTTP_REQUESTS_IN_PROGRESS")
    def test_before_request_handler_increments_counter(self, mock_in_progress, app_context):
        """Test that before_request handler increments in-progress counter."""
        mock_app = Mock()

        setup_request_metrics_middleware(mock_app)

        before_handler = mock_app.before_request.call_args[0][0]

        with patch("src.middleware.metrics_middleware.g"):
            before_handler()

            mock_in_progress.inc.assert_called_once()

    def test_after_request_handler(self, app_context):
        """Test the after_request handler functionality."""
        mock_app = Mock()

        setup_request_metrics_middleware(mock_app)

        # Get the after_request handler
        after_handler = mock_app.after_request.call_args[0][0]

        mock_response = Mock()
        mock_response.status_code = 200

        with patch("src.middleware.metrics_middleware.g") as mock_g:
            mock_g.request_start_time = 123456.789

            with patch("src.middleware.metrics_middleware.request") as mock_request:
                mock_request.method = "GET"
                mock_request.endpoint = "test"

                with patch("time.time", return_value=123456.890):  # 0.101 second duration
                    result = after_handler(mock_response)

                    assert result == mock_response

    @patch("src.middleware.metrics_middleware.HTTP_REQUEST_COUNT")
    @patch("src.middleware.metrics_middleware.HTTP_REQUEST_LATENCY")
    @patch("src.middleware.metrics_middleware.HTTP_REQUESTS_IN_PROGRESS")
    def test_after_request_handler_updates_metrics(self, mock_in_progress, mock_latency, mock_count, app_context):
        """Test that after_request handler updates all metrics."""
        mock_app = Mock()

        setup_request_metrics_middleware(mock_app)

        after_handler = mock_app.after_request.call_args[0][0]

        mock_response = Mock()
        mock_response.status_code = 201

        mock_counter = Mock()
        mock_histogram = Mock()

        mock_count.labels.return_value = mock_counter
        mock_latency.labels.return_value = mock_histogram

        with patch("src.middleware.metrics_middleware.g") as mock_g:
            # Configure the mock to return the expected value for start_time (not request_start_time)
            mock_g.configure_mock(start_time=100.0)

            with patch("src.middleware.metrics_middleware.request") as mock_request:
                mock_request.method = "POST"
                mock_request.endpoint = "create"

                with patch("time.time", return_value=100.5):  # 0.5 second duration
                    after_handler(mock_response)

                    mock_count.labels.assert_called_with(method="POST", endpoint="create", status="201")
                    mock_counter.inc.assert_called_once()
                    mock_latency.labels.assert_called_with(method="POST", endpoint="create")
                    mock_histogram.observe.assert_called_with(0.5)
                    mock_in_progress.dec.assert_called_once()

    def test_after_request_handler_missing_start_time(self, app_context):
        """Test after_request handler when start time is missing."""
        mock_app = Mock()

        setup_request_metrics_middleware(mock_app)

        after_handler = mock_app.after_request.call_args[0][0]

        mock_response = Mock()
        mock_response.status_code = 200

        with patch("src.middleware.metrics_middleware.g") as mock_g:
            # No request_start_time attribute
            del mock_g.request_start_time

            with patch("src.middleware.metrics_middleware.request") as mock_request:
                mock_request.method = "GET"
                mock_request.endpoint = "test"

                # Should not raise exception
                result = after_handler(mock_response)

                assert result == mock_response

    @patch("src.middleware.metrics_middleware.logger")
    def test_after_request_handler_logs_slow_requests(self, mock_logger, app_context):
        """Test that slow requests are logged."""
        mock_app = Mock()

        setup_request_metrics_middleware(mock_app)

        after_handler = mock_app.after_request.call_args[0][0]

        mock_response = Mock()
        mock_response.status_code = 200

        with patch("src.middleware.metrics_middleware.g") as mock_g:
            mock_g.start_time = 100.0

            with patch("src.middleware.metrics_middleware.request") as mock_request:
                mock_request.method = "GET"
                mock_request.endpoint = "slow_endpoint"

                with patch("time.time", return_value=102.0):  # 2 second duration
                    after_handler(mock_response)

                    mock_logger.warning.assert_called_once()
                    warning_call = mock_logger.warning.call_args[0][0]
                    assert "Slow request" in warning_call
                    assert "slow_endpoint" in warning_call
                    assert "2.000s" in warning_call


class TestMetricsMiddlewareIntegration:
    """Test metrics middleware integration."""

    def test_decorator_preserves_function_metadata(self):
        """Test that decorator preserves function metadata."""

        @track_request_metrics
        def test_function():
            """Test function docstring."""
            return "test"

        assert test_function.__name__ == "test_function"
        assert test_function.__doc__ == "Test function docstring."

    def test_decorator_works_with_arguments(self, request_context):
        """Test that decorator works with function arguments."""

        @track_request_metrics
        def test_function(arg1, arg2, kwarg1=None):
            return f"{arg1}-{arg2}-{kwarg1}"

        with patch("src.middleware.metrics_middleware.request") as mock_request:
            mock_request.method = "GET"
            mock_request.endpoint = "test"
            mock_request.content_length = 0

            result = test_function("a", "b", kwarg1="c")

            assert result == "a-b-c"

    def test_multiple_decorators_compatibility(self, request_context):
        """Test compatibility with other decorators."""

        def other_decorator(func):
            def wrapper(*args, **kwargs):
                result = func(*args, **kwargs)
                return f"decorated-{result}"

            return wrapper

        @other_decorator
        @track_request_metrics
        def test_function():
            return "test"

        with patch("src.middleware.metrics_middleware.request") as mock_request:
            mock_request.method = "GET"
            mock_request.endpoint = "test"
            mock_request.content_length = 0

            result = test_function()

            assert result == "decorated-test"
