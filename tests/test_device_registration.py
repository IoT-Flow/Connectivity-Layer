#!/usr/bin/env python3
"""
Unit Test for Device Registration Functionality
Tests the device registration endpoint and its error cases
"""
import os
import unittest
import json
import time
from flask import Flask
from src.models import db, User, Device
from src.routes.devices import device_bp
from src.config.config import config

class TestDeviceRegistration(unittest.TestCase):
    """Test device registration functionality"""

    def setUp(self):
        """Set up test client and database"""
        self.app = Flask(__name__)
        
        # Configure app for testing
        self.app.config.from_object(config['testing'])
        
        # Override database URI to use in-memory SQLite for tests
        self.app.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite:///:memory:'
        self.app.config['TESTING'] = True
        self.app.config['WTF_CSRF_ENABLED'] = False
        
        # Initialize database
        db.init_app(self.app)
        
        # Register blueprints
        self.app.register_blueprint(device_bp)
        
        # Create test client
        self.client = self.app.test_client()
        
        # Create application context
        self.app_context = self.app.app_context()
        self.app_context.push()
        
        # Create database tables
        db.create_all()
        
        # Create a test user
        test_user = User(
            username='testuser',
            email='test@example.com',
            password_hash='password_hash_for_testing',  # Would normally be hashed
            is_active=True
        )
        db.session.add(test_user)
        db.session.commit()
        
        # Save user_id for tests
        self.test_user_id = test_user.user_id
        
    def tearDown(self):
        """Clean up after each test"""
        db.session.remove()
        db.drop_all()
        self.app_context.pop()
        
    def test_successful_device_registration(self):
        """Test successful device registration"""
        device_name = f"Test_Device_{int(time.time())}"
        payload = {
            "name": device_name,
            "device_type": "sensor",
            "description": "Test device",
            "location": "Test Lab",
            "firmware_version": "1.0.0",
            "hardware_version": "v1.0",
            "user_id": self.test_user_id
        }
        
        response = self.client.post(
            '/api/v1/devices/register',
            data=json.dumps(payload),
            content_type='application/json'
        )
        
        data = json.loads(response.data)
        
        # Assert response code is 201 Created
        self.assertEqual(response.status_code, 201)
        
        # Assert response contains success message
        self.assertIn('message', data)
        self.assertEqual(data['message'], 'Device registered successfully')
        
        # Assert device data is returned correctly
        self.assertIn('device', data)
        self.assertEqual(data['device']['name'], device_name)
        self.assertEqual(data['device']['device_type'], 'sensor')
        self.assertEqual(data['device']['description'], 'Test device')
        
        # Assert API key is generated and returned
        self.assertIn('api_key', data['device'])
        self.assertIsNotNone(data['device']['api_key'])
        
        # Assert device was created in database
        device = Device.query.filter_by(name=device_name).first()
        self.assertIsNotNone(device)
        self.assertEqual(device.name, device_name)
        
    def test_duplicate_device_name(self):
        """Test registration with duplicate device name"""
        # Create a device first
        device_name = f"Duplicate_Test_Device_{int(time.time())}"
        
        # First registration
        first_payload = {
            "name": device_name,
            "device_type": "sensor",
            "user_id": self.test_user_id
        }
        
        self.client.post(
            '/api/v1/devices/register',
            data=json.dumps(first_payload),
            content_type='application/json'
        )
        
        # Try to register again with same name
        second_payload = {
            "name": device_name,
            "device_type": "actuator",
            "user_id": self.test_user_id
        }
        
        response = self.client.post(
            '/api/v1/devices/register',
            data=json.dumps(second_payload),
            content_type='application/json'
        )
        
        data = json.loads(response.data)
        
        # Assert response code is 409 Conflict
        self.assertEqual(response.status_code, 409)
        
        # Assert error message is correct
        self.assertIn('error', data)
        self.assertEqual(data['error'], 'Device name already exists')
        
    def test_invalid_user_id(self):
        """Test registration with invalid user ID"""
        payload = {
            "name": f"Invalid_User_Device_{int(time.time())}",
            "device_type": "sensor",
            "user_id": "non_existent_user_id"
        }
        
        response = self.client.post(
            '/api/v1/devices/register',
            data=json.dumps(payload),
            content_type='application/json'
        )
        
        data = json.loads(response.data)
        
        # Assert response code is 401 Unauthorized
        self.assertEqual(response.status_code, 401)
        
        # Assert error message is correct
        self.assertIn('error', data)
        self.assertEqual(data['error'], 'Authentication failed')
        
    def test_missing_required_fields(self):
        """Test registration with missing required fields"""
        # Missing name
        payload = {
            "device_type": "sensor",
            "user_id": self.test_user_id
        }
        
        response = self.client.post(
            '/api/v1/devices/register',
            data=json.dumps(payload),
            content_type='application/json'
        )
        
        # Assert response code is 400 Bad Request
        self.assertEqual(response.status_code, 400)
        
        # Missing device_type
        payload = {
            "name": f"Missing_Type_Device_{int(time.time())}",
            "user_id": self.test_user_id
        }
        
        response = self.client.post(
            '/api/v1/devices/register',
            data=json.dumps(payload),
            content_type='application/json'
        )
        
        # Assert response code is 400 Bad Request
        self.assertEqual(response.status_code, 400)
        
        # Missing user_id
        payload = {
            "name": f"Missing_User_Device_{int(time.time())}",
            "device_type": "sensor"
        }
        
        response = self.client.post(
            '/api/v1/devices/register',
            data=json.dumps(payload),
            content_type='application/json'
        )
        
        # Assert response code is 400 Bad Request
        self.assertEqual(response.status_code, 400)

    def test_inactive_user(self):
        """Test registration with inactive user"""
        # Create an inactive user
        inactive_user = User(
            username='inactiveuser',
            email='inactive@example.com',
            password_hash='password_hash_for_testing',
            is_active=False
        )
        db.session.add(inactive_user)
        db.session.commit()
        
        payload = {
            "name": f"Inactive_User_Device_{int(time.time())}",
            "device_type": "sensor",
            "user_id": inactive_user.user_id
        }
        
        response = self.client.post(
            '/api/v1/devices/register',
            data=json.dumps(payload),
            content_type='application/json'
        )
        
        data = json.loads(response.data)
        
        # Assert response code is 401 Unauthorized
        self.assertEqual(response.status_code, 401)
        
        # Assert error message is correct
        self.assertIn('error', data)
        self.assertEqual(data['error'], 'Authentication failed')
        
    def test_multiple_devices_per_user(self):
        """Test registering multiple devices for a single user"""
        # Register first device
        first_device_name = f"Multi_Device_1_{int(time.time())}"
        first_payload = {
            "name": first_device_name,
            "device_type": "sensor",
            "user_id": self.test_user_id
        }
        
        first_response = self.client.post(
            '/api/v1/devices/register',
            data=json.dumps(first_payload),
            content_type='application/json'
        )
        
        self.assertEqual(first_response.status_code, 201)
        
        # Register second device
        second_device_name = f"Multi_Device_2_{int(time.time())}"
        second_payload = {
            "name": second_device_name,
            "device_type": "actuator",
            "user_id": self.test_user_id
        }
        
        second_response = self.client.post(
            '/api/v1/devices/register',
            data=json.dumps(second_payload),
            content_type='application/json'
        )
        
        self.assertEqual(second_response.status_code, 201)
        
        # Check that both devices are in the database
        devices = Device.query.filter_by(user_id=User.query.filter_by(user_id=self.test_user_id).first().id).all()
        self.assertEqual(len(devices), 2)
        device_names = [device.name for device in devices]
        self.assertIn(first_device_name, device_names)
        self.assertIn(second_device_name, device_names)


def run_tests():
    """Run the unit tests"""
    import sys
    
    # Create a test suite
    test_suite = unittest.TestLoader().loadTestsFromTestCase(TestDeviceRegistration)
    
    # Run the tests
    result = unittest.TextTestRunner(verbosity=2).run(test_suite)
    
    # Return exit code based on test success
    return 0 if result.wasSuccessful() else 1


if __name__ == '__main__':
    import sys
    sys.exit(run_tests())
