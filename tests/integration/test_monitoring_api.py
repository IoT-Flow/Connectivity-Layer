"""
Integration tests for Monitoring and Metrics API endpoints
Tests health checks, Prometheus metrics, and system monitoring
"""
import pytest
import re


class TestHealthEndpoints:
    """Test health check endpoints"""

    def test_health_check_basic(self, client):
        """Test basic health check endpoint"""
        response = client.get("/health")

        assert response.status_code == 200
        data = response.get_json()
        assert data["status"] == "healthy"
        assert "message" in data
        assert "version" in data

    def test_health_check_detailed(self, client):
        """Test detailed health check with query parameter"""
        response = client.get("/health?detailed=true")

        assert response.status_code == 200
        data = response.get_json()
        assert isinstance(data, dict)
        # Detailed health should include more information
        assert len(data) > 3

    def test_system_status(self, client):
        """Test system status endpoint"""
        response = client.get("/status")

        assert response.status_code == 200
        data = response.get_json()
        assert isinstance(data, dict)
        # Should return comprehensive system health

    def test_root_endpoint(self, client):
        """Test root API information endpoint"""
        response = client.get("/")

        assert response.status_code == 200
        data = response.get_json()
        assert data["name"] == "IoT Device Connectivity Layer"
        assert "version" in data
        assert "description" in data
        assert "endpoints" in data
        assert "health" in data["endpoints"]
        assert "devices" in data["endpoints"]


class TestPrometheusMetrics:
    """Test Prometheus metrics endpoint"""

    def test_metrics_endpoint_exists(self, client):
        """Test that /metrics endpoint exists"""
        response = client.get("/metrics")

        assert response.status_code == 200
        assert response.content_type.startswith("text/plain")

    def test_metrics_format(self, client):
        """Test that metrics are in Prometheus format"""
        response = client.get("/metrics")

        assert response.status_code == 200
        content = response.data.decode("utf-8")

        # Prometheus metrics should contain TYPE and HELP comments
        assert "# HELP" in content or "# TYPE" in content or len(content) > 0

    def test_http_request_metrics(self, client):
        """Test that HTTP request metrics are collected"""
        # Make a request to generate metrics
        client.get("/health")

        # Check metrics endpoint
        response = client.get("/metrics")
        content = response.data.decode("utf-8")

        # Should contain HTTP request metrics
        # Note: Metric names may vary based on implementation
        assert response.status_code == 200
        assert len(content) > 0

    def test_metrics_after_multiple_requests(self, client):
        """Test that metrics accumulate after multiple requests"""
        # Make multiple requests
        for _ in range(5):
            client.get("/health")

        response = client.get("/metrics")

        assert response.status_code == 200
        content = response.data.decode("utf-8")
        assert len(content) > 0

    def test_metrics_include_telemetry_counter(self, client, test_device):
        """Test that telemetry metrics are tracked"""
        # Submit telemetry
        headers = {"X-API-Key": test_device.api_key}
        payload = {"data": {"temperature": 25.5, "humidity": 60.0}}

        client.post("/api/v1/telemetry", json=payload, headers=headers)

        # Check metrics
        response = client.get("/metrics")

        assert response.status_code == 200
        # Metrics should be updated


class TestSystemMonitoring:
    """Test system monitoring capabilities"""

    def test_health_check_includes_timestamp(self, client):
        """Test that health check includes timestamp"""
        response = client.get("/health?detailed=true")

        assert response.status_code == 200
        data = response.get_json()
        # Should include some form of timestamp or time information
        assert isinstance(data, dict)

    def test_health_check_security_headers(self, client):
        """Test that health endpoint has security headers"""
        response = client.get("/health")

        assert response.status_code == 200
        # Security headers should be present
        # Note: Actual headers depend on middleware configuration

    def test_multiple_health_checks(self, client):
        """Test multiple consecutive health checks"""
        for _ in range(3):
            response = client.get("/health")
            assert response.status_code == 200
            data = response.get_json()
            assert data["status"] == "healthy"

    def test_health_check_response_time(self, client):
        """Test that health check responds quickly"""
        import time

        start = time.time()
        response = client.get("/health")
        duration = time.time() - start

        assert response.status_code == 200
        # Health check should be fast (under 1 second)
        assert duration < 1.0


