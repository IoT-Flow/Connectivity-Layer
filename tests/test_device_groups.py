"""
Test suite for Device Groups feature
Following TDD approach - tests written before implementation
"""

import pytest
import os

os.environ['DATABASE_URL'] = 'sqlite:///:memory:'

from app import create_app
from src.models import db, User, Device


@pytest.fixture
def app():
    """Create test app"""
    app = create_app()
    app.config['TESTING'] = True
    app.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite:///:memory:'
    
    with app.app_context():
        db.create_all()
        yield app
        db.session.remove()
        db.drop_all()


@pytest.fixture
def client(app):
    """Test client"""
    return app.test_client()


@pytest.fixture
def test_user(app):
    """Create a test user"""
    with app.app_context():
        user = User(
            username="testuser",
            email="test@example.com",
            user_id="test_user_123"
        )
        user.set_password("password123")
        db.session.add(user)
        db.session.commit()
        user_data = {
            'id': user.id,
            'user_id': user.user_id,
            'username': user.username
        }
        return user_data


@pytest.fixture
def test_devices(app, test_user):
    """Create test devices"""
    with app.app_context():
        devices = []
        for i in range(5):
            device = Device(
                name=f"Test Device {i+1}",
                description=f"Test device {i+1}",
                device_type="sensor",
                user_id=test_user['id'],
                status="active"
            )
            db.session.add(device)
            devices.append(device)
        db.session.commit()
        device_data = [{'id': d.id, 'name': d.name} for d in devices]
        return device_data


class TestDeviceGroupCreation:
    """Test device group creation"""
    
    def test_create_group_success(self, client, test_user):
        """Test creating a device group successfully"""
        response = client.post(
            "/api/v1/groups",
            json={
                "name": "Living Room",
                "description": "All living room devices",
                "color": "#FF5733"
            },
            headers={"X-User-ID": test_user['user_id']}
        )
        
        assert response.status_code == 201
        data = response.get_json()
        assert data["status"] == "success"
        assert data["group"]["name"] == "Living Room"
        assert data["group"]["description"] == "All living room devices"
        assert data["group"]["color"] == "#FF5733"
        assert data["group"]["user_id"] == test_user['id']
        assert data["group"]["device_count"] == 0
    
    def test_create_group_missing_name(self, client, test_user):
        """Test creating group without name fails"""
        response = client.post(
            "/api/v1/groups",
            json={"description": "Test"},
            headers={"X-User-ID": test_user['user_id']}
        )
        
        assert response.status_code == 400
        data = response.get_json()
        assert "name" in data["error"].lower()
    
    def test_create_group_no_auth(self, client):
        """Test creating group without authentication fails"""
        response = client.post(
            "/api/v1/groups",
            json={"name": "Test Group"}
        )
        
        assert response.status_code == 401
    
    def test_create_group_duplicate_name(self, client, test_user):
        """Test creating group with duplicate name fails"""
        # Create first group
        client.post(
            "/api/v1/groups",
            json={"name": "Living Room"},
            headers={"X-User-ID": test_user['user_id']}
        )
        
        # Try to create duplicate
        response = client.post(
            "/api/v1/groups",
            json={"name": "Living Room"},
            headers={"X-User-ID": test_user['user_id']}
        )
        
        assert response.status_code == 409


class TestDeviceGroupListing:
    """Test listing device groups"""
    
    def test_list_groups_empty(self, client, test_user):
        """Test listing groups when user has none"""
        response = client.get(
            "/api/v1/groups",
            headers={"X-User-ID": test_user['user_id']}
        )
        
        assert response.status_code == 200
        data = response.get_json()
        assert data["status"] == "success"
        assert len(data["groups"]) == 0
    
    def test_list_groups_with_data(self, client, test_user):
        """Test listing groups with data"""
        # Create groups
        for i in range(3):
            client.post(
                "/api/v1/groups",
                json={"name": f"Group {i+1}"},
                headers={"X-User-ID": test_user['user_id']}
            )
        
        response = client.get(
            "/api/v1/groups",
            headers={"X-User-ID": test_user['user_id']}
        )
        
        assert response.status_code == 200
        data = response.get_json()
        assert len(data["groups"]) == 3
        assert data["meta"]["total"] == 3


