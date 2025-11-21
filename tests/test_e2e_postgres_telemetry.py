"""
End-to-End Test for PostgreSQL Telemetry
Tests the complete flow: HTTP API -> Service -> PostgreSQL Database
"""

import pytest
import json
from datetime import datetime, timezone, timedelta
from flask import Flask
from src.models import db, User, Device
from werkzeug.security import generate_password_hash


@pytest.fixture
def app():
    """Create application for testing"""
    import os
    # Disable MQTT for testing
    os.environ['MQTT_ENABLED'] = 'false'
    os.environ['USE_POSTGRES_TELEMETRY'] = 'true'
    
    from app import create_app
    app = create_app()
    app.config['TESTING'] = True
    app.config['SQLALCHEMY_DATABASE_URI'] = 'postgresql://iotflow:iotflowpass@localhost:5432/iotflow_test'
    
    with app.app_context():
        # Clean up any existing data
        try:
            db.session.execute(db.text("DELETE FROM telemetry_data"))
            db.session.commit()
        except:
            db.session.rollback()
        yield app


@pytest.fixture
def client(app):
    """Create test client"""
    return app.test_client()


@pytest.fixture
def test_user_and_device(app):
    """Create test user and device"""
    with app.app_context():
        # Clean up existing test user if exists
        existing_user = User.query.filter_by(username='e2e_testuser').first()
        if existing_user:
            # Delete associated devices first
            Device.query.filter_by(user_id=existing_user.id).delete()
            db.session.delete(existing_user)
            db.session.commit()
        
        # Create user
        user = User(
            username='e2e_testuser',
            email='e2e@example.com',
            password_hash=generate_password_hash('password123'),
            is_admin=False
        )
        db.session.add(user)
        db.session.commit()
        
        # Create device
        device = Device(
            name='E2E Test Sensor',
            description='End-to-end test device',
            device_type='sensor',
            location='Test Lab',
            firmware_version='1.0.0',
            user_id=user.id
        )
        db.session.add(device)
        db.session.commit()
        
        result = {
            'user_id': user.id,
            'device_id': device.id,
            'api_key': device.api_key
        }
        
        yield result
        
        # Cleanup after test
        db.session.execute(db.text("DELETE FROM telemetry_data WHERE device_id = :device_id"), {'device_id': result['device_id']})
        Device.query.filter_by(id=result['device_id']).delete()
        User.query.filter_by(id=result['user_id']).delete()
        db.session.commit()


