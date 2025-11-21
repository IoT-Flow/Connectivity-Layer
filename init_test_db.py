#!/usr/bin/env python3
"""
Initialize Test Database
Creates all required tables in the iotflow_test database for testing
"""

import os
import sys

# Set environment variables for test database
os.environ['MQTT_ENABLED'] = 'false'
os.environ['USE_POSTGRES_TELEMETRY'] = 'true'

from app import create_app
from src.models import db, User, Device, DeviceAuth, DeviceConfiguration, Chart, ChartDevice, ChartMeasurement, DeviceControl
from werkzeug.security import generate_password_hash
from sqlalchemy import text, inspect


def init_test_database():
    """Initialize test database with all tables"""
    
    # Create app with test database
    app = create_app()
    app.config['SQLALCHEMY_DATABASE_URI'] = 'postgresql://iotflow:iotflowpass@localhost:5432/iotflow_test'
    
    with app.app_context():
        print("=" * 60)
        print("Initializing Test Database: iotflow_test")
        print("=" * 60)
        
        # Drop all existing tables
        print("\n1. Dropping existing tables...")
        try:
            db.drop_all()
            print("   ✓ All tables dropped")
        except Exception as e:
            print(f"   ⚠ Warning dropping tables: {e}")
        
        # Create all tables
        print("\n2. Creating all tables...")
        try:
            db.create_all()
            print("   ✓ All tables created")
        except Exception as e:
            print(f"   ✗ Error creating tables: {e}")
            return False
        
        # Verify tables were created
        print("\n3. Verifying tables...")
        inspector = inspect(db.engine)
        tables = inspector.get_table_names()
        
        expected_tables = [
            'users',
            'devices',
            'device_auth',
            'device_configurations',
            'device_controls',
            'charts',
            'chart_devices',
            'chart_measurements',
            'telemetry_data'
        ]
        
        for table in expected_tables:
            if table in tables:
                print(f"   ✓ {table}")
            else:
                print(f"   ✗ {table} - MISSING")
        
        # Create test admin user
        print("\n4. Creating test admin user...")
        try:
            # Check if admin user exists
            admin = User.query.filter_by(username='admin').first()
            if admin:
                print("   ⚠ Admin user already exists, skipping")
            else:
                admin = User(
                    username='admin',
                    email='admin@iotflow.test',
                    password_hash=generate_password_hash('admin123'),
                    is_admin=True,
                    is_active=True
                )
                db.session.add(admin)
                db.session.commit()
                print(f"   ✓ Admin user created (user_id: {admin.user_id})")
        except Exception as e:
            print(f"   ✗ Error creating admin user: {e}")
            db.session.rollback()
        
        # Create test regular user
        print("\n5. Creating test regular user...")
        try:
            test_user = User.query.filter_by(username='testuser').first()
            if test_user:
                print("   ⚠ Test user already exists, skipping")
            else:
                test_user = User(
                    username='testuser',
                    email='test@iotflow.test',
                    password_hash=generate_password_hash('test123'),
                    is_admin=False,
                    is_active=True
                )
                db.session.add(test_user)
                db.session.commit()
                print(f"   ✓ Test user created (user_id: {test_user.user_id})")
        except Exception as e:
            print(f"   ✗ Error creating test user: {e}")
            db.session.rollback()
        
        print("\n" + "=" * 60)
        print("✓ Test Database Initialization Complete!")
        print("=" * 60)
        print("\nDatabase: iotflow_test")
        print(f"Tables created: {len(tables)}")
        print("\nTest Users:")
        print("  - admin / admin123 (admin)")
        print("  - testuser / test123 (regular user)")
        print("\nYou can now run tests with: pytest tests/")
        print("=" * 60)
        
        return True


if __name__ == '__main__':
    success = init_test_database()
    sys.exit(0 if success else 1)
