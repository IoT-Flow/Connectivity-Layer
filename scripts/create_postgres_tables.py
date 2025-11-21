#!/usr/bin/env python3
"""
PostgreSQL Table Creation Script
Creates all required tables in the PostgreSQL database
"""

import os
import sys
from pathlib import Path

# Add project root to Python path
project_root = Path(__file__).parent.parent
sys.path.insert(0, str(project_root))

from app import create_app
from src.models import db, User, Device, DeviceAuth, DeviceConfiguration, Chart, ChartDevice, ChartMeasurement, DeviceControl
from werkzeug.security import generate_password_hash
from sqlalchemy import text, inspect

def check_database_connection():
    """Check if PostgreSQL database connection is working"""
    app = create_app()
    
    with app.app_context():
        try:
            # Try to execute a simple query
            result = db.session.execute(text('SELECT 1'))
            result.fetchone()
            print("✓ PostgreSQL connection successful")
            
            # Get database info
            result = db.session.execute(text("SELECT version()"))
            version = result.fetchone()[0]
            print(f"✓ PostgreSQL version: {version.split(',')[0]}")
            
            # Check current database
            result = db.session.execute(text("SELECT current_database()"))
            current_db = result.fetchone()[0]
            print(f"✓ Connected to database: {current_db}")
            
            return True
        except Exception as e:
            print(f"✗ Database connection failed: {str(e)}")
            print("\nPlease check:")
            print("1. PostgreSQL is running: docker ps | grep postgres")
            print("2. DATABASE_URL in .env is correct")
            print("3. Database 'iotflow' exists")
            print("4. User has proper permissions")
            return False

def list_existing_tables():
    """List all existing tables in the database"""
    app = create_app()
    
    with app.app_context():
        try:
            inspector = inspect(db.engine)
            existing_tables = inspector.get_table_names()
            
            if existing_tables:
                print(f"\n✓ Found {len(existing_tables)} existing tables:")
                for table in existing_tables:
                    print(f"  - {table}")
            else:
                print("\n⚠ No tables found in database")
            
            return existing_tables
        except Exception as e:
            print(f"✗ Error listing tables: {str(e)}")
            return []

def drop_all_tables():
    """Drop all existing tables (DANGEROUS!)"""
    app = create_app()
    
    with app.app_context():
        try:
            print("\n⚠ WARNING: Dropping all tables...")
            db.drop_all()
            db.session.commit()
            print("✓ All tables dropped successfully")
            return True
        except Exception as e:
            print(f"✗ Error dropping tables: {str(e)}")
            db.session.rollback()
            return False

def create_all_tables():
    """Create all database tables"""
    app = create_app()
    
    with app.app_context():
        try:
            print("\n📋 Creating database tables...")
            
            # Create all tables
            db.create_all()
            db.session.commit()
            
            # Verify tables were created
            inspector = inspect(db.engine)
            created_tables = inspector.get_table_names()
            
            print(f"\n✓ Successfully created {len(created_tables)} tables:")
            for table in created_tables:
                print(f"  - {table}")
            
            return True
        except Exception as e:
            print(f"✗ Error creating tables: {str(e)}")
            db.session.rollback()
            return False

def create_initial_data():
    """Create initial admin user and test data"""
    app = create_app()
    
    with app.app_context():
        try:
            print("\n👤 Creating initial users...")
            
            # Create admin user
            admin_user = User.query.filter_by(username="admin").first()
            if not admin_user:
                admin_user = User(
                    user_id="dcf1a",
                    username="admin",
                    email="admin@iotflow.local",
                    password_hash=generate_password_hash("admin123"),
                    is_admin=True
                )
                db.session.add(admin_user)
                print("  ✓ Created admin user")
            else:
                print("  ⚠ Admin user already exists")
            
            # Create test user
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
                print("  ✓ Created test user")
            else:
                print("  ⚠ Test user already exists")
            
            db.session.commit()
            
            # Display credentials
            print("\n" + "="*60)
            print("ADMIN USER CREDENTIALS:")
            print("="*60)
            print(f"Username: admin")
            print(f"Password: admin123")
            print(f"Email: admin@iotflow.local")
            print(f"User ID: dcf1a")
            
            print("\n" + "="*60)
            print("TEST USER CREDENTIALS:")
            print("="*60)
            print(f"Username: test")
            print(f"Password: test123")
            print(f"Email: test@iotflow.local")
            print(f"User ID: testuser")
            
            return True
        except Exception as e:
            print(f"✗ Error creating initial data: {str(e)}")
            db.session.rollback()
            return False

