#!/usr/bin/env python3
"""
Timestamp Formatter Test
Demonstrates the timestamp parsing and formatting capabilities
"""

import sys
import os
sys.path.append('src')

from datetime import datetime, timezone
from utils.time_util import TimestampFormatter, parse_device_timestamp, format_timestamp_for_display

def test_timestamp_parsing():
    """Test parsing various timestamp formats from devices"""
    print("🕐 Testing Timestamp Parsing and Formatting")
    print("=" * 50)
    
    # Test cases: various timestamp formats devices might send
    test_timestamps = [
        # ISO formats
        "2025-08-07T14:30:15.123Z",
        "2025-08-07T14:30:15Z", 
        "2025-08-07T14:30:15",
        "2025-08-07 14:30:15",
        
        # Epoch timestamps
        1723034415,        # seconds
        1723034415123,     # milliseconds
        "1723034415",      # string seconds
        "1723034415123",   # string milliseconds
        
        # Other formats
        "08/07/2025 14:30:15",  # US format
        "07/08/2025 14:30:15",  # European format
        
        # Invalid formats
        "invalid-timestamp",
        None,
        "",
    ]
    
    print("Input Format → Parsed Result → Display Format")
    print("-" * 50)
    
    for test_input in test_timestamps:
        try:
            # Parse the timestamp
            parsed = parse_device_timestamp(test_input)
            
            if parsed:
                # Format for display
                readable = format_timestamp_for_display(parsed, 'readable')
                iso = format_timestamp_for_display(parsed, 'iso')
                short = format_timestamp_for_display(parsed, 'short')
                
                print(f"✅ {str(test_input)[:20]:<20} → {readable}")
                print(f"   ISO: {iso}")
                print(f"   Short: {short}")
            else:
                print(f"❌ {str(test_input)[:20]:<20} → Failed to parse")
            
            print()
            
        except Exception as e:
            print(f"❌ {str(test_input)[:20]:<20} → Error: {e}")
            print()

def test_environment_config():
    """Test environment-based configuration"""
    print("\n🔧 Testing Environment Configuration")
    print("=" * 50)
    
    # Test with current environment settings
    current_format = TimestampFormatter.get_display_format()
    current_tz = TimestampFormatter.get_timezone()
    
    print(f"Current TIMESTAMP_FORMAT: {current_format}")
    print(f"Current TIMESTAMP_TIMEZONE: {current_tz}")
    
    # Test with a sample timestamp
    sample_time = datetime.now(timezone.utc)
    
    print(f"\nSample timestamp formatting:")
    print(f"Current config: {format_timestamp_for_display(sample_time)}")
    print(f"ISO format: {format_timestamp_for_display(sample_time, 'iso')}")
    print(f"Readable format: {format_timestamp_for_display(sample_time, 'readable')}")
    print(f"Short format: {format_timestamp_for_display(sample_time, 'short')}")
    print(f"Compact format: {format_timestamp_for_display(sample_time, 'compact')}")

if __name__ == "__main__":
    test_timestamp_parsing()
    test_environment_config()
    
    print("\n✨ Timestamp formatter test completed!")
    print("\nTo configure timestamp formatting, set these environment variables:")
    print("  TIMESTAMP_FORMAT=readable|iso|short|compact")
    print("  TIMESTAMP_TIMEZONE=UTC|EST|PST|etc")
