"""
Basic integration tests for admin API endpoints.
"""
import pytest
import json


class TestAdminBasicEndpoints:
    """Test basic admin endpoints that should work."""

    def test_admin_devices_list_unauthorized(self, client):
        """Test admin devices list without authorization."""
        response = client.get("/api/v1/admin/devices")
        assert response.status_code == 401

    def test_admin_device_details_unauthorized(self, client):
        """Test admin device details without authorization."""
        response = client.get("/api/v1/admin/devices/1")
        assert response.status_code == 401

    def test_admin_stats_unauthorized(self, client):
        """Test admin stats without authorization."""
        response = client.get("/api/v1/admin/stats")
        assert response.status_code == 401

    def test_admin_delete_device_unauthorized(self, client):
        """Test admin delete device without authorization."""
        response = client.delete("/api/v1/admin/devices/1")
        assert response.status_code == 401

    def test_admin_update_device_status_unauthorized(self, client):
        """Test admin update device status without authorization."""
        response = client.put("/api/v1/admin/devices/1/status", json={"status": "active"})
        assert response.status_code == 401

    def test_admin_cache_clear_unauthorized(self, client):
        """Test admin cache clear without authorization."""
        response = client.delete("/api/v1/admin/cache/device-status")
        assert response.status_code == 401

    def test_admin_cache_stats_unauthorized(self, client):
        """Test admin cache stats without authorization."""
        response = client.get("/api/v1/admin/cache/device-status")
        assert response.status_code == 401

    def test_admin_redis_sync_status_unauthorized(self, client):
        """Test admin redis sync status without authorization."""
        response = client.get("/api/v1/admin/redis-db-sync/status")
        assert response.status_code == 401
