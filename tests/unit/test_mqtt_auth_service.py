"""
Unit tests for MQTT Authentication Service
Tests device authentication and authorization for MQTT
"""

import pytest
import json
from unittest.mock import Mock, patch, MagicMock
from datetime import datetime, timezone

from src.services.mqtt_auth import MQTTAuthService
from src.models import Device


class TestMQTTAuthService:
    """Test MQTT authentication service"""

    def test_initialization(self):
        """Test service initialization"""
        service = MQTTAuthService()
        assert service.authenticated_devices == {}

    def test_initialization_with_app(self):
        """Test service initialization with Flask app"""
        app = Mock()
        service = MQTTAuthService(app=app)
        assert service.app == app

    def test_authenticate_device_by_api_key_success_mocked(self):
        """Test successful device authentication by API key with mocked database"""
        app = Mock()
        app.app_context.return_value.__enter__ = Mock()
        app.app_context.return_value.__exit__ = Mock()
        app.device_status_cache = Mock()

        mock_device = Mock()
        mock_device.id = 1
        mock_device.name = "Test Device"
        mock_device.status = "active"
        mock_device.update_last_seen = Mock()

        service = MQTTAuthService(app=app)

        with patch("src.services.mqtt_auth.Device") as MockDevice:
            MockDevice.query.filter_by.return_value.first.return_value = mock_device

            authenticated_device = service.authenticate_device_by_api_key("test_api_key_123")

            assert authenticated_device is not None
            assert authenticated_device.id == 1

    def test_authenticate_device_by_api_key_not_found_mocked(self):
        """Test authentication with invalid API key"""
        app = Mock()
        app.app_context.return_value.__enter__ = Mock()
        app.app_context.return_value.__exit__ = Mock()

        service = MQTTAuthService(app=app)

        with patch("src.services.mqtt_auth.Device") as MockDevice:
            MockDevice.query.filter_by.return_value.first.return_value = None

            authenticated_device = service.authenticate_device_by_api_key("invalid_key")

            assert authenticated_device is None

    def test_authenticate_device_by_api_key_no_app(self):
        """Test authentication without Flask app context"""
        service = MQTTAuthService()

        authenticated_device = service.authenticate_device_by_api_key("test_key")

        assert authenticated_device is None

    def test_is_device_authorized_telemetry_topic(self):
        """Test device authorization for telemetry topic"""
        mock_device = Mock()
        mock_device.id = 123
        mock_device.name = "Test Device"

        service = MQTTAuthService()
        service.authenticated_devices[123] = mock_device

        # Test telemetry topic
        assert service.is_device_authorized(123, "iotflow/devices/123/telemetry") is True

        # Test telemetry subtopic
        assert service.is_device_authorized(123, "iotflow/devices/123/telemetry/sensors") is True

    def test_is_device_authorized_status_topic(self):
        """Test device authorization for status topic"""
        mock_device = Mock()
        mock_device.id = 123
        mock_device.name = "Test Device"

        service = MQTTAuthService()
        service.authenticated_devices[123] = mock_device

        # Test status topic
        assert service.is_device_authorized(123, "iotflow/devices/123/status") is True

        # Test status subtopic
        assert service.is_device_authorized(123, "iotflow/devices/123/status/online") is True

    def test_is_device_authorized_unauthorized_topic(self):
        """Test device authorization for unauthorized topic"""
        mock_device = Mock()
        mock_device.id = 123
        mock_device.name = "Test Device"

        service = MQTTAuthService()
        service.authenticated_devices[123] = mock_device

        # Test unauthorized topic
        assert service.is_device_authorized(123, "iotflow/admin/commands") is False

    def test_revoke_device_access(self):
        """Test revoking device access"""
        mock_device = Mock()
        mock_device.id = 123

        service = MQTTAuthService()
        service.authenticated_devices[123] = mock_device

        service.revoke_device_access(123)

        assert 123 not in service.authenticated_devices

    def test_is_device_registered_for_mqtt_missing_api_key(self):
        """Test MQTT registration check with missing API key"""
        service = MQTTAuthService()

        payload = {"temperature": 25.5}  # Missing api_key

        is_authorized, message, device = service.is_device_registered_for_mqtt(payload)

        assert is_authorized is False
        assert "missing" in message.lower()
        assert device is None

    def test_is_device_registered_for_mqtt_success(self):
        """Test successful MQTT registration check"""
        app = Mock()
        app.app_context.return_value.__enter__ = Mock()
        app.app_context.return_value.__exit__ = Mock()
        app.device_status_cache = Mock()

        mock_device = Mock()
        mock_device.id = 1
        mock_device.name = "Test Device"
        mock_device.status = "active"
        mock_device.update_last_seen = Mock()

        service = MQTTAuthService(app=app)

        with patch("src.services.mqtt_auth.Device") as MockDevice:
            MockDevice.query.filter_by.return_value.first.return_value = mock_device

            payload = {"api_key": "test_key_123", "temperature": 25.5}
            is_authorized, message, device = service.is_device_registered_for_mqtt(payload)

            assert is_authorized is True
            assert "authorized" in message.lower()
            assert device is not None
            assert device.id == 1

    def test_is_device_registered_for_mqtt_invalid_key(self):
        """Test MQTT registration check with invalid API key"""
        app = Mock()
        app.app_context.return_value.__enter__ = Mock()
        app.app_context.return_value.__exit__ = Mock()

        service = MQTTAuthService(app=app)

        with patch("src.services.mqtt_auth.Device") as MockDevice:
            MockDevice.query.filter_by.return_value.first.return_value = None

            payload = {"api_key": "invalid_key"}
            is_authorized, message, device = service.is_device_registered_for_mqtt(payload)

            assert is_authorized is False
            assert "invalid" in message.lower() or "not found" in message.lower()
            assert device is None

    def test_validate_device_message_success(self):
        """Test successful device message validation"""
        app = Mock()
        app.app_context.return_value.__enter__ = Mock()
        app.app_context.return_value.__exit__ = Mock()
        app.device_status_cache = Mock()

        mock_device = Mock()
        mock_device.id = 123
        mock_device.name = "Test Device"
        mock_device.status = "active"
        mock_device.update_last_seen = Mock()

        service = MQTTAuthService(app=app)

        with patch("src.services.mqtt_auth.Device") as MockDevice:
            MockDevice.query.filter_by.return_value.first.return_value = mock_device

            device = service.validate_device_message(123, "test_key", "iotflow/devices/123/telemetry")

            assert device is not None
            assert device.id == 123

    def test_validate_device_message_wrong_device_id(self):
        """Test device message validation with mismatched device ID"""
        app = Mock()
        app.app_context.return_value.__enter__ = Mock()
        app.app_context.return_value.__exit__ = Mock()

        mock_device = Mock()
        mock_device.id = 456  # Different from requested
        mock_device.name = "Test Device"
        mock_device.status = "active"
        mock_device.update_last_seen = Mock()

        service = MQTTAuthService(app=app)

        with patch("src.services.mqtt_auth.Device") as MockDevice:
            MockDevice.query.filter_by.return_value.first.return_value = mock_device

            device = service.validate_device_message(123, "test_key", "iotflow/devices/123/telemetry")

            assert device is None

    def test_validate_device_message_unauthorized_topic(self):
        """Test device message validation with unauthorized topic"""
        app = Mock()
        app.app_context.return_value.__enter__ = Mock()
        app.app_context.return_value.__exit__ = Mock()
        app.device_status_cache = Mock()

        mock_device = Mock()
        mock_device.id = 123
        mock_device.name = "Test Device"
        mock_device.status = "active"
        mock_device.update_last_seen = Mock()

        service = MQTTAuthService(app=app)

        with patch("src.services.mqtt_auth.Device") as MockDevice:
            MockDevice.query.filter_by.return_value.first.return_value = mock_device

            device = service.validate_device_message(123, "test_key", "iotflow/admin/commands")

            assert device is None

    def test_handle_telemetry_message_structured_format(self):
        """Test handling telemetry message with structured format"""
        app = Mock()
        app.app_context.return_value.__enter__ = Mock()
        app.app_context.return_value.__exit__ = Mock()
        app.device_status_cache = Mock()

        mock_device = Mock()
        mock_device.id = 123
        mock_device.name = "Test Device"
        mock_device.device_type = "sensor"
        mock_device.user_id = "user1"
        mock_device.status = "active"
        mock_device.update_last_seen = Mock()

        mock_iotdb = Mock()
        mock_iotdb.write_telemetry_data.return_value = True

        service = MQTTAuthService(iotdb_service=mock_iotdb, app=app)

        with patch("src.services.mqtt_auth.Device") as MockDevice:
            MockDevice.query.filter_by.return_value.first.return_value = mock_device

            payload = json.dumps(
                {
                    "api_key": "test_key",
                    "data": {"temperature": 25.5, "humidity": 60},
                    "metadata": {"location": "room1"},
                    "timestamp": "2024-01-15T10:30:00Z",
                }
            )

            result = service.handle_telemetry_message(123, "test_key", "iotflow/devices/123/telemetry", payload)

            assert result is True
            mock_iotdb.write_telemetry_data.assert_called_once()

    def test_handle_telemetry_message_flat_format(self):
        """Test handling telemetry message with flat format"""
        app = Mock()
        app.app_context.return_value.__enter__ = Mock()
        app.app_context.return_value.__exit__ = Mock()
        app.device_status_cache = Mock()

        mock_device = Mock()
        mock_device.id = 123
        mock_device.name = "Test Device"
        mock_device.device_type = "sensor"
        mock_device.user_id = "user1"
        mock_device.status = "active"
        mock_device.update_last_seen = Mock()

        mock_iotdb = Mock()
        mock_iotdb.write_telemetry_data.return_value = True

        service = MQTTAuthService(iotdb_service=mock_iotdb, app=app)

        with patch("src.services.mqtt_auth.Device") as MockDevice:
            MockDevice.query.filter_by.return_value.first.return_value = mock_device

            payload = json.dumps(
                {"api_key": "test_key", "temperature": 25.5, "humidity": 60, "ts": "2024-01-15T10:30:00Z"}
            )

            result = service.handle_telemetry_message(123, "test_key", "iotflow/devices/123/telemetry", payload)

            assert result is True
            mock_iotdb.write_telemetry_data.assert_called_once()

    def test_handle_telemetry_message_invalid_json(self):
        """Test handling telemetry message with invalid JSON"""
        app = Mock()
        app.app_context.return_value.__enter__ = Mock()
        app.app_context.return_value.__exit__ = Mock()

        mock_device = Mock()
        mock_device.id = 123
        mock_device.name = "Test Device"
        mock_device.device_type = "sensor"
        mock_device.user_id = "user1"
        mock_device.status = "active"
        mock_device.update_last_seen = Mock()

        service = MQTTAuthService(app=app)

        with patch("src.services.mqtt_auth.Device") as MockDevice:
            MockDevice.query.filter_by.return_value.first.return_value = mock_device

            payload = "invalid json {"

            result = service.handle_telemetry_message(123, "test_key", "iotflow/devices/123/telemetry", payload)

            assert result is False

    def test_handle_telemetry_message_no_data(self):
        """Test handling telemetry message with no data"""
        app = Mock()
        app.app_context.return_value.__enter__ = Mock()
        app.app_context.return_value.__exit__ = Mock()
        app.device_status_cache = Mock()

        mock_device = Mock()
        mock_device.id = 123
        mock_device.name = "Test Device"
        mock_device.device_type = "sensor"
        mock_device.user_id = "user1"
        mock_device.status = "active"
        mock_device.update_last_seen = Mock()

        service = MQTTAuthService(app=app)

        with patch("src.services.mqtt_auth.Device") as MockDevice:
            MockDevice.query.filter_by.return_value.first.return_value = mock_device

            payload = json.dumps({"api_key": "test_key"})

            result = service.handle_telemetry_message(123, "test_key", "iotflow/devices/123/telemetry", payload)

            assert result is False

    def test_handle_telemetry_message_iotdb_failure(self):
        """Test handling telemetry message when IoTDB write fails"""
        app = Mock()
        app.app_context.return_value.__enter__ = Mock()
        app.app_context.return_value.__exit__ = Mock()
        app.device_status_cache = None  # No cache available

        mock_device = Mock()
        mock_device.id = 123
        mock_device.name = "Test Device"
        mock_device.device_type = "sensor"
        mock_device.user_id = "user1"
        mock_device.status = "active"
        mock_device.update_last_seen = Mock()

        mock_iotdb = Mock()
        mock_iotdb.write_telemetry_data.return_value = False

        service = MQTTAuthService(iotdb_service=mock_iotdb, app=app)

        with patch("src.services.mqtt_auth.Device") as MockDevice:
            MockDevice.query.filter_by.return_value.first.return_value = mock_device

            payload = json.dumps({"api_key": "test_key", "temperature": 25.5})

            result = service.handle_telemetry_message(123, "test_key", "iotflow/devices/123/telemetry", payload)

            # When IoTDB write fails, the function returns False
            assert result is False

    def test_get_device_credentials_success(self):
        """Test getting device credentials"""
        mock_device = Mock()
        mock_device.id = 123
        mock_device.name = "Test Device"
        mock_device.api_key = "test_key_123"

        service = MQTTAuthService()

        with patch("src.services.mqtt_auth.Device") as MockDevice:
            MockDevice.query.filter_by.return_value.first.return_value = mock_device

            credentials = service.get_device_credentials(123)

            assert credentials is not None
            assert credentials["username"] == "123"
            assert credentials["password"] == "test_key_123"
            assert "device_123" in credentials["client_id"]

    def test_get_device_credentials_not_found(self):
        """Test getting credentials for non-existent device"""
        service = MQTTAuthService()

        with patch("src.services.mqtt_auth.Device") as MockDevice:
            MockDevice.query.filter_by.return_value.first.return_value = None

            credentials = service.get_device_credentials(999)

            assert credentials is None

    def test_cleanup_inactive_devices(self):
        """Test cleaning up inactive devices from cache"""
        mock_active_device = Mock()
        mock_active_device.id = 1
        mock_active_device.status = "active"

        service = MQTTAuthService()
        service.authenticated_devices[1] = mock_active_device
        service.authenticated_devices[2] = Mock()  # Will be removed

        with patch("src.services.mqtt_auth.Device") as MockDevice:

            def query_side_effect(id, status):
                if id == 1:
                    return Mock(first=lambda: mock_active_device)
                return Mock(first=lambda: None)

            MockDevice.query.filter_by.side_effect = query_side_effect

            service.cleanup_inactive_devices()

            # Device 1 should remain, device 2 should be removed
            assert 1 in service.authenticated_devices

    def test_validate_device_registration_success(self):
        """Test successful device registration validation"""
        app = Mock()
        app.app_context.return_value.__enter__ = Mock()
        app.app_context.return_value.__exit__ = Mock()

        mock_device = Mock()
        mock_device.id = 123
        mock_device.status = "active"
        mock_device.update_last_seen = Mock()

        service = MQTTAuthService(app=app)

        with patch("src.services.mqtt_auth.Device") as MockDevice:
            MockDevice.query.filter_by.return_value.first.return_value = mock_device

            is_valid, message = service.validate_device_registration(123, "test_key")

            assert is_valid is True
            assert "validated" in message.lower() or "successful" in message.lower()

    def test_validate_device_registration_not_found(self):
        """Test device registration validation for non-existent device"""
        app = Mock()
        app.app_context.return_value.__enter__ = Mock()
        app.app_context.return_value.__exit__ = Mock()

        service = MQTTAuthService(app=app)

        with patch("src.services.mqtt_auth.Device") as MockDevice:
            MockDevice.query.filter_by.return_value.first.return_value = None

            is_valid, message = service.validate_device_registration(123, "test_key")

            assert is_valid is False
            assert "not found" in message.lower() or "invalid" in message.lower()

    def test_validate_device_registration_inactive_device(self):
        """Test device registration validation for inactive device"""
        app = Mock()
        app.app_context.return_value.__enter__ = Mock()
        app.app_context.return_value.__exit__ = Mock()

        mock_device = Mock()
        mock_device.id = 123
        mock_device.status = "inactive"
        mock_device.update_last_seen = Mock()

        service = MQTTAuthService(app=app)

        with patch("src.services.mqtt_auth.Device") as MockDevice:
            MockDevice.query.filter_by.return_value.first.return_value = mock_device

            is_valid, message = service.validate_device_registration(123, "test_key")

            # Should still be valid (inactive devices allowed)
            assert is_valid is True

    def test_validate_device_registration_no_app(self):
        """Test device registration validation without app context"""
        service = MQTTAuthService()

        is_valid, message = service.validate_device_registration(123, "test_key")

        assert is_valid is False
        assert "no flask app" in message.lower() or "context" in message.lower()

    def test_is_device_authorized_commands_topic(self):
        """Test device authorization for commands topic"""
        mock_device = Mock()
        mock_device.id = 123
        mock_device.name = "Test Device"

        service = MQTTAuthService()
        service.authenticated_devices[123] = mock_device

        assert service.is_device_authorized(123, "iotflow/devices/123/commands") is True

    def test_is_device_authorized_config_topic(self):
        """Test device authorization for config topic"""
        mock_device = Mock()
        mock_device.id = 123
        mock_device.name = "Test Device"

        service = MQTTAuthService()
        service.authenticated_devices[123] = mock_device

        assert service.is_device_authorized(123, "iotflow/devices/123/config") is True

    def test_is_device_authorized_heartbeat_topic(self):
        """Test device authorization for heartbeat topic"""
        mock_device = Mock()
        mock_device.id = 123
        mock_device.name = "Test Device"

        service = MQTTAuthService()
        service.authenticated_devices[123] = mock_device

        assert service.is_device_authorized(123, "iotflow/devices/123/heartbeat") is True

    def test_is_device_authorized_device_not_in_cache(self):
        """Test device authorization when device not in cache"""
        mock_device = Mock()
        mock_device.id = 123
        mock_device.name = "Test Device"

        service = MQTTAuthService()

        with patch("src.services.mqtt_auth.Device") as MockDevice:
            MockDevice.query.filter_by.return_value.first.return_value = mock_device

            result = service.is_device_authorized(123, "iotflow/devices/123/telemetry")

            assert result is True
            assert 123 in service.authenticated_devices

    def test_is_device_authorized_device_not_found(self):
        """Test device authorization when device doesn't exist"""
        service = MQTTAuthService()

        with patch("src.services.mqtt_auth.Device") as MockDevice:
            MockDevice.query.filter_by.return_value.first.return_value = None

            result = service.is_device_authorized(999, "iotflow/devices/999/telemetry")

            assert result is False
