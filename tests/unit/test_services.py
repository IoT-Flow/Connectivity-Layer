"""
Unit tests for service layer
Testing IoTDB service, Device Status Cache, and other services
"""

import pytest
from unittest.mock import Mock, patch, MagicMock
from datetime import datetime, timezone
import json


@pytest.mark.unit
class TestIoTDBService:
    """Unit tests for IoTDB service"""

    def test_service_initialization(self):
        """Test IoTDB service initializes correctly"""
        from src.services.iotdb import IoTDBService

        service = IoTDBService()

        # Service should initialize
        assert service is not None
        assert hasattr(service, "session")
        assert hasattr(service, "database")

    def test_is_available_returns_boolean(self):
        """Test is_available method returns boolean"""
        from src.services.iotdb import IoTDBService

        service = IoTDBService()
        result = service.is_available()

        assert isinstance(result, bool)

    def test_get_data_type_mapping(self):
        """Test data type mapping for different Python types"""
        from src.services.iotdb import IoTDBService
        from iotdb.utils.IoTDBConstants import TSDataType

        service = IoTDBService()

        # Test type mappings
        assert service._get_data_type(True) == TSDataType.BOOLEAN
        assert service._get_data_type(42) == TSDataType.INT64
        assert service._get_data_type(3.14) == TSDataType.DOUBLE
        assert service._get_data_type("text") == TSDataType.TEXT
        assert service._get_data_type({"key": "value"}) == TSDataType.TEXT


@pytest.mark.unit
class TestDeviceStatusCache:
    """Unit tests for Device Status Cache service"""

    def test_cache_initialization(self, mock_redis):
        """Test cache initializes with Redis client"""
        from src.services.device_status_cache import DeviceStatusCache

        cache = DeviceStatusCache(redis_client=mock_redis)

        assert cache.redis is not None
        assert cache.available is True

    def test_cache_initialization_without_redis(self):
        """Test cache handles missing Redis gracefully"""
        from src.services.device_status_cache import DeviceStatusCache

        cache = DeviceStatusCache(redis_client=None)

        assert cache.available is False

    def test_set_device_status(self, mock_redis):
        """Test setting device status in cache"""
        from src.services.device_status_cache import DeviceStatusCache

        cache = DeviceStatusCache(redis_client=mock_redis)

        result = cache.set_device_status(device_id=1, status="online")

        assert result is True
        assert mock_redis.data.get("device:status:1") == "online"

    def test_get_device_status(self, mock_redis):
        """Test getting device status from cache"""
        from src.services.device_status_cache import DeviceStatusCache

        cache = DeviceStatusCache(redis_client=mock_redis)

        # Set status first
        mock_redis.data["device:status:1"] = "online"

        # Get status
        status = cache.get_device_status(device_id=1)

        assert status == "online"

    def test_get_device_status_not_found(self, mock_redis):
        """Test getting non-existent device status returns None"""
        from src.services.device_status_cache import DeviceStatusCache

        cache = DeviceStatusCache(redis_client=mock_redis)

        status = cache.get_device_status(device_id=999)

        assert status is None

    def test_clear_device_cache(self, mock_redis):
        """Test clearing device cache"""
        from src.services.device_status_cache import DeviceStatusCache

        cache = DeviceStatusCache(redis_client=mock_redis)

        # Set some data
        mock_redis.data["device:status:1"] = "online"
        mock_redis.data["device:lastseen:1"] = "2025-12-08T10:00:00"

        # Clear cache
        result = cache.clear_device_cache(device_id=1)

        assert result is True

    def test_update_device_last_seen(self, mock_redis):
        """Test updating device last seen timestamp"""
        from src.services.device_status_cache import DeviceStatusCache

        cache = DeviceStatusCache(redis_client=mock_redis)

        timestamp = datetime.now(timezone.utc)
        result = cache.update_device_last_seen(device_id=1, timestamp=timestamp)

        assert result is True

    def test_cache_operations_fail_gracefully_without_redis(self):
        """Test cache operations return False when Redis unavailable"""
        from src.services.device_status_cache import DeviceStatusCache

        cache = DeviceStatusCache(redis_client=None)

        # All operations should return False
        assert cache.set_device_status(1, "online") is False
        assert cache.get_device_status(1) is None
        assert cache.clear_device_cache(1) is False


@pytest.mark.unit
class TestMQTTAuthService:
    """Unit tests for MQTT Authentication service"""

    def test_authenticate_device_by_api_key(self, app, test_device):
        """Test device authentication by API key"""
        from src.services.mqtt_auth import MQTTAuthService

        with app.app_context():
            service = MQTTAuthService(app=app)

            device = service.authenticate_device_by_api_key(test_device.api_key)

            assert device is not None
            assert device.id == test_device.id

    def test_authenticate_device_with_invalid_key(self, app):
        """Test authentication fails with invalid API key"""
        from src.services.mqtt_auth import MQTTAuthService

        with app.app_context():
            service = MQTTAuthService(app=app)

            device = service.authenticate_device_by_api_key("invalid_key_12345")

            assert device is None
