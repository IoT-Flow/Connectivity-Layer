"""
Unit tests for service status metrics (IoTDB, Redis, MQTT, API).
Following TDD approach - tests written first, then implementation.
"""
import pytest
from unittest.mock import patch, MagicMock
from src.metrics import (
    REDIS_STATUS,
    MQTT_CONNECTIONS_ACTIVE,
    APP_UPTIME_SECONDS,
)


class TestServiceStatusMetrics:
    """Test service status metrics definitions"""

    def test_redis_status_metric_exists(self):
        """Test that Redis status metric is defined"""
        assert hasattr(REDIS_STATUS, "_name")
        assert REDIS_STATUS._name == "redis_status"
        assert REDIS_STATUS._type == "gauge"

    def test_mqtt_connections_metric_exists(self):
        """Test that MQTT connections metric exists"""
        assert hasattr(MQTT_CONNECTIONS_ACTIVE, "_name")
        assert MQTT_CONNECTIONS_ACTIVE._name == "mqtt_connections_active"
        assert MQTT_CONNECTIONS_ACTIVE._type == "gauge"

    def test_app_uptime_metric_exists(self):
        """Test that application uptime metric is defined"""
        assert hasattr(APP_UPTIME_SECONDS, "_name")
        assert APP_UPTIME_SECONDS._name == "app_uptime_seconds"
        assert APP_UPTIME_SECONDS._type == "gauge"

    def test_iotdb_status_metric_exists(self):
        """Test that IoTDB connection status metric exists"""
        from src.metrics import IOTDB_CONNECTION_STATUS

        assert hasattr(IOTDB_CONNECTION_STATUS, "_name")
        assert IOTDB_CONNECTION_STATUS._name == "iotdb_connection_status"
        assert IOTDB_CONNECTION_STATUS._type == "gauge"

    def test_iotdb_query_success_metric_exists(self):
        """Test that IoTDB query success rate metric exists"""
        from src.metrics import IOTDB_QUERY_SUCCESS_RATE

        assert hasattr(IOTDB_QUERY_SUCCESS_RATE, "_name")
        assert IOTDB_QUERY_SUCCESS_RATE._name == "iotdb_query_success_rate"


class TestServiceMetricsCollection:
    """Test service metrics collection"""

    def test_redis_status_collection(self):
        """Test Redis status is collected and set"""
        from src.services.redis_metrics import RedisMetricsCollector

        collector = RedisMetricsCollector()
        assert hasattr(collector, "collect_redis_status")

    def test_mqtt_status_collection(self):
        """Test MQTT status is collected"""
        from src.services.mqtt_metrics import MQTTMetricsCollector

        collector = MQTTMetricsCollector()
        assert hasattr(collector, "collect_mqtt_status")

    def test_iotdb_status_collection(self):
        """Test IoTDB status is collected"""
        from src.services.iotdb_metrics import IoTDBMetricsCollector

        collector = IoTDBMetricsCollector()
        assert hasattr(collector, "collect_iotdb_status")


class TestServiceMetricsEndpoint:
    """Test service metrics in /metrics endpoint"""

    def test_service_metrics_in_prometheus_output(self):
        """Test that service status metrics appear in Prometheus output"""
        from prometheus_client import generate_latest

        output = generate_latest().decode("utf-8")

        # Check for service metrics
        assert "redis_status" in output
        assert "mqtt_connections_active" in output
        assert "iotdb_connection_status" in output
        assert "app_uptime_seconds" in output

    def test_service_status_values_are_binary(self):
        """Test that status values are 0 or 1"""
        from prometheus_client import generate_latest

        output = generate_latest().decode("utf-8")
        lines = output.split("\n")

        for line in lines:
            if line.startswith("redis_status ") or line.startswith("iotdb_connection_status "):
                value = float(line.split()[-1])
                assert value in [0.0, 1.0], f"Status value should be 0 or 1, got {value}"
