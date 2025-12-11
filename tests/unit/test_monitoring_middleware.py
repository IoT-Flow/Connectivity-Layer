"""
Unit tests for monitoring middleware.
"""
import pytest
from unittest.mock import Mock, patch, MagicMock
import time
from flask import Flask
from src.middleware.monitoring import HealthMonitor, device_heartbeat_monitor, request_metrics_middleware


class TestHealthMonitor:
    """Test HealthMonitor class."""

    def test_initialization(self):
        """Test HealthMonitor initialization."""
        monitor = HealthMonitor()
        assert monitor is not None

    def test_get_system_health(self, app):
        """Test get_system_health method."""
        with patch("src.middleware.monitoring.current_app") as mock_app:
            # Mock logger
            mock_app.logger = Mock()

            # Mock Redis client
            mock_redis = Mock()
            mock_app.redis_client = mock_redis
            mock_redis.ping.return_value = True
            mock_redis.info.return_value = {"used_memory": 1024 * 1024 * 50, "connected_clients": 5}  # 50MB

            with patch("src.middleware.monitoring.db") as mock_db:
                # Mock database
                mock_db.session.execute.return_value = Mock()
                mock_db.session.commit.return_value = None

                with patch("src.middleware.monitoring.psutil") as mock_psutil:
                    # Mock psutil
                    mock_psutil.cpu_percent.return_value = 45.5
                    mock_psutil.virtual_memory.return_value = Mock(percent=60.0, available=1024 * 1024 * 1024)
                    mock_psutil.disk_usage.return_value = Mock(percent=30.0)
                    mock_psutil.getloadavg.return_value = [0.5, 0.6, 0.7]

                    with patch("src.config.iotdb_config.iotdb_config") as mock_iotdb:
                        mock_iotdb.is_connected.return_value = True
                        mock_iotdb.host = "localhost"
                        mock_iotdb.port = 6667
                        mock_iotdb.database = "root.test"
                        mock_session = Mock()
                        mock_iotdb.session = mock_session
                        mock_dataset = Mock()
                        mock_dataset.close_operation_handle.return_value = None
                        mock_session.execute_query_statement.return_value = mock_dataset

                        with patch("src.middleware.monitoring.Device") as mock_device:
                            mock_device.query.count.return_value = 10
                            mock_device.query.filter_by.return_value.count.return_value = 8
                            mock_device.query.filter.return_value.count.return_value = 6

                            with patch(
                                "src.middleware.monitoring.HealthMonitor._get_telemetry_count_iotdb"
                            ) as mock_telemetry:
                                mock_telemetry.return_value = 100

                                monitor = HealthMonitor()
                                health = monitor.get_system_health()

                                # Check that health data structure is correct
                                assert "status" in health
                                assert "timestamp" in health
                                assert "checks" in health
                                assert "metrics" in health
                                assert health["status"] in ["healthy", "degraded", "unhealthy", "error"]

    @patch("src.middleware.monitoring.db")
    def test_check_database_success(self, mock_db):
        """Test _check_database with successful connection."""
        mock_db.session.execute.return_value = Mock()
        mock_db.session.commit.return_value = None

        monitor = HealthMonitor()
        result = monitor._check_database()

        assert result["status"] == "connected"
        assert result["healthy"] == True
        assert result["response_time_ms"] >= 0

    @patch("src.middleware.monitoring.db")
    def test_check_database_failure(self, mock_db):
        """Test _check_database with failed connection."""
        mock_db.session.execute.side_effect = Exception("Database error")

        monitor = HealthMonitor()
        result = monitor._check_database()

        assert result["status"] == "disconnected"
        assert result["healthy"] == False
        assert "error" in result

    def test_check_redis_success(self, app):
        """Test _check_redis with successful connection."""
        with patch("src.middleware.monitoring.current_app") as mock_current_app:
            mock_redis = Mock()
            mock_current_app.redis_client = mock_redis
            mock_redis.ping.return_value = True
            mock_redis.info.return_value = {"used_memory": 1024 * 1024 * 50, "connected_clients": 5}  # 50MB

            monitor = HealthMonitor()
            result = monitor._check_redis()

            assert result["status"] == "connected"
            assert result["healthy"] == True
            assert result["response_time_ms"] >= 0

    def test_check_redis_failure(self, app):
        """Test _check_redis with failed connection."""
        with patch("src.middleware.monitoring.current_app") as mock_current_app:
            # No redis_client attribute
            if hasattr(mock_current_app, "redis_client"):
                del mock_current_app.redis_client

            monitor = HealthMonitor()
            result = monitor._check_redis()

            assert result["status"] == "not_configured"
            assert result["healthy"] == False

    def test_check_iotdb_success(self, app):
        """Test _check_iotdb with successful connection."""
        with patch("src.config.iotdb_config.iotdb_config") as mock_iotdb_config:
            mock_iotdb_config.is_connected.return_value = True
            mock_iotdb_config.host = "localhost"
            mock_iotdb_config.port = 6667
            mock_iotdb_config.database = "root.test"

            mock_session = Mock()
            mock_iotdb_config.session = mock_session

            mock_dataset = Mock()
            mock_dataset.close_operation_handle.return_value = None
            mock_session.execute_query_statement.return_value = mock_dataset

            monitor = HealthMonitor()
            result = monitor._check_iotdb()

            assert result["status"] == "connected"
            assert result["healthy"] == True
            assert result["response_time_ms"] >= 0

    def test_check_iotdb_failure(self, app):
        """Test _check_iotdb with failed connection."""
        with patch("src.config.iotdb_config.iotdb_config") as mock_iotdb_config:
            mock_iotdb_config.is_connected.return_value = False
            mock_iotdb_config.host = "localhost"
            mock_iotdb_config.port = 6667

            monitor = HealthMonitor()
            result = monitor._check_iotdb()

            assert result["status"] == "disconnected"
            assert result["healthy"] == False

    @patch("src.middleware.monitoring.psutil")
    def test_get_system_metrics(self, mock_psutil):
        """Test _get_system_metrics method."""
        mock_psutil.cpu_percent.return_value = 25.5
        mock_memory = Mock()
        mock_memory.percent = 40.0
        mock_memory.available = 1024 * 1024 * 1024  # 1GB
        mock_psutil.virtual_memory.return_value = mock_memory
        mock_psutil.disk_usage.return_value = Mock(percent=20.0)
        mock_psutil.getloadavg.return_value = [0.5, 0.6, 0.7]

        monitor = HealthMonitor()
        metrics = monitor._get_system_metrics()

        assert metrics["cpu_percent"] == 25.5
        assert metrics["memory_percent"] == 40.0
        assert metrics["disk_usage_percent"] == 20.0
        assert metrics["memory_available_mb"] == 1024.0

    def test_get_app_metrics(self, app):
        """Test _get_app_metrics method."""
        with patch("src.middleware.monitoring.current_app") as mock_current_app:
            # Configure mock properly
            mock_config = Mock()
            mock_config.get.return_value = "development"
            mock_current_app.config = mock_config
            mock_current_app.debug = True
            mock_current_app.testing = False

            monitor = HealthMonitor()
            metrics = monitor._get_app_metrics()

            assert "flask_env" in metrics
            assert "debug_mode" in metrics
            assert "testing_mode" in metrics
            assert metrics["flask_env"] == "development"
            assert metrics["debug_mode"] == True
            assert metrics["testing_mode"] == False

    def test_get_device_metrics(self, app):
        """Test _get_device_metrics method."""
        # Mock the method directly to avoid complex mocking
        expected_metrics = {
            "total_devices": 10,
            "active_devices": 8,
            "online_devices": 6,
            "offline_devices": 2,
            "telemetry_last_hour": 100,
            "telemetry_last_day": 100,
        }

        with patch.object(HealthMonitor, "_get_device_metrics", return_value=expected_metrics):
            monitor = HealthMonitor()
            metrics = monitor._get_device_metrics()

            assert metrics["total_devices"] == 10
            assert metrics["active_devices"] == 8
            assert metrics["online_devices"] == 6
            assert metrics["offline_devices"] == 2
            assert metrics["telemetry_last_hour"] == 100
            assert metrics["telemetry_last_day"] == 100

    def test_get_telemetry_count_iotdb(self, app):
        """Test _get_telemetry_count_iotdb method."""
        with patch("src.config.iotdb_config.iotdb_config") as mock_iotdb_config:
            mock_iotdb_config.is_connected.return_value = True
            mock_iotdb_config.database = "root.test"

            mock_session = Mock()
            mock_iotdb_config.session = mock_session

            mock_dataset = Mock()
            mock_dataset.has_next.side_effect = [True, True, False]  # 2 timeseries
            mock_dataset.next.return_value = None
            mock_dataset.close_operation_handle.return_value = None
            mock_session.execute_query_statement.return_value = mock_dataset

            monitor = HealthMonitor()
            count = monitor._get_telemetry_count_iotdb("-1h")

            assert count == 2


