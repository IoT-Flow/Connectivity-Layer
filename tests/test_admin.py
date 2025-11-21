"""
TDD Test Suite for Admin Management
Following TDD approach - write tests first, then implement/fix functionality
"""

import pytest
import os
from datetime import datetime, timezone

os.environ['DATABASE_URL'] = 'sqlite:///:memory:'
os.environ['IOTFLOW_ADMIN_TOKEN'] = 'test_admin_token'

from app import create_app
from src.models import db, User, Device


@pytest.fixture
def app():
    """Create test app"""
    app = create_app()
    app.config['TESTING'] = True
    app.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite:///:memory:'
    app.config['IOTFLOW_ADMIN_TOKEN'] = 'test_admin_token'
    
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
def test_device(app, test_user):
    """Create test device"""
    with app.app_context():
        device = Device(
            name='Test Device',
            device_type='sensor',
            user_id=test_user['id'],
            status='active'
        )
        db.session.add(device)
        db.session.commit()
        return {
            'id': device.id,
            'api_key': device.api_key,
            'name': device.name
        }


@pytest.fixture
def admin_headers():
    """Admin authentication headers"""
    return {'Authorization': 'admin test_admin_token'}


class TestAdminAuthentication:
    """Test admin authentication"""
    
    def test_admin_endpoint_requires_auth(self, client):
        """Test that admin endpoints require authentication"""
        response = client.get('/api/v1/admin/devices')
        
        # Should return 401 or 403 without auth
        assert response.status_code in [401, 403]
    
    def test_admin_endpoint_with_invalid_token(self, client):
        """Test admin endpoint with invalid token"""
        response = client.get(
            '/api/v1/admin/devices',
            headers={'Authorization': 'Bearer invalid_token'}
        )
        
        # Should return 401 or 403
        assert response.status_code in [401, 403]
    
    def test_admin_endpoint_with_valid_token(self, client, admin_headers):
        """Test admin endpoint with valid token"""
        response = client.get(
            '/api/v1/admin/devices',
            headers=admin_headers
        )
        
        # Should return 200 (success)
        assert response.status_code == 200


