"""
Complete End-to-End User Journey Test
Tests the full workflow: Create User -> Register Device -> Send Telemetry -> Retrieve Data
"""

import pytest
import json
from datetime import datetime, timezone
from flask import Flask
from src.models import db


@pytest.fixture
def app():
    """Create application for testing"""
    import os
    os.environ['MQTT_ENABLED'] = 'false'
    os.environ['USE_POSTGRES_TELEMETRY'] = 'true'
    
    from app import create_app
    app = create_app()
    app.config['TESTING'] = True
    app.config['SQLALCHEMY_DATABASE_URI'] = 'postgresql://iotflow:iotflowpass@localhost:5432/iotflow_test'
    
    with app.app_context():
        # Clean up test data
        try:
            db.session.execute(db.text("DELETE FROM telemetry_data WHERE device_id IN (SELECT id FROM devices WHERE name LIKE 'E2E%')"))
            db.session.execute(db.text("DELETE FROM devices WHERE name LIKE 'E2E%'"))
            db.session.execute(db.text("DELETE FROM users WHERE username LIKE 'e2e_%'"))
            db.session.commit()
        except:
            db.session.rollback()
        
        yield app
        
        # Cleanup after test
        try:
            db.session.execute(db.text("DELETE FROM telemetry_data WHERE device_id IN (SELECT id FROM devices WHERE name LIKE 'E2E%')"))
            db.session.execute(db.text("DELETE FROM devices WHERE name LIKE 'E2E%'"))
            db.session.execute(db.text("DELETE FROM users WHERE username LIKE 'e2e_%'"))
            db.session.commit()
        except:
            db.session.rollback()


@pytest.fixture
def client(app):
    """Create test client"""
    return app.test_client()