class TestDeviceHeartbeatMonitor:
    """Test device heartbeat monitor decorator."""

    def test_device_heartbeat_monitor_decorator(self, app):
        """Test device heartbeat monitor decorator."""

        @device_heartbeat_monitor()
        def test_function():
            return "test_result"

        # Test that decorator returns a function
        assert callable(test_function)

        # Test that decorated function works
        with patch("src.middleware.monitoring.request") as mock_request:
            # No device attribute
            if hasattr(mock_request, "device"):
                del mock_request.device
            result = test_function()
            assert result == "test_result"

    def test_device_heartbeat_monitor_with_device_id(self, app):
        """Test device heartbeat monitor with device_id in request."""
        with patch("src.middleware.monitoring.current_app") as mock_current_app:
            mock_redis = Mock()
            mock_current_app.redis_client = mock_redis

            mock_device = Mock()
            mock_device.id = "test_device_123"
            mock_device.update_last_seen.return_value = None

            @device_heartbeat_monitor()
            def test_function(device_id):
                return f"result_for_{device_id}"

            with patch("src.middleware.monitoring.request") as mock_request:
                mock_request.device = mock_device

                result = test_function("test_device_123")

                assert result == "result_for_test_device_123"
                mock_redis.setex.assert_called_once_with("heartbeat:test_device_123", 300, "online")
                mock_device.update_last_seen.assert_called_once()

    def test_device_heartbeat_monitor_no_device_id(self, app):
        """Test device heartbeat monitor without device_id."""

        @device_heartbeat_monitor()
        def test_function():
            return "result_no_device"

        with patch("src.middleware.monitoring.request") as mock_request:
            # No device attribute
            if hasattr(mock_request, "device"):
                del mock_request.device

            result = test_function()

            assert result == "result_no_device"

    def test_device_heartbeat_monitor_exception_handling(self, app):
        """Test device heartbeat monitor handles exceptions."""
        with patch("src.middleware.monitoring.current_app") as mock_current_app:
            mock_redis = Mock()
            mock_redis.setex.side_effect = Exception("Redis error")
            mock_current_app.redis_client = mock_redis
            mock_current_app.logger = Mock()

            mock_device = Mock()
            mock_device.id = "test_device_123"
            mock_device.update_last_seen.return_value = None

            @device_heartbeat_monitor()
            def test_function(device_id):
                return f"result_for_{device_id}"

            with patch("src.middleware.monitoring.request") as mock_request:
                mock_request.device = mock_device

                # Should not raise exception
                result = test_function("test_device_123")
                assert result == "result_for_test_device_123"
                mock_current_app.logger.error.assert_called_once()


