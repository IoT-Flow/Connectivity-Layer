"""
IoTDB metrics collector for Prometheus.
Collects IoTDB connection status and query performance metrics.
"""
import logging
from typing import Dict, Any

from src.metrics import (
    IOTDB_CONNECTION_STATUS,
    IOTDB_QUERY_SUCCESS_RATE,
    IOTDB_WRITE_SUCCESS_RATE,
)

logger = logging.getLogger(__name__)


class IoTDBMetricsCollector:
    """Collects IoTDB-related metrics."""

    def __init__(self):
        """Initialize the IoTDB metrics collector."""
        self._iotdb_service = None
        self._query_success_count = 0
        self._query_total_count = 0
        self._write_success_count = 0
        self._write_total_count = 0
        self._initialize_iotdb_reference()

    def _initialize_iotdb_reference(self):
        """Initialize reference to IoTDB service."""
        try:
            from src.services.iotdb import IoTDBService

            try:
                self._iotdb_service = IoTDBService()
            except Exception as e:
                logger.debug(f"IoTDB service not available: {e}")
                self._iotdb_service = None

        except ImportError as e:
            logger.warning(f"IoTDB service not available for metrics: {e}")
        except Exception as e:
            logger.error(f"Error initializing IoTDB reference: {e}")

    def collect_all_metrics(self) -> None:
        """Collect all IoTDB metrics."""
        try:
            self.collect_iotdb_status()
            self.collect_performance_metrics()
            logger.debug("IoTDB metrics collected successfully")
        except Exception as e:
            logger.error(f"Error collecting IoTDB metrics: {e}")

    def collect_iotdb_status(self) -> None:
        """Collect IoTDB connection status."""
        try:
            if not self._iotdb_service:
                IOTDB_CONNECTION_STATUS.set(0)
                return

            # Test IoTDB connection
            try:
                if hasattr(self._iotdb_service, "is_connected"):
                    is_connected = self._iotdb_service.is_connected()
                elif hasattr(self._iotdb_service, "check_connection"):
                    is_connected = self._iotdb_service.check_connection()
                elif hasattr(self._iotdb_service, "session"):
                    is_connected = self._iotdb_service.session is not None
                else:
                    # Fallback: assume connected if service exists
                    is_connected = True

                IOTDB_CONNECTION_STATUS.set(1 if is_connected else 0)

            except Exception as e:
                logger.debug(f"IoTDB connection check failed: {e}")
                IOTDB_CONNECTION_STATUS.set(0)

        except Exception as e:
            logger.error(f"Error collecting IoTDB status: {e}")
            IOTDB_CONNECTION_STATUS.set(0)

    def collect_performance_metrics(self) -> None:
        """Collect IoTDB performance metrics."""
        try:
            # Calculate success rates
            if self._query_total_count > 0:
                query_success_rate = (self._query_success_count / self._query_total_count) * 100
                IOTDB_QUERY_SUCCESS_RATE.set(query_success_rate)
            else:
                IOTDB_QUERY_SUCCESS_RATE.set(100.0)  # Default to 100% if no queries yet

            if self._write_total_count > 0:
                write_success_rate = (self._write_success_count / self._write_total_count) * 100
                IOTDB_WRITE_SUCCESS_RATE.set(write_success_rate)
            else:
                IOTDB_WRITE_SUCCESS_RATE.set(100.0)  # Default to 100% if no writes yet

        except Exception as e:
            logger.error(f"Error collecting IoTDB performance metrics: {e}")

    def record_query_success(self):
        """Record a successful IoTDB query."""
        self._query_success_count += 1
        self._query_total_count += 1

    def record_query_failure(self):
        """Record a failed IoTDB query."""
        self._query_total_count += 1

    def record_write_success(self):
        """Record a successful IoTDB write."""
        self._write_success_count += 1
        self._write_total_count += 1

    def record_write_failure(self):
        """Record a failed IoTDB write."""
        self._write_total_count += 1

    def get_connection_status(self) -> Dict[str, Any]:
        """Get current IoTDB connection status."""
        try:
            if not self._iotdb_service:
                return {
                    "connected": False,
                    "message": "IoTDB service not initialized",
                }

            is_connected = IOTDB_CONNECTION_STATUS._value._value == 1

            return {
                "connected": is_connected,
                "query_success_rate": IOTDB_QUERY_SUCCESS_RATE._value._value,
                "write_success_rate": IOTDB_WRITE_SUCCESS_RATE._value._value,
            }

        except Exception as e:
            logger.error(f"Error getting IoTDB connection status: {e}")
            return {"connected": False, "error": str(e)}
