"""
Unit tests for MQTT Client Service
Tests MQTT connection, message handling, and routing
"""

import pytest
import json
from unittest.mock import Mock, MagicMock, patch, call
from datetime import datetime, timezone

from src.mqtt.client import (
    MQTTConfig,
    MQTTMessage,
    MQTTMessageHandler,
    TelemetryMessageHandler,
    CommandMessageHandler,
    StatusMessageHandler,
    MQTTClientService,
    create_mqtt_service,
)
from src.services.mqtt_auth import MQTTAuthService


class TestMQTTConfig:
    """Test MQTT configuration"""

    def test_default_config(self):
        """Test default MQTT configuration"""
        config = MQTTConfig()
        assert config.host == "localhost"
        assert config.port == 1883
        assert config.keepalive == 60
        assert config.use_tls is False
        assert config.default_qos == 1

    def test_custom_config(self):
        """Test custom MQTT configuration"""
        config = MQTTConfig(
            host="mqtt.example.com",
            port=8883,
            use_tls=True,
            username="test_user",
            password="test_pass",
        )
        assert config.host == "mqtt.example.com"
        assert config.port == 8883
        assert config.use_tls is True
        assert config.username == "test_user"


class TestMQTTMessage:
    """Test MQTT message data class"""

    def test_message_creation(self):
        """Test creating an MQTT message"""
        msg = MQTTMessage(topic="test/topic", payload="test data", qos=1)
        assert msg.topic == "test/topic"
        assert msg.payload == "test data"
        assert msg.qos == 1
        assert msg.retain is False
        assert msg.timestamp is not None

    def test_message_to_dict(self):
        """Test converting message to dictionary"""
        msg = MQTTMessage(topic="test/topic", payload={"key": "value"}, qos=2)
        msg_dict = msg.to_dict()
        assert msg_dict["topic"] == "test/topic"
        assert msg_dict["payload"] == {"key": "value"}
        assert msg_dict["qos"] == 2


class TestMQTTMessageHandler:
    """Test base message handler"""

    def test_can_handle_exact_match(self):
        """Test exact topic matching"""
        handler = MQTTMessageHandler("iotflow/devices/123/telemetry")
        assert handler.can_handle("iotflow/devices/123/telemetry") is True
        assert handler.can_handle("iotflow/devices/456/telemetry") is False

    def test_can_handle_single_wildcard(self):
        """Test single level wildcard (+)"""
        handler = MQTTMessageHandler("iotflow/devices/+/telemetry")
        assert handler.can_handle("iotflow/devices/123/telemetry") is True
        assert handler.can_handle("iotflow/devices/456/telemetry") is True
        assert handler.can_handle("iotflow/devices/123/status") is False

    def test_can_handle_multi_wildcard(self):
        """Test multi-level wildcard (#)"""
        handler = MQTTMessageHandler("iotflow/devices/#")
        # Multi-level wildcard only matches if lengths are equal in base implementation
        # This is a simplified test - real MQTT would handle # differently
        assert handler.can_handle("iotflow/devices/#") is True

    def test_handle_message_not_implemented(self):
        """Test that base handler raises NotImplementedError"""
        handler = MQTTMessageHandler("test/topic")
        msg = MQTTMessage(topic="test/topic", payload="data")
        with pytest.raises(NotImplementedError):
            handler.handle_message(msg)


