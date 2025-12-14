"""
Unit tests for disk I/O metrics implementation.
Following TDD approach - tests written first, then implementation.
"""
import pytest
import time
from unittest.mock import patch, MagicMock
from src.metrics import (
    SYSTEM_DISK_IO_READ_BYTES,
    SYSTEM_DISK_IO_WRITE_BYTES,
    SYSTEM_DISK_IO_READ_RATE,
    SYSTEM_DISK_IO_WRITE_RATE,
)
from src.services.system_metrics import SystemMetricsCollector


class TestDiskIOMetrics:
    """Test disk I/O metrics definitions and collection"""

    def test_disk_io_metrics_exist(self):
        """Test that disk I/O metrics are properly defined"""
        # Test that metrics are defined as expected types
        assert hasattr(SYSTEM_DISK_IO_READ_BYTES, "_name")
        assert hasattr(SYSTEM_DISK_IO_WRITE_BYTES, "_name")
        assert hasattr(SYSTEM_DISK_IO_READ_RATE, "_name")
        assert hasattr(SYSTEM_DISK_IO_WRITE_RATE, "_name")

        # Test metric names (Counter._name doesn't include _total suffix, that's added during export)
        assert SYSTEM_DISK_IO_READ_BYTES._name == "system_disk_io_read_bytes"
        assert SYSTEM_DISK_IO_WRITE_BYTES._name == "system_disk_io_write_bytes"
        assert SYSTEM_DISK_IO_READ_RATE._name == "system_disk_io_read_rate_bytes_per_second"
        assert SYSTEM_DISK_IO_WRITE_RATE._name == "system_disk_io_write_rate_bytes_per_second"

    def test_disk_io_metrics_have_labels(self):
        """Test that disk I/O metrics have appropriate labels"""
        # Test that metrics have device labels for per-disk tracking
        assert SYSTEM_DISK_IO_READ_BYTES._labelnames == ("device",)
        assert SYSTEM_DISK_IO_WRITE_BYTES._labelnames == ("device",)
        assert SYSTEM_DISK_IO_READ_RATE._labelnames == ("device",)
        assert SYSTEM_DISK_IO_WRITE_RATE._labelnames == ("device",)

    def test_disk_io_metrics_types(self):
        """Test that disk I/O metrics are correct Prometheus types"""
        from prometheus_client import Counter, Gauge

        # Counters for cumulative bytes
        assert isinstance(SYSTEM_DISK_IO_READ_BYTES, Counter)
        assert isinstance(SYSTEM_DISK_IO_WRITE_BYTES, Counter)

        # Gauges for current rates
        assert isinstance(SYSTEM_DISK_IO_READ_RATE, Gauge)
        assert isinstance(SYSTEM_DISK_IO_WRITE_RATE, Gauge)


class TestSystemMetricsCollectorDiskIO:
    """Test disk I/O metrics collection in SystemMetricsCollector"""

    def setup_method(self):
        """Setup test fixtures"""
        self.collector = SystemMetricsCollector()

    @patch("psutil.disk_io_counters")
    def test_collect_disk_io_metrics_success(self, mock_disk_io):
        """Test successful disk I/O metrics collection"""
        # Mock psutil disk I/O data
        mock_disk_stats = MagicMock()
        mock_disk_stats.read_bytes = 1024000000  # 1GB read
        mock_disk_stats.write_bytes = 512000000  # 512MB written
        mock_disk_stats.read_count = 1000
        mock_disk_stats.write_count = 500

        mock_disk_io.return_value = {"sda": mock_disk_stats, "sdb": mock_disk_stats}

        # Test collection method exists and works
        assert hasattr(self.collector, "collect_disk_io_metrics")

        # Should not raise exception
        self.collector.collect_disk_io_metrics()

        # Verify psutil was called
        mock_disk_io.assert_called_once_with(perdisk=True)

    @patch("psutil.disk_io_counters")
    def test_collect_disk_io_metrics_no_data(self, mock_disk_io):
        """Test disk I/O collection when no data available"""
        mock_disk_io.return_value = None

        # Should handle gracefully without raising exception
        self.collector.collect_disk_io_metrics()

        mock_disk_io.assert_called_once_with(perdisk=True)

    @patch("psutil.disk_io_counters")
    def test_collect_disk_io_metrics_exception(self, mock_disk_io):
        """Test disk I/O collection handles exceptions"""
        mock_disk_io.side_effect = Exception("Disk I/O error")

        # Should handle exception gracefully
        self.collector.collect_disk_io_metrics()

        mock_disk_io.assert_called_once_with(perdisk=True)

    def test_disk_io_rate_calculation(self):
        """Test disk I/O rate calculation logic"""
        # Test that rate calculation method exists
        assert hasattr(self.collector, "_calculate_disk_io_rates")

        # Mock previous readings
        previous_stats = {"sda": {"read_bytes": 1000000, "write_bytes": 500000, "timestamp": time.time() - 1}}
        current_stats = {"sda": {"read_bytes": 1100000, "write_bytes": 600000, "timestamp": time.time()}}

        rates = self.collector._calculate_disk_io_rates(previous_stats, current_stats)

        # Should return rates in bytes per second
        assert "sda" in rates
        assert "read_rate" in rates["sda"]
        assert "write_rate" in rates["sda"]
        assert rates["sda"]["read_rate"] > 0
        assert rates["sda"]["write_rate"] > 0

    def test_disk_io_metrics_integration(self):
        """Test that disk I/O metrics are included in collect_all_metrics"""
        with patch.object(self.collector, "collect_disk_io_metrics") as mock_collect:
            self.collector.collect_all_metrics()
            mock_collect.assert_called_once()