class TestCompleteUserJourney:
    """Test complete user journey from registration to data retrieval"""
    
    def test_complete_workflow(self, client):
        """
        Complete E2E test:
        1. Create a new user (admin creates user)
        2. Register a device for that user
        3. Send telemetry data from the device
        4. Retrieve the telemetry data
        5. Verify data integrity
        """
        
        # ============================================================
        # STEP 1: Use existing admin user (created by init_db.py)
        # ============================================================
        print("\n=== STEP 1: Using existing admin user ===")
        
        # Use admin token from environment (set in init_db.py)
        admin_token = 'test'  # From IOTFLOW_ADMIN_TOKEN in .env
        
        print(f"✓ Using admin token for authentication")
        
        # ============================================================
        # STEP 2: Register a device for the user
        # ============================================================
        print("\n=== STEP 2: Registering device ===")
        
        # Use existing admin user (from init_db.py)
        # Get admin user_id (UUID string, not database ID) from database
        from src.models import User
        with client.application.app_context():
            admin_user = User.query.filter_by(username='admin').first()
            admin_user_id = admin_user.user_id if admin_user else 'c7c1d603d5354b8395d4b0131f68d2ed'  # UUID string
        
        device_data = {
            'name': 'E2E Temperature Sensor',
            'description': 'End-to-end test temperature sensor',
            'device_type': 'sensor',
            'location': 'Test Lab',
            'firmware_version': '1.0.0',
            'hardware_version': 'v1.0',
            'user_id': admin_user_id  # This is the UUID string, not the database ID
        }
        
        response = client.post(
            '/api/v1/devices/register',
            headers={
                'Content-Type': 'application/json'
            },
            data=json.dumps(device_data)
        )
        
        assert response.status_code in [200, 201], f"Device registration failed: {response.data}"
        device_response = json.loads(response.data)
        device_data = device_response.get('device', {})
        device_id = device_data.get('id')
        device_api_key = device_data.get('api_key')
        
        assert device_id is not None, f"Device ID not returned. Response: {device_response}"
        assert device_api_key is not None, f"Device API key not returned. Response: {device_response}"
        
        print(f"✓ Device registered: {device_data['name']} (ID: {device_id})")
        print(f"  API Key: {device_api_key[:20]}...")
        
        # ============================================================
        # STEP 3: Send telemetry data from the device
        # ============================================================
        print("\n=== STEP 3: Sending telemetry data ===")
        
        # Send multiple telemetry readings
        telemetry_readings = [
            {
                'data': {
                    'temperature': 22.5,
                    'humidity': 65.0,
                    'pressure': 1013.25
                },
                'metadata': {
                    'sensor_type': 'DHT22',
                    'location': 'room_1'
                }
            },
            {
                'data': {
                    'temperature': 23.0,
                    'humidity': 63.5,
                    'pressure': 1013.20
                },
                'metadata': {
                    'sensor_type': 'DHT22',
                    'location': 'room_1'
                }
            },
            {
                'data': {
                    'temperature': 23.5,
                    'humidity': 62.0,
                    'pressure': 1013.15
                },
                'metadata': {
                    'sensor_type': 'DHT22',
                    'location': 'room_1'
                }
            }
        ]
        
        for i, reading in enumerate(telemetry_readings):
            response = client.post(
                '/api/v1/telemetry',
                headers={
                    'X-API-Key': device_api_key,
                    'Content-Type': 'application/json'
                },
                data=json.dumps(reading)
            )
            
            assert response.status_code == 201, f"Telemetry send failed (reading {i+1}): {response.data}"
            telemetry_response = json.loads(response.data)
            assert telemetry_response.get('message') == 'Telemetry data stored successfully'
            
            print(f"✓ Telemetry reading {i+1} sent: temp={reading['data']['temperature']}°C")
        
        # ============================================================
        # STEP 4: Retrieve telemetry data
        # ============================================================
        print("\n=== STEP 4: Retrieving telemetry data ===")
        
        # 4a. Get latest telemetry
        response = client.get(
            f'/api/v1/telemetry/{device_id}/latest',
            headers={'X-API-Key': device_api_key}
        )
        
        assert response.status_code == 200, f"Failed to get latest telemetry: {response.data}"
        latest_data = json.loads(response.data)
        
        assert 'latest_data' in latest_data
        assert latest_data['latest_data']['temperature'] == 23.5  # Last reading
        assert latest_data['latest_data']['humidity'] == 62.0
        assert latest_data['latest_data']['pressure'] == 1013.15
        
        print(f"✓ Latest telemetry retrieved:")
        print(f"  Temperature: {latest_data['latest_data']['temperature']}°C")
        print(f"  Humidity: {latest_data['latest_data']['humidity']}%")
        print(f"  Pressure: {latest_data['latest_data']['pressure']} hPa")
        
        # 4b. Get telemetry history
        response = client.get(
            f'/api/v1/telemetry/{device_id}?start_time=-1h&limit=100',
            headers={'X-API-Key': device_api_key}
        )
        
        assert response.status_code == 200, f"Failed to get telemetry history: {response.data}"
        history_data = json.loads(response.data)
        
        assert 'data' in history_data
        assert history_data['count'] >= 3  # At least our 3 readings
        
        print(f"✓ Telemetry history retrieved: {history_data['count']} readings")
        
        # 4c. Get aggregated data
        response = client.get(
            f'/api/v1/telemetry/{device_id}/aggregated?field=temperature&aggregation=mean&window=1h&start_time=-1h',
            headers={'X-API-Key': device_api_key}
        )
        
        assert response.status_code == 200, f"Failed to get aggregated data: {response.data}"
        agg_data = json.loads(response.data)
        
        assert 'data' in agg_data
        print(f"✓ Aggregated data retrieved")
        
        # ============================================================
        # STEP 5: Verify data integrity
        # ============================================================
        print("\n=== STEP 5: Verifying data integrity ===")
        
        # Verify all readings are in history
        temperatures = []
        for reading in history_data['data']:
            if 'measurements' in reading and 'temperature' in reading['measurements']:
                temperatures.append(reading['measurements']['temperature'])
        
        assert 22.5 in temperatures, "First reading not found in history"
        assert 23.0 in temperatures, "Second reading not found in history"
        assert 23.5 in temperatures, "Third reading not found in history"
        
        print(f"✓ All {len(temperatures)} temperature readings verified")
        
        # Verify device info
        response = client.get(
            '/api/v1/devices/status',
            headers={'X-API-Key': device_api_key}
        )
        
        assert response.status_code == 200, f"Failed to get device status: {response.data}"
        status_response = json.loads(response.data)
        device_info = status_response.get('device', {})
        
        assert device_info['name'] == device_data['name']
        assert device_info['device_type'] == device_data['device_type']
        assert device_info['location'] == device_data['location']
        
        print(f"✓ Device information verified")
        
        # ============================================================
        # STEP 6: Test data operations
        # ============================================================
        print("\n=== STEP 6: Testing data operations ===")
        
        # Send one more reading with different data types
        mixed_data = {
            'data': {
                'temperature': 24.0,
                'status': 'online',
                'is_active': True,
                'config': {
                    'mode': 'auto',
                    'threshold': 25
                }
            }
        }
        
        response = client.post(
            '/api/v1/telemetry',
            headers={
                'X-API-Key': device_api_key,
                'Content-Type': 'application/json'
            },
            data=json.dumps(mixed_data)
        )
        
        assert response.status_code == 201
        print(f"✓ Mixed data types sent successfully")
        
        # Retrieve and verify mixed data
        response = client.get(
            f'/api/v1/telemetry/{device_id}/latest',
            headers={'X-API-Key': device_api_key}
        )
        
        assert response.status_code == 200
        latest = json.loads(response.data)['latest_data']
        
        assert latest['temperature'] == 24.0
        assert latest['status'] == 'online'
        assert latest['is_active'] is True
        
        print(f"✓ Mixed data types retrieved and verified")
        
        # ============================================================
        # SUCCESS!
        # ============================================================
        print("\n" + "="*60)
        print("✓ COMPLETE USER JOURNEY TEST PASSED!")
        print("="*60)
        print(f"Summary:")
        print(f"  - User: admin (existing)")
        print(f"  - Device registered: {device_data['name']}")
        print(f"  - Telemetry readings sent: {len(telemetry_readings) + 1}")
        print(f"  - Data retrieved and verified: ✓")
        print(f"  - Data integrity confirmed: ✓")
        print("="*60)
    
    def test_user_journey_with_multiple_devices(self, client):
        """Test user with multiple devices sending telemetry"""
        
        print("\n=== Testing Multiple Devices ===")
        
        # Use admin token
        admin_token = 'test'
        
        # Register multiple devices
        devices = []
        for i in range(3):
            device_data = {
                'name': f'E2E Device {i+1}',
                'description': f'Test device {i+1}',
                'device_type': 'sensor',
                'location': f'Location {i+1}'
            }
            
            # Add user_id to device data (UUID string, not database ID)
            from src.models import User
            with client.application.app_context():
                admin_user = User.query.filter_by(username='admin').first()
                device_data['user_id'] = admin_user.user_id if admin_user else 'c7c1d603d5354b8395d4b0131f68d2ed'
            
            response = client.post(
                '/api/v1/devices/register',
                headers={
                    'Content-Type': 'application/json'
                },
                data=json.dumps(device_data)
            )
            
            assert response.status_code in [200, 201]
            device_response = json.loads(response.data)
            device = device_response.get('device', {})
            devices.append({
                'id': device.get('id'),
                'api_key': device.get('api_key'),
                'name': device_data['name']
            })
            
            print(f"✓ Device {i+1} registered: {device_data['name']}")
        
        # Send telemetry from each device
        for i, device in enumerate(devices):
            telemetry = {
                'data': {
                    'temperature': 20.0 + i,
                    'device_number': i + 1
                }
            }
            
            response = client.post(
                '/api/v1/telemetry',
                headers={
                    'X-API-Key': device['api_key'],
                    'Content-Type': 'application/json'
                },
                data=json.dumps(telemetry)
            )
            
            assert response.status_code == 201
            print(f"✓ Telemetry sent from device {i+1}")
        
        # Verify each device has its own data
        for i, device in enumerate(devices):
            response = client.get(
                f'/api/v1/telemetry/{device["id"]}/latest',
                headers={'X-API-Key': device['api_key']}
            )
            
            assert response.status_code == 200
            data = json.loads(response.data)
            
            assert data['latest_data']['temperature'] == 20.0 + i
            assert data['latest_data']['device_number'] == i + 1
            
            print(f"✓ Device {i+1} data verified independently")
        
        print("\n✓ Multiple devices test passed!")
    
    def test_error_handling(self, client):
        """Test error handling in the user journey"""
        
        print("\n=== Testing Error Handling ===")
        
        # Test 1: Send telemetry without API key
        response = client.post(
            '/api/v1/telemetry',
            headers={'Content-Type': 'application/json'},
            data=json.dumps({'data': {'temperature': 22.0}})
        )
        
        assert response.status_code == 401
        print("✓ Correctly rejected telemetry without API key")
        
        # Test 2: Send telemetry with invalid API key
        response = client.post(
            '/api/v1/telemetry',
            headers={
                'X-API-Key': 'invalid_key_12345',
                'Content-Type': 'application/json'
            },
            data=json.dumps({'data': {'temperature': 22.0}})
        )
        
        assert response.status_code == 401
        print("✓ Correctly rejected telemetry with invalid API key")
        
        # Test 3: Get telemetry for non-existent device
        response = client.get(
            '/api/v1/telemetry/99999/latest',
            headers={'X-API-Key': 'some_key'}
        )
        
        assert response.status_code in [401, 404]
        print("✓ Correctly handled non-existent device")
        
        print("\n✓ Error handling test passed!")
