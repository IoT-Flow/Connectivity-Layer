"""
Basic integration tests for control API endpoints.
"""
import pytest
import json


class TestControlBasicEndpoints:
    """Test basic control endpoints that should work."""

    def test_send_control_command_unauthorized(self, client):
        """Test sending control command without authorization."""
        payload = {"command": "RESTART", "parameters": {}}
        response = client.post("/api/v1/devices/1/control", json=payload)
        assert response.status_code == 401

    def test_get_pending_controls_unauthorized(self, client):
        """Test getting pending controls without authorization."""
        response = client.get("/api/v1/devices/1/control/pending")
        assert response.status_code == 401

    def test_update_control_status_unauthorized(self, client):
        """Test updating control status without authorization."""
        payload = {"status": "completed"}
        response = client.post("/api/v1/devices/1/control/1/status", json=payload)
        assert response.status_code == 401

    def test_send_control_command_invalid_json(self, client, test_device):
        """Test sending control command with invalid JSON."""
        headers = {"X-API-Key": test_device.api_key}
        response = client.post(
            f"/api/v1/devices/{test_device.id}/control",
            data="invalid json",
            headers=headers,
            content_type="application/json",
        )
        assert response.status_code == 400

    def test_send_control_command_missing_command_field(self, client, test_device):
        """Test sending control command without command field."""
        headers = {"X-API-Key": test_device.api_key}
        payload = {"parameters": {"setting": "value"}}
        response = client.post(f"/api/v1/devices/{test_device.id}/control", json=payload, headers=headers)
        assert response.status_code == 400

    def test_update_control_status_invalid_json(self, client, test_device):
        """Test updating control status with invalid JSON."""
        headers = {"X-API-Key": test_device.api_key}
        response = client.post(
            f"/api/v1/devices/{test_device.id}/control/1/status",
            data="invalid json",
            headers=headers,
            content_type="application/json",
        )
        assert response.status_code == 400
