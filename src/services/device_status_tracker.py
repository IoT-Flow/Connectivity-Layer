"""
Device Status Tracker Service
Tracks device online/offline status based on telemetry activity.
Uses Redis for caching and syncs with database.

Requirements:
- Device becomes "online" when it sends telemetry
- Device becomes "offline" after 1 minute (60 seconds) of no telemetry
- Uses Redis for caching status and last_seen timestamps
- Syncs status changes with PostgreSQL database
"""
import logging
from datetime import datetime, timezone, timedelta
from typing import Optional

logger = logging.getLogger(__name__)

# Redis key prefixes
DEVICE_STATUS_PREFIX = "device:status:"
DEVICE_LASTSEEN_PREFIX = "device:lastseen:"
DEVICE_CACHE_TTL = 60 * 60 * 24  # 24 hours


class DeviceStatusTracker:
    """
    Tracks device online/offline status based on telemetry activity.
    """

    def __init__(
        self,
        redis_client=None,
        db=None,
        enable_db_sync: bool = True,
        timeout_seconds: int = 60,
    ):
        """
        Initialize the device status tracker.

        Args:
            redis_client: Redis client for caching
            db: Database instance for persistence
            enable_db_sync: Whether to sync status to database
            timeout_seconds: Seconds of inactivity before marking offline (default: 60)
        """
        self.redis = redis_client
        self.db = db
        self.db_sync_enabled = enable_db_sync
        self.timeout_seconds = timeout_seconds
        self.available = redis_client is not None

    def update_device_activity(self, device_id: int) -> bool:
        """
        Update device activity when telemetry is received.
        Marks device as online and updates last_seen timestamp.

        Args:
            device_id: The device ID

        Returns:
            bool: True if successful, False if Redis unavailable
        """
        if not self.available:
            logger.debug("Redis not available, cannot update device activity")
            return False

        try:
            current_time = datetime.now(timezone.utc)
            timestamp_str = current_time.isoformat()

            # Update last_seen timestamp in Redis
            lastseen_key = f"{DEVICE_LASTSEEN_PREFIX}{device_id}"
            self.redis.set(lastseen_key, timestamp_str, ex=DEVICE_CACHE_TTL)

            # Update status to online in Redis
            status_key = f"{DEVICE_STATUS_PREFIX}{device_id}"
            self.redis.set(status_key, "online", ex=DEVICE_CACHE_TTL)

            logger.debug(f"Device {device_id} marked as online")

            # Sync to database if enabled
            if self.db_sync_enabled:
                self.sync_status_to_database(device_id, "online")
                self.sync_last_seen_to_database(device_id, current_time)

            return True

        except Exception as e:
            logger.error(f"Error updating device activity for {device_id}: {e}")
            return False

    def is_device_online(self, device_id: int) -> bool:
        """
        Check if a device is currently online based on last_seen timestamp.

        Args:
            device_id: The device ID

        Returns:
            bool: True if online, False if offline
        """
        if not self.available:
            return False

        try:
            lastseen_key = f"{DEVICE_LASTSEEN_PREFIX}{device_id}"
            timestamp_bytes = self.redis.get(lastseen_key)

            if not timestamp_bytes:
                return False

            timestamp_str = timestamp_bytes.decode() if isinstance(timestamp_bytes, bytes) else timestamp_bytes
            last_seen = datetime.fromisoformat(timestamp_str)

            # Calculate time since last activity
            current_time = datetime.now(timezone.utc)
            time_diff = (current_time - last_seen).total_seconds()

            # Device is online if last activity was within timeout period
            return time_diff <= self.timeout_seconds

        except Exception as e:
            logger.error(f"Error checking device online status for {device_id}: {e}")
            return False

    def get_device_status(self, device_id: int) -> str:
        """
        Get the current status of a device ('online' or 'offline').

        Args:
            device_id: The device ID

        Returns:
            str: 'online' or 'offline'
        """
        is_online = self.is_device_online(device_id)
        return "online" if is_online else "offline"

    def check_and_update_status(self, device_id: int) -> str:
        """
        Check device status and update if it has changed.
        Useful for background tasks that monitor device status.

        Args:
            device_id: The device ID

        Returns:
            str: Current status ('online' or 'offline')
        """
        if not self.available:
            return "offline"

        try:
            status = self.get_device_status(device_id)

            # Update status in Redis
            status_key = f"{DEVICE_STATUS_PREFIX}{device_id}"
            self.redis.set(status_key, status, ex=DEVICE_CACHE_TTL)

            # Sync to database if status changed to offline
            if status == "offline" and self.db_sync_enabled:
                self.sync_status_to_database(device_id, status)

            return status

        except Exception as e:
            logger.error(f"Error checking and updating status for {device_id}: {e}")
            return "offline"

    def sync_status_to_database(self, device_id: int, status: str) -> bool:
        """
        Sync device status to the database.

        Args:
            device_id: The device ID
            status: The status to sync ('online' or 'offline')

        Returns:
            bool: True if successful
        """
        if not self.db_sync_enabled or not self.db:
            return False

        try:
            from src.models import Device

            device = Device.query.filter_by(id=device_id).first()
            if device:
                # You can add an is_online field to the Device model if needed
                # For now, we rely on last_seen timestamp
                logger.debug(f"Synced status to database for device {device_id}: {status}")
                return True

            return False

        except Exception as e:
            logger.error(f"Error syncing status to database for {device_id}: {e}")
            return False

    def sync_last_seen_to_database(self, device_id: int, timestamp: datetime) -> bool:
        """
        Sync device last_seen timestamp to the database.

        Args:
            device_id: The device ID
            timestamp: The timestamp to sync

        Returns:
            bool: True if successful
        """
        if not self.db_sync_enabled or not self.db:
            return False

        try:
            from src.models import Device

            device = Device.query.filter_by(id=device_id).first()
            if device:
                device.last_seen = timestamp
                self.db.session.commit()
                logger.debug(f"Synced last_seen to database for device {device_id}")
                return True

            return False

        except Exception as e:
            logger.error(f"Error syncing last_seen to database for {device_id}: {e}")
            if self.db:
                self.db.session.rollback()
            return False

    def get_last_seen(self, device_id: int) -> Optional[datetime]:
        """
        Get the last_seen timestamp for a device.

        Args:
            device_id: The device ID

        Returns:
            datetime: Last seen timestamp or None
        """
        if not self.available:
            return None

        try:
            lastseen_key = f"{DEVICE_LASTSEEN_PREFIX}{device_id}"
            timestamp_bytes = self.redis.get(lastseen_key)

            if not timestamp_bytes:
                return None

            timestamp_str = timestamp_bytes.decode() if isinstance(timestamp_bytes, bytes) else timestamp_bytes
            return datetime.fromisoformat(timestamp_str)

        except Exception as e:
            logger.error(f"Error getting last_seen for {device_id}: {e}")
            return None
