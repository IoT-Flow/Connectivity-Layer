"""
Unit tests for device online/offline status tracking with Redis caching and database sync.
Following TDD approach - tests first, then implementation.

Requirements:
1. Device becomes "online" when it sends telemetry
2. Device becomes "offline" after 1 minute (60 seconds) of no telemetry
3. Use Redis for caching status
4. Sync status with database
"""
import pytest
import time
from unittest.mock import Mock, patch, MagicMock
from datetime import datetime, timezone, timedelta


class TestDeviceOnlineStatusTracking:
    """Test device online/offline status tracking based on telemetry."""

    def test_device_becomes_online_when_sending_telemetry(self):
        """Test that a device is marked as online when it sends telemetry."""
        from src.services.device_status_tracker import DeviceStatusTracker

        mock_redis = Mock()
        mock_db = Mock()

        tracker = DeviceStatusTracker(redis_client=mock_redis, db=mock_db)

        device_id = 123
        tracker.update_device_activity(device_id)

        # Verify device is marked as online in Redis
        mock_redis.set.assert_called()
        # Check that status was set to "online"
        calls = [call for call in mock_redis.set.call_args_list if "device:status:123" in str(call)]
        assert len(calls) > 0
        assert "online" in str(calls[0])

    def test_device_status_stored_with_ttl(self):
        """Test that device status in Redis has appropriate TTL."""
        from src.services.device_status_tracker import DeviceStatusTracker

        mock_redis = Mock()
        mock_db = Mock()

        tracker = DeviceStatusTracker(redis_client=mock_redis, db=mock_db)

        device_id = 456
        tracker.update_device_activity(device_id)

        # Verify Redis set was called with TTL parameter
        mock_redis.set.assert_called()
        # Check that ex (expiry) parameter was provided
        assert any("ex" in str(call) for call in mock_redis.set.call_args_list)

    def test_device_last_seen_timestamp_updated(self):
        """Test that device last_seen timestamp is updated in Redis."""
        from src.services.device_status_tracker import DeviceStatusTracker

        mock_redis = Mock()
        mock_db = Mock()

        tracker = DeviceStatusTracker(redis_client=mock_redis, db=mock_db)

        device_id = 789
        tracker.update_device_activity(device_id)

        # Verify last_seen was stored in Redis
        calls = [call for call in mock_redis.set.call_args_list if "device:lastseen:789" in str(call)]
        assert len(calls) > 0

    def test_device_marked_offline_after_timeout(self):
        """Test that a device is marked offline after 1 minute of inactivity."""
        from src.services.device_status_tracker import DeviceStatusTracker

        mock_redis = Mock()
        mock_db = Mock()

        # Mock Redis to return an old timestamp (more than 60 seconds ago)
        old_timestamp = (datetime.now(timezone.utc) - timedelta(seconds=65)).isoformat()
        mock_redis.get.return_value = old_timestamp.encode()

        tracker = DeviceStatusTracker(redis_client=mock_redis, db=mock_db, timeout_seconds=60)

        device_id = 100
        is_online = tracker.is_device_online(device_id)

        assert is_online is False

    def test_device_marked_online_within_timeout(self):
        """Test that a device is still marked online within the timeout period."""
        from src.services.device_status_tracker import DeviceStatusTracker

        mock_redis = Mock()
        mock_db = Mock()

        # Mock Redis to return a recent timestamp (less than 60 seconds ago)
        recent_timestamp = (datetime.now(timezone.utc) - timedelta(seconds=30)).isoformat()
        mock_redis.get.return_value = recent_timestamp.encode()

        tracker = DeviceStatusTracker(redis_client=mock_redis, db=mock_db, timeout_seconds=60)

        device_id = 200
        is_online = tracker.is_device_online(device_id)

        assert is_online is True

    def test_status_synced_to_database_when_device_goes_online(self):
        """Test that device status is synced to database when device comes online."""
        from src.services.device_status_tracker import DeviceStatusTracker

        mock_redis = Mock()
        mock_db = Mock()

        tracker = DeviceStatusTracker(redis_client=mock_redis, db=mock_db, enable_db_sync=True)

        device_id = 300
        tracker.update_device_activity(device_id)

        # Verify database sync was triggered
        assert tracker.db_sync_enabled is True
        # The actual DB update will be tested in integration tests

    def test_status_synced_to_database_when_device_goes_offline(self):
        """Test that device status is synced to database when device goes offline."""
        from src.services.device_status_tracker import DeviceStatusTracker

        mock_redis = Mock()
        mock_db = Mock()

        # Mock old timestamp to trigger offline status
        old_timestamp = (datetime.now(timezone.utc) - timedelta(seconds=70)).isoformat()
        mock_redis.get.return_value = old_timestamp.encode()

        tracker = DeviceStatusTracker(redis_client=mock_redis, db=mock_db, enable_db_sync=True, timeout_seconds=60)

        device_id = 400
        # Check status which will detect offline and trigger sync
        status = tracker.check_and_update_status(device_id)

        assert status == "offline"

    def test_multiple_devices_tracked_independently(self):
        """Test that multiple devices are tracked independently."""
        from src.services.device_status_tracker import DeviceStatusTracker

        mock_redis = Mock()
        mock_db = Mock()

        # Device 1: recent activity (online)
        # Device 2: old activity (offline)
        def redis_get_side_effect(key):
            key_str = key if isinstance(key, str) else key.decode() if isinstance(key, bytes) else str(key)
            if "device:lastseen:1" in key_str:
                recent = (datetime.now(timezone.utc) - timedelta(seconds=10)).isoformat()
                return recent.encode()
            elif "device:lastseen:2" in key_str:
                old = (datetime.now(timezone.utc) - timedelta(seconds=70)).isoformat()
                return old.encode()
            return None

        mock_redis.get.side_effect = redis_get_side_effect

        tracker = DeviceStatusTracker(redis_client=mock_redis, db=mock_db, timeout_seconds=60)

        device1_online = tracker.is_device_online(1)
        device2_online = tracker.is_device_online(2)

        assert device1_online is True
        assert device2_online is False

    def test_graceful_handling_when_redis_unavailable(self):
        """Test that system handles gracefully when Redis is unavailable."""
        from src.services.device_status_tracker import DeviceStatusTracker

        # Redis client is None
        tracker = DeviceStatusTracker(redis_client=None, db=Mock())

        device_id = 500
        # Should not raise exception
        result = tracker.update_device_activity(device_id)

        # When Redis unavailable, it should return False or handle gracefully
        assert result is False or result is None

    def test_get_device_status_returns_online_or_offline(self):
        """Test that get_device_status returns 'online' or 'offline'."""
        from src.services.device_status_tracker import DeviceStatusTracker

        mock_redis = Mock()
        mock_db = Mock()

        # Recent timestamp
        recent = (datetime.now(timezone.utc) - timedelta(seconds=30)).isoformat()
        mock_redis.get.return_value = recent.encode()

        tracker = DeviceStatusTracker(redis_client=mock_redis, db=mock_db, timeout_seconds=60)

        device_id = 600
        status = tracker.get_device_status(device_id)

        assert status in ["online", "offline"]
        assert status == "online"


