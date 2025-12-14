"""
Integration tests for device online/offline status tracking with telemetry.
Tests the full flow from telemetry receipt to status update.
"""
import pytest
from unittest.mock import Mock, patch, MagicMock
from datetime import datetime, timezone, timedelta
import json


class TestDeviceStatusWithTelemetryIntegration:
    """Integration tests for device status tracking with telemetry processing."""

    def test_device_marked_online_when_telemetry_received(self):
        """Test that device is marked online when it sends telemetry."""
        from src.services.mqtt_auth import MQTTAuthService
        from src.services.device_status_tracker import DeviceStatusTracker

        # Setup mocks
        mock_redis = Mock()
        mock_db = Mock()
        mock_iotdb = Mock()
        mock_iotdb.write_telemetry_data.return_value = True

        # Create status tracker
        status_tracker = DeviceStatusTracker(
            redis_client=mock_redis, db=mock_db, enable_db_sync=True, timeout_seconds=60
        )

        # Create mock Flask app
        mock_app = Mock()
        mock_app.app_context.return_value.__enter__ = Mock()
        mock_app.app_context.return_value.__exit__ = Mock()

        # Create mock device
        mock_device = Mock()
        mock_device.id = 123
        mock_device.device_id = "test-device-123"
        mock_device.device_type = "sensor"
        mock_device.user_id = 1
        mock_device.name = "Test Device"
        mock_device.update_last_seen = Mock()

        # Create auth service with status tracker
        auth_service = MQTTAuthService(iotdb_service=mock_iotdb, app=mock_app, status_tracker=status_tracker)

        # Mock the validation methods
        auth_service.validate_device_registration = Mock(return_value=(True, "OK"))
        auth_service.is_device_registered_for_mqtt = Mock(return_value=(True, "OK", mock_device))
        auth_service.validate_device_message = Mock(return_value=mock_device)

        # Prepare telemetry data
        device_id = 123
        api_key = "test-api-key"
        topic = "iotflow/devices/test-device-123/telemetry"
        payload = json.dumps(
            {"data": {"temperature": 25.5, "humidity": 60}, "timestamp": datetime.now(timezone.utc).isoformat()}
        )

        # Process telemetry
        success = auth_service.handle_telemetry_message(device_id, api_key, topic, payload)

        # Verify success
        assert success is True

        # Verify Redis was updated with status
        status_calls = [call for call in mock_redis.set.call_args_list if "device:status:123" in str(call)]
        assert len(status_calls) > 0

        # Verify status is online
        assert "online" in str(status_calls[0])

    def test_device_status_includes_last_seen_timestamp(self):
        """Test that last_seen timestamp is stored when telemetry is received."""
        from src.services.device_status_tracker import DeviceStatusTracker

        mock_redis = Mock()
        mock_db = Mock()

        tracker = DeviceStatusTracker(redis_client=mock_redis, db=mock_db, timeout_seconds=60)

        device_id = 456
        tracker.update_device_activity(device_id)

        # Verify last_seen was stored
        lastseen_calls = [call for call in mock_redis.set.call_args_list if "device:lastseen:456" in str(call)]
        assert len(lastseen_calls) > 0

        # Verify timestamp format
        call_str = str(lastseen_calls[0])
        # Should contain ISO format timestamp
        assert "T" in call_str  # ISO format has 'T' separator

    def test_device_goes_offline_after_timeout(self):
        """Test that device is marked offline after timeout period."""
        from src.services.device_status_tracker import DeviceStatusTracker

        mock_redis = Mock()
        mock_db = Mock()

        # Set up old timestamp (70 seconds ago)
        old_time = datetime.now(timezone.utc) - timedelta(seconds=70)
        mock_redis.get.return_value = old_time.isoformat().encode()

        tracker = DeviceStatusTracker(redis_client=mock_redis, db=mock_db, timeout_seconds=60)

        device_id = 789
        status = tracker.get_device_status(device_id)

        assert status == "offline"

    def test_status_synced_to_database_on_telemetry(self):
        """Test that status is synced to database when telemetry is received."""
        from src.services.device_status_tracker import DeviceStatusTracker

        mock_redis = Mock()
        mock_db = Mock()

        tracker = DeviceStatusTracker(redis_client=mock_redis, db=mock_db, enable_db_sync=True, timeout_seconds=60)

        device_id = 999

        # Mock Device model
        with patch("src.models.Device") as mock_device_model:
            mock_device = Mock()
            mock_device.id = device_id
            mock_device.last_seen = None
            mock_device_model.query.filter_by.return_value.first.return_value = mock_device

            # Update activity (which should trigger DB sync)
            tracker.update_device_activity(device_id)

            # Verify database was accessed
            mock_device_model.query.filter_by.assert_called()