class TestDeviceGroupDetails:
    """Test getting group details"""
    
    def test_get_group_details(self, client, test_user):
        """Test getting group details"""
        # Create group
        create_response = client.post(
            "/api/v1/groups",
            json={"name": "Test Group"},
            headers={"X-User-ID": test_user['user_id']}
        )
        group_id = create_response.get_json()["group"]["id"]
        
        # Get details
        response = client.get(
            f"/api/v1/groups/{group_id}",
            headers={"X-User-ID": test_user['user_id']}
        )
        
        assert response.status_code == 200
        data = response.get_json()
        assert data["group"]["name"] == "Test Group"
    
    def test_get_group_not_found(self, client, test_user):
        """Test getting non-existent group"""
        response = client.get(
            "/api/v1/groups/999",
            headers={"X-User-ID": test_user['user_id']}
        )
        
        assert response.status_code == 404
    
    def test_get_group_wrong_user(self, client, test_user, app):
        """Test getting another user's group fails"""
        # Create another user
        with app.app_context():
            other_user = User(
                username="otheruser",
                email="other@example.com",
                user_id="other_user_123"
            )
            other_user.set_password("password")
            db.session.add(other_user)
            db.session.commit()
            other_user_id = other_user.user_id
        
        # Create group as test_user
        create_response = client.post(
            "/api/v1/groups",
            json={"name": "Test Group"},
            headers={"X-User-ID": test_user['user_id']}
        )
        group_id = create_response.get_json()["group"]["id"]
        
        # Try to access as other_user
        response = client.get(
            f"/api/v1/groups/{group_id}",
            headers={"X-User-ID": other_user_id}
        )
        
        assert response.status_code == 403


class TestDeviceGroupUpdate:
    """Test updating device groups"""
    
    def test_update_group(self, client, test_user):
        """Test updating group details"""
        # Create group
        create_response = client.post(
            "/api/v1/groups",
            json={"name": "Old Name"},
            headers={"X-User-ID": test_user['user_id']}
        )
        group_id = create_response.get_json()["group"]["id"]
        
        # Update group
        response = client.put(
            f"/api/v1/groups/{group_id}",
            json={
                "name": "New Name",
                "description": "Updated description",
                "color": "#33FF57"
            },
            headers={"X-User-ID": test_user['user_id']}
        )
        
        assert response.status_code == 200
        data = response.get_json()
        assert data["group"]["name"] == "New Name"
        assert data["group"]["description"] == "Updated description"
        assert data["group"]["color"] == "#33FF57"


class TestDeviceGroupDeletion:
    """Test deleting device groups"""
    
    def test_delete_group(self, client, test_user):
        """Test deleting a group"""
        # Create group
        create_response = client.post(
            "/api/v1/groups",
            json={"name": "Test Group"},
            headers={"X-User-ID": test_user['user_id']}
        )
        group_id = create_response.get_json()["group"]["id"]
        
        # Delete group
        response = client.delete(
            f"/api/v1/groups/{group_id}",
            headers={"X-User-ID": test_user['user_id']}
        )
        
        assert response.status_code == 200
        
        # Verify it's deleted
        get_response = client.get(
            f"/api/v1/groups/{group_id}",
            headers={"X-User-ID": test_user['user_id']}
        )
        assert get_response.status_code == 404