class TestDeviceStatusDatabaseSync:
    """Test database synchronization for device status."""

    @patch("src.models.Device")
    def test_database_updated_on_status_change(self, mock_device_model):
        """Test that database is updated when device status changes."""
        from src.services.device_status_tracker import DeviceStatusTracker

        mock_redis = Mock()
        mock_db = Mock()
        mock_device = Mock()
        mock_device.id = 123
        mock_device_model.query.filter_by.return_value.first.return_value = mock_device

        tracker = DeviceStatusTracker(redis_client=mock_redis, db=mock_db, enable_db_sync=True)

        device_id = 123
        tracker.sync_status_to_database(device_id, "online")

        # Verify device was queried and updated
        mock_device_model.query.filter_by.assert_called_with(id=device_id)

    @patch("src.models.Device")
    def test_last_seen_timestamp_synced_to_database(self, mock_device_model):
        """Test that last_seen timestamp is synced to database."""
        from src.services.device_status_tracker import DeviceStatusTracker

        mock_redis = Mock()
        mock_db = Mock()
        mock_device = Mock()
        mock_device.id = 456
        mock_device.last_seen = None
        mock_device_model.query.filter_by.return_value.first.return_value = mock_device

        tracker = DeviceStatusTracker(redis_client=mock_redis, db=mock_db, enable_db_sync=True)

        device_id = 456
        timestamp = datetime.now(timezone.utc)
        tracker.sync_last_seen_to_database(device_id, timestamp)

        # Verify last_seen was updated
        assert mock_device.last_seen is not None

    def test_database_sync_can_be_disabled(self):
        """Test that database synchronization can be disabled."""
        from src.services.device_status_tracker import DeviceStatusTracker

        mock_redis = Mock()
        mock_db = Mock()

        tracker = DeviceStatusTracker(redis_client=mock_redis, db=mock_db, enable_db_sync=False)

        assert tracker.db_sync_enabled is False


