"""
Unit tests for Device Status Cache Service
Tests Redis caching for device status and last seen timestamps
"""

import pytest
from unittest.mock import Mock, patch, MagicMock
from datetime import datetime, timezone, timedelta

from src.services.device_status_cache import DeviceStatusCache


class TestDeviceStatusCache:
    """Test device status cache service"""

    def test_initialization_with_redis(self):
        """Test initialization with Redis client"""
        redis_client = Mock()
        cache = DeviceStatusCache(redis_client)

        assert cache.redis == redis_client
        assert cache.available is True
        assert cache.db_sync_enabled is True

    def test_initialization_without_redis(self):
        """Test initialization without Redis client"""
        cache = DeviceStatusCache(None)

        assert cache.redis is None
        assert cache.available is False

    def test_set_device_status_success(self):
        """Test setting device status successfully"""
        redis_client = Mock()
        cache = DeviceStatusCache(redis_client)
        cache.db_sync_enabled = False  # Disable DB sync for unit test

        result = cache.set_device_status(123, "online")

        assert result is True
        redis_client.set.assert_called_once()
        call_args = redis_client.set.call_args
        assert "device:status:123" in call_args[0][0]
        assert call_args[0][1] == "online"

    def test_set_device_status_without_redis(self):
        """Test setting device status without Redis"""
        cache = DeviceStatusCache(None)

        result = cache.set_device_status(123, "online")

        assert result is False

    def test_get_device_status_success(self):
        """Test getting device status successfully"""
        redis_client = Mock()
        redis_client.get.return_value = "online"
        cache = DeviceStatusCache(redis_client)

        status = cache.get_device_status(123)

        assert status == "online"
        redis_client.get.assert_called_once()

    def test_get_device_status_not_found(self):
        """Test getting device status when not in cache"""
        redis_client = Mock()
        redis_client.get.return_value = None
        cache = DeviceStatusCache(redis_client)

        status = cache.get_device_status(123)

        assert status is None

    def test_get_device_status_without_redis(self):
        """Test getting device status without Redis"""
        cache = DeviceStatusCache(None)

        status = cache.get_device_status(123)

        assert status is None

    def test_update_device_last_seen_success(self):
        """Test updating device last seen timestamp"""
        redis_client = Mock()
        cache = DeviceStatusCache(redis_client)
        cache.db_sync_enabled = False

        timestamp = datetime.now(timezone.utc)
        result = cache.update_device_last_seen(123, timestamp)

        assert result is True
        # Should call set twice: once for last_seen, once for status
        assert redis_client.set.call_count == 2

    def test_update_device_last_seen_default_timestamp(self):
        """Test updating device last seen with default timestamp"""
        redis_client = Mock()
        cache = DeviceStatusCache(redis_client)
        cache.db_sync_enabled = False

        result = cache.update_device_last_seen(123)

        assert result is True
        redis_client.set.assert_called()

    def test_get_device_last_seen_success(self):
        """Test getting device last seen timestamp"""
        redis_client = Mock()
        timestamp = datetime.now(timezone.utc)
        redis_client.get.return_value = timestamp.isoformat()
        cache = DeviceStatusCache(redis_client)

        last_seen = cache.get_device_last_seen(123)

        assert last_seen is not None
        assert isinstance(last_seen, datetime)

    def test_get_device_last_seen_not_found(self):
        """Test getting last seen when not in cache"""
        redis_client = Mock()
        redis_client.get.return_value = None
        cache = DeviceStatusCache(redis_client)

        last_seen = cache.get_device_last_seen(123)

        assert last_seen is None

    def test_set_device_offline(self):
        """Test setting device offline"""
        redis_client = Mock()
        cache = DeviceStatusCache(redis_client)
        cache.db_sync_enabled = False

        result = cache.set_device_offline(123)

        assert result is True
        redis_client.set.assert_called_once()
        call_args = redis_client.set.call_args
        assert call_args[0][1] == "offline"

    def test_get_all_device_statuses(self):
        """Test getting statuses for multiple devices"""
        redis_client = Mock()
        pipeline = Mock()
        pipeline.execute.return_value = ["online", "offline", None]
        redis_client.pipeline.return_value = pipeline

        cache = DeviceStatusCache(redis_client)

        device_ids = [1, 2, 3]
        statuses = cache.get_all_device_statuses(device_ids)

        assert statuses[1] == "online"
        assert statuses[2] == "offline"
        assert statuses[3] is None

    def test_get_all_device_statuses_empty_list(self):
        """Test getting statuses with empty device list"""
        redis_client = Mock()
        cache = DeviceStatusCache(redis_client)

        statuses = cache.get_all_device_statuses([])

        assert statuses == {}

    def test_get_all_device_last_seen(self):
        """Test getting last seen for multiple devices"""
        redis_client = Mock()
        pipeline = Mock()
        timestamp1 = datetime.now(timezone.utc)
        timestamp2 = datetime.now(timezone.utc) - timedelta(hours=1)
        pipeline.execute.return_value = [timestamp1.isoformat(), timestamp2.isoformat(), None]
        redis_client.pipeline.return_value = pipeline

        cache = DeviceStatusCache(redis_client)

        device_ids = [1, 2, 3]
        last_seen = cache.get_all_device_last_seen(device_ids)

        assert isinstance(last_seen[1], datetime)
        assert isinstance(last_seen[2], datetime)
        assert last_seen[3] is None

    def test_get_device_status_summary(self):
        """Test getting status summary for devices"""
        redis_client = Mock()
        timestamp = datetime.now(timezone.utc)

        def mock_get(key):
            if "status" in key:
                return "online"
            elif "lastseen" in key:
                return timestamp.isoformat()
            return None

        redis_client.get.side_effect = mock_get
        cache = DeviceStatusCache(redis_client)

        summary = cache.get_device_status_summary([123])

        assert 123 in summary
        assert summary[123]["status"] == "online"
        assert summary[123]["last_seen"] is not None

    def test_clear_device_cache(self):
        """Test clearing cache for specific device"""
        redis_client = Mock()
        pipeline = Mock()
        redis_client.pipeline.return_value = pipeline

        cache = DeviceStatusCache(redis_client)

        result = cache.clear_device_cache(123)

        assert result is True
        pipeline.delete.assert_called()
        pipeline.execute.assert_called_once()

    def test_clear_device_cache_without_redis(self):
        """Test clearing cache without Redis"""
        cache = DeviceStatusCache(None)

        result = cache.clear_device_cache(123)

        assert result is False

    def test_clear_all_device_caches(self):
        """Test clearing all device caches"""
        redis_client = Mock()
        redis_client.keys.side_effect = [["device:status:1", "device:status:2"], ["device:lastseen:1"]]
        pipeline = Mock()
        redis_client.pipeline.return_value = pipeline

        cache = DeviceStatusCache(redis_client)

        result = cache.clear_all_device_caches()

        assert result is True
        pipeline.delete.assert_called()
        pipeline.execute.assert_called_once()

    def test_clear_all_device_caches_no_keys(self):
        """Test clearing all caches when no keys exist"""
        redis_client = Mock()
        redis_client.keys.return_value = []

        cache = DeviceStatusCache(redis_client)

        result = cache.clear_all_device_caches()

        assert result is True

    def test_enable_database_sync(self):
        """Test enabling database synchronization"""
        cache = DeviceStatusCache(Mock())

        cache.disable_database_sync()
        assert cache.db_sync_enabled is False

        cache.enable_database_sync()
        assert cache.db_sync_enabled is True

    def test_disable_database_sync(self):
        """Test disabling database synchronization"""
        cache = DeviceStatusCache(Mock())

        cache.disable_database_sync()
        assert cache.db_sync_enabled is False

    def test_is_database_sync_enabled(self):
        """Test checking if database sync is enabled"""
        cache = DeviceStatusCache(Mock())

        assert cache.is_database_sync_enabled() is True

        cache.disable_database_sync()
        assert cache.is_database_sync_enabled() is False

    def test_register_status_change_callback(self):
        """Test registering status change callback"""
        cache = DeviceStatusCache(Mock())

        def callback(device_id, old_status, new_status):
            pass

        cache.register_status_change_callback(callback)

        assert callback in cache.status_change_callbacks

    def test_unregister_status_change_callback(self):
        """Test unregistering status change callback"""
        cache = DeviceStatusCache(Mock())

        def callback(device_id, old_status, new_status):
            pass

        cache.register_status_change_callback(callback)
        cache.unregister_status_change_callback(callback)

        assert callback not in cache.status_change_callbacks

    def test_status_change_triggers_callback(self):
        """Test that status changes trigger callbacks"""
        redis_client = Mock()
        redis_client.get.return_value = None  # No old status
        cache = DeviceStatusCache(redis_client)

        callback = Mock()
        callback.__name__ = "test_callback"  # Add __name__ attribute for logging
        cache.register_status_change_callback(callback)

        cache.set_device_status(123, "online")

        # Callback should be triggered
        callback.assert_called_once_with(123, None, "online")

    def test_force_sync_device_to_database(self):
        """Test forcing device sync to database"""
        redis_client = Mock()
        redis_client.get.return_value = "online"
        cache = DeviceStatusCache(redis_client)

        # Mock the sync method
        cache._sync_status_to_database = Mock()

        result = cache.force_sync_device_to_database(123)

        assert result is True
        cache._sync_status_to_database.assert_called_once_with(123, "online")

    def test_force_sync_device_no_status(self):
        """Test forcing sync when device has no status in Redis"""
        redis_client = Mock()
        redis_client.get.return_value = None
        cache = DeviceStatusCache(redis_client)

        result = cache.force_sync_device_to_database(123)

        assert result is False

    def test_redis_error_handling(self):
        """Test graceful handling of Redis errors"""
        redis_client = Mock()
        redis_client.set.side_effect = Exception("Redis connection error")

        cache = DeviceStatusCache(redis_client)

        result = cache.set_device_status(123, "online")

        assert result is False

    def test_get_status_redis_error_handling(self):
        """Test graceful handling of Redis errors on get"""
        redis_client = Mock()
        redis_client.get.side_effect = Exception("Redis connection error")

        cache = DeviceStatusCache(redis_client)

        status = cache.get_device_status(123)

        assert status is None
