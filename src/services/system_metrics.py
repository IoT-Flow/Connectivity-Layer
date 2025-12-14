"""
System metrics collector for Prometheus.
Collects CPU, memory, disk, and network metrics using psutil.
"""
import logging
import psutil
import time
from typing import Dict, Any

from src.metrics import (
    SYSTEM_CPU_USAGE,
    SYSTEM_CPU_CORES,
    SYSTEM_LOAD_AVERAGE,
    SYSTEM_MEMORY_USAGE,
    SYSTEM_MEMORY_TOTAL,
    SYSTEM_MEMORY_USED,
    SYSTEM_DISK_USAGE,
    SYSTEM_DISK_TOTAL,
    SYSTEM_DISK_USED,
    SYSTEM_DISK_IO_READ_BYTES,
    SYSTEM_DISK_IO_WRITE_BYTES,
    SYSTEM_DISK_IO_READ_RATE,
    SYSTEM_DISK_IO_WRITE_RATE,
    SYSTEM_NETWORK_BYTES_SENT,
    SYSTEM_NETWORK_BYTES_RECEIVED,
    SYSTEM_NETWORK_PACKETS_SENT,
    SYSTEM_NETWORK_PACKETS_RECEIVED,
)

logger = logging.getLogger(__name__)


class SystemMetricsCollector:
    """Collects system-level metrics using psutil."""

    def __init__(self):
        """Initialize the system metrics collector."""
        self._last_network_stats = None
        self._last_network_time = None
        self._last_disk_io_stats = {}
        self._last_disk_io_time = {}

    def collect_all_metrics(self) -> None:
        """Collect all system metrics."""
        try:
            self.collect_cpu_metrics()
            self.collect_memory_metrics()
            self.collect_disk_metrics()
            self.collect_disk_io_metrics()
            self.collect_network_metrics()
            logger.debug("System metrics collected successfully")
        except Exception as e:
            logger.error(f"Error collecting system metrics: {e}")

    def collect_cpu_metrics(self) -> None:
        """Collect CPU usage and load metrics."""
        try:
            # CPU usage percentage (non-blocking, uses cached value)
            # First call initializes, subsequent calls return actual usage
            cpu_percent = psutil.cpu_percent(interval=0.1)
            SYSTEM_CPU_USAGE.set(cpu_percent)

            # CPU core count
            cpu_cores = psutil.cpu_count()
            SYSTEM_CPU_CORES.set(cpu_cores)

            # Load average (Unix systems only)
            try:
                load_avg = psutil.getloadavg()
                SYSTEM_LOAD_AVERAGE.labels(period="1min").set(load_avg[0])
                SYSTEM_LOAD_AVERAGE.labels(period="5min").set(load_avg[1])
                SYSTEM_LOAD_AVERAGE.labels(period="15min").set(load_avg[2])
            except (AttributeError, OSError):
                # getloadavg not available on Windows
                logger.debug("Load average not available on this platform")

        except Exception as e:
            logger.error(f"Error collecting CPU metrics: {e}")

    def collect_memory_metrics(self) -> None:
        """Collect memory usage metrics."""
        try:
            memory = psutil.virtual_memory()

            SYSTEM_MEMORY_USAGE.set(memory.percent)
            SYSTEM_MEMORY_TOTAL.set(memory.total)
            SYSTEM_MEMORY_USED.set(memory.used)

        except Exception as e:
            logger.error(f"Error collecting memory metrics: {e}")

    def collect_disk_metrics(self) -> None:
        """Collect disk usage metrics for all mount points."""
        try:
            # Get all disk partitions
            partitions = psutil.disk_partitions()

            for partition in partitions:
                try:
                    # Skip special filesystems
                    if partition.fstype in ("", "tmpfs", "devtmpfs", "squashfs"):
                        continue

                    usage = psutil.disk_usage(partition.mountpoint)

                    # Use mountpoint as label
                    mount_point = partition.mountpoint

                    SYSTEM_DISK_USAGE.labels(path=mount_point).set((usage.used / usage.total) * 100)
                    SYSTEM_DISK_TOTAL.labels(path=mount_point).set(usage.total)
                    SYSTEM_DISK_USED.labels(path=mount_point).set(usage.used)

                except (PermissionError, OSError) as e:
                    logger.debug(f"Cannot access disk {partition.mountpoint}: {e}")
                    continue

        except Exception as e:
            logger.error(f"Error collecting disk metrics: {e}")

    def collect_disk_io_metrics(self) -> None:
        """Collect disk I/O metrics for all disks."""
        try:
            current_time = time.time()
            disk_io = psutil.disk_io_counters(perdisk=True)

            if not disk_io:
                logger.debug("No disk I/O data available")
                return

            for device, stats in disk_io.items():
                try:
                    # Update cumulative counters
                    SYSTEM_DISK_IO_READ_BYTES.labels(device=device)._value._value = stats.read_bytes
                    SYSTEM_DISK_IO_WRITE_BYTES.labels(device=device)._value._value = stats.write_bytes

                    # Calculate rates if we have previous data
                    if device in self._last_disk_io_stats and device in self._last_disk_io_time:
                        last_stats = self._last_disk_io_stats[device]
                        last_time = self._last_disk_io_time[device]
                        time_delta = current_time - last_time

                        if time_delta > 0:
                            read_rate = (stats.read_bytes - last_stats.read_bytes) / time_delta
                            write_rate = (stats.write_bytes - last_stats.write_bytes) / time_delta

                            SYSTEM_DISK_IO_READ_RATE.labels(device=device).set(max(0, read_rate))
                            SYSTEM_DISK_IO_WRITE_RATE.labels(device=device).set(max(0, write_rate))

                    # Store current stats for next calculation
                    self._last_disk_io_stats[device] = stats
                    self._last_disk_io_time[device] = current_time

                except Exception as e:
                    logger.debug(f"Error collecting disk I/O for {device}: {e}")
                    continue

        except Exception as e:
            logger.error(f"Error collecting disk I/O metrics: {e}")

    def _calculate_disk_io_rates(self, previous_stats: Dict, current_stats: Dict) -> Dict:
        """Calculate disk I/O rates for all devices.

        Args:
            previous_stats: Dict with device names as keys and stats dicts with 'read_bytes', 'write_bytes', 'timestamp'
            current_stats: Dict with device names as keys and stats dicts with 'read_bytes', 'write_bytes', 'timestamp'

        Returns:
            Dict with device names as keys and rate dicts with 'read_rate' and 'write_rate' in bytes/second
        """
        rates = {}

        for device, current in current_stats.items():
            if device not in previous_stats:
                continue

            previous = previous_stats[device]
            time_delta = current.get("timestamp", 0) - previous.get("timestamp", 0)

            if time_delta <= 0:
                continue

            read_rate = (current.get("read_bytes", 0) - previous.get("read_bytes", 0)) / time_delta
            write_rate = (current.get("write_bytes", 0) - previous.get("write_bytes", 0)) / time_delta

            rates[device] = {"read_rate": max(0, read_rate), "write_rate": max(0, write_rate)}

        return rates

    def collect_network_metrics(self) -> None:
        """Collect network I/O metrics."""
        try:
            current_stats = psutil.net_io_counters()
            current_time = time.time()

            if current_stats:
                # Update counters with total values
                SYSTEM_NETWORK_BYTES_SENT._value._value = current_stats.bytes_sent
                SYSTEM_NETWORK_BYTES_RECEIVED._value._value = current_stats.bytes_recv
                SYSTEM_NETWORK_PACKETS_SENT._value._value = current_stats.packets_sent
                SYSTEM_NETWORK_PACKETS_RECEIVED._value._value = current_stats.packets_recv

                # Store current stats for next calculation
                self._last_network_stats = current_stats
                self._last_network_time = current_time

        except Exception as e:
            logger.error(f"Error collecting network metrics: {e}")

    def get_system_info(self) -> Dict[str, Any]:
        """Get basic system information."""
        try:
            return {
                "platform": psutil.LINUX if hasattr(psutil, "LINUX") else "unknown",
                "cpu_count": psutil.cpu_count(),
                "memory_total": psutil.virtual_memory().total,
                "boot_time": psutil.boot_time(),
            }
        except Exception as e:
            logger.error(f"Error getting system info: {e}")
            return {}
