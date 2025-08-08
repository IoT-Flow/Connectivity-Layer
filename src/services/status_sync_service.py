"""
Device Status Synchronization Service
Handles periodic synchronization between Redis cache and database for device statuses
"""

import logging
import threading
import time
from typing import Optional, Set
import redis

logger = logging.getLogger(__name__)


class StatusSyncService:
    """
    Service for synchronizing device status between Redis cache and database
    Runs as a background thread to ensure data consistency
    """

    def __init__(
        self, redis_client: Optional[redis.Redis] = None, sync_interval: int = 30
    ):
        """
        Initialize the status sync service

        Args:
            redis_client: Redis client instance
            sync_interval: Interval in seconds between sync operations
        """
        self.redis_client = redis_client
        self.sync_interval = sync_interval
        self.running = False
        self.sync_thread = None
        self._processed_devices: Set[int] = set()

        if not self.redis_client:
            self._initialize_redis()

    def _initialize_redis(self):
        """Initialize Redis connection"""
        try:
            from src.config.config import Config

            self.redis_client = redis.from_url(Config.REDIS_URL, decode_responses=True)
            self.redis_client.ping()
            logger.info("Status sync service connected to Redis")
        except Exception as e:
            logger.error(f"Failed to initialize Redis for status sync: {e}")
            self.redis_client = None

    def start(self):
        """Start the background synchronization service"""
        if self.running:
            logger.warning("Status sync service is already running")
            return

        if not self.redis_client:
            logger.error("Cannot start status sync service - Redis not available")
            return

        self.running = True
        self.sync_thread = threading.Thread(target=self._sync_loop, daemon=True)
        self.sync_thread.start()
        logger.info(f"Status sync service started with {self.sync_interval}s interval")

    def stop(self):
        """Stop the background synchronization service"""
        if not self.running:
            return

        self.running = False
        if self.sync_thread and self.sync_thread.is_alive():
            self.sync_thread.join(timeout=5)
        logger.info("Status sync service stopped")

    def _sync_loop(self):
        """Main synchronization loop"""
        while self.running:
            try:
                self._perform_sync()
                time.sleep(self.sync_interval)
            except Exception as e:
                logger.error(f"Error in status sync loop: {e}")
                time.sleep(5)  # Short delay on error

    def _perform_sync(self):
        """Perform a single synchronization pass"""
        if not self.redis_client:
            return

        try:
            # Get all device status keys from Redis
            status_keys = self.redis_client.keys("device:status:*")

            if not status_keys:
                logger.debug("No device statuses in Redis to sync")
                return

            synced_count = 0

            for key in status_keys:
                try:
                    # Extract device ID from key
                    device_id = int(key.split(":")[-1])

                    # Get status from Redis
                    redis_status = self.redis_client.get(key)

                    if redis_status:
                        # Sync to database
                        self._sync_device_to_database(device_id, redis_status)
                        synced_count += 1

                except (ValueError, AttributeError) as e:
                    logger.warning(f"Invalid device key format: {key} - {e}")
                    continue
                except Exception as e:
                    logger.error(f"Failed to sync device from key {key}: {e}")
                    continue

            if synced_count > 0:
                logger.debug(f"Synced {synced_count} device statuses to database")

        except Exception as e:
            logger.error(f"Failed to perform status sync: {e}")

    def _sync_device_to_database(self, device_id: int, redis_status: str):
        """
        Sync a single device status to database

        Args:
            device_id: The device ID
            redis_status: Status from Redis ('online' or 'offline')
        """
        try:
            # Use the standalone sync function to avoid Flask context issues
            from src.utils.redis_util import _sync_to_database_standalone

            _sync_to_database_standalone(device_id, redis_status)

            # Track that we've processed this device
            self._processed_devices.add(device_id)

        except Exception as e:
            logger.error(f"Failed to sync device {device_id} to database: {e}")

    def force_sync_all(self):
        """Force immediate synchronization of all device statuses"""
        logger.info("Forcing immediate sync of all device statuses")
        self._perform_sync()

    def force_sync_device(self, device_id: int) -> bool:
        """
        Force synchronization of a specific device

        Args:
            device_id: The device ID to sync

        Returns:
            bool: True if successful, False otherwise
        """
        if not self.redis_client:
            logger.error("Cannot sync device - Redis not available")
            return False

        try:
            key = f"device:status:{device_id}"
            redis_status = self.redis_client.get(key)

            if redis_status:
                self._sync_device_to_database(device_id, redis_status)
                logger.info(f"Force synced device {device_id} status: {redis_status}")
                return True
            else:
                logger.warning(f"No Redis status found for device {device_id}")
                return False

        except Exception as e:
            logger.error(f"Failed to force sync device {device_id}: {e}")
            return False

    def get_sync_stats(self) -> dict:
        """
        Get synchronization statistics

        Returns:
            dict: Statistics about the sync service
        """
        if not self.redis_client:
            return {"status": "redis_unavailable"}

        try:
            total_devices = len(self.redis_client.keys("device:status:*"))
            processed_devices = len(self._processed_devices)

            return {
                "status": "running" if self.running else "stopped",
                "sync_interval": self.sync_interval,
                "total_devices_in_redis": total_devices,
                "processed_devices": processed_devices,
                "redis_available": True,
            }
        except Exception as e:
            logger.error(f"Failed to get sync stats: {e}")
            return {"status": "error", "error": str(e)}

    def clear_processed_devices(self):
        """Clear the set of processed devices (for testing/reset)"""
        self._processed_devices.clear()
        logger.debug("Cleared processed devices set")


# Global service instance
_sync_service_instance = None


def get_status_sync_service() -> Optional[StatusSyncService]:
    """Get the global status sync service instance"""
    global _sync_service_instance
    if _sync_service_instance is None:
        _sync_service_instance = StatusSyncService()
    return _sync_service_instance


def start_status_sync_service(sync_interval: int = 30) -> bool:
    """
    Start the global status sync service

    Args:
        sync_interval: Interval in seconds between sync operations

    Returns:
        bool: True if started successfully, False otherwise
    """
    try:
        service = get_status_sync_service()
        if service:
            service.sync_interval = sync_interval
            service.start()
            return True
        return False
    except Exception as e:
        logger.error(f"Failed to start status sync service: {e}")
        return False


def stop_status_sync_service():
    """Stop the global status sync service"""
    global _sync_service_instance
    if _sync_service_instance:
        _sync_service_instance.stop()
        _sync_service_instance = None
