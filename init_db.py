#!/usr/bin/env python3
"""
Database initialization script for IoT Connectivity Layer
Creates database tables including telemetry_data table
"""

import os
import sys
from pathlib import Path

# Add project root to Python path
project_root = Path(__file__).parent
sys.path.insert(0, str(project_root))

from app import create_app
from src.models import db, User
from src.services.postgres_telemetry import PostgresTelemetryService
from werkzeug.security import generate_password_hash
from sqlalchemy import text

def init_database():
    """Initialize the database with all tables"""
    app = create_app()
    
    with app.app_context():
        try:
            print("\n1. Creating SQLAlchemy tables (users, devices, charts)...")
            db.create_all()
            print("   ✓ SQLAlchemy tables created")
            
            print("\n2. Creating telemetry_data table...")
            telemetry_service = PostgresTelemetryService()
            # Table is created automatically in __init__
            print("   ✓ Telemetry table created")
            
            print("\n3. Creating admin user...")
            admin_user = User.query.filter_by(username="admin").first()
            if not admin_user:
                admin_user = User(
                    username="admin",
                    email="admin@iotflow.local",
                    is_admin=True
                )
                admin_user.set_password("admin123")
                db.session.add(admin_user)
                db.session.commit()
                print(f"   ✓ Admin user created (user_id: {admin_user.user_id})")
            else:
                print(f"   ✓ Admin user already exists (user_id: {admin_user.user_id})")
            
            print("\n4. Creating test user...")
            test_user = User.query.filter_by(username="testuser").first()
            if not test_user:
                test_user = User(
                    username="testuser",
                    email="test@iotflow.local",
                    is_admin=False
                )
                test_user.set_password("test123")
                db.session.add(test_user)
                db.session.commit()
                print(f"   ✓ Test user created (user_id: {test_user.user_id})")
            else:
                print(f"   ✓ Test user already exists (user_id: {test_user.user_id})")
            
            print("\n" + "="*60)
            print("✓ Database initialization completed successfully!")
            print("="*60)
            print("\nUser Credentials:")
            print("  - admin / admin123 (admin)")
            print("  - testuser / test123 (regular user)")
            print("="*60)
            
            return True
            
        except Exception as e:
            print(f"\n✗ Error initializing database: {str(e)}")
            db.session.rollback()
            return False

def check_database_connection():
    """Check if database connection is working"""
    app = create_app()
    
    with app.app_context():
        try:
            result = db.session.execute(text('SELECT 1'))
            result.fetchone()
            print("✓ Database connection successful")
            return True
        except Exception as e:
            print(f"✗ Database connection failed: {str(e)}")
            return False

if __name__ == '__main__':
    print("IoT Connectivity Layer - Database Initialization")
    print("="*60)
    
    # Check database connection first
    if not check_database_connection():
        sys.exit(1)
    
    # Initialize database
    if init_database():
        sys.exit(0)
    else:
        sys.exit(1)
