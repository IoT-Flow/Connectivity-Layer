#!/usr/bin/env python3
"""
Migration Script: Split metadata JSONB into location and sensor_type columns
"""

import os
os.environ['MQTT_ENABLED'] = 'false'

from app import create_app
from src.models import db
from sqlalchemy import text

def migrate_metadata_columns():
    """Migrate metadata JSONB to separate location and sensor_type columns"""
    
    app = create_app()
    
    with app.app_context():
        print("="*60)
        print("Migrating telemetry_data metadata column")
        print("="*60)
        
        # Step 1: Add new columns
        print("\n1. Adding location and sensor_type columns...")
        try:
            db.session.execute(text("""
                ALTER TABLE telemetry_data 
                ADD COLUMN IF NOT EXISTS location VARCHAR(200),
                ADD COLUMN IF NOT EXISTS sensor_type VARCHAR(100)
            """))
            db.session.commit()
            print("   ✓ Columns added successfully")
        except Exception as e:
            print(f"   ⚠ Warning: {e}")
            db.session.rollback()
        
        # Step 2: Migrate existing data from metadata JSONB to new columns
        print("\n2. Migrating existing metadata to new columns...")
        try:
            db.session.execute(text("""
                UPDATE telemetry_data 
                SET 
                    location = metadata->>'location',
                    sensor_type = metadata->>'sensor_type'
                WHERE metadata IS NOT NULL
            """))
            rows_updated = db.session.execute(text("SELECT COUNT(*) FROM telemetry_data WHERE metadata IS NOT NULL")).scalar()
            db.session.commit()
            print(f"   ✓ Migrated {rows_updated} rows")
        except Exception as e:
            print(f"   ✗ Error migrating data: {e}")
            db.session.rollback()
            return False
        
        # Step 3: Create indexes on new columns
        print("\n3. Creating indexes on new columns...")
        try:
            db.session.execute(text("""
                CREATE INDEX IF NOT EXISTS idx_telemetry_location 
                ON telemetry_data (location)
            """))
            db.session.execute(text("""
                CREATE INDEX IF NOT EXISTS idx_telemetry_sensor_type 
                ON telemetry_data (sensor_type)
            """))
            db.session.commit()
            print("   ✓ Indexes created successfully")
        except Exception as e:
            print(f"   ⚠ Warning: {e}")
            db.session.rollback()
        
        # Step 4: Optionally drop metadata column (commented out for safety)
        print("\n4. Metadata column status:")
        print("   ℹ The metadata column is kept for backward compatibility")
        print("   ℹ To remove it, uncomment the DROP COLUMN statement in the script")
        
        # Uncomment to drop metadata column:
        # try:
        #     db.session.execute(text("ALTER TABLE telemetry_data DROP COLUMN metadata"))
        #     db.session.commit()
        #     print("   ✓ Metadata column dropped")
        # except Exception as e:
        #     print(f"   ✗ Error dropping column: {e}")
        #     db.session.rollback()
        
        # Verify the changes
        print("\n5. Verifying table structure...")
        result = db.session.execute(text("""
            SELECT column_name, data_type 
            FROM information_schema.columns 
            WHERE table_name = 'telemetry_data' 
            AND column_name IN ('location', 'sensor_type', 'metadata')
            ORDER BY column_name
        """))
        
        print("   Current columns:")
        for row in result:
            print(f"     - {row[0]}: {row[1]}")
        
        print("\n" + "="*60)
        print("✓ Migration completed successfully!")
        print("="*60)
        print("\nNext steps:")
        print("1. Update your application code to use location and sensor_type")
        print("2. Test the changes")
        print("3. If everything works, you can drop the metadata column")
        print("="*60)
        
        return True

if __name__ == '__main__':
    success = migrate_metadata_columns()
    exit(0 if success else 1)