def verify_setup():
    """Verify the database setup is complete"""
    app = create_app()
    
    with app.app_context():
        try:
            print("\n🔍 Verifying database setup...")
            
            # Check tables
            inspector = inspect(db.engine)
            tables = inspector.get_table_names()
            expected_tables = ['users', 'devices', 'device_auth', 'device_configurations', 
                             'device_control', 'charts', 'chart_devices', 'chart_measurements']
            
            missing_tables = [t for t in expected_tables if t not in tables]
            
            if missing_tables:
                print(f"✗ Missing tables: {missing_tables}")
                return False
            
            print(f"✓ All {len(expected_tables)} required tables exist")
            
            # Check users
            user_count = User.query.count()
            print(f"✓ Found {user_count} users in database")
            
            # Check devices
            device_count = Device.query.count()
            print(f"✓ Found {device_count} devices in database")
            
            print("\n✅ Database setup verification passed!")
            return True
            
        except Exception as e:
            print(f"✗ Verification failed: {str(e)}")
            return False

def main():
    """Main execution function"""
    print("="*60)
    print("PostgreSQL Table Creation Script")
    print("IoT Connectivity Layer")
    print("="*60)
    
    # Step 1: Check database connection
    print("\n[Step 1/5] Checking database connection...")
    if not check_database_connection():
        print("\n❌ Cannot proceed without database connection")
        sys.exit(1)
    
    # Step 2: List existing tables
    print("\n[Step 2/5] Checking existing tables...")
    existing_tables = list_existing_tables()
    
    # Step 3: Ask if user wants to drop existing tables
    if existing_tables:
        print("\n⚠ WARNING: Tables already exist in the database!")
        response = input("Do you want to DROP all existing tables and recreate them? (yes/no): ")
        
        if response.lower() == 'yes':
            if not drop_all_tables():
                print("\n❌ Failed to drop tables")
                sys.exit(1)
        elif response.lower() == 'no':
            print("\n✓ Keeping existing tables, will only create missing ones")
        else:
            print("\n❌ Invalid response. Exiting.")
            sys.exit(1)
    
    # Step 4: Create tables
    print("\n[Step 3/5] Creating database tables...")
    if not create_all_tables():
        print("\n❌ Failed to create tables")
        sys.exit(1)
    
    # Step 5: Create initial data
    print("\n[Step 4/5] Creating initial data...")
    if not create_initial_data():
        print("\n❌ Failed to create initial data")
        sys.exit(1)
    
    # Step 6: Verify setup
    print("\n[Step 5/5] Verifying setup...")
    if not verify_setup():
        print("\n❌ Setup verification failed")
        sys.exit(1)
    
    print("\n" + "="*60)
    print("✅ DATABASE SETUP COMPLETED SUCCESSFULLY!")
    print("="*60)
    print("\nYou can now:")
    print("1. Start the Flask application: poetry run python app.py")
    print("2. Register devices via API")
    print("3. Submit telemetry data")
    print("4. Run device simulators")
    print("\nNext steps:")
    print("  curl http://localhost:5000/health")
    print("  poetry run python simulators/new_mqtt_device_simulator.py --name TestDevice")

if __name__ == '__main__':
    main()