class TestAdminDeviceManagement:
    """Test admin device management"""
    
    def test_list_all_devices_endpoint_exists(self, client, admin_headers):
        """Test that GET /api/v1/admin/devices endpoint exists"""
        response = client.get('/api/v1/admin/devices', headers=admin_headers)
        
        # Should not return 404
        assert response.status_code != 404
    
    def test_list_all_devices_empty(self, client, admin_headers):
        """Test listing devices when none exist"""
        response = client.get('/api/v1/admin/devices', headers=admin_headers)
        
        assert response.status_code == 200
        data = response.get_json()
        assert 'devices' in data
        assert isinstance(data['devices'], list)
    
    def test_list_all_devices_with_data(self, client, admin_headers, test_device):
        """Test listing devices with data"""
        response = client.get('/api/v1/admin/devices', headers=admin_headers)
        
        assert response.status_code == 200
        data = response.get_json()
        assert 'devices' in data
        assert len(data['devices']) >= 1
        assert 'total_devices' in data
    
    def test_list_devices_hides_api_keys(self, client, admin_headers, test_device):
        """Test that API keys are not exposed in device listing"""
        response = client.get('/api/v1/admin/devices', headers=admin_headers)
        
        assert response.status_code == 200
        data = response.get_json()
        if len(data['devices']) > 0:
            # API keys should not be in the response
            assert 'api_key' not in data['devices'][0]
    
    def test_get_device_details_endpoint_exists(self, client, admin_headers, test_device):
        """Test that GET /api/v1/admin/devices/:id endpoint exists"""
        response = client.get(
            f'/api/v1/admin/devices/{test_device["id"]}',
            headers=admin_headers
        )
        
        # Should not return 404
        assert response.status_code != 404
    
    def test_get_device_details_success(self, client, admin_headers, test_device):
        """Test getting device details"""
        response = client.get(
            f'/api/v1/admin/devices/{test_device["id"]}',
            headers=admin_headers
        )
        
        assert response.status_code == 200
        data = response.get_json()
        assert 'device' in data
        assert data['device']['name'] == test_device['name']
    
    def test_get_device_details_not_found(self, client, admin_headers):
        """Test getting details of non-existent device"""
        response = client.get(
            '/api/v1/admin/devices/99999',
            headers=admin_headers
        )
        
        assert response.status_code == 404
    
    def test_update_device_status_endpoint_exists(self, client, admin_headers, test_device):
        """Test that PUT /api/v1/admin/devices/:id/status endpoint exists"""
        response = client.put(
            f'/api/v1/admin/devices/{test_device["id"]}/status',
            json={'status': 'inactive'},
            headers=admin_headers
        )
        
        # Should not return 404
        assert response.status_code != 404
    
    def test_update_device_status_success(self, client, admin_headers, test_device):
        """Test updating device status"""
        response = client.put(
            f'/api/v1/admin/devices/{test_device["id"]}/status',
            json={'status': 'inactive'},
            headers=admin_headers
        )
        
        assert response.status_code == 200
        data = response.get_json()
        assert data['new_status'] == 'inactive'
    
    def test_update_device_status_invalid_status(self, client, admin_headers, test_device):
        """Test updating device with invalid status"""
        response = client.put(
            f'/api/v1/admin/devices/{test_device["id"]}/status',
            json={'status': 'invalid_status'},
            headers=admin_headers
        )
        
        # Should return 400 Bad Request
        assert response.status_code == 400
    
    def test_delete_device_endpoint_exists(self, client, admin_headers, test_device):
        """Test that DELETE /api/v1/admin/devices/:id endpoint exists"""
        response = client.delete(
            f'/api/v1/admin/devices/{test_device["id"]}',
            headers=admin_headers
        )
        
        # Should not return 404
        assert response.status_code != 404
    
    def test_delete_device_success(self, client, admin_headers, test_device):
        """Test deleting a device"""
        response = client.delete(
            f'/api/v1/admin/devices/{test_device["id"]}',
            headers=admin_headers
        )
        
        assert response.status_code == 200
        
        # Verify device is deleted
        response = client.get(
            f'/api/v1/admin/devices/{test_device["id"]}',
            headers=admin_headers
        )
        assert response.status_code == 404


class TestAdminSystemStats:
    """Test admin system statistics"""
    
    def test_system_stats_endpoint_exists(self, client, admin_headers):
        """Test that GET /api/v1/admin/stats endpoint exists"""
        response = client.get('/api/v1/admin/stats', headers=admin_headers)
        
        # Should not return 404
        assert response.status_code != 404
    
    def test_system_stats_returns_data(self, client, admin_headers):
        """Test that system stats returns data"""
        response = client.get('/api/v1/admin/stats', headers=admin_headers)
        
        assert response.status_code == 200
        data = response.get_json()
        assert data is not None
        # Should have some statistics
        assert 'total_devices' in data or 'devices' in data or 'stats' in data
    
    def test_system_stats_with_devices(self, client, admin_headers, test_device):
        """Test system stats with devices"""
        response = client.get('/api/v1/admin/stats', headers=admin_headers)
        
        assert response.status_code == 200
        data = response.get_json()
        # Should show at least 1 device
        if 'total_devices' in data:
            assert data['total_devices'] >= 1


class TestAdminSecurity:
    """Test admin security features"""
    
    def test_admin_endpoints_not_accessible_with_device_api_key(self, client, test_device):
        """Test that device API keys don't work for admin endpoints"""
        response = client.get(
            '/api/v1/admin/devices',
            headers={'X-API-Key': test_device['api_key']}
        )
        
        # Should return 401 or 403
        assert response.status_code in [401, 403]
    
    def test_admin_endpoints_not_accessible_without_admin_prefix(self, client):
        """Test that admin token requires 'admin' prefix"""
        response = client.get(
            '/api/v1/admin/devices',
            headers={'Authorization': 'test_admin_token'}  # Missing 'admin '
        )
        
        # Should return 401 or 403
        assert response.status_code in [401, 403]


if __name__ == '__main__':
    pytest.main([__file__, '-v'])
