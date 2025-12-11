"""
Application metrics collector for Prometheus.
Collects IoTFlow-specific application metrics.
"""
import logging
import os
import time
import platform
from datetime import datetime, timezone
from typing import Dict, Any

from src.models import Device, User, DeviceControl
from src.metrics import (
    APP_INFO,
    APP_UPTIME_SECONDS,
    APP_START_TIME,
    IOTFLOW_DEVICES_TOTAL,
    IOTFLOW_DEVICES_ACTIVE,
    IOTFLOW_DEVICES_ONLINE,
    IOTFLOW_USERS_TOTAL,
    IOTFLOW_TELEMETRY_MESSAGES,
    IOTFLOW_CONTROL_COMMANDS,
)

logger = logging.getLogger(__name__)


class ApplicationMetricsCollector:
    """Collects application-specific metrics."""

    def __init__(self):
        """Initialize the application metrics collector."""
        self.start_time = time.time()
        self._set_app_start_time()
        self._set_app_info()

    def _set_app_start_time(self):
        """Set the application start time metric."""
        try:
            APP_START_TIME.set(self.start_time)
        except Exception as e:
            logger.error(f"Error setting app start time: {e}")

    def _set_app_info(self):
        """Set application information metric."""
        try:
            # Get application version (could be from environment or config)
            app_version = self._get_app_version()

            APP_INFO.info(
                {
                    "version": app_version,
                    "python_version": platform.python_version(),
                    "platform": platform.system(),
                    "architecture": platform.machine(),
                    "hostname": platform.node(),
                }
            )

        except Exception as e:
            logger.error(f"Error setting app info: {e}")

    def _get_app_version(self) -> str:
        """Get application version."""
        try:
            # Try to get version from environment variable
            import os

            version = os.environ.get("APP_VERSION", "1.0.0")

            # Try to get from package if available
            try:
                import pkg_resources

                version = pkg_resources.get_distribution("iot-connectivity-layer").version
            except Exception:
                pass

            return version

        except Exception:
            return "1.0.0"

    def collect_all_metrics(self) -> None:
        """Collect all application metrics."""
        try:
            self.collect_uptime_metrics()
            self.collect_device_metrics()
            self.collect_user_metrics()
            self.collect_control_metrics()
            logger.debug("Application metrics collected successfully")
        except Exception as e:
            logger.error(f"Error collecting application metrics: {e}")

    def collect_uptime_metrics(self) -> None:
        """Collect application uptime metrics."""
        try:
            current_time = time.time()
            uptime_seconds = current_time - self.start_time
            APP_UPTIME_SECONDS.set(uptime_seconds)

        except Exception as e:
            logger.error(f"Error collecting uptime metrics: {e}")

    def collect_device_metrics(self) -> None:
        """Collect device-related metrics."""
        try:
            # Total devices
            total_devices = Device.query.count()
            IOTFLOW_DEVICES_TOTAL.set(total_devices)

            # Active devices (status = 'active')
            active_devices = Device.query.filter(Device.status == "active").count()
            IOTFLOW_DEVICES_ACTIVE.set(active_devices)

            # Online devices (recently seen)
            # Consider devices online if seen within last 5 minutes
            five_minutes_ago = datetime.now(timezone.utc).timestamp() - 300
            online_devices = Device.query.filter(
                Device.last_seen >= datetime.fromtimestamp(five_minutes_ago, timezone.utc)
            ).count()
            IOTFLOW_DEVICES_ONLINE.set(online_devices)

        except Exception as e:
            logger.error(f"Error collecting device metrics: {e}")
            # Set to 0 on error to avoid stale metrics
            IOTFLOW_DEVICES_TOTAL.set(0)
            IOTFLOW_DEVICES_ACTIVE.set(0)
            IOTFLOW_DEVICES_ONLINE.set(0)

    def collect_user_metrics(self) -> None:
        """Collect user-related metrics."""
        try:
            total_users = User.query.count()
            IOTFLOW_USERS_TOTAL.set(total_users)

        except Exception as e:
            logger.error(f"Error collecting user metrics: {e}")
            IOTFLOW_USERS_TOTAL.set(0)

    def collect_control_metrics(self) -> None:
        """Collect device control command metrics."""
        try:
            # Count control commands by status
            pending_commands = DeviceControl.query.filter(DeviceControl.status == "pending").count()

            completed_commands = DeviceControl.query.filter(DeviceControl.status == "completed").count()

            failed_commands = DeviceControl.query.filter(DeviceControl.status == "failed").count()

            # Update counters (these should be cumulative)
            # Note: For proper counter behavior, we should track increments
            # For now, we'll set the current totals
            IOTFLOW_CONTROL_COMMANDS.labels(status="pending")._value._value = pending_commands
            IOTFLOW_CONTROL_COMMANDS.labels(status="completed")._value._value = completed_commands
            IOTFLOW_CONTROL_COMMANDS.labels(status="failed")._value._value = failed_commands

        except Exception as e:
            logger.error(f"Error collecting control metrics: {e}")

    def collect_app_info_metrics(self) -> None:
        """Update application info metrics."""
        try:
            self._set_app_info()
        except Exception as e:
            logger.error(f"Error collecting app info metrics: {e}")

    def increment_telemetry_message(self):
        """Increment telemetry message counter (called by telemetry handlers)."""
        try:
            IOTFLOW_TELEMETRY_MESSAGES.inc()
        except Exception as e:
            logger.error(f"Error incrementing telemetry message counter: {e}")

    def increment_control_command(self, status: str = "pending"):
        """Increment control command counter (called by control handlers)."""
        try:
            IOTFLOW_CONTROL_COMMANDS.labels(status=status).inc()
        except Exception as e:
            logger.error(f"Error incrementing control command counter: {e}")

    def get_application_info(self) -> Dict[str, Any]:
        """Get comprehensive application information."""
        try:
            current_time = time.time()
            uptime_seconds = current_time - self.start_time

            # Get database counts
            try:
                device_count = Device.query.count()
                user_count = User.query.count()
                control_count = DeviceControl.query.count()
            except Exception as e:
                logger.error(f"Error getting database counts: {e}")
                device_count = user_count = control_count = 0

            return {
                "version": self._get_app_version(),
                "python_version": platform.python_version(),
                "platform": platform.system(),
                "architecture": platform.machine(),
                "hostname": platform.node(),
                "start_time": self.start_time,
                "uptime_seconds": uptime_seconds,
                "uptime_formatted": self._format_uptime(uptime_seconds),
                "total_devices": device_count,
                "total_users": user_count,
                "total_controls": control_count,
                "memory_usage": self._get_memory_usage(),
                "process_id": os.getpid() if "os" in globals() else None,
            }

        except Exception as e:
            logger.error(f"Error getting application info: {e}")
            return {"version": self._get_app_version(), "error": str(e)}

    def _format_uptime(self, uptime_seconds: float) -> str:
        """Format uptime in human-readable format."""
        try:
            days = int(uptime_seconds // 86400)
            hours = int((uptime_seconds % 86400) // 3600)
            minutes = int((uptime_seconds % 3600) // 60)
            seconds = int(uptime_seconds % 60)

            if days > 0:
                return f"{days}d {hours}h {minutes}m {seconds}s"
            elif hours > 0:
                return f"{hours}h {minutes}m {seconds}s"
            elif minutes > 0:
                return f"{minutes}m {seconds}s"
            else:
                return f"{seconds}s"

        except Exception:
            return f"{int(uptime_seconds)}s"

    def _get_memory_usage(self) -> Dict[str, Any]:
        """Get current memory usage information."""
        try:
            import psutil
            import os

            process = psutil.Process(os.getpid())
            memory_info = process.memory_info()

            return {
                "rss": memory_info.rss,  # Resident Set Size
                "vms": memory_info.vms,  # Virtual Memory Size
                "percent": process.memory_percent(),
                "available": psutil.virtual_memory().available,
            }

        except Exception as e:
            logger.debug(f"Could not get memory usage: {e}")
            return {}
