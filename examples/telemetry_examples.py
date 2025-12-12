#!/usr/bin/env python3
"""
Telemetry Examples

This file contains example usage of the telemetry sender script.
Run these examples to test different types of sensor data.
"""

import os
import sys
import time
import random
from datetime import datetime, timezone

# Add parent directory to path to import the sender
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from send_telemetry import TelemetrySender


def example_basic_sensors(api_key: str, base_url: str = "http://localhost:5000"):
    """Example: Basic sensor readings"""
    print("🌡️  Example 1: Basic Sensor Readings")
    
    sender = TelemetrySender(api_key, base_url)
    
    # Simulate sensor readings
    data = {
        "temperature": 23.5,
        "humidity": 65.2,
        "pressure": 1013.25
    }
    
    metadata = {
        "sensor_type": "DHT22",
        "location": "living_room",
        "firmware_version": "1.2.3"
    }
    
    success = sender.send_telemetry(data, metadata)
    return success


def example_iot_device(api_key: str, base_url: str = "http://localhost:5000"):
    """Example: IoT device with multiple measurements"""
    print("🏠 Example 2: Smart Home Device")
    
    sender = TelemetrySender(api_key, base_url)
    
    # Smart home device data
    data = {
        "temperature": 22.1,
        "humidity": 58.7,
        "light_level": 450,
        "motion_detected": False,
        "air_quality": 85,
        "noise_level": 35.2,
        "battery_level": 87
    }
    
    metadata = {
        "device_type": "smart_sensor",
        "room": "bedroom",
        "floor": 2,
        "building": "main_house"
    }
    
    success = sender.send_telemetry(data, metadata)
    return success


def example_industrial_sensor(api_key: str, base_url: str = "http://localhost:5000"):
    """Example: Industrial sensor with electrical measurements"""
    print("⚡ Example 3: Industrial Electrical Sensor")
    
    sender = TelemetrySender(api_key, base_url)
    
    # Industrial sensor data
    data = {
        "voltage": 230.5,
        "current": 12.3,
        "power": 2835.15,
        "frequency": 50.02,
        "power_factor": 0.95,
        "energy_consumed": 1250.75,
        "temperature": 45.2
    }
    
    metadata = {
        "equipment_id": "PUMP_001",
        "location": "factory_floor_A",
        "maintenance_due": "2024-03-15",
        "operator": "john_doe"
    }
    
    success = sender.send_telemetry(data, metadata)
    return success


def example_environmental_station(api_key: str, base_url: str = "http://localhost:5000"):
    """Example: Environmental monitoring station"""
    print("🌍 Example 4: Environmental Monitoring Station")
    
    sender = TelemetrySender(api_key, base_url)
    
    # Environmental data
    data = {
        "temperature": 18.7,
        "humidity": 72.3,
        "pressure": 1008.5,
        "wind_speed": 5.2,
        "wind_direction": 245,
        "rainfall": 0.0,
        "uv_index": 3,
        "co2": 415.2,
        "pm2_5": 12.5,
        "pm10": 18.3
    }
    
    metadata = {
        "station_id": "ENV_STATION_001",
        "coordinates": {"lat": 40.7128, "lon": -74.0060},
        "elevation": 10,
        "data_quality": "good"
    }
    
    success = sender.send_telemetry(data, metadata)
    return success


def example_continuous_monitoring(api_key: str, base_url: str = "http://localhost:5000", duration: int = 60):
    """Example: Continuous monitoring with random data"""
    print(f"📊 Example 5: Continuous Monitoring ({duration} seconds)")
    
    sender = TelemetrySender(api_key, base_url)
    
    start_time = time.time()
    count = 0
    success_count = 0
    
    while time.time() - start_time < duration:
        # Generate random sensor data
        data = {
            "temperature": round(20 + random.uniform(-5, 10), 2),
            "humidity": round(50 + random.uniform(-20, 30), 2),
            "pressure": round(1013 + random.uniform(-20, 20), 2),
            "light": round(random.uniform(0, 1000), 1),
            "battery": round(random.uniform(20, 100), 1)
        }
        
        metadata = {
            "sequence": count,
            "simulation": True
        }
        
        success = sender.send_telemetry(data, metadata)
        if success:
            success_count += 1
        
        count += 1
        time.sleep(5)  # Send every 5 seconds
    
    print(f"📈 Sent {success_count}/{count} messages successfully")
    return success_count == count


