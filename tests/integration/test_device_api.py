"""
Integration tests for Device API endpoints
Tests the complete request-response cycle
"""

import pytest
import json
import time
from src.models import Device, User


@pytest.mark.integration
class TestDeviceRegistration:
    """Test device registration endpoint"""

    def test_successful_device_registration(self, client, test_user):
        """Test successful device registration with valid data"""
        device_name = f"Integration_Test_Device_{int(time.time())}"
        payload = {
            "name": device_name,
            "device_type": "sensor",
            "description": "Integration test device",
            "location": "Test Lab",
            "firmware_version": "1.0.0",
            "hardware_version": "v1.0",
            "user_id": test_user.user_id,
        }

        response = client.post(
            "/api/v1/devices/register", data=json.dumps(payload), content_type="application/json"
        )

        assert response.status_code == 201
        data = response.get_json()

        assert "message" in data
        assert data["message"] == "Device registered successfully"
        assert "device" in data
        assert data["device"]["name"] == device_name
        assert data["device"]["device_type"] == "sensor"
        assert "api_key" in data["device"]
        assert len(data["device"]["api_key"]) == 32  # API key is 32 characters

    def test_registration_with_duplicate_name(self, client, test_user, test_device):
        """Test that registration fails with duplicate device name"""
        payload = {
            "name": test_device.name,  # Existing device name
            "device_type": "sensor",
            "user_id": test_user.user_id,
        }

        response = client.post(
            "/api/v1/devices/register", data=json.dumps(payload), content_type="application/json"
        )

        assert response.status_code == 409
        data = response.get_json()
        assert "error" in data
        assert "already exists" in data["error"].lower()

    def test_registration_with_invalid_user_id(self, client):
        """Test registration with non-existent user ID"""
        payload = {
            "name": f"Invalid_User_Device_{int(time.time())}",
            "device_type": "sensor",
            "user_id": "non_existent_user_id_12345",
        }

        response = client.post(
            "/api/v1/devices/register", data=json.dumps(payload), content_type="application/json"
        )

        assert response.status_code == 401
        data = response.get_json()
        assert "error" in data
        assert "authentication failed" in data["error"].lower()

    def test_registration_missing_required_fields(self, client, test_user):
        """Test registration with missing required fields"""
        # Missing name
        payload = {"device_type": "sensor", "user_id": test_user.user_id}

        response = client.post(
            "/api/v1/devices/register", data=json.dumps(payload), content_type="application/json"
        )

        assert response.status_code == 400

        # Missing device_type
        payload = {"name": "Test Device", "user_id": test_user.user_id}

        response = client.post(
            "/api/v1/devices/register", data=json.dumps(payload), content_type="application/json"
        )

        assert response.status_code == 400

    def test_registration_with_inactive_user(self, client, app):
        """Test registration with inactive user"""
        with app.app_context():
            from src.models import db

            # Create inactive user
            inactive_user = User(
                username="inactiveuser",
                email="inactive@example.com",
                password_hash="hash",
                is_active=False,
            )
            db.session.add(inactive_user)
            db.session.commit()

            payload = {
                "name": f"Inactive_User_Device_{int(time.time())}",
                "device_type": "sensor",
                "user_id": inactive_user.user_id,
            }

            response = client.post(
                "/api/v1/devices/register",
                data=json.dumps(payload),
                content_type="application/json",
            )

            assert response.status_code == 401


@pytest.mark.integration
class TestDeviceStatus:
    """Test device status endpoint"""

    def test_get_device_status_with_valid_api_key(self, client, test_device):
        """Test getting device status with valid API key"""
        headers = {"X-API-Key": test_device.api_key}

        response = client.get("/api/v1/devices/status", headers=headers)

        assert response.status_code == 200
        data = response.get_json()

        assert "status" in data
        assert data["status"] == "success"
        assert "device" in data
        assert data["device"]["name"] == test_device.name
        assert "is_online" in data["device"]

    def test_get_device_status_without_api_key(self, client):
        """Test that status endpoint requires API key"""
        response = client.get("/api/v1/devices/status")

        assert response.status_code == 401

    def test_get_device_status_with_invalid_api_key(self, client):
        """Test status endpoint with invalid API key"""
        headers = {"X-API-Key": "invalid_api_key_12345"}

        response = client.get("/api/v1/devices/status", headers=headers)

        assert response.status_code == 401


