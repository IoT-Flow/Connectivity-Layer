#!/usr/bin/env python3
"""
Migration Script: Simplify telemetry_data table to only numeric values
Drops all columns except: id, device_id, timestamp, measurement_name, numeric_value
"""

import os
os.environ['MQTT_ENABLED'] = 'false'

from app import create_app
from src.models import db
from sqlalchemy import text

def migrate_simplify_telemetry():
    """Simplify telemetry_data table to only store numeric values"""
    
    app = create_app()
    
    with app.app_context():
        print("="*60)
        print("Simplifying telemetry_data table")
        print("="*60)
        
        # Step 1: Backup existing data (optional)
        print("\n1. Checking current table structure...")
        try:
            result = db.session.execute(text("""
                SELECT column_name, data_type 
                FROM information_schema.columns 
                WHERE table_name = 'telemetry_data'
                ORDER BY ordinal_position
            """))
            
            print("   Current columns:")
            for row in result:
                print(f"     - {row[0]}: {row[1]}")
        except Exception as e:
            print(f"   ✗ Error: {e}")
            return False
        
        # Step 2: Create new simplified table
        print("\n2. Creating new simplified table...")
        try:
            # Drop old table
            db.session.execute(text("DROP TABLE IF EXISTS telemetry_data_old CASCADE"))
            
            # Rename current table to old
            db.session.execute(text("ALTER TABLE telemetry_data RENAME TO telemetry_data_old"))
            
            # Create new simplified table
            db.session.execute(text("""
                CREATE TABLE telemetry_data (
                    id BIGSERIAL PRIMARY KEY,
                    device_id INTEGER NOT NULL,
                    timestamp TIMESTAMP WITH TIME ZONE NOT NULL DEFAULT NOW(),
                    measurement_name VARCHAR(100) NOT NULL,
                    numeric_value DOUBLE PRECISION NOT NULL
                )
            """))
            
            print("   ✓ New table created")
        except Exception as e:
            print(f"   ✗ Error: {e}")
            db.session.rollback()
            return False
        
        # Step 3: Migrate numeric data from old table
        print("\n3. Migrating numeric data from old table...")
        try:
            db.session.execute(text("""
                INSERT INTO telemetry_data (device_id, timestamp, measurement_name, numeric_value)
                SELECT device_id, timestamp, measurement_name, numeric_value
                FROM telemetry_data_old
                WHERE numeric_value IS NOT NULL
            """))
            
            migrated_count = db.session.execute(text("SELECT COUNT(*) FROM telemetry_data")).scalar()
            old_count = db.session.execute(text("SELECT COUNT(*) FROM telemetry_data_old")).scalar()
            
            db.session.commit()
            print(f"   ✓ Migrated {migrated_count} numeric records out of {old_count} total records")
        except Exception as e:
            print(f"   ✗ Error migrating data: {e}")
            db.session.rollback()
            return False
        
        # Step 4: Create indexes
        print("\n4. Creating indexes...")
        try:
            db.session.execute(text("""
                CREATE INDEX idx_telemetry_device_time 
                ON telemetry_data (device_id, timestamp DESC)
            """))
            
            db.session.execute(text("""
                CREATE INDEX idx_telemetry_measurement 
                ON telemetry_data (measurement_name)
            """))
            
            db.session.execute(text("""
                CREATE INDEX idx_telemetry_device_measurement_time 
                ON telemetry_data (device_id, measurement_name, timestamp DESC)
            """))
            
            db.session.commit()
            print("   ✓ Indexes created")
        except Exception as e:
            print(f"   ⚠ Warning: {e}")
            db.session.rollback()
        
        # Step 5: Verify new structure
        print("\n5. Verifying new table structure...")
        result = db.session.execute(text("""
            SELECT column_name, data_type 
            FROM information_schema.columns 
            WHERE table_name = 'telemetry_data'
            ORDER BY ordinal_position
        """))
        
        print("   New columns:")
        for row in result:
            print(f"     - {row[0]}: {row[1]}")
        
        print("\n" + "="*60)
        print("✓ Migration completed successfully!")
        print("="*60)
        print("\nSummary:")
        print(f"  - Old table renamed to: telemetry_data_old")
        print(f"  - New simplified table created")
        print(f"  - Only numeric values migrated")
        print("\nNext steps:")
        print("1. Test the application with the new table")
        print("2. If everything works, drop the old table:")
        print("   DROP TABLE telemetry_data_old;")
        print("="*60)
        
        return True

if __name__ == '__main__':
    success = migrate_simplify_telemetry()
    exit(0 if success else 1)