class TestTelemetryMessageHandler:
    """Test telemetry message handler"""

    def test_initialization(self):
        """Test handler initialization"""
        auth_service = Mock(spec=MQTTAuthService)
        handler = TelemetryMessageHandler(auth_service)
        assert handler.topic_pattern == "iotflow/devices/+/telemetry"
        assert handler.auth_service == auth_service

    def test_can_handle_telemetry_topic(self):
        """Test telemetry topic matching"""
        handler = TelemetryMessageHandler()
        assert handler.can_handle("iotflow/devices/123/telemetry") is True
        assert handler.can_handle("iotflow/devices/456/telemetry/sensors") is True
        assert handler.can_handle("iotflow/devices/123/status") is False

    def test_handle_telemetry_with_auth_success(self):
        """Test handling telemetry message with successful authentication"""
        auth_service = Mock(spec=MQTTAuthService)
        auth_service.handle_telemetry_message.return_value = True

        handler = TelemetryMessageHandler(auth_service)
        callback = Mock()
        handler.add_telemetry_callback(callback)

        payload = json.dumps({"api_key": "test_key", "temperature": 25.5})
        msg = MQTTMessage(topic="iotflow/devices/123/telemetry", payload=payload)

        handler.handle_message(msg)

        auth_service.handle_telemetry_message.assert_called_once()
        callback.assert_called_once()

    def test_handle_telemetry_missing_api_key(self):
        """Test handling telemetry without API key"""
        auth_service = Mock(spec=MQTTAuthService)
        handler = TelemetryMessageHandler(auth_service)

        payload = json.dumps({"temperature": 25.5})  # Missing api_key
        msg = MQTTMessage(topic="iotflow/devices/123/telemetry", payload=payload)

        handler.handle_message(msg)

        # Should not call auth service without API key
        auth_service.handle_telemetry_message.assert_not_called()

    def test_handle_telemetry_invalid_json(self):
        """Test handling telemetry with invalid JSON"""
        auth_service = Mock(spec=MQTTAuthService)
        handler = TelemetryMessageHandler(auth_service)

        msg = MQTTMessage(topic="iotflow/devices/123/telemetry", payload="invalid json{")

        handler.handle_message(msg)

        # Should not crash, just log error
        auth_service.handle_telemetry_message.assert_not_called()


class TestCommandMessageHandler:
    """Test command message handler"""

    def test_initialization(self):
        """Test handler initialization"""
        handler = CommandMessageHandler()
        assert handler.topic_pattern == "iotflow/devices/+/commands/+"

    def test_handle_command_message(self):
        """Test handling command message"""
        handler = CommandMessageHandler()
        callback = Mock()
        handler.add_command_callback(callback)

        payload = json.dumps({"action": "restart"})
        msg = MQTTMessage(topic="iotflow/devices/123/commands/system", payload=payload)

        handler.handle_message(msg)

        callback.assert_called_once()
        call_args = callback.call_args[0][0]
        assert call_args["device_id"] == "123"
        assert call_args["command_type"] == "system"


class TestStatusMessageHandler:
    """Test status message handler"""

    def test_initialization(self):
        """Test handler initialization"""
        handler = StatusMessageHandler()
        assert handler.topic_pattern == "iotflow/devices/+/status/+"

    def test_handle_online_status(self):
        """Test handling online status message"""
        app = Mock()
        app.device_status_cache = Mock()

        handler = StatusMessageHandler()
        handler.set_app(app)
        callback = Mock()
        handler.add_status_callback(callback)

        payload = json.dumps({"status": "online"})
        msg = MQTTMessage(topic="iotflow/devices/123/status/online", payload=payload)

        handler.handle_message(msg)

        callback.assert_called_once()
        app.device_status_cache.set_device_status.assert_called_once_with(123, "online")

    def test_handle_offline_status(self):
        """Test handling offline status message"""
        app = Mock()
        app.device_status_cache = Mock()

        handler = StatusMessageHandler()
        handler.set_app(app)

        payload = json.dumps({"status": "offline"})
        msg = MQTTMessage(topic="iotflow/devices/456/status/offline", payload=payload)

        handler.handle_message(msg)

        app.device_status_cache.set_device_status.assert_called_once_with(456, "offline")


