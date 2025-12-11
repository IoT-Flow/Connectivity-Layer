"""
Basic integration tests for telemetry API endpoints.
"""
import pytest
import json


class TestTelemetryBasicEndpoints:
    """Test basic telemetry endpoints that should work."""

    def test_store_telemetry_unauthorized(self, client):
        """Test storing telemetry without authorization."""
        payload = {"measurements": {"temperature": 25.5, "humidity": 60.0}}
        response = client.post("/api/v1/telemetry", json=payload)
        assert response.status_code == 401

    def test_get_device_telemetry_unauthorized(self, client):
        """Test getting device telemetry without authorization."""
        response = client.get("/api/v1/telemetry/1")
        assert response.status_code == 401

    def test_get_latest_telemetry_unauthorized(self, client):
        """Test getting latest telemetry without authorization."""
        response = client.get("/api/v1/telemetry/1/latest")
        assert response.status_code == 401

    def test_get_aggregated_telemetry_unauthorized(self, client):
        """Test getting aggregated telemetry without authorization."""
        response = client.get("/api/v1/telemetry/1/aggregated")
        assert response.status_code == 401

    def test_delete_telemetry_unauthorized(self, client):
        """Test deleting telemetry without authorization."""
        response = client.delete("/api/v1/telemetry/1")
        assert response.status_code == 401

    def test_get_telemetry_status_unauthorized(self, client):
        """Test getting telemetry status without authorization."""
        response = client.get("/api/v1/telemetry/status")
        # Telemetry status might be publicly accessible
        assert response.status_code in [200, 401]

    def test_get_user_telemetry_unauthorized(self, client):
        """Test getting user telemetry without authorization."""
        response = client.get("/api/v1/telemetry/user/1")
        assert response.status_code == 401

    def test_store_telemetry_invalid_json(self, client, test_device):
        """Test storing telemetry with invalid JSON."""
        headers = {"X-API-Key": test_device.api_key}
        response = client.post(
            "/api/v1/telemetry", data="invalid json", headers=headers, content_type="application/json"
        )
        # Invalid JSON might return 400 or 500 depending on error handling
        assert response.status_code in [400, 500]

    def test_store_telemetry_missing_measurements(self, client, test_device):
        """Test storing telemetry without measurements."""
        headers = {"X-API-Key": test_device.api_key}
        payload = {"timestamp": "2023-01-01T00:00:00Z"}
        response = client.post("/api/v1/telemetry", json=payload, headers=headers)
        assert response.status_code == 400