class TestDiskIOMetricsPrometheus:
    """Test disk I/O metrics Prometheus integration"""

    def test_disk_io_metrics_in_prometheus_output(self):
        """Test that disk I/O metrics appear in Prometheus output"""
        from prometheus_client import generate_latest

        # Set some test values
        SYSTEM_DISK_IO_READ_BYTES.labels(device="sda").inc(1000000)
        SYSTEM_DISK_IO_WRITE_BYTES.labels(device="sda").inc(500000)
        SYSTEM_DISK_IO_READ_RATE.labels(device="sda").set(1024.5)
        SYSTEM_DISK_IO_WRITE_RATE.labels(device="sda").set(512.25)

        # Generate Prometheus output
        output = generate_latest().decode("utf-8")

        # Check that our metrics are present
        assert "system_disk_io_read_bytes_total" in output
        assert "system_disk_io_write_bytes_total" in output
        assert "system_disk_io_read_rate_bytes_per_second" in output
        assert "system_disk_io_write_rate_bytes_per_second" in output

        # Check device labels
        assert 'device="sda"' in output

    def test_disk_io_metrics_help_text(self):
        """Test that disk I/O metrics have proper help text"""
        from prometheus_client import generate_latest

        output = generate_latest().decode("utf-8")

        # Check for HELP comments
        assert "# HELP system_disk_io_read_bytes_total" in output
        assert "# HELP system_disk_io_write_bytes_total" in output
        assert "# HELP system_disk_io_read_rate_bytes_per_second" in output
        assert "# HELP system_disk_io_write_rate_bytes_per_second" in output

    def test_disk_io_metrics_type_declarations(self):
        """Test that disk I/O metrics have correct TYPE declarations"""
        from prometheus_client import generate_latest

        output = generate_latest().decode("utf-8")

        # Check for TYPE declarations
        assert "# TYPE system_disk_io_read_bytes_total counter" in output
        assert "# TYPE system_disk_io_write_bytes_total counter" in output
        assert "# TYPE system_disk_io_read_rate_bytes_per_second gauge" in output
        assert "# TYPE system_disk_io_write_rate_bytes_per_second gauge" in output


class TestDiskIOMetricsEndpoint:
    """Test disk I/O metrics in /metrics endpoint"""

    def test_metrics_endpoint_includes_disk_io(self, client):
        """Test that /metrics endpoint includes disk I/O metrics"""
        # This test requires admin authentication
        headers = {"Authorization": "admin test"}

        response = client.get("/metrics", headers=headers)
        assert response.status_code == 200

        content = response.data.decode("utf-8")

        # Check that disk I/O metrics are present
        assert "system_disk_io_read_bytes_total" in content
        assert "system_disk_io_write_bytes_total" in content
        assert "system_disk_io_read_rate_bytes_per_second" in content
        assert "system_disk_io_write_rate_bytes_per_second" in content

    def test_disk_io_metrics_values_realistic(self, client):
        """Test that disk I/O metrics have realistic values"""
        headers = {"Authorization": "admin test"}

        response = client.get("/metrics", headers=headers)
        assert response.status_code == 200

        content = response.data.decode("utf-8")

        # Parse metrics and check for reasonable values
        lines = content.split("\n")
        disk_io_lines = [line for line in lines if "system_disk_io" in line and not line.startswith("#")]

        # Should have at least some disk I/O metrics
        assert len(disk_io_lines) > 0

        # Values should be non-negative numbers
        for line in disk_io_lines:
            if " " in line:
                value_part = line.split(" ")[-1]
                try:
                    value = float(value_part)
                    assert value >= 0, f"Disk I/O metric should be non-negative: {line}"
                except ValueError:
                    pass  # Skip lines that don't end with numbers


class TestDiskIOMetricsDocumentation:
    """Test that disk I/O metrics are properly documented"""

    def test_disk_io_metrics_in_documentation(self):
        """Test that disk I/O metrics are documented in metrics.py"""
        import src.metrics as metrics_module

        # Check that metrics are defined in the module
        assert hasattr(metrics_module, "SYSTEM_DISK_IO_READ_BYTES")
        assert hasattr(metrics_module, "SYSTEM_DISK_IO_WRITE_BYTES")
        assert hasattr(metrics_module, "SYSTEM_DISK_IO_READ_RATE")
        assert hasattr(metrics_module, "SYSTEM_DISK_IO_WRITE_RATE")

    def test_disk_io_metrics_comments(self):
        """Test that disk I/O metrics have descriptive comments"""
        # Read the metrics.py file to check for comments
        with open("src/metrics.py", "r") as f:
            content = f.read()

        # Should have comments explaining disk I/O metrics
        assert "Disk I/O Metrics" in content or "DISK I/O" in content
        assert "read_bytes" in content
        assert "write_bytes" in content
        assert "bytes per second" in content.lower()


# Integration test for the complete disk I/O metrics flow
class TestDiskIOMetricsIntegration:
    """Integration tests for complete disk I/O metrics flow"""

    @patch("psutil.disk_io_counters")
    def test_complete_disk_io_flow(self, mock_disk_io):
        """Test complete flow from collection to Prometheus output"""
        # Mock realistic disk I/O data
        mock_stats = MagicMock()
        mock_stats.read_bytes = 2048000000  # 2GB
        mock_stats.write_bytes = 1024000000  # 1GB

        mock_disk_io.return_value = {"sda": mock_stats}

        # Create collector and collect metrics
        collector = SystemMetricsCollector()
        collector.collect_disk_io_metrics()

        # Generate Prometheus output
        from prometheus_client import generate_latest

        output = generate_latest().decode("utf-8")

        # Verify complete integration
        assert 'system_disk_io_read_bytes_total{device="sda"}' in output
        assert 'system_disk_io_write_bytes_total{device="sda"}' in output
