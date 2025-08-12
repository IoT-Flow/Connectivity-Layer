"""
Redis Utility for Device Status Management
Provides Redis operations that work both inside and outside Flask application context
"""

import logging
import redis
from datetime import datetime, timezone
from typing import Optional

logger = logging.getLogger(__name__)


class DeviceRedisUtil:
    """Utility class for device Redis operations that work outside Flask context"""

    def __init__(self, redis_url: str = "redis://localhost:6379/0"):
        self.redis_url = redis_url
        self._redis_client = None
        self.available = False
        self._initialize_redis()

    def _initialize_redis(self):
        """Initialize Redis connection"""
        try:
            self._redis_client = redis.from_url(self.redis_url, decode_responses=True)
            # Test connection
            self._redis_client.ping()
            self.available = True
            logger.debug("Redis utility initialized successfully")
        except Exception as e:
            logger.warning(f"Redis utility initialization failed: {e}")
            self.available = False
            self._redis_client = None

    def set_device_status(self, device_id: int, status: str) -> bool:
        """Set device status in Redis"""
        if not self.available:
            return False

        try:
            key = f"device:status:{device_id}"
            self._redis_client.set(key, status, ex=86400)  # 24 hours TTL
            logger.debug(f"Device {device_id} status set to {status}")
            return True
        except Exception as e:
            logger.error(f"Failed to set device {device_id} status: {e}")
            return False

    def get_device_status(self, device_id: int) -> Optional[str]:
        """Get device status from Redis"""
        if not self.available:
            return None

        try:
            key = f"device:status:{device_id}"
            status = self._redis_client.get(key)
            return status
        except Exception as e:
            logger.error(f"Failed to get device {device_id} status: {e}")
            return None

    def set_device_last_seen(self, device_id: int, timestamp: datetime) -> bool:
        """Set device last seen timestamp in Redis"""
        if not self.available:
            return False

        try:
            key = f"device:lastseen:{device_id}"
            timestamp_str = timestamp.isoformat()
            self._redis_client.set(key, timestamp_str, ex=86400)  # 24 hours TTL
            logger.debug(f"Device {device_id} last seen updated")
            return True
        except Exception as e:
            logger.error(f"Failed to set device {device_id} last seen: {e}")
            return False

    def get_device_last_seen(self, device_id: int) -> Optional[datetime]:
        """Get device last seen timestamp from Redis"""
        if not self.available:
            return None

        try:
            key = f"device:lastseen:{device_id}"
            timestamp_str = self._redis_client.get(key)
            if timestamp_str:
                return datetime.fromisoformat(timestamp_str)
            return None
        except Exception as e:
            logger.error(f"Failed to get device {device_id} last seen: {e}")
            return None


# Global instance
_redis_util = None


def get_redis_util() -> Optional[DeviceRedisUtil]:
    """Get global Redis utility instance"""
    global _redis_util
    if _redis_util is None:
        try:
            import os

            redis_url = os.environ.get("REDIS_URL", "redis://localhost:6379/0")
            _redis_util = DeviceRedisUtil(redis_url)
        except Exception as e:
            logger.error(f"Failed to initialize Redis utility: {e}")
            _redis_util = None
    return _redis_util


def sync_device_status_safe(device_id: int, is_online: bool, time_since_last_seen: Optional[float] = None):
    """
    Safely sync device status to Redis and database without requiring Flask application context

    Args:
        device_id: The device ID
        is_online: Whether the device is online
        time_since_last_seen: Time since last seen in seconds (optional)
    """
    redis_util = get_redis_util()
    if not redis_util or not redis_util.available:
        logger.debug(f"Redis not available for device {device_id} status sync")
        return

    try:
        # Get current status
        current_status = redis_util.get_device_status(device_id)
        new_status = "online" if is_online else "offline"

        # Only update if status changed
        if current_status != new_status:
            if redis_util.set_device_status(device_id, new_status):
                if time_since_last_seen is not None:
                    logger.info(
                        f"Updated device {device_id} status in Redis: {new_status} "
                        f"(last seen {time_since_last_seen:.1f}s ago)"
                    )
                else:
                    logger.info(f"Updated device {device_id} status in Redis: {new_status}")

                # Also sync to database
                _sync_to_database_standalone(device_id, new_status, current_status)

        # Update last seen if device is online
        if is_online:
            redis_util.set_device_last_seen(device_id, datetime.now(timezone.utc))

    except Exception as e:
        logger.error(f"Error in safe device status sync for device {device_id}: {e}")


# Cache the engine to avoid recreating it every time
_standalone_engine = None
_standalone_session_factory = None


def _get_standalone_db_session():
    """Get a database session for standalone operations (outside Flask context)"""
    global _standalone_engine, _standalone_session_factory

    if _standalone_engine is None:
        # Import SQLAlchemy for direct database access
        from sqlalchemy import create_engine
        from sqlalchemy.orm import sessionmaker
        import os
        from dotenv import load_dotenv

        # Load environment variables
        load_dotenv()

        # Get database URL - ensure we use the same database as Flask
        # Use environment variables for database paths
        possible_db_paths = [
            os.environ.get("DB_PRIMARY_PATH", "instance/iotflow.db"),  # Primary path from env
            os.environ.get("DB_FALLBACK_PATH", "iotflow.db"),  # Fallback path from env
        ]

        db_url = None
        for db_path in possible_db_paths:
            if os.path.exists(db_path):
                db_url = f"sqlite:///{os.path.abspath(db_path)}"
                logger.debug(f"Found database at: {db_path}")
                break

        if not db_url:
            # Create with instance path as default
            instance_path = "instance/iotflow.db"
            os.makedirs(os.path.dirname(instance_path), exist_ok=True)
            db_url = f"sqlite:///{os.path.abspath(instance_path)}"
            logger.debug(f"Using default database path: {instance_path}")

        logger.debug(f"Using database URL: {db_url}")

        # Create engine with SQLite optimizations
        _standalone_engine = create_engine(
            db_url,
            # SQLite-specific optimizations
            connect_args={
                "check_same_thread": False,  # Allow multiple threads
                "timeout": 20,  # Wait up to 20 seconds for locks
            },
            # Enable connection pool checking
            pool_pre_ping=True,  # Verify connections before use
        )
        _standalone_session_factory = sessionmaker(bind=_standalone_engine)

    return _standalone_session_factory()


def _sync_to_database_standalone(device_id: int, new_status: str, old_status: str = None):
    """
    Sync device status to database without Flask application context

    Args:
        device_id: The device ID
        new_status: New status ('online' or 'offline')
        old_status: Previous status (for logging)
    """
    try:
        from sqlalchemy import text

        # Get a database session
        session = _get_standalone_db_session()

        try:
            # Map Redis status to database status
            db_status = "active" if new_status == "online" else "Offline"
            current_time = datetime.now(timezone.utc)

            # Update device status in database
            result = session.execute(
                text("UPDATE devices SET status = :status, updated_at = :updated_at WHERE id = :device_id"),
                {
                    "status": db_status,
                    "updated_at": current_time,
                    "device_id": device_id,
                },
            )

            if result.rowcount > 0:
                session.commit()
                logger.info(
                    f"Database sync completed for device {device_id}: "
                    f"Redis({old_status}→{new_status}) → DB({db_status})"
                )
            else:
                logger.warning(f"Device {device_id} not found in database for status sync")
                session.rollback()

        except Exception as db_error:
            session.rollback()
            raise db_error
        finally:
            session.close()

    except Exception as e:
        logger.error(f"Failed to sync device {device_id} status to database: {e}")