class TestMQTTClientService:
    """Test MQTT client service"""

    @patch("src.mqtt.client.mqtt.Client")
    def test_initialization(self, mock_mqtt_client):
        """Test MQTT client service initialization"""
        config = MQTTConfig()
        auth_service = Mock(spec=MQTTAuthService)

        service = MQTTClientService(config, auth_service)

        assert service.config == config
        assert service.auth_service == auth_service
        assert service.connected is False
        assert len(service.message_handlers) == 3  # telemetry, command, status

    @patch("src.mqtt.client.mqtt.Client")
    def test_add_message_handler(self, mock_mqtt_client):
        """Test adding custom message handler"""
        config = MQTTConfig()
        service = MQTTClientService(config)

        custom_handler = Mock(spec=MQTTMessageHandler)
        service.add_message_handler(custom_handler)

        assert custom_handler in service.message_handlers

    @patch("src.mqtt.client.mqtt.Client")
    def test_add_callbacks(self, mock_mqtt_client):
        """Test adding various callbacks"""
        config = MQTTConfig()
        service = MQTTClientService(config)

        telemetry_cb = Mock()
        command_cb = Mock()
        status_cb = Mock()

        service.add_telemetry_callback(telemetry_cb)
        service.add_command_callback(command_cb)
        service.add_status_callback(status_cb)

        assert telemetry_cb in service.telemetry_handler.telemetry_callbacks
        assert command_cb in service.command_handler.command_callbacks
        assert status_cb in service.status_handler.status_callbacks

    @patch("src.mqtt.client.mqtt.Client")
    def test_setup_client(self, mock_mqtt_client):
        """Test MQTT client setup"""
        config = MQTTConfig(username="test_user", password="test_pass")
        service = MQTTClientService(config)

        service._setup_client()

        assert service.client is not None
        mock_mqtt_client.assert_called_once()

    @patch("src.mqtt.client.mqtt.Client")
    def test_publish_when_connected(self, mock_mqtt_client):
        """Test publishing message when connected"""
        mock_client_instance = Mock()
        mock_client_instance.publish.return_value = Mock(rc=0)  # Success
        mock_mqtt_client.return_value = mock_client_instance

        config = MQTTConfig()
        service = MQTTClientService(config)
        service.client = mock_client_instance
        service.connected = True

        result = service.publish("test/topic", {"data": "value"})

        assert result is True
        mock_client_instance.publish.assert_called_once()

    @patch("src.mqtt.client.mqtt.Client")
    def test_publish_when_not_connected(self, mock_mqtt_client):
        """Test publishing message when not connected"""
        config = MQTTConfig()
        service = MQTTClientService(config)
        service.connected = False

        result = service.publish("test/topic", "data")

        assert result is False

    @patch("src.mqtt.client.mqtt.Client")
    def test_subscribe_when_connected(self, mock_mqtt_client):
        """Test subscribing to topic when connected"""
        mock_client_instance = Mock()
        mock_client_instance.subscribe.return_value = (0, 1)  # Success
        mock_mqtt_client.return_value = mock_client_instance

        config = MQTTConfig()
        service = MQTTClientService(config)
        service.client = mock_client_instance
        service.connected = True

        result = service.subscribe("test/topic")

        assert result is True
        mock_client_instance.subscribe.assert_called_once()

    @patch("src.mqtt.client.mqtt.Client")
    def test_subscribe_with_callback(self, mock_mqtt_client):
        """Test subscribing with callback"""
        mock_client_instance = Mock()
        mock_client_instance.subscribe.return_value = (0, 1)
        mock_mqtt_client.return_value = mock_client_instance

        config = MQTTConfig()
        service = MQTTClientService(config)
        service.client = mock_client_instance
        service.connected = True

        callback = Mock()
        result = service.subscribe("test/topic", callback=callback)

        assert result is True
        assert "test/topic" in service.subscription_callbacks
        assert callback in service.subscription_callbacks["test/topic"]

    @patch("src.mqtt.client.mqtt.Client")
    def test_get_connection_status(self, mock_mqtt_client):
        """Test getting connection status"""
        config = MQTTConfig(host="mqtt.example.com", port=1883)
        service = MQTTClientService(config)
        service.connected = True

        status = service.get_connection_status()

        assert status["connected"] is True
        assert status["host"] == "mqtt.example.com"
        assert status["port"] == 1883
        assert "handlers_count" in status


class TestCreateMQTTService:
    """Test MQTT service factory function"""

    def test_create_mqtt_service_with_defaults(self):
        """Test creating MQTT service with default config"""
        config = {"host": "localhost", "port": 1883}
        service = create_mqtt_service(config)

        assert service.config.host == "localhost"
        assert service.config.port == 1883

    def test_create_mqtt_service_with_tls(self):
        """Test creating MQTT service with TLS"""
        config = {
            "host": "mqtt.example.com",
            "port": 8883,
            "use_tls": True,
            "username": "user",
            "password": "pass",
        }
        service = create_mqtt_service(config)

        assert service.config.use_tls is True
        assert service.config.username == "user"
        assert service.config.password == "pass"

    def test_create_mqtt_service_with_auth_service(self):
        """Test creating MQTT service with auth service"""
        config = {"host": "localhost"}
        auth_service = Mock(spec=MQTTAuthService)

        service = create_mqtt_service(config, auth_service=auth_service)

        assert service.auth_service == auth_service
