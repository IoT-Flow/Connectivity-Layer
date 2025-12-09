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
