"""
Unit tests for Redis utility functions.
"""
import pytest
from unittest.mock import Mock, patch, MagicMock
import redis
from datetime import datetime, timezone
from src.utils.redis_util import DeviceRedisUtil, get_redis_util, sync_device_status_safe


class TestDeviceRedisUtil:
    """Test DeviceRedisUtil class."""

    @patch("src.utils.redis_util.redis.from_url")
    def test_initialization_success(self, mock_from_url):
        """Test successful initialization."""
        mock_client = Mock()
        mock_from_url.return_value = mock_client
        mock_client.ping.return_value = True

        util = DeviceRedisUtil("redis://localhost:6379/0")

        assert util.available is True
        assert util._redis_client == mock_client
        mock_from_url.assert_called_once_with("redis://localhost:6379/0", decode_responses=True)
        mock_client.ping.assert_called_once()

    @patch("src.utils.redis_util.redis.from_url")
    def test_initialization_failure(self, mock_from_url):
        """Test initialization failure."""
        mock_from_url.side_effect = redis.ConnectionError("Connection failed")

        util = DeviceRedisUtil("redis://localhost:6379/0")

        assert util.available is False
        assert util._redis_client is None

    @patch("src.utils.redis_util.redis.from_url")
    def test_set_device_status_success(self, mock_from_url):
        """Test setting device status successfully."""
        mock_client = Mock()
        mock_from_url.return_value = mock_client
        mock_client.ping.return_value = True
        mock_client.set.return_value = True

        util = DeviceRedisUtil()
        result = util.set_device_status(123, "online")

        assert result is True
        mock_client.set.assert_called_once_with("device:status:123", "online", ex=86400)

    @patch("src.utils.redis_util.redis.from_url")
    def test_set_device_status_unavailable(self, mock_from_url):
        """Test setting device status when Redis unavailable."""
        mock_from_url.side_effect = redis.ConnectionError()

        util = DeviceRedisUtil()
        result = util.set_device_status(123, "online")

        assert result is False

    @patch("src.utils.redis_util.redis.from_url")
    def test_get_device_status_success(self, mock_from_url):
        """Test getting device status successfully."""
        mock_client = Mock()
        mock_from_url.return_value = mock_client
        mock_client.ping.return_value = True
        mock_client.get.return_value = "online"

        util = DeviceRedisUtil()
        result = util.get_device_status(123)

        assert result == "online"
        mock_client.get.assert_called_once_with("device:status:123")

    @patch("src.utils.redis_util.redis.from_url")
    def test_get_device_status_not_found(self, mock_from_url):
        """Test getting device status when not found."""
        mock_client = Mock()
        mock_from_url.return_value = mock_client
        mock_client.ping.return_value = True
        mock_client.get.return_value = None

        util = DeviceRedisUtil()
        result = util.get_device_status(123)

        assert result is None

    @patch("src.utils.redis_util.redis.from_url")
    def test_set_device_last_seen(self, mock_from_url):
        """Test setting device last seen timestamp."""
        mock_client = Mock()
        mock_from_url.return_value = mock_client
        mock_client.ping.return_value = True
        mock_client.set.return_value = True

        util = DeviceRedisUtil()
        timestamp = datetime.now(timezone.utc)
        result = util.set_device_last_seen(123, timestamp)

        assert result is True
        mock_client.set.assert_called_once_with("device:lastseen:123", timestamp.isoformat(), ex=86400)

    @patch("src.utils.redis_util.redis.from_url")
    def test_get_device_last_seen(self, mock_from_url):
        """Test getting device last seen timestamp."""
        mock_client = Mock()
        mock_from_url.return_value = mock_client
        mock_client.ping.return_value = True

        timestamp = datetime.now(timezone.utc)
        mock_client.get.return_value = timestamp.isoformat()

        util = DeviceRedisUtil()
        result = util.get_device_last_seen(123)

        assert result is not None
        assert abs((result - timestamp).total_seconds()) < 1  # Within 1 second


class TestGlobalRedisUtil:
    """Test global Redis utility functions."""

    @patch("src.utils.redis_util._redis_util", None)
    @patch("src.utils.redis_util.DeviceRedisUtil")
    @patch("os.environ.get")
    def test_get_redis_util_creates_instance(self, mock_env_get, mock_device_redis_util):
        """Test that get_redis_util creates instance if needed."""
        mock_env_get.return_value = "redis://test:6379/0"
        mock_util = Mock()
        mock_device_redis_util.return_value = mock_util

        result = get_redis_util()

        assert result == mock_util
        mock_device_redis_util.assert_called_once_with("redis://test:6379/0")

    @patch("src.utils.redis_util._redis_util", None)
    @patch("src.utils.redis_util.DeviceRedisUtil")
    def test_get_redis_util_handles_exception(self, mock_device_redis_util):
        """Test that get_redis_util handles initialization exceptions."""
        mock_device_redis_util.side_effect = Exception("Init failed")

        result = get_redis_util()

        assert result is None

    @patch("src.utils.redis_util.get_redis_util")
    def test_sync_device_status_safe_success(self, mock_get_util):
        """Test sync_device_status_safe with successful operation."""
        mock_util = Mock()
        mock_util.available = True
        mock_util.get_device_status.return_value = "offline"
        mock_util.set_device_status.return_value = True
        mock_util.set_device_last_seen.return_value = True
        mock_get_util.return_value = mock_util

        with patch("src.utils.redis_util._sync_to_database_standalone") as mock_db_sync:
            sync_device_status_safe(123, True, 30.5)

            mock_util.set_device_status.assert_called_once_with(123, "online")
            mock_util.set_device_last_seen.assert_called_once()
            mock_db_sync.assert_called_once_with(123, "online", "offline")

    @patch("src.utils.redis_util.get_redis_util")
    def test_sync_device_status_safe_no_change(self, mock_get_util):
        """Test sync_device_status_safe when status hasn't changed."""
        mock_util = Mock()
        mock_util.available = True
        mock_util.get_device_status.return_value = "online"
        mock_get_util.return_value = mock_util

        sync_device_status_safe(123, True)

        # Should not call set_device_status since status hasn't changed
        mock_util.set_device_status.assert_not_called()

    @patch("src.utils.redis_util.get_redis_util")
    def test_sync_device_status_safe_unavailable(self, mock_get_util):
        """Test sync_device_status_safe when Redis unavailable."""
        mock_get_util.return_value = None

        # Should not raise exception
        sync_device_status_safe(123, True)

    @patch("src.utils.redis_util.get_redis_util")
    def test_sync_device_status_safe_exception_handling(self, mock_get_util):
        """Test sync_device_status_safe handles exceptions gracefully."""
        mock_util = Mock()
        mock_util.available = True
        mock_util.get_device_status.side_effect = Exception("Redis error")
        mock_get_util.return_value = mock_util

        # Should not raise exception
        sync_device_status_safe(123, True)
