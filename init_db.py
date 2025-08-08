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
            else:app.
                print("All tables already exist. Proceeding with data initialization...")

            # Create admin user only if not exists

            admin_user = User.query.filter_by(username="admin").first()
            if not admin_user:
                print("Creating admin user...")
                admin_user = User(
                    user_id="dcf1ab8e07364bfea0d7b34cc54c8c48",
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
                    user_id="testuser00000000000000000000000001",
                    username="test",
                    email="test@iotflow.local",
                    password_hash=generate_password_hash("test123"),
                    is_admin=False
                )
                db.session.add(test_user)
                db.session.flush()

            print(f"  - Admin user: {admin_user.username}")

            # Create sample devices for testing only if not exist
            # sample_devices = [
            #     {
            #         'name': 'Temperature Sensor 001',
            #         'description': 'Living room temperature and humidity sensor',
            #         'device_type': 'sensor',
            #         'location': 'Living Room',
            #         'firmware_version': '1.2.3',
            #         'hardware_version': 'v2.1',
            #         'user_id': admin_user.id
            #     },
            #     {
            #         'name': 'Smart Door Lock',
            #         'description': 'WiFi enabled smart door lock',
            #         'device_type': 'actuator',
            #         'location': 'Front Door',
            #         'firmware_version': '2.0.1',
            #         'hardware_version': 'v1.0',
            #         'user_id': admin_user.id
            #     },
            #     {
            #         'name': 'Security Camera 01',
            #         'description': 'Outdoor security camera with motion detection',
            #         'device_type': 'camera',
            #         'location': 'Front Yard',
            #         'firmware_version': '3.1.0',
            #         'hardware_version': 'v3.2',
            #         'user_id': admin_user.id
            #     }
            # ]
            # for device_data in sample_devices:
            #     if not Device.query.filter_by(name=device_data['name']).first():
            #         device = Device(**device_data)
            #         db.session.add(device)
            #         print(f"  - Created device: {device.name}")
            db.session.commit()
            # print(f"\nDatabase initialization completed successfully!")
            # print(f"Created/checked {len(sample_devices)} sample devices.")
            
            # Display admin user credentials for testing
            print("\n" + "="*60)
            print("ADMIN USER CREDENTIALS:")
            print("="*60)
            
            admin = User.query.filter_by(username="admin").first()
            print(f"Username: {admin.username}")
            print(f"Email: {admin.email}")
            print(f"Password: admin123 (change this in production)")
            
            print("\n" + "="*60)
            print("SAMPLE DEVICE API KEYS FOR TESTING:")
            print("="*60)
            
            devices = Device.query.all()
            for device in devices:
                print(f"Device: {device.name}")
                print(f"Owner ID: {device.user_id}")
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
