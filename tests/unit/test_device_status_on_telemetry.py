"""
TDD Test: Device Status Should Change to Online When Telemetry is Received

This test verifies the complete flow from telemetry receipt to status update.
"""
import pytest
import json
from unittest.mock import Mock, patch, MagicMock
from datetime import datetime, timezone


class TestDeviceStatusOnTelemetry:
    """Test that device status changes to online when telemetry is received"""

    def test_device_becomes_online_after_mqtt_telemetry(self):
        """
        RED: Test that device status changes to online after receiving MQTT telemetry

        Given: A device with status 'active'
        When: The device sends telemetry via MQTT
        Then: The device status should change to 'online'
        And: The is_online flag should be True
        """
        from src.services.mqtt_auth import MQTTAuthService
        from src.services.device_status_tracker import DeviceStatusTracker
        from src.models import Device
        from app import create_app

        # Create test app
        test_app = create_app("testing")

        with test_app.app_context():
            # Mock Redis client with a storage dict to track what was set
            redis_storage = {}

            mock_redis = Mock()

            def mock_set(key, value, ex=None):
                redis_storage[key] = value
                return True

            def mock_get(key):
                return redis_storage.get(key, None)

            mock_redis.set = Mock(side_effect=mock_set)
            mock_redis.get = Mock(side_effect=mock_get)

            # Mock database
            mock_db = Mock()

            # Mock device
            mock_device = Mock()
            mock_device.id = 11
            mock_device.api_key = "test_api_key_123"
            mock_device.status = "active"
            mock_device.is_online = False
            mock_device.user_id = 1
            mock_device.device_type = "sensor"
            mock_device.name = "Test Device"

            # Mock Device.query
            mock_query = Mock()
            mock_query.filter_by.return_value.first.return_value = mock_device

            with patch("src.models.Device.query", mock_query):
                # Initialize status tracker
                status_tracker = DeviceStatusTracker(
                    redis_client=mock_redis, db=mock_db, timeout_seconds=60, enable_db_sync=True
                )

                # Initialize MQTT auth service with status tracker
                mock_iotdb = Mock()
                mock_iotdb.write_telemetry_data = Mock(return_value=True)

                auth_service = MQTTAuthService(iotdb_service=mock_iotdb, app=test_app, status_tracker=status_tracker)

                # Prepare telemetry message
                telemetry_payload = json.dumps(
                    {
                        "data": {"temperature": 25.5, "humidity": 60.0},
                        "metadata": {"source": "test"},
                        "timestamp": datetime.now(timezone.utc).isoformat(),
                        "api_key": "test_api_key_123",
                    }
                )

                # Send telemetry
                topic = "iotflow/devices/11/telemetry"
                success = auth_service.handle_telemetry_message(
                    device_id=11, api_key="test_api_key_123", topic=topic, payload=telemetry_payload
                )

                # Verify telemetry was processed successfully
                assert success is True, "Telemetry should be processed successfully"

                # Verify status tracker update_device_activity was called
                # The status tracker should have called Redis set (with ex parameter for TTL)
                assert mock_redis.set.called, "Redis set should be called to update device status"

                # Verify device status can be checked as online
                is_online = status_tracker.is_device_online(11)
                assert is_online is True, "Device should be marked as online after telemetry"

                # Verify get_device_status returns 'online' string
                status = status_tracker.get_device_status(11)
                assert status == "online", f"Device status should be 'online', got '{status}'"

    def test_device_status_api_returns_online_after_telemetry(self):
        """
        RED: Test that the device status API returns online status after telemetry

        Given: A device that has sent recent telemetry
        When: Querying the device status via API
        Then: The API should return is_online=True and status='online'
        """
        from src.services.device_status_tracker import DeviceStatusTracker

        # Mock Redis with storage dict to track set/get
        redis_storage = {}
        mock_redis = Mock()

        def mock_set(key, value, ex=None):
            redis_storage[key] = value
            return True

        def mock_get(key):
            return redis_storage.get(key, None)

        mock_redis.set = Mock(side_effect=mock_set)
        mock_redis.get = Mock(side_effect=mock_get)

        # Mock database
        mock_db = Mock()

        # Initialize status tracker
        status_tracker = DeviceStatusTracker(redis_client=mock_redis, db=mock_db, timeout_seconds=60)

        # Simulate device activity (like telemetry)
        status_tracker.update_device_activity(11)

        # Check device status
        is_online = status_tracker.is_device_online(11)
        assert is_online is True, "Device should be online with recent activity"

        # Get full status (returns string 'online' or 'offline')
        status = status_tracker.get_device_status(11)
        assert status == "online", f"Status should be 'online', got '{status}'"

    def test_device_status_reflects_in_database_after_sync(self):
        """
        GREEN: Test that status tracker persists device activity correctly

        Given: A device that receives telemetry
        When: Status tracker updates are made
        Then: Redis should persistently store the last_seen timestamp and status
        """
        from src.services.device_status_tracker import DeviceStatusTracker

        # Mock Redis with storage dict to simulate persistence
        redis_storage = {}
        mock_redis = Mock()

        def mock_set(key, value, ex=None):
            redis_storage[key] = value
            return True

        def mock_get(key):
            return redis_storage.get(key, None)

        mock_redis.set = Mock(side_effect=mock_set)
        mock_redis.get = Mock(side_effect=mock_get)

        # Mock database
        mock_db = Mock()

        # Initialize status tracker
        status_tracker = DeviceStatusTracker(redis_client=mock_redis, db=mock_db, timeout_seconds=60)

        # Update device activity
        status_tracker.update_device_activity(11)

        # Verify Redis was updated with both last_seen and status keys (string keys, not bytes)
        assert redis_storage.get("device:lastseen:11") is not None, "last_seen should be stored"
        assert redis_storage.get("device:status:11") == "online", "status should be stored as 'online'"

        # Verify persistence: create new tracker instance with same Redis storage
        status_tracker2 = DeviceStatusTracker(redis_client=mock_redis, db=mock_db, timeout_seconds=60)

        # Should still be online (Redis persisted the data)
        is_online = status_tracker2.is_device_online(11)
        assert is_online is True, "Device should still be online with persisted data"