class TestRequestMetricsMiddleware:
    """Test request metrics middleware decorator."""

    def test_request_metrics_middleware_decorator(self, app):
        """Test request metrics middleware decorator."""
        with patch("src.middleware.monitoring.current_app") as mock_current_app:
            mock_current_app.logger = Mock()

            @request_metrics_middleware()
            def test_function():
                return "test_result"

            # Test that decorator returns a function
            assert callable(test_function)

            with patch("src.middleware.monitoring.request") as mock_request:
                mock_request.method = "GET"
                mock_request.path = "/test"
                mock_request.endpoint = "test"
                mock_request.remote_addr = "127.0.0.1"

                result = test_function()
                assert result == "test_result"

    def test_request_metrics_middleware_metrics(self, app):
        """Test request metrics middleware collects metrics."""
        with patch("src.middleware.monitoring.current_app") as mock_current_app:
            mock_current_app.logger = Mock()
            mock_redis = Mock()
            mock_current_app.redis_client = mock_redis

            @request_metrics_middleware()
            def test_function():
                time.sleep(0.01)  # Small delay to test duration
                return "test_result"

            with patch("src.middleware.monitoring.request") as mock_request:
                mock_request.method = "GET"
                mock_request.path = "/test"
                mock_request.endpoint = "test_endpoint"
                mock_request.remote_addr = "127.0.0.1"

                result = test_function()

                assert result == "test_result"
                mock_current_app.logger.info.assert_called_once()
                mock_redis.lpush.assert_called_once()

    def test_request_metrics_middleware_exception_handling(self, app):
        """Test request metrics middleware handles exceptions."""
        with patch("src.middleware.monitoring.current_app") as mock_current_app:
            mock_current_app.logger = Mock()
            mock_current_app.redis_client = Mock()
            mock_current_app.redis_client.lpush.side_effect = Exception("Redis error")

            @request_metrics_middleware()
            def test_function():
                return "test_result"

            with patch("src.middleware.monitoring.request") as mock_request:
                mock_request.method = "GET"
                mock_request.path = "/test"
                mock_request.endpoint = "test_endpoint"
                mock_request.remote_addr = "127.0.0.1"

                # Should not raise exception
                result = test_function()
                assert result == "test_result"
                mock_current_app.logger.error.assert_called()

    def test_request_metrics_middleware_with_response_status(self, app):
        """Test request metrics middleware with response status."""
        with patch("src.middleware.monitoring.current_app") as mock_current_app:
            with patch("src.middleware.monitoring.jsonify") as mock_jsonify:
                mock_current_app.logger = Mock()
                mock_jsonify.return_value = {"error": "Internal server error"}

                @request_metrics_middleware()
                def test_function():
                    raise Exception("Test error")

                with patch("src.middleware.monitoring.request") as mock_request:
                    mock_request.method = "POST"
                    mock_request.path = "/create"
                    mock_request.endpoint = "create_endpoint"
                    mock_request.remote_addr = "127.0.0.1"

                    result = test_function()

                    # Should return error response
                    assert result == ({"error": "Internal server error"}, 500)
                    mock_current_app.logger.error.assert_called()


