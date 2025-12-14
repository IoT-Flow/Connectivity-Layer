"""
Redis metrics collector for Prometheus.
Collects Redis status, memory, and performance metrics.
"""
import logging
from typing import Dict, Any

from src.utils.redis_util import get_redis_util
from src.metrics import (
    REDIS_STATUS,
    REDIS_MEMORY_USED,
    REDIS_MEMORY_PEAK,
    REDIS_MEMORY_FRAGMENTATION,
    REDIS_KEYS_TOTAL,
    REDIS_KEYS_EVICTED,
    REDIS_COMMANDS_PROCESSED,
    REDIS_CACHE_HITS,
    REDIS_CACHE_MISSES,
)

logger = logging.getLogger(__name__)


class RedisMetricsCollector:
    """Collects Redis-related metrics."""

    def __init__(self):
        """Initialize the Redis metrics collector."""
        self._redis_util = None
        self._redis_client = None
        self._last_stats = {}

    def collect_all_metrics(self) -> None:
        """Collect all Redis metrics."""
        try:
            self._initialize_redis_connection()
            self.collect_status_metrics()
            self.collect_memory_metrics()
            self.collect_performance_metrics()
            logger.debug("Redis metrics collected successfully")
        except Exception as e:
            logger.error(f"Error collecting Redis metrics: {e}")

    def _initialize_redis_connection(self):
        """Initialize Redis connection for metrics collection."""
        try:
            # Try to get Redis utility
            self._redis_util = get_redis_util()

            if self._redis_util and self._redis_util.available:
                self._redis_client = self._redis_util._redis_client
            else:
                # Try alternative Redis connection method
                try:
                    from src.utils.redis_util import DeviceRedisUtil

                    redis_util = DeviceRedisUtil()
                    if redis_util.available:
                        self._redis_client = redis_util._redis_client
                except Exception:
                    pass

        except Exception as e:
            logger.error(f"Error initializing Redis connection for metrics: {e}")
            self._redis_client = None

    def collect_status_metrics(self) -> None:
        """Collect Redis status and basic metrics."""
        try:
            if not self._redis_client:
                REDIS_STATUS.set(0)
                REDIS_KEYS_TOTAL.set(0)
                return

            # Test Redis connection
            try:
                self._redis_client.ping()
                REDIS_STATUS.set(1)

                # Get basic info
                info = self._redis_client.info()

                # Memory metrics
                if "used_memory" in info:
                    REDIS_MEMORY_USED.set(info["used_memory"])

                if "used_memory_peak" in info:
                    REDIS_MEMORY_PEAK.set(info["used_memory_peak"])

                if "mem_fragmentation_ratio" in info:
                    REDIS_MEMORY_FRAGMENTATION.set(info["mem_fragmentation_ratio"])

                # Commands processed
                if "total_commands_processed" in info:
                    REDIS_COMMANDS_PROCESSED._value._value = info["total_commands_processed"]

                # Keys evicted
                if "evicted_keys" in info:
                    REDIS_KEYS_EVICTED._value._value = info["evicted_keys"]

                # Get key count
                try:
                    key_count = self._redis_client.dbsize()
                    REDIS_KEYS_TOTAL.set(key_count)
                except Exception as e:
                    logger.debug(f"Could not get Redis key count: {e}")
                    REDIS_KEYS_TOTAL.set(0)

            except Exception as e:
                logger.error(f"Redis connection failed: {e}")
                REDIS_STATUS.set(0)
                REDIS_KEYS_TOTAL.set(0)

        except Exception as e:
            logger.error(f"Error collecting Redis status metrics: {e}")
            REDIS_STATUS.set(0)

    def collect_memory_metrics(self) -> None:
        """Collect detailed Redis memory metrics."""
        try:
            if not self._redis_client or not self._is_redis_available():
                return

            # Get memory info
            memory_info = self._redis_client.info("memory")

            if "used_memory" in memory_info:
                REDIS_MEMORY_USED.set(memory_info["used_memory"])

            if "used_memory_peak" in memory_info:
                REDIS_MEMORY_PEAK.set(memory_info["used_memory_peak"])

            if "mem_fragmentation_ratio" in memory_info:
                REDIS_MEMORY_FRAGMENTATION.set(memory_info["mem_fragmentation_ratio"])

        except Exception as e:
            logger.error(f"Error collecting Redis memory metrics: {e}")

    def collect_performance_metrics(self) -> None:
        """Collect Redis performance metrics."""
        try:
            if not self._redis_client or not self._is_redis_available():
                return

            # Get stats info
            stats_info = self._redis_client.info("stats")

            # Commands processed (cumulative counter)
            if "total_commands_processed" in stats_info:
                REDIS_COMMANDS_PROCESSED._value._value = stats_info["total_commands_processed"]

            # Evicted keys (cumulative counter)
            if "evicted_keys" in stats_info:
                REDIS_KEYS_EVICTED._value._value = stats_info["evicted_keys"]

            # Cache hits and misses
            if "keyspace_hits" in stats_info:
                REDIS_CACHE_HITS._value._value = stats_info["keyspace_hits"]

            if "keyspace_misses" in stats_info:
                REDIS_CACHE_MISSES._value._value = stats_info["keyspace_misses"]

        except Exception as e:
            logger.error(f"Error collecting Redis performance metrics: {e}")

    def _is_redis_available(self) -> bool:
        """Check if Redis is available."""
        try:
            if not self._redis_client:
                return False

            self._redis_client.ping()
            return True

        except Exception:
            return False

    def get_redis_info(self) -> Dict[str, Any]:
        """Get basic Redis information."""
        try:
            if not self._redis_client or not self._is_redis_available():
                return {"redis_available": False, "connection_status": "disconnected"}

            info = self._redis_client.info("server")

            return {
                "redis_available": True,
                "connection_status": "connected",
                "redis_version": info.get("redis_version", "unknown"),
                "redis_mode": info.get("redis_mode", "unknown"),
                "os": info.get("os", "unknown"),
                "uptime_in_seconds": info.get("uptime_in_seconds", 0),
            }

        except Exception as e:
            logger.error(f"Error getting Redis info: {e}")
            return {"redis_available": False, "connection_status": "error", "error": str(e)}

    def test_redis_operations(self) -> Dict[str, bool]:
        """Test basic Redis operations for health checking."""
        try:
            if not self._redis_client:
                return {"ping": False, "set": False, "get": False, "delete": False}

            results = {}

            # Test ping
            try:
                results["ping"] = self._redis_client.ping()
            except Exception:
                results["ping"] = False

            # Test set/get/delete
            test_key = "metrics_test_key"
            test_value = "metrics_test_value"

            try:
                # Test SET
                results["set"] = self._redis_client.set(test_key, test_value, ex=60)

                # Test GET
                retrieved_value = self._redis_client.get(test_key)
                results["get"] = retrieved_value == test_value

                # Test DELETE
                results["delete"] = self._redis_client.delete(test_key) > 0

            except Exception as e:
                logger.debug(f"Redis operation test failed: {e}")
                results.update({"set": False, "get": False, "delete": False})

            return results

        except Exception as e:
            logger.error(f"Error testing Redis operations: {e}")
            return {"ping": False, "set": False, "get": False, "delete": False}

    def increment_cache_hit(self):
        """Increment cache hit counter (called by application code)."""
        try:
            REDIS_CACHE_HITS.inc()
        except Exception as e:
            logger.error(f"Error incrementing Redis cache hit: {e}")

    def increment_cache_miss(self):
        """Increment cache miss counter (called by application code)."""
        try:
            REDIS_CACHE_MISSES.inc()
        except Exception as e:
            logger.error(f"Error incrementing Redis cache miss: {e}")

    def collect_redis_status(self):
        """Alias for collect_status_metrics for test compatibility."""
        self.collect_status_metrics()
