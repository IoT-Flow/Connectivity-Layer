"""
PostgreSQL Telemetry Service
Replaces IoTDB with PostgreSQL for time-series telemetry storage
"""

import logging
from datetime import datetime, timezone, timedelta
from typing import Dict, List, Optional, Any
from sqlalchemy import text, func
from src.models import db

logger = logging.getLogger(__name__)


class PostgresTelemetryService:
    """Service for managing telemetry data in PostgreSQL"""
    
    def __init__(self):
        """Initialize the PostgreSQL telemetry service"""
        self.logger = logger
        self._ensure_telemetry_table()
    
    def _ensure_telemetry_table(self):
        """Ensure telemetry_data table exists"""
        try:
            # Check if table exists
            result = db.session.execute(text("""
                SELECT EXISTS (
                    SELECT FROM information_schema.tables 
                    WHERE table_name = 'telemetry_data'
                )
            """))
            exists = result.scalar()
            
            if not exists:
                self.logger.info("Creating telemetry_data table...")
                self._create_telemetry_table()
        except Exception as e:
            self.logger.error(f"Error checking telemetry table: {e}")
    
    def _create_telemetry_table(self):
        """Create the telemetry_data table"""
        try:
            db.session.execute(text("""
                CREATE TABLE IF NOT EXISTS telemetry_data (
                    id BIGSERIAL PRIMARY KEY,
                    device_id INTEGER NOT NULL,
                    user_id INTEGER NOT NULL,
                    timestamp TIMESTAMP WITH TIME ZONE NOT NULL DEFAULT NOW(),
                    measurement_name VARCHAR(100) NOT NULL,
                    numeric_value DOUBLE PRECISION,
                    text_value TEXT,
                    boolean_value BOOLEAN,
                    json_value JSONB,
                    metadata JSONB,
                    quality_flag SMALLINT DEFAULT 0,
                    created_at TIMESTAMP WITH TIME ZONE NOT NULL DEFAULT NOW(),
                    CONSTRAINT chk_value_not_null CHECK (
                        numeric_value IS NOT NULL OR 
                        text_value IS NOT NULL OR 
                        boolean_value IS NOT NULL OR 
                        json_value IS NOT NULL
                    )
                )
            """))
            
            # Create indexes
            db.session.execute(text("""
                CREATE INDEX IF NOT EXISTS idx_telemetry_device_time 
                ON telemetry_data (device_id, timestamp DESC)
            """))
            
            db.session.execute(text("""
                CREATE INDEX IF NOT EXISTS idx_telemetry_user_time 
                ON telemetry_data (user_id, timestamp DESC)
            """))
            
            db.session.execute(text("""
                CREATE INDEX IF NOT EXISTS idx_telemetry_measurement 
                ON telemetry_data (measurement_name)
            """))
            
            db.session.execute(text("""
                CREATE INDEX IF NOT EXISTS idx_telemetry_device_measurement_time 
                ON telemetry_data (device_id, measurement_name, timestamp DESC)
            """))
            
            db.session.commit()
            self.logger.info("Telemetry table created successfully")
        except Exception as e:
            db.session.rollback()
            self.logger.error(f"Error creating telemetry table: {e}")
            raise
    
    def is_available(self) -> bool:
        """Check if PostgreSQL telemetry service is available"""
        try:
            db.session.execute(text("SELECT 1"))
            return True
        except Exception as e:
            self.logger.error(f"PostgreSQL not available: {e}")
            return False
    
    def write_telemetry_data(
        self,
        device_id: str,
        data: Dict[str, Any],
        device_type: str,
        user_id: int,
        metadata: Optional[Dict] = None,
        timestamp: Optional[datetime] = None
    ) -> bool:
        """
        Write telemetry data to PostgreSQL
        
        Args:
            device_id: Device ID
            data: Dictionary of measurement name -> value
            device_type: Type of device
            user_id: User ID who owns the device
            metadata: Optional metadata dictionary
            timestamp: Optional custom timestamp
        
        Returns:
            True if successful, False otherwise
        """
        try:
            if timestamp is None:
                timestamp = datetime.now(timezone.utc)
            
            # Convert device_id to integer
            device_id_int = int(device_id)
            
            # Insert each measurement as a separate row
            for measurement_name, value in data.items():
                # Determine value type and set appropriate column
                numeric_value = None
                text_value = None
                boolean_value = None
                json_value = None
                
                if isinstance(value, bool):
                    boolean_value = value
                elif isinstance(value, (int, float)):
                    numeric_value = float(value)
                elif isinstance(value, str):
                    text_value = value
                elif isinstance(value, (dict, list)):
                    import json
                    json_value = json.dumps(value)
                else:
                    # Convert to string as fallback
                    text_value = str(value)
                
                # Convert metadata to JSON string if present
                metadata_json = None
                if metadata:
                    import json
                    metadata_json = json.dumps(metadata)
                
                # Insert telemetry record
                db.session.execute(text("""
                    INSERT INTO telemetry_data (
                        device_id, user_id, timestamp, measurement_name,
                        numeric_value, text_value, boolean_value, json_value, metadata
                    ) VALUES (
                        :device_id, :user_id, :timestamp, :measurement_name,
                        :numeric_value, :text_value, :boolean_value, 
                        CAST(:json_value AS JSONB), CAST(:metadata AS JSONB)
                    )
                """), {
                    'device_id': device_id_int,
                    'user_id': user_id,
                    'timestamp': timestamp,
                    'measurement_name': measurement_name,
                    'numeric_value': numeric_value,
                    'text_value': text_value,
                    'boolean_value': boolean_value,
                    'json_value': json_value,
                    'metadata': metadata_json
                })
            
            db.session.commit()
            self.logger.debug(f"Telemetry written for device {device_id}: {len(data)} measurements")
            return True
            
        except Exception as e:
            db.session.rollback()
            self.logger.error(f"Error writing telemetry: {e}")
            return False
    
    def _parse_time_range(self, time_str: str) -> datetime:
        """
        Parse time range string to datetime
        Supports formats like: -1h, -24h, -7d, -1w
        """
        now = datetime.now(timezone.utc)
        
        if not time_str or time_str == 'now':
            return now
        
        if time_str.startswith('-'):
            time_str = time_str[1:]
            
            if time_str.endswith('h'):
                hours = int(time_str[:-1])
                return now - timedelta(hours=hours)
            elif time_str.endswith('d'):
                days = int(time_str[:-1])
                return now - timedelta(days=days)
            elif time_str.endswith('w'):
                weeks = int(time_str[:-1])
                return now - timedelta(weeks=weeks)
            elif time_str.endswith('m'):
                minutes = int(time_str[:-1])
                return now - timedelta(minutes=minutes)
        
        # Try to parse as ISO format
        try:
            return datetime.fromisoformat(time_str.replace('Z', '+00:00'))
        except:
            # Default to 1 hour ago
            return now - timedelta(hours=1)
    
    def get_device_telemetry(
        self,
        device_id: str,
        start_time: str = '-1h',
        end_time: Optional[str] = None,
        limit: int = 1000
    ) -> List[Dict]:
        """
        Get telemetry data for a device
        
        Args:
            device_id: Device ID
            start_time: Start time (e.g., '-1h', '-24h', ISO format)
            end_time: End time (optional)
            limit: Maximum number of records
        
        Returns:
            List of telemetry records grouped by timestamp
        """
        try:
            device_id_int = int(device_id)
            start_dt = self._parse_time_range(start_time)
            end_dt = self._parse_time_range(end_time) if end_time else datetime.now(timezone.utc)
            
            # Query telemetry data
            result = db.session.execute(text("""
                SELECT 
                    timestamp,
                    measurement_name,
                    numeric_value,
                    text_value,
                    boolean_value,
                    json_value,
                    metadata
                FROM telemetry_data
                WHERE device_id = :device_id
                    AND timestamp BETWEEN :start_time AND :end_time
                ORDER BY timestamp DESC
                LIMIT :limit
            """), {
                'device_id': device_id_int,
                'start_time': start_dt,
                'end_time': end_dt,
                'limit': limit
            })
            
            # Group by timestamp
            telemetry_by_time = {}
            for row in result:
                ts = row.timestamp.isoformat()
                if ts not in telemetry_by_time:
                    telemetry_by_time[ts] = {
                        'timestamp': ts,
                        'measurements': {}
                    }
                
                # Get the actual value
                value = (
                    row.numeric_value if row.numeric_value is not None
                    else row.text_value if row.text_value is not None
                    else row.boolean_value if row.boolean_value is not None
                    else row.json_value
                )
                
                telemetry_by_time[ts]['measurements'][row.measurement_name] = value
                
                if row.metadata:
                    telemetry_by_time[ts]['metadata'] = row.metadata
            
            return list(telemetry_by_time.values())
            
        except Exception as e:
            self.logger.error(f"Error getting device telemetry: {e}")
            return []
    
    def get_device_latest_telemetry(self, device_id: str) -> Optional[Dict]:
        """
        Get the latest telemetry data for a device
        
        Args:
            device_id: Device ID
        
        Returns:
            Dictionary of measurement name -> value
        """
        try:
            device_id_int = int(device_id)
            
            # Get latest timestamp
            result = db.session.execute(text("""
                SELECT MAX(timestamp) as latest_time
                FROM telemetry_data
                WHERE device_id = :device_id
            """), {'device_id': device_id_int})
            
            latest_time = result.scalar()
            if not latest_time:
                return None
            
            # Get all measurements at that timestamp
            result = db.session.execute(text("""
                SELECT 
                    measurement_name,
                    numeric_value,
                    text_value,
                    boolean_value,
                    json_value
                FROM telemetry_data
                WHERE device_id = :device_id
                    AND timestamp = :timestamp
            """), {
                'device_id': device_id_int,
                'timestamp': latest_time
            })
            
            measurements = {}
            for row in result:
                value = (
                    row.numeric_value if row.numeric_value is not None
                    else row.text_value if row.text_value is not None
                    else row.boolean_value if row.boolean_value is not None
                    else row.json_value
                )
                measurements[row.measurement_name] = value
            
            return measurements if measurements else None
            
        except Exception as e:
            self.logger.error(f"Error getting latest telemetry: {e}")
            return None

    
    def get_device_aggregated_data(
        self,
        device_id: str,
        field: str,
        aggregation: str = 'mean',
        window: str = '1h',
        start_time: str = '-24h'
    ) -> List[Dict]:
        """
        Get aggregated telemetry data
        
        Args:
            device_id: Device ID
            field: Measurement field name
            aggregation: Aggregation function (mean, sum, count, min, max)
            window: Time window for aggregation
            start_time: Start time
        
        Returns:
            List of aggregated data points
        """
        try:
            device_id_int = int(device_id)
            start_dt = self._parse_time_range(start_time)
            
            # Parse window (e.g., '1h' -> 1 hour)
            if window.endswith('h'):
                interval_minutes = int(window[:-1]) * 60
            elif window.endswith('m'):
                interval_minutes = int(window[:-1])
            else:
                interval_minutes = 60  # Default to 1 hour
            
            # Map aggregation function
            agg_func_map = {
                'mean': 'AVG',
                'sum': 'SUM',
                'count': 'COUNT',
                'min': 'MIN',
                'max': 'MAX',
                'first': 'FIRST',
                'last': 'LAST'
            }
            
            agg_func = agg_func_map.get(aggregation, 'AVG')
            
            # Query aggregated data
            result = db.session.execute(text(f"""
                SELECT 
                    date_trunc('hour', timestamp) + 
                        (EXTRACT(MINUTE FROM timestamp)::INTEGER / :interval_minutes) * 
                        (:interval_minutes || ' minutes')::INTERVAL as time_bucket,
                    {agg_func}(numeric_value) as value,
                    COUNT(*) as count
                FROM telemetry_data
                WHERE device_id = :device_id
                    AND measurement_name = :field
                    AND timestamp >= :start_time
                    AND numeric_value IS NOT NULL
                GROUP BY time_bucket
                ORDER BY time_bucket DESC
            """), {
                'device_id': device_id_int,
                'field': field,
                'start_time': start_dt,
                'interval_minutes': interval_minutes
            })
            
            return [
                {
                    'timestamp': row.time_bucket.isoformat(),
                    'value': float(row.value) if row.value is not None else None,
                    'count': row.count
                }
                for row in result
            ]
            
        except Exception as e:
            self.logger.error(f"Error getting aggregated data: {e}")
            return []
    
    def delete_device_data(
        self,
        device_id: str,
        start_time: str,
        stop_time: str
    ) -> bool:
        """
        Delete telemetry data for a device within a time range
        
        Args:
            device_id: Device ID
            start_time: Start time (ISO format)
            stop_time: Stop time (ISO format)
        
        Returns:
            True if successful, False otherwise
        """
        try:
            device_id_int = int(device_id)
            start_dt = self._parse_time_range(start_time)
            stop_dt = self._parse_time_range(stop_time)
            
            result = db.session.execute(text("""
                DELETE FROM telemetry_data
                WHERE device_id = :device_id
                    AND timestamp BETWEEN :start_time AND :stop_time
            """), {
                'device_id': device_id_int,
                'start_time': start_dt,
                'stop_time': stop_dt
            })
            
            db.session.commit()
            deleted_count = result.rowcount
            self.logger.info(f"Deleted {deleted_count} telemetry records for device {device_id}")
            return True
            
        except Exception as e:
            db.session.rollback()
            self.logger.error(f"Error deleting telemetry data: {e}")
            return False
    
    def get_user_telemetry(
        self,
        user_id: str,
        start_time: str = '-24h',
        end_time: Optional[str] = None,
        limit: int = 1000
    ) -> List[Dict]:
        """
        Get telemetry data for all devices belonging to a user
        
        Args:
            user_id: User ID
            start_time: Start time
            end_time: End time (optional)
            limit: Maximum number of records
        
        Returns:
            List of telemetry records
        """
        try:
            user_id_int = int(user_id)
            start_dt = self._parse_time_range(start_time)
            end_dt = self._parse_time_range(end_time) if end_time else datetime.now(timezone.utc)
            
            result = db.session.execute(text("""
                SELECT 
                    t.device_id,
                    t.timestamp,
                    t.measurement_name,
                    t.numeric_value,
                    t.text_value,
                    t.boolean_value,
                    t.json_value,
                    t.metadata
                FROM telemetry_data t
                WHERE t.user_id = :user_id
                    AND t.timestamp BETWEEN :start_time AND :end_time
                ORDER BY t.timestamp DESC
                LIMIT :limit
            """), {
                'user_id': user_id_int,
                'start_time': start_dt,
                'end_time': end_dt,
                'limit': limit
            })
            
            telemetry_data = []
            for row in result:
                value = (
                    row.numeric_value if row.numeric_value is not None
                    else row.text_value if row.text_value is not None
                    else row.boolean_value if row.boolean_value is not None
                    else row.json_value
                )
                
                telemetry_data.append({
                    'device_id': row.device_id,
                    'timestamp': row.timestamp.isoformat(),
                    'measurement_name': row.measurement_name,
                    'value': value,
                    'metadata': row.metadata
                })
            
            return telemetry_data
            
        except Exception as e:
            self.logger.error(f"Error getting user telemetry: {e}")
            return []
    
    def get_user_telemetry_count(
        self,
        user_id: str,
        start_time: str = '-24h'
    ) -> int:
        """
        Get count of telemetry records for a user
        
        Args:
            user_id: User ID
            start_time: Start time
        
        Returns:
            Count of telemetry records
        """
        try:
            user_id_int = int(user_id)
            start_dt = self._parse_time_range(start_time)
            
            result = db.session.execute(text("""
                SELECT COUNT(*) as count
                FROM telemetry_data
                WHERE user_id = :user_id
                    AND timestamp >= :start_time
            """), {
                'user_id': user_id_int,
                'start_time': start_dt
            })
            
            return result.scalar() or 0
            
        except Exception as e:
            self.logger.error(f"Error getting user telemetry count: {e}")
            return 0