def example_batch_historical_data(api_key: str, base_url: str = "http://localhost:5000"):
    """Example: Send historical data with specific timestamps"""
    print("📅 Example 6: Historical Data with Timestamps")
    
    sender = TelemetrySender(api_key, base_url)
    
    # Send data for the last 24 hours (every hour)
    success_count = 0
    total_count = 24
    
    for i in range(total_count):
        # Calculate timestamp (i hours ago)
        timestamp = datetime.now(timezone.utc).replace(
            minute=0, second=0, microsecond=0
        ) - timedelta(hours=i)
        
        # Generate realistic temperature curve (cooler at night)
        hour = timestamp.hour
        base_temp = 20 + 5 * math.sin((hour - 6) * math.pi / 12)
        
        data = {
            "temperature": round(base_temp + random.uniform(-2, 2), 2),
            "humidity": round(60 + random.uniform(-15, 15), 2),
            "pressure": round(1013 + random.uniform(-10, 10), 2)
        }
        
        metadata = {
            "historical": True,
            "hour_offset": i
        }
        
        success = sender.send_telemetry(
            data, 
            metadata, 
            timestamp=timestamp.isoformat()
        )
        
        if success:
            success_count += 1
        
        time.sleep(0.5)  # Small delay between requests
    
    print(f"📊 Historical data: {success_count}/{total_count} records sent")
    return success_count == total_count


def main():
    """Run all examples"""
    import argparse
    
    parser = argparse.ArgumentParser(description="Run telemetry examples")
    parser.add_argument("api_key", help="Device API key")
    parser.add_argument("--url", default="http://localhost:5000", help="API base URL")
    parser.add_argument("--example", type=int, choices=range(1, 7), help="Run specific example (1-6)")
    parser.add_argument("--continuous-duration", type=int, default=60, help="Duration for continuous monitoring (seconds)")
    
    args = parser.parse_args()
    
    print(f"🚀 Running telemetry examples with API key: {args.api_key[:8]}...")
    print(f"🌐 Target URL: {args.url}")
    print()
    
    examples = [
        example_basic_sensors,
        example_iot_device,
        example_industrial_sensor,
        example_environmental_station,
        lambda api_key, base_url: example_continuous_monitoring(api_key, base_url, args.continuous_duration),
        example_batch_historical_data
    ]
    
    if args.example:
        # Run specific example
        example_func = examples[args.example - 1]
        success = example_func(args.api_key, args.url)
        print(f"\n{'✅' if success else '❌'} Example {args.example} {'completed successfully' if success else 'failed'}")
    else:
        # Run all examples
        success_count = 0
        for i, example_func in enumerate(examples, 1):
            try:
                if i == 5:  # Continuous monitoring
                    print(f"⏭️  Skipping continuous monitoring example (use --example 5 to run)")
                    continue
                if i == 6:  # Historical data
                    print(f"⏭️  Skipping historical data example (use --example 6 to run)")
                    continue
                    
                success = example_func(args.api_key, args.url)
                if success:
                    success_count += 1
                print(f"{'✅' if success else '❌'} Example {i} {'completed' if success else 'failed'}")
                print()
                time.sleep(2)  # Pause between examples
            except KeyboardInterrupt:
                print("\n⏹️  Examples interrupted by user")
                break
            except Exception as e:
                print(f"❌ Example {i} failed with error: {e}")
                print()
        
        print(f"📊 Summary: {success_count} examples completed successfully")


if __name__ == "__main__":
    import math
    from datetime import timedelta
    main()