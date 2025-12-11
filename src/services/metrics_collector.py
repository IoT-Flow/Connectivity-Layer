"""
Main metrics collector coordinator for Prometheus.
Manages background collection of all metrics every 15 seconds.
"""
import logging
import threading
import time
from typing import Optional

from src.services.system_metrics import SystemMetricsCollector
from src.services.database_metrics import DatabaseMetricsCollector
from src.services.mqtt_metrics import MQTTMetricsCollector
from src.services.redis_metrics import RedisMetricsCollector
from src.services.application_metrics import ApplicationMetricsCollector

logger = logging.getLogger(__name__)


class MetricsCollector:
    """Main coordinator for all metrics collection."""

    def __init__(self, collection_interval: int = 15):
        """
        Initialize the metrics collector.

        Args:
            collection_interval: Interval in seconds between collections (default: 15)
        """
        self.collection_interval = collection_interval
        self._running = False
        self._thread: Optional[threading.Thread] = None

        # Initialize individual collectors
        self.system_collector = SystemMetricsCollector()
        self.database_collector = DatabaseMetricsCollector()
        self.mqtt_collector = MQTTMetricsCollector()
        self.redis_collector = RedisMetricsCollector()
        self.application_collector = ApplicationMetricsCollector()

        logger.info(f"Metrics collector initialized with {collection_interval}s interval")

    def start(self) -> None:
        """Start the background metrics collection thread."""
        if self._running:
            logger.warning("Metrics collector is already running")
            return

        self._running = True
        self._thread = threading.Thread(target=self._collection_loop, name="MetricsCollector", daemon=True)
        self._thread.start()
        logger.info("Metrics collection started")

    def stop(self) -> None:
        """Stop the background metrics collection thread."""
        if not self._running:
            logger.warning("Metrics collector is not running")
            return

        self._running = False
        if self._thread and self._thread.is_alive():
            self._thread.join(timeout=5)

        logger.info("Metrics collection stopped")

    def _collection_loop(self) -> None:
        """Main collection loop that runs in background thread."""
        logger.info("Metrics collection loop started")

        while self._running:
            try:
                start_time = time.time()

                # Collect all metrics
                self._collect_all_metrics()

                # Calculate collection duration
                collection_duration = time.time() - start_time
                logger.debug(f"Metrics collection completed in {collection_duration:.3f}s")

                # Sleep for the remaining interval time
                sleep_time = max(0, self.collection_interval - collection_duration)
                if sleep_time > 0:
                    time.sleep(sleep_time)
                else:
                    logger.warning(
                        f"Metrics collection took {collection_duration:.3f}s, "
                        f"longer than interval {self.collection_interval}s"
                    )

            except Exception as e:
                logger.error(f"Error in metrics collection loop: {e}")
                # Sleep before retrying to avoid tight error loops
                time.sleep(min(self.collection_interval, 30))

        logger.info("Metrics collection loop ended")

    def _collect_all_metrics(self) -> None:
        """Collect metrics from all collectors."""
        collectors = [
            ("System", self.system_collector),
            ("Database", self.database_collector),
            ("MQTT", self.mqtt_collector),
            ("Redis", self.redis_collector),
            ("Application", self.application_collector),
        ]

        for name, collector in collectors:
            try:
                collector.collect_all_metrics()
            except Exception as e:
                logger.error(f"Error collecting {name} metrics: {e}")
                # Continue with other collectors even if one fails

    def collect_once(self) -> None:
        """Collect metrics once (synchronous, for testing or manual collection)."""
        try:
            start_time = time.time()
            self._collect_all_metrics()
            duration = time.time() - start_time
            logger.info(f"Manual metrics collection completed in {duration:.3f}s")
        except Exception as e:
            logger.error(f"Error in manual metrics collection: {e}")
            raise

    def get_collection_stats(self) -> dict:
        """Get statistics about the metrics collection process."""
        return {
            "running": self._running,
            "collection_interval": self.collection_interval,
            "thread_alive": self._thread.is_alive() if self._thread else False,
            "thread_name": self._thread.name if self._thread else None,
            "collectors": {
                "system": self.system_collector is not None,
                "database": self.database_collector is not None,
                "mqtt": self.mqtt_collector is not None,
                "redis": self.redis_collector is not None,
                "application": self.application_collector is not None,
            },
        }

    def is_running(self) -> bool:
        """Check if the metrics collector is currently running."""
        return self._running and (self._thread is not None and self._thread.is_alive())

    def restart(self) -> None:
        """Restart the metrics collection (stop and start)."""
        logger.info("Restarting metrics collector")
        self.stop()
        time.sleep(1)  # Brief pause
        self.start()


# Global metrics collector instance
_metrics_collector: Optional[MetricsCollector] = None


def get_metrics_collector() -> MetricsCollector:
    """Get the global metrics collector instance."""
    global _metrics_collector
    if _metrics_collector is None:
        _metrics_collector = MetricsCollector()
    return _metrics_collector


def start_metrics_collection() -> None:
    """Start the global metrics collection."""
    global _metrics_collector
    collector = get_metrics_collector()
    collector.start()
    _metrics_collector = collector


def stop_metrics_collection() -> None:
    """Stop the global metrics collection."""
    global _metrics_collector
    if _metrics_collector:
        _metrics_collector.stop()
        _metrics_collector = None


def is_metrics_collection_running() -> bool:
    """Check if metrics collection is running."""
    return _metrics_collector is not None and _metrics_collector.is_running()


def collect_metrics_once() -> None:
    """Collect metrics once (for testing or manual collection)."""
    collector = get_metrics_collector()
    collector.collect_once()
