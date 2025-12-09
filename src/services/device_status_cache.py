"""
Device Status Cache Service
Provides caching for device online/offline status and last seen timestamps using Redis
Automatically syncs status changes to SQLite database
"""

import logging
from datetime import datetime, timezone
from typing import Optional, Dict, Any, List

logger = logging.getLogger(__name__)

# Key prefixes for Redis
DEVICE_STATUS_PREFIX = "device:status:"
DEVICE_LASTSEEN_PREFIX = "device:lastseen:"
DEVICE_CACHE_TTL = 60 * 60 * 24  # 24 hours


class DeviceStatusCache:
    """Service for caching device status information in Redis"""

    def __init__(self, redis_client=None):
        self.redis = redis_client
        self.available = redis_client is not None
        self.db_sync_enabled = True  # Flag to enable/disable automatic DB sync
        self.status_change_callbacks = []  # List of callback functions

    def set_device_status(self, device_id: int, status: str) -> bool:
        """
        Set the online/offline status of a device
        Automatically syncs to SQLite database if enabled

        Args:
            device_id: The device ID
            status: 'online' or 'offline'

        Returns:
            bool: True if successful, False otherwise
        """
        if not self.available:
            logger.debug("Redis not available, skipping device status cache")
            return False

        # Get old status for comparison (to detect actual changes)
        old_status = self.get_device_status(device_id)

        try:
            key = f"{DEVICE_STATUS_PREFIX}{device_id}"
            self.redis.set(key, status, ex=DEVICE_CACHE_TTL)
            logger.debug(f"Device {device_id} status cached: {status}")

            # Sync to database if enabled and status actually changed
            if self.db_sync_enabled and old_status != status:
                self._sync_status_to_database(device_id, status, old_status)

                # Trigger any registered callbacks
                self._trigger_status_change_callbacks(device_id, old_status, status)

            return True
        except Exception as e:
            logger.warning(f"Failed to cache device {device_id} status: {str(e)}")
            return False

    def get_device_status(self, device_id: int) -> Optional[str]:
        """
        Get the cached online/offline status of a device

        Args:
            device_id: The device ID

        Returns:
            str: 'online', 'offline', or None if not in cache
        """
        if not self.available:
            return None

        try:
            key = f"{DEVICE_STATUS_PREFIX}{device_id}"
            status = self.redis.get(key)
            return status
        except Exception as e:
            logger.warning(f"Failed to get cached status for device {device_id}: {str(e)}")
            return None

    def update_device_last_seen(self, device_id: int, timestamp: Optional[datetime] = None) -> bool:
        """
        Update the last seen timestamp for a device

        Args:
            device_id: The device ID
            timestamp: The timestamp (defaults to current time)

        Returns:
            bool: True if successful, False otherwise
        """
        if not self.available:
            logger.debug("Redis not available, skipping device last seen cache")
            return False

        try:
            if timestamp is None:
                timestamp = datetime.now(timezone.utc)

            key = f"{DEVICE_LASTSEEN_PREFIX}{device_id}"
            timestamp_str = timestamp.isoformat()
            self.redis.set(key, timestamp_str, ex=DEVICE_CACHE_TTL)

            # Also set status to online
            self.set_device_status(device_id, "online")

            logger.debug(f"Device {device_id} last seen cached: {timestamp_str}")
            return True
        except Exception as e:
            logger.warning(f"Failed to cache device {device_id} last seen: {str(e)}")
            return False

    def get_device_last_seen(self, device_id: int) -> Optional[datetime]:
        """
        Get the last seen timestamp for a device

        Args:
            device_id: The device ID

        Returns:
            datetime: The last seen timestamp, or None if not in cache
        """
        if not self.available:
            return None

        try:
            key = f"{DEVICE_LASTSEEN_PREFIX}{device_id}"
            timestamp_str = self.redis.get(key)
            if timestamp_str:
                return datetime.fromisoformat(timestamp_str)
            return None
        except Exception as e:
            logger.warning(f"Failed to get cached last seen for device {device_id}: {str(e)}")
            return None

    def set_device_offline(self, device_id: int) -> bool:
        """
        Set a device as offline in the cache
        This will also trigger database sync if enabled

        Args:
            device_id: The device ID

        Returns:
            bool: True if successful, False otherwise
        """
        return self.set_device_status(device_id, "offline")

    def get_all_device_statuses(self, device_ids: List[int]) -> Dict[int, str]:
        """
        Get online/offline status for multiple devices efficiently

        Args:
            device_ids: List of device IDs

        Returns:
            Dict mapping device_id to status ('online'/'offline'/None)
        """
        if not self.available or not device_ids:
            return {}

        try:
            pipeline = self.redis.pipeline()

            # Queue all get operations
            for device_id in device_ids:
                key = f"{DEVICE_STATUS_PREFIX}{device_id}"
                pipeline.get(key)

            # Execute pipeline and map results
            results = pipeline.execute()

            # Map results back to device IDs
            statuses = {}
            for i, device_id in enumerate(device_ids):
                statuses[device_id] = results[i]

            return statuses
        except Exception as e:
            logger.warning(f"Failed to get cached statuses for devices: {str(e)}")
            return {}

    def get_all_device_last_seen(self, device_ids: List[int]) -> Dict[int, Optional[datetime]]:
        """
        Get last seen timestamps for multiple devices efficiently

        Args:
            device_ids: List of device IDs

        Returns:
            Dict mapping device_id to last seen timestamp
        """
        if not self.available or not device_ids:
            return {}

        try:
            pipeline = self.redis.pipeline()

            # Queue all get operations
            for device_id in device_ids:
                key = f"{DEVICE_LASTSEEN_PREFIX}{device_id}"
                pipeline.get(key)

            # Execute pipeline and map results
            results = pipeline.execute()

            # Map results back to device IDs
            last_seen = {}
            for i, device_id in enumerate(device_ids):
                timestamp_str = results[i]
                if timestamp_str:
                    try:
                        last_seen[device_id] = datetime.fromisoformat(timestamp_str)
                    except ValueError:
                        last_seen[device_id] = None
                else:
                    last_seen[device_id] = None

            return last_seen
        except Exception as e:
            logger.warning(f"Failed to get cached last seen for devices: {str(e)}")
            return {}

    def get_device_status_summary(self, device_ids: List[int]) -> Dict[int, Dict[str, Any]]:
        """
        Get status summary for multiple devices

        Args:
            device_ids: List of device IDs

        Returns:
            Dict[int, Dict]: Dictionary with device_id as key and status info as value
        """
        if not self.available:
            return {}

        result = {}
        for device_id in device_ids:
            status = self.get_device_status(device_id)
            last_seen = self.get_device_last_seen(device_id)

            result[device_id] = {
                "status": status or "unknown",
                "last_seen": last_seen.isoformat() if last_seen else None,
            }

        return result

    def clear_device_cache(self, device_id: int) -> bool:
        """
        Clear all cached data for a specific device

        Args:
            device_id: The device ID to clear

        Returns:
            bool: True if successful, False otherwise
        """
        if not self.available:
            logger.debug("Redis not available, cannot clear device cache")
            return False

        try:
            status_key = f"{DEVICE_STATUS_PREFIX}{device_id}"
            lastseen_key = f"{DEVICE_LASTSEEN_PREFIX}{device_id}"

            pipeline = self.redis.pipeline()
            pipeline.delete(status_key)
            pipeline.delete(lastseen_key)
            pipeline.execute()

            logger.info(f"Cleared cache for device {device_id}")
            return True
        except Exception as e:
            logger.warning(f"Failed to clear cache for device {device_id}: {str(e)}")
            return False

    def clear_all_device_caches(self) -> bool:
        """
        Clear all device status and last seen caches

        Returns:
            bool: True if successful, False otherwise
        """
        if not self.available:
            logger.debug("Redis not available, cannot clear device caches")
            return False

        try:
            # Delete all keys with our prefixes
            status_pattern = f"{DEVICE_STATUS_PREFIX}*"
            lastseen_pattern = f"{DEVICE_LASTSEEN_PREFIX}*"

            # Get all matching keys
            status_keys = self.redis.keys(status_pattern)
            lastseen_keys = self.redis.keys(lastseen_pattern)

            if status_keys or lastseen_keys:
                pipeline = self.redis.pipeline()

                # Add delete commands to pipeline
                if status_keys:
                    pipeline.delete(*status_keys)

                if lastseen_keys:
                    pipeline.delete(*lastseen_keys)

                # Execute all deletes
                pipeline.execute()

                logger.info(
                    f"Cleared all device caches ({len(status_keys)} status, {len(lastseen_keys)} last seen)"
                )
                return True
            else:
                logger.info("No device caches to clear")
                return True

        except Exception as e:
            logger.warning(f"Failed to clear all device caches: {str(e)}")
            return False

    def _sync_status_to_database(self, device_id: int, redis_status: str, old_status: str = None):
        """
        Sync Redis status change to SQLite database

        Args:
            device_id: The device ID
            redis_status: New status from Redis ('online' or 'offline')
            old_status: Previous status (for logging)
        """
        try:
            # Check if we're in a Flask request context
            from flask import has_request_context

            if has_request_context():
                # We're in a Flask request context, use the normal approach
                from src.models import Device, db

                # Map Redis status to database status
                db_status = "active" if redis_status == "online" else "inactive"

                # Get device from database
                device = Device.query.get(device_id)
                if not device:
                    logger.warning(f"Device {device_id} not found in database for status sync")
                    return

                # Only update if status actually needs to change
                if device.status != db_status:
                    old_db_status = device.status
                    device.status = db_status
                    device.updated_at = datetime.now(timezone.utc)

                    # Commit the change
                    db.session.commit()

                    logger.info(
                        f"Synced device {device_id} status to database: "
                        f"Redis({old_status}→{redis_status}) → DB({old_db_status}→{db_status})"
                    )
                else:
                    logger.debug(f"Device {device_id} database status already matches: {db_status}")
            else:
                # We're outside Flask context (e.g., MQTT background thread)
                # Use the direct database sync function
                try:
                    from src.utils.redis_util import _sync_to_database_standalone

                    _sync_to_database_standalone(device_id, redis_status, old_status)
                    logger.info(f"Background sync completed for device {device_id}: {redis_status}")
                except ImportError:
                    logger.error(f"Cannot sync device {device_id} - Redis utility not available")
                except Exception as util_error:
                    logger.error(f"Failed to sync device {device_id} via utility: {util_error}")

        except Exception as e:
            logger.error(f"Failed to sync device {device_id} status to database: {e}")
            try:
                # Only try rollback if we have Flask context
                from flask import has_request_context

                if has_request_context():
                    from src.models import db

                    db.session.rollback()
            except Exception:
                pass

    def register_status_change_callback(self, callback):
        """
        Register a function to be called when device status changes

        Args:
            callback: Function with signature (device_id, old_status, new_status)
        """
        if callback not in self.status_change_callbacks:
            self.status_change_callbacks.append(callback)
            logger.debug(f"Registered status change callback: {callback.__name__}")

    def unregister_status_change_callback(self, callback):
        """
        Unregister a status change callback

        Args:
            callback: The callback function to remove
        """
        if callback in self.status_change_callbacks:
            self.status_change_callbacks.remove(callback)
            logger.debug(f"Unregistered status change callback: {callback.__name__}")

    def _trigger_status_change_callbacks(self, device_id: int, old_status: str, new_status: str):
        """
        Trigger all registered status change callbacks

        Args:
            device_id: The device ID
            old_status: Previous status
            new_status: New status
        """
        for callback in self.status_change_callbacks:
            try:
                callback(device_id, old_status, new_status)
            except Exception as e:
                logger.error(f"Status change callback {callback.__name__} failed: {e}")

    def enable_database_sync(self):
        """Enable automatic database synchronization"""
        self.db_sync_enabled = True
        logger.info("Database synchronization enabled")

    def disable_database_sync(self):
        """Disable automatic database synchronization"""
        self.db_sync_enabled = False
        logger.info("Database synchronization disabled")

    def is_database_sync_enabled(self) -> bool:
        """Check if database synchronization is enabled"""
        return self.db_sync_enabled

    def force_sync_device_to_database(self, device_id: int) -> bool:
        """
        Force synchronization of a specific device status to database
        regardless of db_sync_enabled flag

        Args:
            device_id: The device ID to sync

        Returns:
            bool: True if successful, False otherwise
        """
        redis_status = self.get_device_status(device_id)
        if redis_status:
            try:
                self._sync_status_to_database(device_id, redis_status)
                return True
            except Exception as e:
                logger.error(f"Failed to force sync device {device_id}: {e}")
                return False
        else:
            logger.warning(f"No Redis status found for device {device_id}")
            return False