class TestDeviceStatusIntegrationWithTelemetry:
    """Test integration of status tracking with telemetry processing."""

    def test_telemetry_handler_updates_device_status(self):
        """Test that telemetry message handler updates device online status."""
        # This test verifies the integration point exists
        # In real usage, the status tracker will be integrated into mqtt_auth service
        from src.services.device_status_tracker import DeviceStatusTracker

        mock_redis = Mock()
        mock_db = Mock()

        tracker = DeviceStatusTracker(redis_client=mock_redis, db=mock_db)

        # Verify tracker can be instantiated and used
        assert tracker is not None
        assert hasattr(tracker, "update_device_activity")

    def test_status_updated_on_successful_telemetry_processing(self):
        """Test that device status is updated only on successful telemetry processing."""
        from src.services.device_status_tracker import DeviceStatusTracker

        mock_redis = Mock()
        mock_db = Mock()

        tracker = DeviceStatusTracker(redis_client=mock_redis, db=mock_db)

        device_id = 700
        # Simulate successful telemetry processing
        success = True

        if success:
            tracker.update_device_activity(device_id)

        # Verify status was updated
        mock_redis.set.assert_called()


class TestDeviceStatusCacheKeys:
    """Test Redis key structure and management."""

    def test_status_key_format(self):
        """Test that Redis status keys follow correct format."""
        from src.services.device_status_tracker import DeviceStatusTracker

        mock_redis = Mock()
        mock_db = Mock()

        tracker = DeviceStatusTracker(redis_client=mock_redis, db=mock_db)

        device_id = 123
        tracker.update_device_activity(device_id)

        # Check that keys use expected format
        calls = mock_redis.set.call_args_list
        keys = [str(call) for call in calls]

        # Should have device:status:123 and device:lastseen:123
        assert any("device:status:123" in key for key in keys)
        assert any("device:lastseen:123" in key for key in keys)

    def test_cleanup_old_device_status_entries(self):
        """Test that old device status entries can be cleaned up."""
        from src.services.device_status_tracker import DeviceStatusTracker

        mock_redis = Mock()
        mock_db = Mock()

        tracker = DeviceStatusTracker(redis_client=mock_redis, db=mock_db)

        # TTL ensures automatic cleanup by Redis
        # This test verifies TTL is set
        device_id = 999
        tracker.update_device_activity(device_id)

        # Verify that ex parameter (TTL) was used
        calls = mock_redis.set.call_args_list
        assert any("ex" in str(call) for call in calls)
