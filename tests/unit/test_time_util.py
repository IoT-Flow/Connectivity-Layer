"""
Unit tests for Time Utility Functions
Tests timestamp parsing and formatting
"""

import pytest
from datetime import datetime, timezone, timedelta
from unittest.mock import patch

from src.utils.time_util import (
    TimestampFormatter,
    parse_device_timestamp,
    format_timestamp_for_storage,
    format_timestamp_for_display,
    get_current_timestamp,
)


class TestTimestampFormatter:
    """Test timestamp formatter class"""

    def test_parse_iso_timestamp_with_z(self):
        """Test parsing ISO timestamp with Z suffix"""
        timestamp_str = "2024-01-15T10:30:45Z"
        result = TimestampFormatter.parse_device_timestamp(timestamp_str)

        assert result is not None
        assert result.year == 2024
        assert result.month == 1
        assert result.day == 15
        assert result.hour == 10
        assert result.minute == 30
        assert result.second == 45
        assert result.tzinfo == timezone.utc

    def test_parse_iso_timestamp_with_microseconds(self):
        """Test parsing ISO timestamp with microseconds"""
        timestamp_str = "2024-01-15T10:30:45.123456Z"
        result = TimestampFormatter.parse_device_timestamp(timestamp_str)

        assert result is not None
        assert result.microsecond == 123456

    def test_parse_iso_timestamp_basic(self):
        """Test parsing basic ISO timestamp"""
        timestamp_str = "2024-01-15T10:30:45"
        result = TimestampFormatter.parse_device_timestamp(timestamp_str)

        assert result is not None
        assert result.year == 2024

    def test_parse_space_separated_timestamp(self):
        """Test parsing space-separated timestamp"""
        timestamp_str = "2024-01-15 10:30:45"
        result = TimestampFormatter.parse_device_timestamp(timestamp_str)

        assert result is not None
        assert result.year == 2024
        assert result.hour == 10

    def test_parse_us_format_timestamp(self):
        """Test parsing US format timestamp"""
        timestamp_str = "01/15/2024 10:30:45"
        result = TimestampFormatter.parse_device_timestamp(timestamp_str)

        assert result is not None
        assert result.month == 1
        assert result.day == 15
        assert result.year == 2024

    def test_parse_epoch_seconds(self):
        """Test parsing epoch timestamp in seconds"""
        epoch = 1705318245  # 2024-01-15 10:30:45 UTC
        result = TimestampFormatter.parse_device_timestamp(epoch)

        assert result is not None
        assert result.year == 2024
        assert result.month == 1

    def test_parse_epoch_milliseconds(self):
        """Test parsing epoch timestamp in milliseconds"""
        epoch_ms = 1705318245000  # 2024-01-15 10:30:45 UTC in milliseconds
        result = TimestampFormatter.parse_device_timestamp(epoch_ms)

        assert result is not None
        assert result.year == 2024

    def test_parse_epoch_as_string(self):
        """Test parsing epoch timestamp as string"""
        epoch_str = "1705318245"
        result = TimestampFormatter.parse_device_timestamp(epoch_str)

        assert result is not None
        assert result.year == 2024

    def test_parse_none_timestamp(self):
        """Test parsing None timestamp"""
        result = TimestampFormatter.parse_device_timestamp(None)

        assert result is None

    def test_parse_invalid_timestamp(self):
        """Test parsing invalid timestamp"""
        result = TimestampFormatter.parse_device_timestamp("invalid-timestamp")

        assert result is None

    def test_parse_malformed_double_timezone(self):
        """Test parsing timestamp with double timezone indicator"""
        timestamp_str = "2025-08-07T17:32:25.246962+00:00Z"
        result = TimestampFormatter.parse_device_timestamp(timestamp_str)

        assert result is not None
        assert result.year == 2025

    def test_format_for_storage(self):
        """Test formatting datetime for storage"""
        dt = datetime(2024, 1, 15, 10, 30, 45, tzinfo=timezone.utc)
        result = TimestampFormatter.format_for_storage(dt)

        assert "2024-01-15" in result
        assert "10:30:45" in result

    def test_format_for_storage_naive_datetime(self):
        """Test formatting naive datetime for storage"""
        dt = datetime(2024, 1, 15, 10, 30, 45)  # No timezone
        result = TimestampFormatter.format_for_storage(dt)

        assert "2024-01-15" in result

    @patch.dict("os.environ", {"TIMESTAMP_FORMAT": "iso"})
    def test_format_for_display_iso(self):
        """Test formatting datetime for display in ISO format"""
        dt = datetime(2024, 1, 15, 10, 30, 45, tzinfo=timezone.utc)
        result = TimestampFormatter.format_for_display(dt, "iso")

        assert "2024-01-15" in result
        assert "T" in result

    @patch.dict("os.environ", {"TIMESTAMP_FORMAT": "readable", "TIMESTAMP_TIMEZONE": "UTC"})
    def test_format_for_display_readable(self):
        """Test formatting datetime for display in readable format"""
        dt = datetime(2024, 1, 15, 10, 30, 45, tzinfo=timezone.utc)
        result = TimestampFormatter.format_for_display(dt, "readable")

        assert "2024-01-15" in result
        assert "10:30:45" in result
        assert "UTC" in result

    def test_format_for_display_short(self):
        """Test formatting datetime for display in short format"""
        dt = datetime(2024, 1, 15, 10, 30, 45, tzinfo=timezone.utc)
        result = TimestampFormatter.format_for_display(dt, "short")

        assert "01/15" in result
        assert "10:30:45" in result

    def test_format_for_display_compact(self):
        """Test formatting datetime for display in compact format"""
        dt = datetime(2024, 1, 15, 10, 30, 45, tzinfo=timezone.utc)
        result = TimestampFormatter.format_for_display(dt, "compact")

        assert "20240115" in result
        assert "103045" in result

    def test_get_current_utc(self):
        """Test getting current UTC timestamp"""
        result = TimestampFormatter.get_current_utc()

        assert result is not None
        assert isinstance(result, datetime)
        assert result.tzinfo == timezone.utc

    def test_ensure_utc_with_timezone(self):
        """Test ensuring datetime is in UTC when it has timezone"""
        dt = datetime(2024, 1, 15, 10, 30, 45, tzinfo=timezone.utc)
        result = TimestampFormatter.ensure_utc(dt)

        assert result.tzinfo == timezone.utc

    def test_ensure_utc_naive_datetime(self):
        """Test ensuring naive datetime is in UTC"""
        dt = datetime(2024, 1, 15, 10, 30, 45)
        result = TimestampFormatter.ensure_utc(dt)

        assert result.tzinfo == timezone.utc

    @patch.dict("os.environ", {"TIMESTAMP_FORMAT": "readable"})
    def test_get_display_format(self):
        """Test getting display format from environment"""
        result = TimestampFormatter.get_display_format()

        assert result == "readable"

    @patch.dict("os.environ", {"TIMESTAMP_TIMEZONE": "EST"})
    def test_get_timezone(self):
        """Test getting timezone from environment"""
        result = TimestampFormatter.get_timezone()

        assert result == "EST"