class TestDeviceGroupMembership:
    """Test adding/removing devices to/from groups"""
    
    def test_add_device_to_group(self, client, test_user, test_devices):
        """Test adding a device to a group"""
        # Create group
        create_response = client.post(
            "/api/v1/groups",
            json={"name": "Test Group"},
            headers={"X-User-ID": test_user['user_id']}
        )
        group_id = create_response.get_json()["group"]["id"]
        
        # Add device
        response = client.post(
            f"/api/v1/groups/{group_id}/devices",
            json={"device_id": test_devices[0]['id']},
            headers={"X-User-ID": test_user['user_id']}
        )
        
        assert response.status_code == 201
        data = response.get_json()
        assert data["status"] == "success"
        assert data["membership"]["device_id"] == test_devices[0]['id']
    
    def test_add_device_duplicate(self, client, test_user, test_devices):
        """Test adding same device twice fails"""
        # Create group
        create_response = client.post(
            "/api/v1/groups",
            json={"name": "Test Group"},
            headers={"X-User-ID": test_user['user_id']}
        )
        group_id = create_response.get_json()["group"]["id"]
        
        # Add device first time
        client.post(
            f"/api/v1/groups/{group_id}/devices",
            json={"device_id": test_devices[0]['id']},
            headers={"X-User-ID": test_user['user_id']}
        )
        
        # Try to add again
        response = client.post(
            f"/api/v1/groups/{group_id}/devices",
            json={"device_id": test_devices[0]['id']},
            headers={"X-User-ID": test_user['user_id']}
        )
        
        assert response.status_code == 409
    
    def test_remove_device_from_group(self, client, test_user, test_devices):
        """Test removing a device from a group"""
        # Create group and add device
        create_response = client.post(
            "/api/v1/groups",
            json={"name": "Test Group"},
            headers={"X-User-ID": test_user['user_id']}
        )
        group_id = create_response.get_json()["group"]["id"]
        
        client.post(
            f"/api/v1/groups/{group_id}/devices",
            json={"device_id": test_devices[0]['id']},
            headers={"X-User-ID": test_user['user_id']}
        )
        
        # Remove device
        response = client.delete(
            f"/api/v1/groups/{group_id}/devices/{test_devices[0]['id']}",
            headers={"X-User-ID": test_user['user_id']}
        )
        
        assert response.status_code == 200
    
    def test_bulk_add_devices(self, client, test_user, test_devices):
        """Test adding multiple devices at once"""
        # Create group
        create_response = client.post(
            "/api/v1/groups",
            json={"name": "Test Group"},
            headers={"X-User-ID": test_user['user_id']}
        )
        group_id = create_response.get_json()["group"]["id"]
        
        # Bulk add
        device_ids = [d['id'] for d in test_devices[:3]]
        response = client.post(
            f"/api/v1/groups/{group_id}/devices/bulk",
            json={"device_ids": device_ids},
            headers={"X-User-ID": test_user['user_id']}
        )
        
        assert response.status_code == 201
        data = response.get_json()
        assert data["added"] == 3


class TestGroupDevicesListing:
    """Test listing devices in a group"""
    
    def test_list_group_devices(self, client, test_user, test_devices):
        """Test listing devices in a group"""
        # Create group and add devices
        create_response = client.post(
            "/api/v1/groups",
            json={"name": "Test Group"},
            headers={"X-User-ID": test_user['user_id']}
        )
        group_id = create_response.get_json()["group"]["id"]
        
        for device in test_devices[:2]:
            client.post(
                f"/api/v1/groups/{group_id}/devices",
                json={"device_id": device['id']},
                headers={"X-User-ID": test_user['user_id']}
            )
        
        # List devices
        response = client.get(
            f"/api/v1/groups/{group_id}/devices",
            headers={"X-User-ID": test_user['user_id']}
        )
        
        assert response.status_code == 200
        data = response.get_json()
        assert len(data["devices"]) == 2


class TestDeviceGroupsListing:
    """Test listing groups for a device"""
    
    def test_list_device_groups(self, client, test_user, test_devices):
        """Test listing groups that contain a device"""
        # Create groups
        group_ids = []
        for i in range(2):
            create_response = client.post(
                "/api/v1/groups",
                json={"name": f"Group {i+1}"},
                headers={"X-User-ID": test_user['user_id']}
            )
            group_ids.append(create_response.get_json()["group"]["id"])
        
        # Add device to both groups
        for group_id in group_ids:
            client.post(
                f"/api/v1/groups/{group_id}/devices",
                json={"device_id": test_devices[0]['id']},
                headers={"X-User-ID": test_user['user_id']}
            )
        
        # List device's groups
        response = client.get(
            f"/api/v1/devices/{test_devices[0]['id']}/groups",
            headers={"X-User-ID": test_user['user_id']}
        )
        
        assert response.status_code == 200
        data = response.get_json()
        assert data["total_groups"] == 2
        assert len(data["groups"]) == 2