class TestDeviceStatusMonitoring:
    """Tests for monitoring device status over time."""

    def test_check_and_update_status_detects_offline(self):
        """Test that check_and_update_status detects when device goes offline."""
        from src.services.device_status_tracker import DeviceStatusTracker

        mock_redis = Mock()
        mock_db = Mock()

        # Device was online 70 seconds ago
        old_time = datetime.now(timezone.utc) - timedelta(seconds=70)
        mock_redis.get.return_value = old_time.isoformat().encode()

        tracker = DeviceStatusTracker(redis_client=mock_redis, db=mock_db, enable_db_sync=True, timeout_seconds=60)

        device_id = 111
        status = tracker.check_and_update_status(device_id)

        assert status == "offline"

        # Verify status was updated in Redis
        status_update_calls = [call for call in mock_redis.set.call_args_list if "device:status:111" in str(call)]
        assert len(status_update_calls) > 0

    def test_get_last_seen_returns_timestamp(self):
        """Test that get_last_seen returns the correct timestamp."""
        from src.services.device_status_tracker import DeviceStatusTracker

        mock_redis = Mock()
        mock_db = Mock()

        # Set up a specific timestamp
        test_time = datetime.now(timezone.utc) - timedelta(seconds=30)
        mock_redis.get.return_value = test_time.isoformat().encode()

        tracker = DeviceStatusTracker(redis_client=mock_redis, db=mock_db, timeout_seconds=60)

        device_id = 222
        last_seen = tracker.get_last_seen(device_id)

        assert last_seen is not None
        # Should be close to our test time
        time_diff = abs((last_seen - test_time).total_seconds())
        assert time_diff < 1  # Within 1 second


class TestDeviceStatusEdgeCases:
    """Tests for edge cases in device status tracking."""

    def test_status_tracker_handles_none_redis(self):
        """Test that status tracker handles None redis client gracefully."""
        from src.services.device_status_tracker import DeviceStatusTracker

        tracker = DeviceStatusTracker(redis_client=None, db=Mock(), timeout_seconds=60)

        # Should not raise exceptions
        result = tracker.update_device_activity(123)
        assert result is False

        status = tracker.get_device_status(123)
        assert status == "offline"

    def test_status_tracker_handles_redis_errors(self):
        """Test that status tracker handles Redis errors gracefully."""
        from src.services.device_status_tracker import DeviceStatusTracker

        mock_redis = Mock()
        mock_redis.set.side_effect = Exception("Redis connection error")

        tracker = DeviceStatusTracker(redis_client=mock_redis, db=Mock(), timeout_seconds=60)

        # Should handle error gracefully
        result = tracker.update_device_activity(456)
        assert result is False

    def test_different_timeout_periods(self):
        """Test that different timeout periods work correctly."""
        from src.services.device_status_tracker import DeviceStatusTracker

        mock_redis = Mock()

        # Device last seen 45 seconds ago
        time_45s_ago = datetime.now(timezone.utc) - timedelta(seconds=45)
        mock_redis.get.return_value = time_45s_ago.isoformat().encode()

        # With 60 second timeout, should be online
        tracker_60 = DeviceStatusTracker(redis_client=mock_redis, db=Mock(), timeout_seconds=60)
        assert tracker_60.is_device_online(789) is True

        # With 30 second timeout, should be offline
        tracker_30 = DeviceStatusTracker(redis_client=mock_redis, db=Mock(), timeout_seconds=30)
        assert tracker_30.is_device_online(789) is False
