#!/usr/bin/env python3
"""
Migration script to transition from IoTDB to PostgreSQL for telemetry storage
Follows the migration path outlined in the architecture document
"""

import sys
import logging
from pathlib import Path

# Add project root to Python path
project_root = Path(__file__).parent
sys.path.insert(0, str(project_root))

from app import create_app
from src.models import db
from src.services.postgres_telemetry import PostgresTelemetryService
from sqlalchemy import text

logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)


def check_prerequisites():
    """Check if prerequisites are met"""
    logger.info("Checking prerequisites...")
    
    app = create_app()
    with app.app_context():
        try:
            # Check PostgreSQL connection
            db.session.execute(text("SELECT 1"))
            logger.info("✓ PostgreSQL connection successful")
            
            # Check if devices table exists
            result = db.session.execute(text("""
                SELECT EXISTS (
                    SELECT FROM information_schema.tables 
                    WHERE table_name = 'devices'
                )
            """))
            if result.scalar():
                logger.info("✓ Devices table exists")
            else:
                logger.error("✗ Devices table not found. Run init_db.py first.")
                return False
            
            return True
            
        except Exception as e:
            logger.error(f"✗ Prerequisites check failed: {e}")
            return False


def create_telemetry_schema():
    """Create telemetry schema in PostgreSQL (Phase 1)"""
    logger.info("\n" + "="*60)
    logger.info("PHASE 1: Creating PostgreSQL Telemetry Schema")
    logger.info("="*60)
    
    app = create_app()
    with app.app_context():
        try:
            telemetry_service = PostgresTelemetryService()
            
            if telemetry_service.is_available():
                logger.info("✓ Telemetry schema created successfully")
                return True
            else:
                logger.error("✗ Failed to create telemetry schema")
                return False
                
        except Exception as e:
            logger.error(f"✗ Error creating schema: {e}")
            return False


def verify_schema():
    """Verify the telemetry schema"""
    logger.info("\nVerifying schema...")
    
    app = create_app()
    with app.app_context():
        try:
            # Check if telemetry_data table exists
            result = db.session.execute(text("""
                SELECT EXISTS (
                    SELECT FROM information_schema.tables 
                    WHERE table_name = 'telemetry_data'
                )
            """))
            
            if result.scalar():
                logger.info("✓ telemetry_data table exists")
                
                # Check indexes
                result = db.session.execute(text("""
                    SELECT indexname 
                    FROM pg_indexes 
                    WHERE tablename = 'telemetry_data'
                """))
                
                indexes = [row[0] for row in result]
                logger.info(f"✓ Found {len(indexes)} indexes")
                for idx in indexes:
                    logger.info(f"  - {idx}")
                
                return True
            else:
                logger.error("✗ telemetry_data table not found")
                return False
                
        except Exception as e:
            logger.error(f"✗ Schema verification failed: {e}")
            return False


def test_write_operations():
    """Test writing telemetry data (Phase 2 preparation)"""
    logger.info("\n" + "="*60)
    logger.info("PHASE 2: Testing Write Operations")
    logger.info("="*60)
    
    app = create_app()
    with app.app_context():
        try:
            from src.models import Device
            
            # Get a test device
            device = Device.query.first()
            if not device:
                logger.warning("No devices found. Creating test device...")
                from src.models import User
                from werkzeug.security import generate_password_hash
                
                user = User.query.first()
                if not user:
                    user = User(
                        username='migration_test',
                        email='migration@test.local',
                        password_hash=generate_password_hash('test123')
                    )
                    db.session.add(user)
                    db.session.commit()
                
                device = Device(
                    name='Migration Test Device',
                    device_type='sensor',
                    user_id=user.id
                )
                db.session.add(device)
                db.session.commit()
            
            logger.info(f"Using device: {device.name} (ID: {device.id})")
            
            # Test write
            telemetry_service = PostgresTelemetryService()
            test_data = {
                'temperature': 22.5,
                'humidity': 65.0,
                'status': 'online'
            }
            
            success = telemetry_service.write_telemetry_data(
                device_id=str(device.id),
                data=test_data,
                device_type=device.device_type,
                user_id=device.user_id,
                metadata={'test': 'migration'}
            )
            
            if success:
                logger.info("✓ Test write successful")
                
                # Test read
                telemetry = telemetry_service.get_device_latest_telemetry(str(device.id))
                if telemetry:
                    logger.info(f"✓ Test read successful: {telemetry}")
                    return True
                else:
                    logger.error("✗ Test read failed")
                    return False
            else:
                logger.error("✗ Test write failed")
                return False
                
        except Exception as e:
            logger.error(f"✗ Write operation test failed: {e}")
            return False


def display_migration_status():
    """Display current migration status"""
    logger.info("\n" + "="*60)
    logger.info("MIGRATION STATUS")
    logger.info("="*60)
    
    app = create_app()
    with app.app_context():
        try:
            # Count telemetry records
            result = db.session.execute(text("""
                SELECT COUNT(*) as count FROM telemetry_data
            """))
            telemetry_count = result.scalar()
            
            # Count devices
            result = db.session.execute(text("""
                SELECT COUNT(*) as count FROM devices
            """))
            device_count = result.scalar()
            
            # Get date range of telemetry
            result = db.session.execute(text("""
                SELECT 
                    MIN(timestamp) as earliest,
                    MAX(timestamp) as latest
                FROM telemetry_data
            """))
            row = result.fetchone()
            
            logger.info(f"Total devices: {device_count}")
            logger.info(f"Total telemetry records: {telemetry_count}")
            if row and row.earliest:
                logger.info(f"Earliest telemetry: {row.earliest}")
                logger.info(f"Latest telemetry: {row.latest}")
            
            # Get measurement types
            result = db.session.execute(text("""
                SELECT DISTINCT measurement_name 
                FROM telemetry_data 
                LIMIT 10
            """))
            measurements = [row[0] for row in result]
            if measurements:
                logger.info(f"Measurement types: {', '.join(measurements)}")
            
        except Exception as e:
            logger.error(f"Error getting migration status: {e}")


def main():
    """Main migration workflow"""
    print("\n" + "="*60)
    print("IoTDB to PostgreSQL Migration Tool")
    print("="*60)
    
    # Check prerequisites
    if not check_prerequisites():
        logger.error("\nPrerequisites not met. Please fix the issues and try again.")
        sys.exit(1)
    
    # Phase 1: Create schema
    if not create_telemetry_schema():
        logger.error("\nFailed to create telemetry schema.")
        sys.exit(1)
    
    # Verify schema
    if not verify_schema():
        logger.error("\nSchema verification failed.")
        sys.exit(1)
    
    # Phase 2: Test operations
    if not test_write_operations():
        logger.error("\nWrite operation tests failed.")
        sys.exit(1)
    
    # Display status
    display_migration_status()
    
    print("\n" + "="*60)
    print("MIGRATION PREPARATION COMPLETE")
    print("="*60)
    print("\nNext steps:")
    print("1. Update your application to use PostgresTelemetryService")
    print("2. Test dual-write mode (write to both IoTDB and PostgreSQL)")
    print("3. Validate data consistency")
    print("4. Switch reads to PostgreSQL")
    print("5. Stop IoTDB writes")
    print("6. Decommission IoTDB")
    print("\nFor more details, see: docs/postgres-telemetry-architecture.md")
    print("="*60)


if __name__ == '__main__':
    main()
