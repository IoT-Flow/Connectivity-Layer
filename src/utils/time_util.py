"""
Time Utility Functions for IoTFlow
Provides standardized timestamp parsing and formatting for device data
"""

import logging
import os
from datetime import datetime, timezone
from typing import Union, Optional

logger = logging.getLogger(__name__)


class TimestampFormatter:
    """Handles parsing and formatting of timestamps from IoT devices"""

    # Common timestamp formats from devices
    SUPPORTED_FORMATS = [
        "%Y-%m-%dT%H:%M:%S.%fZ",  # ISO 8601 with microseconds and Z
        "%Y-%m-%dT%H:%M:%SZ",  # ISO 8601 with Z
        "%Y-%m-%dT%H:%M:%S.%f",  # ISO 8601 with microseconds
        "%Y-%m-%dT%H:%M:%S",  # ISO 8601 basic
        "%Y-%m-%d %H:%M:%S.%f",  # Space-separated with microseconds
        "%Y-%m-%d %H:%M:%S",  # Space-separated basic
        "%m/%d/%Y %H:%M:%S",  # US format
        "%d/%m/%Y %H:%M:%S",  # European format
    ]

    @staticmethod
    def get_display_format() -> str:
        """Get timestamp display format from environment"""
        format_type = os.environ.get("TIMESTAMP_FORMAT", "readable").lower()
        return format_type

    @staticmethod
    def get_timezone() -> str:
        """Get timezone setting from environment"""
        return os.environ.get("TIMESTAMP_TIMEZONE", "UTC")

    @staticmethod
    def parse_device_timestamp(
        timestamp_input: Union[str, int, float, None],
    ) -> Optional[datetime]:
        """
        Parse various timestamp formats from IoT devices

        Args:
            timestamp_input: Timestamp from device (string, epoch seconds/ms, or None)

        Returns:
            datetime object in UTC timezone, or None if parsing fails
        """
        if timestamp_input is None:
            return None

        try:
            # Handle numeric timestamps (epoch)
            if isinstance(timestamp_input, (int, float)):
                return TimestampFormatter._parse_epoch_timestamp(float(timestamp_input))

            # Handle string timestamps
            if isinstance(timestamp_input, str):
                timestamp_str = timestamp_input.strip()

                # Try to parse as number first (string representation of epoch)
                if timestamp_str.replace(".", "").isdigit():
                    return TimestampFormatter._parse_epoch_timestamp(
                        float(timestamp_str)
                    )

                # Try ISO format parsing (handles timezone info)
                return TimestampFormatter._parse_iso_timestamp(timestamp_str)

        except Exception as e:
            logger.warning(f"Failed to parse timestamp '{timestamp_input}': {e}")

        return None

    @staticmethod
    def _parse_epoch_timestamp(epoch_value: float) -> datetime:
        """Parse epoch timestamp (seconds or milliseconds)"""
        # Determine if timestamp is in seconds or milliseconds
        if epoch_value < 1e10:  # Less than 10 billion = seconds
            return datetime.fromtimestamp(epoch_value, tz=timezone.utc)
        else:  # Assume milliseconds
            return datetime.fromtimestamp(epoch_value / 1000, tz=timezone.utc)

    @staticmethod
    def _parse_iso_timestamp(timestamp_str: str) -> datetime:
        """Parse ISO format timestamp string"""
        # Clean up common malformed timestamp issues
        # Fix double timezone indicators (e.g., "2025-08-07T17:32:25.246962+00:00Z")
        if "+00:00Z" in timestamp_str:
            timestamp_str = timestamp_str.replace("+00:00Z", "Z")
        elif "+00:00z" in timestamp_str.lower():
            timestamp_str = timestamp_str.replace("+00:00z", "Z").replace(
                "+00:00Z", "Z"
            )

        # Handle timezone suffix
        if timestamp_str.endswith("Z"):
            timestamp_str = timestamp_str[:-1] + "+00:00"

        # Try fromisoformat first (Python 3.7+)
        try:
            dt = datetime.fromisoformat(timestamp_str)
            # Ensure timezone is set
            if dt.tzinfo is None:
                dt = dt.replace(tzinfo=timezone.utc)
            return dt.astimezone(timezone.utc)
        except ValueError:
            pass

        # Fallback to manual format parsing
        for fmt in TimestampFormatter.SUPPORTED_FORMATS:
            try:
                dt = datetime.strptime(timestamp_str, fmt)
                return dt.replace(tzinfo=timezone.utc)
            except ValueError:
                continue

        raise ValueError(f"Unsupported timestamp format: {timestamp_str}")

    @staticmethod
    def format_for_storage(dt: datetime) -> str:
        """
        Format datetime for consistent storage

        Args:
            dt: datetime object

        Returns:
            ISO format string in UTC timezone
        """
        if dt.tzinfo is None:
            dt = dt.replace(tzinfo=timezone.utc)

        return dt.astimezone(timezone.utc).isoformat()

    @staticmethod
    def format_for_display(dt: datetime, format_type: Optional[str] = None) -> str:
        """
        Format datetime for display purposes

        Args:
            dt: datetime object
            format_type: 'iso', 'readable', 'short', or None (uses env config)

        Returns:
            Formatted timestamp string
        """
        if dt.tzinfo is None:
            dt = dt.replace(tzinfo=timezone.utc)

        utc_dt = dt.astimezone(timezone.utc)

        # Use environment config if format_type not specified
        if format_type is None:
            format_type = TimestampFormatter.get_display_format()

        if format_type == "iso":
            return utc_dt.isoformat()
        elif format_type == "readable":
            tz_name = TimestampFormatter.get_timezone()
            return utc_dt.strftime(f"%Y-%m-%d %H:%M:%S {tz_name}")
        elif format_type == "short":
            return utc_dt.strftime("%m/%d %H:%M:%S")
        elif format_type == "compact":
            return utc_dt.strftime("%Y%m%d_%H%M%S")
        else:
            return utc_dt.isoformat()

    @staticmethod
    def get_current_utc() -> datetime:
        """Get current UTC timestamp"""
        return datetime.now(timezone.utc)

    @staticmethod
    def ensure_utc(dt: datetime) -> datetime:
        """Ensure datetime is in UTC timezone"""
        if dt.tzinfo is None:
            return dt.replace(tzinfo=timezone.utc)
        return dt.astimezone(timezone.utc)


# Convenience functions for common operations
def parse_device_timestamp(
    timestamp_input: Union[str, int, float, None],
) -> Optional[datetime]:
    """Parse timestamp from device - convenience function"""
    return TimestampFormatter.parse_device_timestamp(timestamp_input)


def format_timestamp_for_storage(dt: datetime) -> str:
    """Format timestamp for storage - convenience function"""
    return TimestampFormatter.format_for_storage(dt)


def format_timestamp_for_display(
    dt: datetime, format_type: Optional[str] = None
) -> str:
    """Format timestamp for display - convenience function"""
    return TimestampFormatter.format_for_display(dt, format_type)


def get_current_timestamp() -> datetime:
    """Get current UTC timestamp - convenience function"""
    return TimestampFormatter.get_current_utc()
