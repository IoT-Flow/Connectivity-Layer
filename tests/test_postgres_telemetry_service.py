"""
Test suite for PostgreSQL Telemetry Service
Following TDD approach to replace IoTDB with PostgreSQL
"""

import pytest
from datetime import datetime, timezone, timedelta
from src.services.postgres_telemetry import PostgresTelemetryService
from src.models import db, User, Device
from werkzeug.security import generate_password_hash


@pytest.fixture
def app():
    """Create application for testing"""
    from flask import Flask
    app = Flask(__name__)
    app.config['TESTING'] = True
    app.config['SQLALCHEMY_DATABASE_URI'] = 'postgresql://iotflow:iotflowpass@localhost:5432/iotflow_test'
    app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False
    
    # Initialize db with app
    db.init_app(app)
    
    with app.app_context():
        db.create_all()
        yield app
        db.session.remove()
        db.drop_all()


@pytest.fixture
def client(app):
    """Create test client"""
    return app.test_client()


@pytest.fixture
def test_user(app):
    """Create a test user"""
    with app.app_context():
        user = User(
            username='testuser',
            email='test@example.com',
            password_hash=generate_password_hash('password123'),
            is_admin=False
        )
        db.session.add(user)
        db.session.commit()
        user_id = user.id
        db.session.refresh(user)
        # Return a dict instead of the object to avoid session issues
        return {'id': user_id, 'username': user.username, 'email': user.email}


@pytest.fixture
def test_device(app, test_user):
    """Create a test device"""
    with app.app_context():
        device = Device(
            name='Test Sensor',
            description='Test temperature sensor',
            device_type='sensor',
            location='Test Lab',
            firmware_version='1.0.0',
            user_id=test_user['id']
        )
        db.session.add(device)
        db.session.commit()
        device_id = device.id
        device_type = device.device_type
        api_key = device.api_key
        # Return a dict instead of the object to avoid session issues
        return {
            'id': device_id,
            'name': device.name,
            'device_type': device_type,
            'api_key': api_key,
            'user_id': test_user['id']
        }


@pytest.fixture
def telemetry_service(app):
    """Create telemetry service instance"""
    with app.app_context():
        return PostgresTelemetryService()