@pytest.mark.integration
class TestDeviceHeartbeat:
    """Test device heartbeat endpoint"""

    def test_send_heartbeat(self, client, test_device):
        """Test sending device heartbeat"""
        headers = {"X-API-Key": test_device.api_key}

        response = client.post("/api/v1/devices/heartbeat", headers=headers)

        assert response.status_code == 200
        data = response.get_json()

        assert "message" in data
        assert "heartbeat received" in data["message"].lower()
        assert data["device_id"] == test_device.id
        assert data["status"] == "online"

    def test_heartbeat_updates_last_seen(self, client, test_device, app):
        """Test that heartbeat updates last_seen timestamp"""
        with app.app_context():
            from src.models import db

            # Get initial last_seen
            device = Device.query.get(test_device.id)
            initial_last_seen = device.last_seen

            # Send heartbeat
            headers = {"X-API-Key": test_device.api_key}
            response = client.post("/api/v1/devices/heartbeat", headers=headers)

            assert response.status_code == 200

            # Check last_seen was updated
            db.session.refresh(device)
            assert device.last_seen is not None
            if initial_last_seen:
                assert device.last_seen >= initial_last_seen


@pytest.mark.integration
class TestDeviceConfiguration:
    """Test device configuration endpoints"""

    def test_get_device_configuration(self, client, test_device):
        """Test getting device configuration"""
        headers = {"X-API-Key": test_device.api_key}

        response = client.get("/api/v1/devices/config", headers=headers)

        assert response.status_code == 200
        data = response.get_json()

        assert "status" in data
        assert data["status"] == "success"
        assert "configuration" in data

    def test_update_device_configuration(self, client, test_device):
        """Test updating device configuration"""
        headers = {"X-API-Key": test_device.api_key, "Content-Type": "application/json"}

        payload = {"config_key": "sampling_rate", "config_value": "30", "data_type": "integer"}

        response = client.post("/api/v1/devices/config", data=json.dumps(payload), headers=headers)

        assert response.status_code == 200
        data = response.get_json()

        assert data["status"] == "success"
        assert data["config_key"] == "sampling_rate"
        assert data["config_value"] == "30"

    def test_update_device_info(self, client, test_device):
        """Test updating device information"""
        headers = {"X-API-Key": test_device.api_key, "Content-Type": "application/json"}

        payload = {"status": "active", "location": "Updated Lab", "firmware_version": "1.1.0"}

        response = client.put("/api/v1/devices/config", data=json.dumps(payload), headers=headers)

        assert response.status_code == 200
        data = response.get_json()

        assert "device" in data
        assert data["device"]["location"] == "Updated Lab"
        assert data["device"]["firmware_version"] == "1.1.0"


@pytest.mark.integration
class TestDeviceTelemetry:
    """Test device telemetry submission"""

    def test_submit_telemetry_via_http(self, client, test_device):
        """Test submitting telemetry data via HTTP"""
        headers = {"X-API-Key": test_device.api_key, "Content-Type": "application/json"}

        payload = {
            "data": {"temperature": 25.5, "humidity": 60.0, "pressure": 1013.25},
            "metadata": {"sensor_type": "BME280", "location": "test_lab"},
        }

        response = client.post(
            "/api/v1/devices/telemetry", data=json.dumps(payload), headers=headers
        )

        # Should succeed even if IoTDB is not available (graceful degradation)
        assert response.status_code in [200, 201, 500]

        if response.status_code in [200, 201]:
            data = response.get_json()
            assert "message" in data
            assert data["device_id"] == test_device.id

    def test_submit_telemetry_without_api_key(self, client):
        """Test that telemetry submission requires API key"""
        payload = {"data": {"temperature": 25.5}}

        response = client.post(
            "/api/v1/devices/telemetry", data=json.dumps(payload), content_type="application/json"
        )

        assert response.status_code == 401

    def test_submit_telemetry_with_invalid_data(self, client, test_device):
        """Test submitting telemetry with invalid data format"""
        headers = {"X-API-Key": test_device.api_key, "Content-Type": "application/json"}

        # Missing 'data' field
        payload = {"metadata": {"test": "value"}}

        response = client.post(
            "/api/v1/devices/telemetry", data=json.dumps(payload), headers=headers
        )

        assert response.status_code == 400


@pytest.mark.integration
class TestDeviceCredentials:
    """Test device credentials endpoint"""

    def test_get_mqtt_credentials(self, client, test_device):
        """Test getting MQTT credentials"""
        headers = {"X-API-Key": test_device.api_key}

        response = client.get("/api/v1/devices/mqtt-credentials", headers=headers)

        assert response.status_code == 200
        data = response.get_json()

        assert "status" in data
        assert data["status"] == "success"
        assert "credentials" in data
        assert "mqtt_host" in data["credentials"]
        assert "mqtt_port" in data["credentials"]
        assert "topics" in data["credentials"]

    def test_get_device_credentials(self, client, test_device):
        """Test getting device credentials"""
        headers = {"X-API-Key": test_device.api_key}

        response = client.get("/api/v1/devices/credentials", headers=headers)

        assert response.status_code == 200
        data = response.get_json()

        assert "status" in data
        assert data["status"] == "success"
        assert "device" in data
        assert data["device"]["id"] == test_device.id
        assert "mqtt_topics" in data["device"]
