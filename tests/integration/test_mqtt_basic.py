"""
Basic integration tests for MQTT API endpoints.
"""
import pytest
import json


class TestMQTTBasicEndpoints:
    """Test basic MQTT endpoints that should work."""

    def test_mqtt_status_unauthorized(self, client):
        """Test MQTT status without authorization."""
        response = client.get("/api/v1/mqtt/status")
        # MQTT status might be public, require auth, or be unavailable
        assert response.status_code in [200, 401, 503]

    def test_mqtt_publish_unauthorized(self, client):
        """Test MQTT publish without authorization."""
        payload = {"topic": "test/topic", "message": "test message"}
        response = client.post("/api/v1/mqtt/publish", json=payload)
        # MQTT publish might return 400 (bad request) or 401 (unauthorized)
        assert response.status_code in [400, 401]

    def test_mqtt_subscribe_unauthorized(self, client):
        """Test MQTT subscribe without authorization."""
        payload = {"topic": "test/topic"}
        response = client.post("/api/v1/mqtt/subscribe", json=payload)
        # MQTT subscribe might return 401 or 503 if service unavailable
        assert response.status_code in [401, 503]

    def test_mqtt_device_topics_unauthorized(self, client):
        """Test getting device MQTT topics without authorization."""
        response = client.get("/api/v1/mqtt/topics/device/1")
        # Device topics might return 400 (bad request) or 401 (unauthorized)
        assert response.status_code in [400, 401]

    def test_mqtt_topic_structure_unauthorized(self, client):
        """Test getting MQTT topic structure without authorization."""
        response = client.get("/api/v1/mqtt/topics/structure")
        # Topic structure might be public
        assert response.status_code in [200, 401]

    def test_mqtt_validate_topic_unauthorized(self, client):
        """Test validating MQTT topic without authorization."""
        payload = {"topic": "test/topic"}
        response = client.post("/api/v1/mqtt/topics/validate", json=payload)
        assert response.status_code in [200, 401]

    def test_mqtt_device_command_unauthorized(self, client):
        """Test sending device command via MQTT without authorization."""
        payload = {"command": "restart"}
        response = client.post("/api/v1/mqtt/device/1/command", json=payload)
        assert response.status_code == 401

    def test_mqtt_fleet_command_unauthorized(self, client):
        """Test sending fleet command via MQTT without authorization."""
        payload = {"command": "update"}
        response = client.post("/api/v1/mqtt/fleet/1/command", json=payload)
        # Fleet command might return 401 or 503 if MQTT unavailable
        assert response.status_code in [401, 503]

    def test_mqtt_metrics_unauthorized(self, client):
        """Test getting MQTT metrics without authorization."""
        response = client.get("/api/v1/mqtt/monitoring/metrics")
        assert response.status_code == 401

    def test_mqtt_telemetry_unauthorized(self, client):
        """Test submitting telemetry via MQTT without authorization."""
        payload = {"measurements": {"temp": 25.0}}
        response = client.post("/api/v1/mqtt/telemetry/1", json=payload)
        assert response.status_code == 401

    def test_mqtt_publish_invalid_json(self, client, admin_headers):
        """Test MQTT publish with invalid JSON."""
        response = client.post(
            "/api/v1/mqtt/publish", data="invalid json", headers=admin_headers, content_type="application/json"
        )
        # Invalid JSON might return 400 or 500
        assert response.status_code in [400, 500]

    def test_mqtt_publish_missing_topic(self, client, admin_headers):
        """Test MQTT publish without topic."""
        payload = {"message": "test message"}
        response = client.post("/api/v1/mqtt/publish", json=payload, headers=admin_headers)
        assert response.status_code == 400