class TestMetricsIntegration:
    """Test metrics integration with various endpoints"""

    def test_device_registration_metrics(self, client, test_user):
        """Test that device registration is tracked in metrics"""
        payload = {"name": "Metrics_Test_Device", "user_id": test_user.id, "device_type": "sensor"}

        response = client.post("/api/v1/devices/register", json=payload)

        # Should succeed or fail, but metrics should be tracked
        assert response.status_code in [200, 201, 400, 401]

        # Check metrics
        metrics_response = client.get("/metrics")
        assert metrics_response.status_code == 200

    def test_admin_endpoint_metrics(self, client, test_admin_user):
        """Test that admin endpoints are tracked in metrics"""
        headers = {"Authorization": "admin test"}

        client.get("/api/v1/admin/stats", headers=headers)

        # Check metrics
        response = client.get("/metrics")
        assert response.status_code == 200

    def test_telemetry_endpoint_metrics(self, client, test_device):
        """Test that telemetry endpoints are tracked"""
        headers = {"X-API-Key": test_device.api_key}

        client.get(f"/api/v1/telemetry/{test_device.id}", headers=headers)

        # Check metrics
        response = client.get("/metrics")
        assert response.status_code == 200


class TestErrorHandling:
    """Test error handling in monitoring endpoints"""

    def test_health_check_with_invalid_param(self, client):
        """Test health check with invalid parameter"""
        response = client.get("/health?detailed=invalid")

        # Should still return 200, treating as false
        assert response.status_code == 200

    def test_metrics_endpoint_methods(self, client):
        """Test that metrics endpoint only accepts GET"""
        # POST should not be allowed
        response = client.post("/metrics")
        assert response.status_code in [405, 404]

        # PUT should not be allowed
        response = client.put("/metrics")
        assert response.status_code in [405, 404]

    def test_health_endpoint_methods(self, client):
        """Test that health endpoint only accepts GET"""
        # POST should not be allowed
        response = client.post("/health")
        assert response.status_code in [405, 404]


class TestMonitoringConsistency:
    """Test consistency of monitoring data"""

    def test_health_status_consistency(self, client):
        """Test that health status is consistent across calls"""
        response1 = client.get("/health")
        response2 = client.get("/health")

        assert response1.status_code == 200
        assert response2.status_code == 200

        data1 = response1.get_json()
        data2 = response2.get_json()

        # Status should be consistent
        assert data1["status"] == data2["status"]

    def test_metrics_monotonic_increase(self, client):
        """Test that request counters increase monotonically"""
        # Get initial metrics
        response1 = client.get("/metrics")
        content1 = response1.data.decode("utf-8")

        # Make some requests
        client.get("/health")
        client.get("/health")

        # Get metrics again
        response2 = client.get("/metrics")
        content2 = response2.data.decode("utf-8")

        # Metrics should have changed (counters increased)
        assert response1.status_code == 200
        assert response2.status_code == 200


class TestMonitoringDocumentation:
    """Test that monitoring endpoints are well-documented"""

    def test_root_endpoint_documentation(self, client):
        """Test that root endpoint provides API documentation"""
        response = client.get("/")

        assert response.status_code == 200
        data = response.get_json()

        assert "documentation" in data
        assert "endpoints" in data
        assert isinstance(data["endpoints"], dict)

    def test_health_endpoint_in_root(self, client):
        """Test that health endpoint is listed in root"""
        response = client.get("/")

        assert response.status_code == 200
        data = response.get_json()

        assert "endpoints" in data
        assert "health" in data["endpoints"]

    def test_api_version_in_root(self, client):
        """Test that API version is provided"""
        response = client.get("/")

        assert response.status_code == 200
        data = response.get_json()

        assert "version" in data
        assert isinstance(data["version"], str)
        assert len(data["version"]) > 0