class TestE2EPostgresTelemetry:
    """End-to-End tests for PostgreSQL telemetry"""
    
    def test_complete_telemetry_flow(self, client, test_user_and_device):
        """Test complete flow: POST telemetry -> GET telemetry -> Verify in DB"""
        api_key = test_user_and_device['api_key']
        device_id = test_user_and_device['device_id']
        
        # Step 1: POST telemetry data
        telemetry_data = {
            'data': {
                'temperature': 25.5,
                'humidity': 60.0,
                'pressure': 1013.25
            },
            'metadata': {
                'sensor_type': 'DHT22',
                'location': 'room_1'
            }
        }
        
        response = client.post(
            '/api/v1/telemetry',
            headers={'X-API-Key': api_key, 'Content-Type': 'application/json'},
            data=json.dumps(telemetry_data)
        )
        
        assert response.status_code == 201
        data = json.loads(response.data)
        assert data['message'] == 'Telemetry data stored successfully'
        assert data['device_id'] == device_id
        assert 'stored_in_postgres' in data
        
        # Step 2: GET latest telemetry
        response = client.get(
            f'/api/v1/telemetry/{device_id}/latest',
            headers={'X-API-Key': api_key}
        )
        
        assert response.status_code == 200
        data = json.loads(response.data)
        assert data['device_id'] == device_id
        assert 'latest_data' in data
        assert data['latest_data']['temperature'] == 25.5
        assert data['latest_data']['humidity'] == 60.0
        assert data['latest_data']['pressure'] == 1013.25
        
        # Step 3: GET telemetry history
        response = client.get(
            f'/api/v1/telemetry/{device_id}?start_time=-1h&limit=100',
            headers={'X-API-Key': api_key}
        )
        
        assert response.status_code == 200
        data = json.loads(response.data)
        assert data['device_id'] == device_id
        assert len(data['data']) > 0
        assert data['count'] > 0
        assert data['postgres_available'] is True
    
    def test_multiple_telemetry_posts(self, client, test_user_and_device):
        """Test posting multiple telemetry records"""
        api_key = test_user_and_device['api_key']
        device_id = test_user_and_device['device_id']
        
        # Post 5 telemetry records
        for i in range(5):
            telemetry_data = {
                'data': {
                    'temperature': 20.0 + i,
                    'reading_number': i
                }
            }
            
            response = client.post(
                '/api/v1/telemetry',
                headers={'X-API-Key': api_key, 'Content-Type': 'application/json'},
                data=json.dumps(telemetry_data)
            )
            
            assert response.status_code == 201
        
        # Verify all records are retrievable
        response = client.get(
            f'/api/v1/telemetry/{device_id}?start_time=-1h&limit=100',
            headers={'X-API-Key': api_key}
        )
        
        assert response.status_code == 200
        data = json.loads(response.data)
        assert data['count'] >= 5
    
    def test_telemetry_with_custom_timestamp(self, client, test_user_and_device):
        """Test posting telemetry with custom timestamp"""
        api_key = test_user_and_device['api_key']
        device_id = test_user_and_device['device_id']
        
        custom_time = (datetime.now(timezone.utc) - timedelta(hours=2)).isoformat()
        
        telemetry_data = {
            'data': {
                'temperature': 22.0
            },
            'timestamp': custom_time
        }
        
        response = client.post(
            '/api/v1/telemetry',
            headers={'X-API-Key': api_key, 'Content-Type': 'application/json'},
            data=json.dumps(telemetry_data)
        )
        
        assert response.status_code == 201
        data = json.loads(response.data)
        assert 'timestamp' in data
    
    def test_aggregated_telemetry(self, client, test_user_and_device):
        """Test aggregated telemetry queries"""
        api_key = test_user_and_device['api_key']
        device_id = test_user_and_device['device_id']
        
        # Post multiple temperature readings
        temperatures = [20.0, 21.0, 22.0, 23.0, 24.0, 25.0]
        for temp in temperatures:
            telemetry_data = {
                'data': {
                    'temperature': temp
                }
            }
            
            response = client.post(
                '/api/v1/telemetry',
                headers={'X-API-Key': api_key, 'Content-Type': 'application/json'},
                data=json.dumps(telemetry_data)
            )
            
            assert response.status_code == 201
        
        # Get aggregated data
        response = client.get(
            f'/api/v1/telemetry/{device_id}/aggregated?field=temperature&aggregation=mean&window=1h&start_time=-1h',
            headers={'X-API-Key': api_key}
        )
        
        assert response.status_code == 200
        data = json.loads(response.data)
        assert data['device_id'] == device_id
        assert data['field'] == 'temperature'
        assert data['aggregation'] == 'mean'
        assert isinstance(data['data'], list)
    
    def test_delete_telemetry(self, client, test_user_and_device):
        """Test deleting telemetry data"""
        api_key = test_user_and_device['api_key']
        device_id = test_user_and_device['device_id']
        
        # Post telemetry
        telemetry_data = {
            'data': {
                'temperature': 22.0
            }
        }
        
        response = client.post(
            '/api/v1/telemetry',
            headers={'X-API-Key': api_key, 'Content-Type': 'application/json'},
            data=json.dumps(telemetry_data)
        )
        
        assert response.status_code == 201
        
        # Delete telemetry
        start_time = (datetime.now(timezone.utc) - timedelta(hours=2)).isoformat()
        stop_time = datetime.now(timezone.utc).isoformat()
        
        delete_data = {
            'start_time': start_time,
            'stop_time': stop_time
        }
        
        response = client.delete(
            f'/api/v1/telemetry/{device_id}',
            headers={'X-API-Key': api_key, 'Content-Type': 'application/json'},
            data=json.dumps(delete_data)
        )
        
        assert response.status_code == 200
        data = json.loads(response.data)
        assert 'message' in data
    
    def test_telemetry_status_endpoint(self, client, test_user_and_device):
        """Test telemetry status endpoint"""
        response = client.get('/api/v1/telemetry/status')
        
        assert response.status_code == 200
        data = json.loads(response.data)
        assert 'postgres_available' in data
        assert data['postgres_available'] is True
        assert 'backend' in data
        assert data['backend'] == 'PostgreSQL'
        assert 'status' in data
        assert data['status'] == 'healthy'
    
    def test_invalid_api_key(self, client, test_user_and_device):
        """Test with invalid API key"""
        telemetry_data = {
            'data': {
                'temperature': 22.0
            }
        }
        
        response = client.post(
            '/api/v1/telemetry',
            headers={'X-API-Key': 'invalid_key', 'Content-Type': 'application/json'},
            data=json.dumps(telemetry_data)
        )
        
        assert response.status_code == 401
        data = json.loads(response.data)
        assert 'error' in data
    
    def test_missing_api_key(self, client, test_user_and_device):
        """Test without API key"""
        telemetry_data = {
            'data': {
                'temperature': 22.0
            }
        }
        
        response = client.post(
            '/api/v1/telemetry',
            headers={'Content-Type': 'application/json'},
            data=json.dumps(telemetry_data)
        )
        
        assert response.status_code == 401
        data = json.loads(response.data)
        assert 'error' in data
        assert data['error'] == 'API key required'
    
    def test_mixed_data_types(self, client, test_user_and_device):
        """Test telemetry with mixed data types"""
        api_key = test_user_and_device['api_key']
        device_id = test_user_and_device['device_id']
        
        telemetry_data = {
            'data': {
                'temperature': 25.5,           # numeric
                'status': 'online',            # text
                'is_active': True,             # boolean
                'config': {                    # json
                    'mode': 'auto',
                    'threshold': 30
                }
            }
        }
        
        response = client.post(
            '/api/v1/telemetry',
            headers={'X-API-Key': api_key, 'Content-Type': 'application/json'},
            data=json.dumps(telemetry_data)
        )
        
        assert response.status_code == 201
        
        # Verify data is retrievable
        response = client.get(
            f'/api/v1/telemetry/{device_id}/latest',
            headers={'X-API-Key': api_key}
        )
        
        assert response.status_code == 200
        data = json.loads(response.data)
        assert data['latest_data']['temperature'] == 25.5
        assert data['latest_data']['status'] == 'online'
        assert data['latest_data']['is_active'] is True
        # JSON can be returned as dict or string depending on how it's retrieved
        assert isinstance(data['latest_data']['config'], (str, dict))
    
    def test_user_telemetry_endpoint(self, client, test_user_and_device):
        """Test user-level telemetry endpoint"""
        api_key = test_user_and_device['api_key']
        user_id = test_user_and_device['user_id']
        
        # Post some telemetry
        telemetry_data = {
            'data': {
                'temperature': 23.0
            }
        }
        
        response = client.post(
            '/api/v1/telemetry',
            headers={'X-API-Key': api_key, 'Content-Type': 'application/json'},
            data=json.dumps(telemetry_data)
        )
        
        assert response.status_code == 201
        
        # Get user telemetry
        response = client.get(
            f'/api/v1/telemetry/user/{user_id}?start_time=-1h&limit=100',
            headers={'X-API-Key': api_key}
        )
        
        assert response.status_code == 200
        data = json.loads(response.data)
        assert data['status'] == 'success'
        assert data['user_id'] == user_id
        assert isinstance(data['telemetry'], list)
        assert data['count'] > 0
    
    def test_concurrent_telemetry_posts(self, client, test_user_and_device):
        """Test posting telemetry rapidly (simulating concurrent devices)"""
        api_key = test_user_and_device['api_key']
        device_id = test_user_and_device['device_id']
        
        # Rapidly post 10 telemetry records
        success_count = 0
        for i in range(10):
            telemetry_data = {
                'data': {
                    'temperature': 20.0 + (i * 0.5),
                    'sequence': i
                }
            }
            
            response = client.post(
                '/api/v1/telemetry',
                headers={'X-API-Key': api_key, 'Content-Type': 'application/json'},
                data=json.dumps(telemetry_data)
            )
            
            if response.status_code == 201:
                success_count += 1
        
        assert success_count == 10
        
        # Verify all records are in database
        response = client.get(
            f'/api/v1/telemetry/{device_id}?start_time=-1h&limit=100',
            headers={'X-API-Key': api_key}
        )
        
        assert response.status_code == 200
        data = json.loads(response.data)
        assert data['count'] >= 10
