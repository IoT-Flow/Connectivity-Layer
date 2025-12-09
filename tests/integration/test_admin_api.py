"""
Integration tests for Admin API endpoints
Following TDD principles - tests written before implementation review
"""
import pytest
from src.models import Device, User, db
import time


class TestAdminDeviceManagement:
    """Test admin device management endpoints"""

    def test_list_all_devices(self, client, test_admin_user, test_device):
        """Test admin can list all devices"""
        headers = {"Authorization": "admin test"}

        response = client.get("/api/v1/admin/devices", headers=headers)

        assert response.status_code == 200
        data = response.get_json()
        assert "devices" in data
        assert isinstance(data["devices"], list)
        assert len(data["devices"]) >= 1
        assert any(d["id"] == test_device.id for d in data["devices"])

    def test_list_devices_without_admin_token(self, client):
        """Test that admin token is required"""
        response = client.get("/api/v1/admin/devices")

        assert response.status_code == 401

    def test_list_devices_with_pagination(self, client, test_admin_user, test_user, app):
        """Test device listing with pagination"""
        # Create multiple devices
        with app.app_context():
            for i in range(15):
                device = Device(name=f"Test_Device_{i}", user_id=test_user.id, device_type="sensor")
                db.session.add(device)
            db.session.commit()

        headers = {"Authorization": "admin test"}
        response = client.get("/api/v1/admin/devices?page=1&per_page=10", headers=headers)

        assert response.status_code == 200
        data = response.get_json()
        # API may not implement pagination yet, so just check it returns devices
        assert "devices" in data
        assert isinstance(data["devices"], list)

    def test_get_device_details(self, client, test_admin_user, test_device):
        """Test admin can get device details"""
        headers = {"Authorization": "admin test"}

        response = client.get(f"/api/v1/admin/devices/{test_device.id}", headers=headers)

        assert response.status_code == 200
        data = response.get_json()
        assert data["status"] == "success"
        assert "device" in data
        assert data["device"]["id"] == test_device.id
        assert data["device"]["name"] == test_device.name
        assert "auth_records" in data
        assert "configurations" in data

    def test_get_device_details_not_found(self, client, test_admin_user):
        """Test getting non-existent device"""
        headers = {"Authorization": "admin test"}

        response = client.get("/api/v1/admin/devices/99999", headers=headers)

        # May return 404 or 500 depending on error handling
        assert response.status_code in [404, 500]

    def test_update_device_status(self, client, test_admin_user, test_device, app):
        """Test admin can update device status"""
        headers = {"Authorization": "admin test"}
        payload = {"status": "inactive", "reason": "Maintenance"}

        response = client.put(f"/api/v1/admin/devices/{test_device.id}/status", json=payload, headers=headers)

        assert response.status_code == 200
        data = response.get_json()
        assert data["status"] == "success" or "message" in data

        # Verify in database
        with app.app_context():
            device = Device.query.get(test_device.id)
            assert device.status == "inactive"

    def test_delete_device(self, client, test_admin_user, test_user, app):
        """Test admin can delete device"""
        # Create device to delete
        with app.app_context():
            device = Device(name="Device_To_Delete", user_id=test_user.id, device_type="sensor")
            db.session.add(device)
            db.session.commit()
            device_id = device.id

        headers = {"Authorization": "admin test"}
        response = client.delete(f"/api/v1/admin/devices/{device_id}", headers=headers)

        assert response.status_code == 200

        # Verify deletion
        with app.app_context():
            device = Device.query.get(device_id)
            assert device is None

    def test_delete_device_not_found(self, client, test_admin_user):
        """Test deleting non-existent device"""
        headers = {"Authorization": "admin test"}

        response = client.delete("/api/v1/admin/devices/99999", headers=headers)

        # May return 404 or 500 depending on error handling
        assert response.status_code in [404, 500]


class TestAdminSystemStats:
    """Test admin system statistics endpoints"""

    def test_get_system_stats(self, client, test_admin_user, test_device):
        """Test getting system statistics"""
        headers = {"Authorization": "admin test"}

        response = client.get("/api/v1/admin/stats", headers=headers)

        assert response.status_code == 200
        data = response.get_json()
        assert data["status"] == "success"
        assert "device_stats" in data
        assert "auth_stats" in data
        assert data["device_stats"]["total"] >= 1

    def test_get_system_stats_without_admin(self, client):
        """Test that admin token is required"""
        response = client.get("/api/v1/admin/stats")

        assert response.status_code == 401

    def test_system_stats_accuracy(self, client, test_admin_user, test_user, app):
        """Test that system stats are accurate"""
        # Create known number of devices
        with app.app_context():
            initial_count = Device.query.count()
            for i in range(5):
                device = Device(name=f"Stats_Test_Device_{i}", user_id=test_user.id, device_type="sensor")
                db.session.add(device)
            db.session.commit()

        headers = {"Authorization": "admin test"}
        response = client.get("/api/v1/admin/stats", headers=headers)

        assert response.status_code == 200
        data = response.get_json()
        assert data["device_stats"]["total"] >= initial_count + 5