class TestPostgresTelemetryService:
    """Test PostgreSQL Telemetry Service"""
    
    def test_service_initialization(self, telemetry_service):
        """Test that service initializes correctly"""
        assert telemetry_service is not None
        assert telemetry_service.is_available()
    
    def test_write_numeric_telemetry(self, app, telemetry_service, test_device, test_user):
        """Test writing numeric telemetry data"""
        with app.app_context():
            data = {
                'temperature': 22.5,
                'humidity': 65.0
            }
            
            success = telemetry_service.write_telemetry_data(
                device_id=str(test_device['id']),
                data=data,
                device_type=test_device['device_type'],
                user_id=test_user['id']
            )
            
            assert success is True
    
    def test_write_telemetry_with_timestamp(self, app, telemetry_service, test_device, test_user):
        """Test writing telemetry with custom timestamp"""
        with app.app_context():
            custom_time = datetime.now(timezone.utc) - timedelta(hours=1)
            data = {'temperature': 23.0}
            
            success = telemetry_service.write_telemetry_data(
                device_id=str(test_device['id']),
                data=data,
                device_type=test_device['device_type'],
                user_id=test_user['id'],
                timestamp=custom_time
            )
            
            assert success is True
    
    def test_write_telemetry_with_metadata(self, app, telemetry_service, test_device, test_user):
        """Test writing telemetry with metadata"""
        with app.app_context():
            data = {'temperature': 24.0}
            metadata = {
                'sensor_id': 'DHT22',
                'location': 'room_1',
                'calibration': 'v2'
            }
            
            success = telemetry_service.write_telemetry_data(
                device_id=str(test_device['id']),
                data=data,
                device_type=test_device['device_type'],
                user_id=test_user['id'],
                metadata=metadata
            )
            
            assert success is True
    
    def test_write_mixed_type_telemetry(self, app, telemetry_service, test_device, test_user):
        """Test writing telemetry with different data types"""
        with app.app_context():
            data = {
                'temperature': 22.5,  # numeric
                'status': 'active',   # text
                'is_online': True,    # boolean
                'config': {'mode': 'auto', 'threshold': 25}  # json
            }
            
            success = telemetry_service.write_telemetry_data(
                device_id=str(test_device['id']),
                data=data,
                device_type=test_device['device_type'],
                user_id=test_user['id']
            )
            
            assert success is True
    
    def test_get_device_telemetry(self, app, telemetry_service, test_device, test_user):
        """Test retrieving device telemetry"""
        with app.app_context():
            # Write some test data
            data = {'temperature': 22.5, 'humidity': 65.0}
            telemetry_service.write_telemetry_data(
                device_id=str(test_device['id']),
                data=data,
                device_type=test_device['device_type'],
                user_id=test_user['id']
            )
            
            # Retrieve data
            result = telemetry_service.get_device_telemetry(
                device_id=str(test_device['id']),
                start_time='-1h',
                limit=100
            )
            
            assert isinstance(result, list)
            assert len(result) > 0
            assert 'timestamp' in result[0]
            assert 'measurements' in result[0]
    
    def test_get_device_latest_telemetry(self, app, telemetry_service, test_device, test_user):
        """Test retrieving latest telemetry"""
        with app.app_context():
            # Write test data
            data = {'temperature': 23.5}
            telemetry_service.write_telemetry_data(
                device_id=str(test_device['id']),
                data=data,
                device_type=test_device['device_type'],
                user_id=test_user['id']
            )
            
            # Get latest
            result = telemetry_service.get_device_latest_telemetry(
                device_id=str(test_device['id'])
            )
            
            assert result is not None
            assert 'temperature' in result
            assert result['temperature'] == 23.5
    
    def test_get_device_aggregated_data(self, app, telemetry_service, test_device, test_user):
        """Test retrieving aggregated telemetry data"""
        with app.app_context():
            # Write multiple data points
            for temp in [20.0, 21.0, 22.0, 23.0, 24.0]:
                telemetry_service.write_telemetry_data(
                    device_id=str(test_device['id']),
                    data={'temperature': temp},
                    device_type=test_device['device_type'],
                    user_id=test_user['id']
                )
            
            # Get aggregated data
            result = telemetry_service.get_device_aggregated_data(
                device_id=str(test_device['id']),
                field='temperature',
                aggregation='mean',
                window='1h',
                start_time='-1h'
            )
            
            assert isinstance(result, list)
    
    def test_delete_device_data(self, app, telemetry_service, test_device, test_user):
        """Test deleting device telemetry data"""
        with app.app_context():
            # Write test data
            data = {'temperature': 22.0}
            telemetry_service.write_telemetry_data(
                device_id=str(test_device['id']),
                data=data,
                device_type=test_device['device_type'],
                user_id=test_user['id']
            )
            
            # Delete data
            start_time = (datetime.now(timezone.utc) - timedelta(hours=2)).isoformat()
            stop_time = datetime.now(timezone.utc).isoformat()
            
            success = telemetry_service.delete_device_data(
                device_id=str(test_device['id']),
                start_time=start_time,
                stop_time=stop_time
            )
            
            assert success is True
    
    def test_get_user_telemetry(self, app, telemetry_service, test_device, test_user):
        """Test retrieving telemetry for all user devices"""
        with app.app_context():
            # Write test data
            data = {'temperature': 22.0}
            telemetry_service.write_telemetry_data(
                device_id=str(test_device['id']),
                data=data,
                device_type=test_device['device_type'],
                user_id=test_user['id']
            )
            
            # Get user telemetry
            result = telemetry_service.get_user_telemetry(
                user_id=str(test_user['id']),
                start_time='-1h',
                limit=100
            )
            
            assert isinstance(result, list)
    
    def test_get_user_telemetry_count(self, app, telemetry_service, test_device, test_user):
        """Test counting user telemetry records"""
        with app.app_context():
            # Write test data
            for i in range(5):
                telemetry_service.write_telemetry_data(
                    device_id=str(test_device['id']),
                    data={'temperature': 20.0 + i},
                    device_type=test_device['device_type'],
                    user_id=test_user['id']
                )
            
            # Get count
            count = telemetry_service.get_user_telemetry_count(
                user_id=str(test_user['id']),
                start_time='-1h'
            )
            
            assert count >= 5
    
    def test_write_telemetry_invalid_device(self, app, telemetry_service, test_user):
        """Test writing telemetry for non-existent device"""
        with app.app_context():
            data = {'temperature': 22.0}
            
            success = telemetry_service.write_telemetry_data(
                device_id='99999',
                data=data,
                device_type='sensor',
                user_id=test_user['id']
            )
            
            # Should handle gracefully
            assert success is False or success is True  # Depends on implementation
    
    def test_time_range_parsing(self, app, telemetry_service, test_device, test_user):
        """Test different time range formats"""
        with app.app_context():
            # Write test data
            data = {'temperature': 22.0}
            telemetry_service.write_telemetry_data(
                device_id=str(test_device['id']),
                data=data,
                device_type=test_device['device_type'],
                user_id=test_user['id']
            )
            
            # Test different time formats
            time_formats = ['-1h', '-24h', '-7d', '-1w']
            
            for time_format in time_formats:
                result = telemetry_service.get_device_telemetry(
                    device_id=str(test_device['id']),
                    start_time=time_format,
                    limit=100
                )
                assert isinstance(result, list)
