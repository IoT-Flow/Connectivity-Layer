"""
TDD Test Suite for User Devices Endpoint
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
    """Create test user"""
    with app.app_context():
        user = User(username='testuser', email='test@example.com', password_hash='hash')
        db.session.add(user)
        db.session.commit()
        return {
            'id': user.id,
            'user_id': user.user_id,
            'username': user.username
        }


@pytest.fixture
def test_user_with_devices(app):
    """Create test user with multiple devices"""
    with app.app_context():
        user = User(username='deviceowner', email='owner@example.com', password_hash='hash')
        db.session.add(user)
        db.session.commit()
        
        # Create multiple devices
        devices = []
        for i in range(5):
            device = Device(
                name=f'Device {i+1}',
                device_type='sensor',
                user_id=user.id,
                status='active' if i < 3 else 'inactive'
            )
            db.session.add(device)
            devices.append(device)
        
        db.session.commit()
        
        return {
            'id': user.id,
            'user_id': user.user_id,
            'username': user.username,
            'device_count': len(devices)
        }


class TestGetUserDevices:
    """Test getting devices for a specific user"""
    
    def test_endpoint_exists(self, client, test_user):
        """Test that GET /api/v1/devices/user/{user_id} endpoint exists"""
        response = client.get(f'/api/v1/devices/user/{test_user["user_id"]}')
        
        # Should not return 404
        assert response.status_code != 404
    
    def test_get_user_devices_empty(self, client, test_user):
        """Test getting devices for user with no devices"""
        response = client.get(f'/api/v1/devices/user/{test_user["user_id"]}')
        
        assert response.status_code == 200
        data = response.get_json()
        assert data['status'] == 'success'
        assert data['user_id'] == test_user['user_id']
        assert data['total_devices'] == 0
        assert len(data['devices']) == 0
    
    def test_get_user_devices_success(self, client, test_user_with_devices):
        """Test getting devices for user with devices"""
        response = client.get(f'/api/v1/devices/user/{test_user_with_devices["user_id"]}')
        
        assert response.status_code == 200
        data = response.get_json()
        assert data['status'] == 'success'
        assert data['user_id'] == test_user_with_devices['user_id']
        assert data['username'] == test_user_with_devices['username']
        assert data['total_devices'] == 5
        assert len(data['devices']) == 5
    
    def test_get_user_devices_invalid_user(self, client):
        """Test getting devices for non-existent user"""
        response = client.get('/api/v1/devices/user/invalid-user-id')
        
        assert response.status_code == 404
        data = response.get_json()
        assert 'error' in data
        assert 'User not found' in data['error']
    
    def test_get_user_devices_filter_by_status(self, client, test_user_with_devices):
        """Test filtering devices by status"""
        # Get only active devices
        response = client.get(
            f'/api/v1/devices/user/{test_user_with_devices["user_id"]}?status=active'
        )
        
        assert response.status_code == 200
        data = response.get_json()
        assert data['status'] == 'success'
        assert data['total_devices'] == 3  # Only 3 active devices
        assert len(data['devices']) == 3
        
        # Verify all returned devices are active
        for device in data['devices']:
            assert device['status'] == 'active'
    
    def test_get_user_devices_pagination(self, client, test_user_with_devices):
        """Test pagination of user devices"""
        # Get first 2 devices
        response = client.get(
            f'/api/v1/devices/user/{test_user_with_devices["user_id"]}?limit=2&offset=0'
        )
        
        assert response.status_code == 200
        data = response.get_json()
        assert data['status'] == 'success'
        assert data['total_devices'] == 5
        assert len(data['devices']) == 2
        assert data['meta']['limit'] == 2
        assert data['meta']['offset'] == 0
        assert data['meta']['returned'] == 2
        
        # Get next 2 devices
        response = client.get(
            f'/api/v1/devices/user/{test_user_with_devices["user_id"]}?limit=2&offset=2'
        )
        
        assert response.status_code == 200
        data = response.get_json()
        assert len(data['devices']) == 2
        assert data['meta']['offset'] == 2
    
    def test_get_user_devices_no_api_key_in_response(self, client, test_user_with_devices):
        """Test that API keys are not included in device list"""
        response = client.get(f'/api/v1/devices/user/{test_user_with_devices["user_id"]}')
        
        assert response.status_code == 200
        data = response.get_json()
        
        # Verify no device has api_key in response
        for device in data['devices']:
            assert 'api_key' not in device
    
    def test_get_user_devices_response_structure(self, client, test_user_with_devices):
        """Test response structure"""
        response = client.get(f'/api/v1/devices/user/{test_user_with_devices["user_id"]}')
        
        assert response.status_code == 200
        data = response.get_json()
        
        # Check required fields
        assert 'status' in data
        assert 'user_id' in data
        assert 'username' in data
        assert 'total_devices' in data
        assert 'devices' in data
        assert 'meta' in data
        
        # Check meta structure
        assert 'limit' in data['meta']
        assert 'offset' in data['meta']
        assert 'returned' in data['meta']
        
        # Check device structure
        if len(data['devices']) > 0:
            device = data['devices'][0]
            assert 'id' in device
            assert 'name' in device
            assert 'device_type' in device
            assert 'status' in device


if __name__ == '__main__':
    pytest.main([__file__, '-v'])