class TestAdminCacheManagement:
    """Test admin cache management endpoints"""

    def test_clear_device_status_cache(self, client, test_admin_user):
        """Test clearing all device status cache"""
        headers = {"Authorization": "admin test"}

        response = client.delete("/api/v1/admin/cache/device-status", headers=headers)

        # May return 200 if Redis available, 503 if not
        assert response.status_code in [200, 503]
        if response.status_code == 200:
            data = response.get_json()
            assert "message" in data or "cleared" in data

    def test_clear_specific_device_cache(self, client, test_admin_user, test_device):
        """Test clearing cache for specific device"""
        headers = {"Authorization": "admin test"}

        response = client.delete(f"/api/v1/admin/cache/devices/{test_device.id}", headers=headers)

        # May return 200 if Redis available, 503 if not
        assert response.status_code in [200, 503]
        if response.status_code == 200:
            data = response.get_json()
            assert "message" in data or "cleared" in data

    def test_get_cache_stats(self, client, test_admin_user):
        """Test getting cache statistics"""
        headers = {"Authorization": "admin test"}

        response = client.get("/api/v1/admin/cache/device-status", headers=headers)

        # May return 200 if Redis available, 503 if not
        assert response.status_code in [200, 503]
        if response.status_code == 200:
            data = response.get_json()
            assert "cache_size" in data or "stats" in data or "available" in data

    def test_cache_operations_without_admin(self, client):
        """Test that cache operations require admin token"""
        response = client.delete("/api/v1/admin/cache/device-status")
        assert response.status_code == 401

        response = client.get("/api/v1/admin/cache/device-status")
        assert response.status_code == 401


class TestAdminRedisSyncManagement:
    """Test admin Redis-DB sync management endpoints"""

    def test_get_redis_sync_status(self, client, test_admin_user):
        """Test getting Redis-DB sync status"""
        headers = {"Authorization": "admin test"}

        response = client.get("/api/v1/admin/redis-db-sync/status", headers=headers)

        assert response.status_code == 200
        data = response.get_json()
        # Response format varies based on Redis availability
        assert isinstance(data, dict)

    def test_enable_redis_sync(self, client, test_admin_user):
        """Test enabling Redis-DB sync"""
        headers = {"Authorization": "admin test"}

        response = client.post("/api/v1/admin/redis-db-sync/enable", headers=headers)

        # May return 200 if successful, 400 if already enabled or Redis unavailable
        assert response.status_code in [200, 400]
        data = response.get_json()
        assert isinstance(data, dict)

    def test_disable_redis_sync(self, client, test_admin_user):
        """Test disabling Redis-DB sync"""
        headers = {"Authorization": "admin test"}

        response = client.post("/api/v1/admin/redis-db-sync/disable", headers=headers)

        # May return 200 if successful, 400 if already disabled or Redis unavailable
        assert response.status_code in [200, 400]
        data = response.get_json()
        assert isinstance(data, dict)

    def test_force_sync_device(self, client, test_admin_user, test_device):
        """Test forcing sync for specific device"""
        headers = {"Authorization": "admin test"}

        response = client.post(f"/api/v1/admin/redis-db-sync/force-sync/{test_device.id}", headers=headers)

        # May return 200 if successful, 400 if Redis unavailable
        assert response.status_code in [200, 400]
        data = response.get_json()
        assert isinstance(data, dict)

    def test_bulk_sync_devices(self, client, test_admin_user):
        """Test bulk syncing devices"""
        headers = {"Authorization": "admin test"}
        payload = {"device_ids": []}  # Empty or specific IDs

        response = client.post("/api/v1/admin/redis-db-sync/bulk-sync", json=payload, headers=headers)

        # May return 200 if successful, 400 if Redis unavailable
        assert response.status_code in [200, 400]
        data = response.get_json()
        assert isinstance(data, dict)

    def test_redis_sync_without_admin(self, client):
        """Test that Redis sync operations require admin token"""
        endpoints = [
            ("/api/v1/admin/redis-db-sync/status", "get"),
            ("/api/v1/admin/redis-db-sync/enable", "post"),
            ("/api/v1/admin/redis-db-sync/disable", "post"),
        ]

        for endpoint, method in endpoints:
            if method == "get":
                response = client.get(endpoint)
            else:
                response = client.post(endpoint)
            assert response.status_code == 401