class TestConvenienceFunctions:
    """Test convenience wrapper functions"""

    def test_parse_device_timestamp_function(self):
        """Test parse_device_timestamp convenience function"""
        timestamp_str = "2024-01-15T10:30:45Z"
        result = parse_device_timestamp(timestamp_str)

        assert result is not None
        assert result.year == 2024

    def test_format_timestamp_for_storage_function(self):
        """Test format_timestamp_for_storage convenience function"""
        dt = datetime(2024, 1, 15, 10, 30, 45, tzinfo=timezone.utc)
        result = format_timestamp_for_storage(dt)

        assert "2024-01-15" in result

    def test_format_timestamp_for_display_function(self):
        """Test format_timestamp_for_display convenience function"""
        dt = datetime(2024, 1, 15, 10, 30, 45, tzinfo=timezone.utc)
        result = format_timestamp_for_display(dt, "iso")

        assert "2024-01-15" in result

    def test_get_current_timestamp_function(self):
        """Test get_current_timestamp convenience function"""
        result = get_current_timestamp()

        assert result is not None
        assert isinstance(result, datetime)
        assert result.tzinfo == timezone.utc


class TestEdgeCases:
    """Test edge cases and error handling"""

    def test_parse_empty_string(self):
        """Test parsing empty string"""
        result = TimestampFormatter.parse_device_timestamp("")

        assert result is None

    def test_parse_whitespace_string(self):
        """Test parsing whitespace string"""
        result = TimestampFormatter.parse_device_timestamp("   ")

        assert result is None

    def test_parse_very_old_epoch(self):
        """Test parsing very old epoch timestamp"""
        epoch = 0  # 1970-01-01
        result = TimestampFormatter.parse_device_timestamp(epoch)

        assert result is not None
        assert result.year == 1970

    def test_parse_future_timestamp(self):
        """Test parsing future timestamp"""
        future_dt = datetime.now(timezone.utc) + timedelta(days=365)
        timestamp_str = future_dt.isoformat()
        result = TimestampFormatter.parse_device_timestamp(timestamp_str)

        assert result is not None
        assert result > datetime.now(timezone.utc)

    def test_parse_float_epoch(self):
        """Test parsing float epoch timestamp"""
        epoch = 1705318245.123
        result = TimestampFormatter.parse_device_timestamp(epoch)

        assert result is not None
        assert result.year == 2024

    def test_format_datetime_with_different_timezone(self):
        """Test formatting datetime with non-UTC timezone"""
        # Create datetime in a different timezone
        from datetime import timedelta

        other_tz = timezone(timedelta(hours=5))
        dt = datetime(2024, 1, 15, 10, 30, 45, tzinfo=other_tz)

        result = TimestampFormatter.format_for_storage(dt)

        # Should be converted to UTC
        assert result is not None
