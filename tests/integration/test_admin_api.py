"""
Integration tests for admin API endpoints.
"""
import pytest
import json
from src.models import Device, User, db


class TestAdminDeviceManagement:
    """Test admin device management endpoints."""

    def test_list_all_devices(self, client, admin_token, test_device):
        """Test listing all devices as admin."""
        headers = {"Authorization": f"Bearer {admin_token}"}

        response = client.get("/api/v1/admin/devices", headers=headers)

        assert response.status_code == 200
        data = response.get_json()
        assert "devices" in data
        assert len(data["devices"]) >= 1

        # Check device data structure
        device = data["devices"][0]
        assert "id" in device
        assert "name" in device
        assert "status" in device
        assert "user_id" in device

    def test_list_devices_without_admin_token(self, client, test_device):
        """Test listing devices without admin token."""
        response = client.get("/api/v1/admin/devices")

        assert response.status_code == 401

    def test_list_devices_with_pagination(self, client, admin_token, app):
        """Test listing devices with pagination."""
        # Create multiple devices
        with app.app_context():
            user = User.query.first()
            for i in range(5):
                device = Device(name=f"test_device_{i}", user_id=user.id, device_type="sensor")
                db.session.add(device)
            db.session.commit()

        headers = {"Authorization": f"Bearer {admin_token}"}

        # Test with limit
        response = client.get("/api/v1/admin/devices?limit=3", headers=headers)
        assert response.status_code == 200
        data = response.get_json()
        assert len(data["devices"]) <= 3

        # Test with offset
        response = client.get("/api/v1/admin/devices?offset=2&limit=2", headers=headers)
        assert response.status_code == 200
        data = response.get_json()
        assert len(data["devices"]) <= 2

    def test_get_device_details(self, client, admin_token, test_device):
        """Test getting device details as admin."""
        headers = {"Authorization": f"Bearer {admin_token}"}

        response = client.get(f"/api/v1/admin/devices/{test_device.id}", headers=headers)

        assert response.status_code == 200
        data = response.get_json()
        assert data["id"] == test_device.id
        assert data["name"] == test_device.name
        assert "api_key" in data
        assert "created_at" in data
        assert "last_seen" in data

    def test_get_device_details_not_found(self, client, admin_token):
        """Test getting details for non-existent device."""
        headers = {"Authorization": f"Bearer {admin_token}"}

        response = client.get("/api/v1/admin/devices/999999", headers=headers)

        assert response.status_code == 404

    def test_update_device_status(self, client, admin_token, test_device):
        """Test updating device status as admin."""
        headers = {"Authorization": f"Bearer {admin_token}"}
        payload = {"status": "maintenance"}

        response = client.put(f"/api/v1/admin/devices/{test_device.id}/status", json=payload, headers=headers)

        assert response.status_code == 200
        data = response.get_json()
        assert data["status"] == "maintenance"

    def test_delete_device(self, client, admin_token, app):
        """Test deleting device as admin."""
        # Create a device to delete
        with app.app_context():
            user = User.query.first()
            device = Device(name="device_to_delete", user_id=user.id, device_type="sensor")
            db.session.add(device)
            db.session.commit()
            device_id = device.id

        headers = {"Authorization": f"Bearer {admin_token}"}

        response = client.delete(f"/api/v1/admin/devices/{device_id}", headers=headers)

        assert response.status_code == 200

        # Verify device is deleted
        with app.app_context():
            deleted_device = Device.query.get(device_id)
            assert deleted_device is None

    def test_delete_device_not_found(self, client, admin_token):
        """Test deleting non-existent device."""
        headers = {"Authorization": f"Bearer {admin_token}"}

        response = client.delete("/api/v1/admin/devices/999999", headers=headers)

        assert response.status_code == 404


class TestAdminSystemStats:
    """Test admin system statistics endpoints."""

    def test_get_system_stats(self, client, admin_token, test_device):
        """Test getting system statistics."""
        headers = {"Authorization": f"Bearer {admin_token}"}

        response = client.get("/api/v1/admin/stats", headers=headers)

        assert response.status_code == 200
        data = response.get_json()

        # Check required statistics
        assert "total_devices" in data
        assert "active_devices" in data
        assert "total_users" in data
        assert "system_health" in data
        assert data["total_devices"] >= 1

    def test_get_system_stats_without_admin(self, client):
        """Test getting system stats without admin token."""
        response = client.get("/api/v1/admin/stats")

        assert response.status_code == 401

    def test_system_stats_accuracy(self, client, admin_token, app):
        """Test system statistics accuracy."""
        # Create known number of devices and users
        with app.app_context():
            initial_device_count = Device.query.count()
            initial_user_count = User.query.count()

            # Add more test data
            user = User(username="stats_user", email="stats@test.com")
            db.session.add(user)
            db.session.commit()

            for i in range(3):
                device = Device(
                    name=f"stats_device_{i}",
                    user_id=user.id,
                    device_type="sensor",
                    status="active" if i < 2 else "inactive",
                )
                db.session.add(device)
            db.session.commit()

        headers = {"Authorization": f"Bearer {admin_token}"}
        response = client.get("/api/v1/admin/stats", headers=headers)

        assert response.status_code == 200
        data = response.get_json()

        assert data["total_devices"] == initial_device_count + 3
        assert data["total_users"] == initial_user_count + 1
        assert data["active_devices"] >= 2