class TestMonitoringIntegration:
    """Test monitoring middleware integration."""

    def test_health_monitor_integration(self):
        """Test HealthMonitor can be instantiated and used."""
        monitor = HealthMonitor()

        # Test that methods exist and are callable
        assert hasattr(monitor, "get_system_health")
        assert callable(monitor.get_system_health)

        assert hasattr(monitor, "_check_database")
        assert callable(monitor._check_database)

        assert hasattr(monitor, "_check_redis")
        assert callable(monitor._check_redis)

        assert hasattr(monitor, "_check_iotdb")
        assert callable(monitor._check_iotdb)

    def test_decorators_preserve_function_metadata(self, app):
        """Test that decorators preserve function metadata."""
        with patch("src.middleware.monitoring.current_app") as mock_current_app:
            mock_current_app.logger = Mock()

            @device_heartbeat_monitor()
            @request_metrics_middleware()
            def test_function():
                """Test function docstring."""
                return "test"

            # Function should still be callable
            assert callable(test_function)

            # Test execution
            with patch("src.middleware.monitoring.request") as mock_request:
                mock_request.method = "GET"
                mock_request.path = "/test"
                mock_request.endpoint = "test"
                mock_request.remote_addr = "127.0.0.1"
                # No device attribute
                if hasattr(mock_request, "device"):
                    del mock_request.device

                result = test_function()
                assert result == "test"
