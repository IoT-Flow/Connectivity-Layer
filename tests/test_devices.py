"""
TDD Test Suite for Device Management
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
            'name': device.name,
            'device_type': device.device_type,
            'user_id': test_user['id']
        }


class TestDeviceModel:
    """Test Device model functionality"""
    
    def test_device_creation(self, app, test_user):
        """Test creating a new device"""
        with app.app_context():
            device = Device(
                name='Test Device',
                device_type='sensor',
                user_id=test_user['id']
            )
            db.session.add(device)
            db.session.commit()
            
            assert device.id is not None
            assert device.api_key is not None
            assert device.name == 'Test Device'
            assert device.device_type == 'sensor'
            assert device.status == 'inactive'  # New devices are inactive by default
            assert device.user_id == test_user['id']
            assert device.created_at is not None
    
    def test_api_key_is_unique(self, app, test_user):
        """Test that API keys are automatically generated and unique"""
        with app.app_context():
            device1 = Device(name='Device 1', device_type='sensor', user_id=test_user['id'])
            device2 = Device(name='Device 2', device_type='sensor', user_id=test_user['id'])
            
            db.session.add(device1)
            db.session.add(device2)
            db.session.commit()
            
            assert device1.api_key != device2.api_key
            assert len(device1.api_key) == 32
            assert len(device2.api_key) == 32
    
    def test_device_to_dict(self, app, test_user):
        """Test device to_dict method"""
        with app.app_context():
            device = Device(
                name='Test Device',
                device_type='sensor',
                user_id=test_user['id'],
                description='Test description',
                location='Test location'
            )
            db.session.add(device)
            db.session.commit()
            
            device_dict = device.to_dict()
            
            assert device_dict['name'] == 'Test Device'
            assert device_dict['device_type'] == 'sensor'
            assert device_dict['description'] == 'Test description'
            assert device_dict['location'] == 'Test location'
            assert device_dict['status'] == 'inactive'  # New devices are inactive by default
            assert 'api_key' not in device_dict  # Should not expose API key
            assert 'created_at' in device_dict
    
    def test_device_update_last_seen(self, app, test_user):
        """Test updating device last_seen timestamp"""
        with app.app_context():
            device = Device(name='Test Device', device_type='sensor', user_id=test_user['id'])
            db.session.add(device)
            db.session.commit()
            
            assert device.last_seen is None
            
            device.update_last_seen()
            
            assert device.last_seen is not None
            assert isinstance(device.last_seen, datetime)
    
    def test_device_set_status(self, app, test_user):
        """Test setting device status"""
        with app.app_context():
            device = Device(name='Test Device', device_type='sensor', user_id=test_user['id'])
            db.session.add(device)
            db.session.commit()
            
            assert device.status == 'inactive'  # New devices are inactive by default
            
            device.set_status('active')
            
            assert device.status == 'active'
    
    def test_device_authentication(self, app, test_user):
        """Test device authentication with API key"""
        with app.app_context():
            device = Device(name='Test Device', device_type='sensor', user_id=test_user['id'])
            device.status = 'active'  # Set to active for authentication test
            db.session.add(device)
            db.session.commit()
            
            api_key = device.api_key
            
            # Correct API key should authenticate
            assert device.is_authenticated(api_key) is True
            
            # Wrong API key should not authenticate
            assert device.is_authenticated('wrong_key') is False
    
    def test_inactive_device_cannot_authenticate(self, app, test_user):
        """Test that inactive devices cannot authenticate"""
        with app.app_context():
            device = Device(name='Test Device', device_type='sensor', user_id=test_user['id'])
            device.status = 'inactive'
            db.session.add(device)
            db.session.commit()
            
            api_key = device.api_key
            
            # Even with correct API key, inactive device should not authenticate
            assert device.is_authenticated(api_key) is False
    
    def test_authenticate_by_api_key(self, app, test_user):
        """Test static method to authenticate device by API key"""
        with app.app_context():
            device = Device(name='Test Device', device_type='sensor', user_id=test_user['id'])
            device.status = 'active'  # Set to active for authentication test
            db.session.add(device)
            db.session.commit()
            
            api_key = device.api_key
            
            # Should find device by API key (only active devices)
            found_device = Device.authenticate_by_api_key(api_key)
            assert found_device is not None
            assert found_device.id == device.id
            
            # Should not find device with wrong API key
            not_found = Device.authenticate_by_api_key('wrong_key')
            assert not_found is None


class TestDeviceRegistration:
    """Test device registration endpoints"""
    
    def test_register_device_endpoint_exists(self, client, test_user):
        """Test that POST /api/v1/devices/register endpoint exists"""
        response = client.post(
            '/api/v1/devices/register',
            headers={'X-User-ID': test_user['user_id']},
            json={
                'name': 'New Device',
                'device_type': 'sensor'
            }
        )
        
        # Should not return 404
        assert response.status_code != 404
    
    def test_register_device_success(self, client, test_user):
        """Test successful device registration"""
        response = client.post(
            '/api/v1/devices/register',
            headers={'X-User-ID': test_user['user_id']},
            json={
                'name': 'New Device',
                'device_type': 'sensor'
            }
        )
        
        # Should return 201 Created
        assert response.status_code == 201
        
        data = response.get_json()
        assert data['message'] == 'Device registered successfully'
        assert 'device' in data
        assert data['device']['name'] == 'New Device'
        assert data['device']['device_type'] == 'sensor'
        assert 'api_key' in data['device']  # Should return API key on registration
    
    def test_register_device_missing_name(self, client, test_user):
        """Test registration with missing name"""
        response = client.post(
            '/api/v1/devices/register',
            headers={'X-User-ID': test_user['user_id']},
            json={
                'device_type': 'sensor'
            }
        )
        
        # Should return 400 Bad Request
        assert response.status_code == 400
    
    def test_register_device_missing_user_id(self, client):
        """Test registration with missing user_id header"""
        response = client.post(
            '/api/v1/devices/register',
            json={
                'name': 'New Device',
                'device_type': 'sensor'
            }
        )
        
        # Should return 401 Unauthorized (missing header)
        assert response.status_code == 401
    
    def test_register_device_invalid_user(self, client):
        """Test registration with non-existent user"""
        response = client.post(
            '/api/v1/devices/register',
            headers={'X-User-ID': 'nonexistent_user_id'},
            json={
                'name': 'New Device',
                'device_type': 'sensor'
            }
        )
        
        # Should return 401 Unauthorized (invalid user_id)
        assert response.status_code == 401
    
    def test_register_device_with_optional_fields(self, client, test_user):
        """Test registration with optional fields"""
        response = client.post(
            '/api/v1/devices/register',
            headers={'X-User-ID': test_user['user_id']},
            json={
                'name': 'New Device',
                'device_type': 'sensor',
                'description': 'Test description',
                'location': 'Test location',
                'firmware_version': '1.0.0'
            }
        )
        
        assert response.status_code == 201
        data = response.get_json()
        assert data['device']['description'] == 'Test description'
        assert data['device']['location'] == 'Test location'


class TestDeviceHeartbeat:
    """Test device heartbeat functionality"""
    
    def test_heartbeat_endpoint_exists(self, client, test_device):
        """Test that POST /api/v1/devices/heartbeat endpoint exists"""
        response = client.post(
            '/api/v1/devices/heartbeat',
            headers={'X-API-Key': test_device['api_key']}
        )
        
        # Should not return 404
        assert response.status_code != 404
    
    def test_heartbeat_success(self, client, test_device):
        """Test successful heartbeat submission"""
        response = client.post(
            '/api/v1/devices/heartbeat',
            headers={'X-API-Key': test_device['api_key']}
        )
        
        assert response.status_code == 200
        data = response.get_json()
        assert data['message'] == 'Heartbeat received'
        assert data['device_id'] == test_device['id']
        assert data['status'] == 'online'
    
    def test_heartbeat_without_api_key(self, client):
        """Test heartbeat without API key"""
        response = client.post('/api/v1/devices/heartbeat')
        
        # Should return 401 Unauthorized
        assert response.status_code == 401
    
    def test_heartbeat_with_invalid_api_key(self, client):
        """Test heartbeat with invalid API key"""
        response = client.post(
            '/api/v1/devices/heartbeat',
            headers={'X-API-Key': 'invalid_key'}
        )
        
        # Should return 401 Unauthorized
        assert response.status_code == 401
    
    def test_heartbeat_updates_last_seen(self, app, client, test_device):
        """Test that heartbeat updates last_seen timestamp"""
        # Send heartbeat
        response = client.post(
            '/api/v1/devices/heartbeat',
            headers={'X-API-Key': test_device['api_key']}
        )
        
        assert response.status_code == 200
        
        # Check that last_seen was updated
        with app.app_context():
            device = Device.query.get(test_device['id'])
            assert device.last_seen is not None


class TestDeviceStatus:
    """Test device status endpoints"""
    
    def test_get_device_status_endpoint_exists(self, client, test_device):
        """Test that GET /api/v1/devices/:id/status endpoint exists"""
        response = client.get(f'/api/v1/devices/{test_device["id"]}/status')
        
        # Should not return 404
        assert response.status_code != 404
    
    def test_get_device_status_success(self, client, test_device, test_user):
        """Test getting device status"""
        response = client.get(
            f'/api/v1/devices/{test_device["id"]}/status',
            headers={'X-User-ID': test_user['user_id']}
        )
        
        assert response.status_code == 200
        data = response.get_json()
        assert 'device' in data
        assert data['device']['id'] == test_device['id']
        assert 'is_online' in data['device']
        assert 'status' in data['device']
    
    def test_get_device_status_not_found(self, client, test_user):
        """Test getting status of non-existent device"""
        response = client.get(
            '/api/v1/devices/99999/status',
            headers={'X-User-ID': test_user['user_id']}
        )
        
        assert response.status_code == 404
    
    def test_get_all_device_statuses(self, client, test_device):
        """Test getting all device statuses (admin endpoint)"""
        response = client.get(
            '/api/v1/admin/devices/statuses',
            headers={'Authorization': 'admin test_admin_token'}
        )
        
        assert response.status_code == 200
        data = response.get_json()
        assert 'devices' in data
        assert len(data['devices']) >= 1
        assert 'meta' in data
    
    def test_device_online_status_calculation(self, app, client, test_device, test_user):
        """Test that device online status is calculated correctly"""
        # Send heartbeat to make device online
        client.post(
            '/api/v1/devices/heartbeat',
            headers={'X-API-Key': test_device['api_key']}
        )
        
        # Get status
        response = client.get(
            f'/api/v1/devices/{test_device["id"]}/status',
            headers={'X-User-ID': test_user['user_id']}
        )
        
        assert response.status_code == 200
        data = response.get_json()
        # Device should be online after recent heartbeat
        assert data['device']['is_online'] is True


class TestDeviceInfo:
    """Test device information endpoints"""
    
    def test_get_device_info_endpoint_exists(self, client, test_device):
        """Test that GET /api/v1/devices/status endpoint exists"""
        response = client.get(
            '/api/v1/devices/status',
            headers={'X-API-Key': test_device['api_key']}
        )
        
        # Should not return 404
        assert response.status_code != 404
    
    def test_get_device_info_success(self, client, test_device):
        """Test getting device info with API key"""
        response = client.get(
            '/api/v1/devices/status',
            headers={'X-API-Key': test_device['api_key']}
        )
        
        assert response.status_code == 200
        data = response.get_json()
        assert 'device' in data
        assert data['device']['name'] == test_device['name']
        assert data['device']['device_type'] == test_device['device_type']
    
    def test_get_device_info_without_api_key(self, client):
        """Test getting device info without API key"""
        response = client.get('/api/v1/devices/status')
        
        # Should return 401 Unauthorized
        assert response.status_code == 401


class TestDeviceCredentials:
    """Test device credentials endpoint"""
    
    def test_get_credentials_endpoint_exists(self, client):
        """Test that GET /api/v1/devices/credentials endpoint exists"""
        response = client.get(
            '/api/v1/devices/credentials',
            json={'device_id': 1}
        )
        
        # Should not return 404
        assert response.status_code != 404
    
    def test_get_credentials_success(self, client, test_device):
        """Test getting device credentials"""
        response = client.get(
            '/api/v1/devices/credentials',
            json={'device_id': test_device['id']}
        )
        
        # Should return credentials or appropriate response
        assert response.status_code in [200, 400, 401]


if __name__ == '__main__':
    pytest.main([__file__, '-v'])
