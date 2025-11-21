#!/usr/bin/env python3
"""
Database initialization script for IoT Connectivity Layer
This script creates the database tables and sets up initial data
"""

import os
import sys
from pathlib import Path

# Add project root to Python path
project_root = Path(__file__).parent
sys.path.insert(0, str(project_root))

from app import create_app
from src.models import db, User, Device, DeviceAuth, DeviceConfiguration, Chart, ChartDevice, ChartMeasurement, DeviceControl
from werkzeug.security import generate_password_hash
from sqlalchemy import text, inspect

def init_database():
    """Initialize the database with tables and sample data"""
    app = create_app()
    with app.app_context():
        try:
            inspector = inspect(db.engine)
            existing_tables = inspector.get_table_names()
            all_models = [User, Device, DeviceAuth, DeviceConfiguration, Chart, ChartDevice, ChartMeasurement, DeviceControl]
            missing_tables = []
            for model in all_models:
                if model.__tablename__ not in existing_tables:
                    missing_tables.append(model.__table__)
            if not existing_tables:
                print("No database found or database is empty. Creating all tables...")
                db.create_all()
            elif missing_tables:
                print(f"Found missing tables: {[t.name for t in missing_tables]}. Creating only missing tables...")
                db.create_all(tables=missing_tables)
            else:
                print("All tables already exist. Proceeding with data initialization...")

            # Create admin user only if not exists

            admin_user = User.query.filter_by(username="admin").first()
            if not admin_user:
                print("Creating admin user...")
                admin_user = User(
                    user_id="dcf1a",
                    username="admin",
                    email="admin@iotflow.local",
                    password_hash=generate_password_hash("admin123"),
                    is_admin=True
                )
                db.session.add(admin_user)
                db.session.flush()
            else:
                print("Admin user already exists.")

            test_user = User.query.filter_by(username="test").first()
            if not test_user:
                test_user = User(
                    user_id="testuser",
                    username="test",
                    email="test@iotflow.local",
                    password_hash=generate_password_hash("test123"),
                    is_admin=False
                )
                db.session.add(test_user)
                db.session.flush()
                print("Creating test user...")
            else:
                print("Test user already exists.")

            # Create additional sample users
            sample_users = [
                {
                    'username': 'john_doe',
                    'email': 'john@iotflow.local',
                    'password': 'john123',
                    'is_admin': False
                },
                {
                    'username': 'jane_smith',
                    'email': 'jane@iotflow.local',
                    'password': 'jane123',
                    'is_admin': False
                },
                {
                    'username': 'operator',
                    'email': 'operator@iotflow.local',
                    'password': 'operator123',
                    'is_admin': False
                }
            ]

            created_users = [admin_user, test_user]
            for user_data in sample_users:
                existing_user = User.query.filter_by(username=user_data['username']).first()
                if not existing_user:
                    new_user = User(
                        username=user_data['username'],
                        email=user_data['email'],
                        password_hash=generate_password_hash(user_data['password']),
                        is_admin=user_data['is_admin']
                    )
                    db.session.add(new_user)
                    db.session.flush()
                    created_users.append(new_user)
                    print(f"  - Created user: {new_user.username}")
                else:
                    created_users.append(existing_user)
                    print(f"  - User already exists: {existing_user.username}")

            print(f"\n  - Admin user: {admin_user.username}")

            # Create sample devices for testing only if not exist
            sample_devices = [
                # Admin user devices
                {
                    'name': 'Temperature Sensor 001',
                    'description': 'Living room temperature and humidity sensor',
                    'device_type': 'sensor',
                    'location': 'Living Room',
                    'firmware_version': '1.2.3',
                    'hardware_version': 'v2.1',
                    'user_id': admin_user.id
                },
                {
                    'name': 'Smart Door Lock',
                    'description': 'WiFi enabled smart door lock',
                    'device_type': 'actuator',
                    'location': 'Front Door',
                    'firmware_version': '2.0.1',
                    'hardware_version': 'v1.0',
                    'user_id': admin_user.id
                },
                {
                    'name': 'Security Camera 01',
                    'description': 'Outdoor security camera with motion detection',
                    'device_type': 'camera',
                    'location': 'Front Yard',
                    'firmware_version': '3.1.0',
                    'hardware_version': 'v3.2',
                    'user_id': admin_user.id
                },
                # Test user devices
                {
                    'name': 'Humidity Sensor 001',
                    'description': 'Basement humidity monitor',
                    'device_type': 'sensor',
                    'location': 'Basement',
                    'firmware_version': '1.0.5',
                    'hardware_version': 'v1.0',
                    'user_id': test_user.id
                },
                {
                    'name': 'Smart Thermostat',
                    'description': 'WiFi enabled smart thermostat',
                    'device_type': 'actuator',
                    'location': 'Hallway',
                    'firmware_version': '2.1.0',
                    'hardware_version': 'v2.0',
                    'user_id': test_user.id
                },
                # Additional devices for other users
                {
                    'name': 'Motion Sensor 001',
                    'description': 'PIR motion sensor for security',
                    'device_type': 'sensor',
                    'location': 'Garage',
                    'firmware_version': '1.1.2',
                    'hardware_version': 'v1.5',
                    'user_id': created_users[2].id if len(created_users) > 2 else admin_user.id
                },
                {
                    'name': 'Smart Light Bulb 01',
                    'description': 'RGB smart light bulb',
                    'device_type': 'actuator',
                    'location': 'Bedroom',
                    'firmware_version': '1.3.0',
                    'hardware_version': 'v1.0',
                    'user_id': created_users[3].id if len(created_users) > 3 else admin_user.id
                },
                {
                    'name': 'Water Leak Sensor',
                    'description': 'Water leak detection sensor',
                    'device_type': 'sensor',
                    'location': 'Kitchen',
                    'firmware_version': '1.0.1',
                    'hardware_version': 'v1.0',
                    'user_id': created_users[4].id if len(created_users) > 4 else admin_user.id
                },
                {
                    'name': 'Smart Plug 01',
                    'description': 'WiFi enabled smart power outlet',
                    'device_type': 'actuator',
                    'location': 'Office',
                    'firmware_version': '2.0.0',
                    'hardware_version': 'v2.1',
                    'user_id': created_users[2].id if len(created_users) > 2 else admin_user.id
                },
                {
                    'name': 'Air Quality Monitor',
                    'description': 'Indoor air quality sensor (CO2, VOC, PM2.5)',
                    'device_type': 'sensor',
                    'location': 'Living Room',
                    'firmware_version': '1.4.2',
                    'hardware_version': 'v1.3',
                    'user_id': created_users[3].id if len(created_users) > 3 else admin_user.id
                }
            ]
            
            for device_data in sample_devices:
                if not Device.query.filter_by(name=device_data['name']).first():
                    device = Device(**device_data)
                    db.session.add(device)
                    print(f"  - Created device: {device.name}")
            db.session.commit()
            print(f"\nDatabase initialization completed successfully!")
            print(f"Created/checked {len(sample_devices)} sample devices.")
            
            # Display user credentials for testing
            print("\n" + "="*60)
            print("USER CREDENTIALS:")
            print("="*60)
            
            all_users = User.query.all()
            for user in all_users:
                # Show password hint for sample users
                password_hint = "admin123" if user.username == "admin" else \
                               "test123" if user.username == "test" else \
                               f"{user.username.split('_')[0]}123" if '_' in user.username else \
                               f"{user.username}123"
                print(f"Username: {user.username}")
                print(f"Email: {user.email}")
                print(f"Password: {password_hint}")
                print(f"Admin: {user.is_admin}")
                print("-" * 40)
            
            print("\n" + "="*60)
            print("SAMPLE DEVICE API KEYS FOR TESTING:")
            print("="*60)
            
            devices = Device.query.all()
            for device in devices:
                owner = User.query.get(device.user_id)
                print(f"Device: {device.name}")
                print(f"Type: {device.device_type}")
                print(f"Location: {device.location}")
                print(f"Owner: {owner.username if owner else 'Unknown'}")
                print(f"Device ID: {device.id}")
                print(f"API Key: {device.api_key}")
                print("-" * 40)
            
            print("\nYou can use these API keys to test the device endpoints.")
            print("Example:")
            print("curl -H 'X-API-Key: <api_key>' -H 'Content-Type: application/json' \\")
            print("  -X POST http://localhost:5000/api/v1/devices/telemetry \\")
            print("  -d '{\"data\": {\"temperature\": 22.5, \"humidity\": 65}}'")
            
        except Exception as e:
            print(f"Error initializing database: {str(e)}")
            db.session.rollback()
            return False
    
    return True

def check_database_connection():
    """Check if database connection is working"""
    
    app = create_app()
    
    with app.app_context():
        try:
            # Try to execute a simple query
            result = db.session.execute(text('SELECT 1'))
            result.fetchone()
            print("✓ Database connection successful")
            return True
        except Exception as e:
            print(f"✗ Database connection failed: {str(e)}")
            print("\nPlease check:")
            print("1. Database file permissions")
            print("2. Disk space available")
            print("3. SQLite installation")
            return False

if __name__ == '__main__':
    print("IoT Connectivity Layer - Database Initialization")
    print("="*50)
    
    # Check database connection first
    if not check_database_connection():
        sys.exit(1)
    
    # Ask for confirmation
    response = input("\nThis will drop and recreate all database tables. Continue? (y/N): ")
    
    if response.lower() != 'y':
        print("Database initialization cancelled.")
        sys.exit(0)
    
    # Initialize database
    if init_database():
        print("\n✓ Database initialization completed successfully!")
    else:
        print("\n✗ Database initialization failed!")
        sys.exit(1)
