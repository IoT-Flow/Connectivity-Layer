#!/usr/bin/env python3
"""
Configuration file for MQTT Device Simulator
Defines device types, sensor configurations, and default settings
"""

import json
from typing import Dict, Any, List
from dataclasses import dataclass, asdict


@dataclass
class SensorConfig:
    """Configuration for a sensor"""

    min_value: float
    max_value: float
    unit: str
    precision: int = 2
    noise_factor: float = 0.05  # 5% noise by default


@dataclass
class DeviceTypeConfig:
    """Configuration for a device type"""

    name: str
    description: str
    sensors: Dict[str, SensorConfig]
    default_telemetry_interval: int = 30  # seconds
    default_heartbeat_interval: int = 60  # seconds


# Predefined device type configurations
DEVICE_TYPES = {
    "environmental": DeviceTypeConfig(
        name="environmental",
        description="Environmental monitoring device",
        sensors={
            "temperature": SensorConfig(-10.0, 50.0, "°C"),
            "humidity": SensorConfig(0.0, 100.0, "%"),
            "pressure": SensorConfig(950.0, 1050.0, "hPa"),
            "light": SensorConfig(0, 100000, "lux", precision=0),
            "air_quality": SensorConfig(0, 500, "AQI", precision=0),
        },
        default_telemetry_interval=30,
        default_heartbeat_interval=60,
    ),
    "industrial": DeviceTypeConfig(
        name="industrial",
        description="Industrial monitoring device",
        sensors={
            "temperature": SensorConfig(0.0, 300.0, "°C"),
            "vibration": SensorConfig(0.0, 10.0, "mm/s"),
            "pressure": SensorConfig(500.0, 3000.0, "hPa"),
            "current": SensorConfig(0.0, 50.0, "A"),
            "voltage": SensorConfig(100.0, 500.0, "V"),
            "rpm": SensorConfig(0, 10000, "RPM", precision=0),
        },
        default_telemetry_interval=15,
        default_heartbeat_interval=30,
    ),
    "agricultural": DeviceTypeConfig(
        name="agricultural",
        description="Agricultural monitoring device",
        sensors={
            "soil_temperature": SensorConfig(5.0, 40.0, "°C"),
            "soil_moisture": SensorConfig(0.0, 100.0, "%"),
            "soil_ph": SensorConfig(3.0, 10.0, "pH"),
            "light_intensity": SensorConfig(0, 100000, "lux", precision=0),
            "ambient_temperature": SensorConfig(-5.0, 45.0, "°C"),
            "ambient_humidity": SensorConfig(0.0, 100.0, "%"),
        },
        default_telemetry_interval=60,
        default_heartbeat_interval=120,
    ),
    "energy": DeviceTypeConfig(
        name="energy",
        description="Energy monitoring device",
        sensors={
            "voltage": SensorConfig(200.0, 250.0, "V"),
            "current": SensorConfig(0.0, 20.0, "A"),
            "power": SensorConfig(0.0, 5000.0, "W"),
            "energy": SensorConfig(0.0, 999999.0, "kWh"),
            "frequency": SensorConfig(49.0, 51.0, "Hz"),
            "power_factor": SensorConfig(0.1, 1.0, "PF"),
        },
        default_telemetry_interval=20,
        default_heartbeat_interval=60,
    ),
    "automotive": DeviceTypeConfig(
        name="automotive",
        description="Automotive monitoring device",
        sensors={
            "engine_temperature": SensorConfig(70.0, 110.0, "°C"),
            "rpm": SensorConfig(500, 8000, "RPM", precision=0),
            "speed": SensorConfig(0, 200, "km/h", precision=0),
            "fuel_level": SensorConfig(0.0, 100.0, "%"),
            "battery_voltage": SensorConfig(11.0, 14.5, "V"),
            "oil_pressure": SensorConfig(0.5, 8.0, "bar"),
        },
        default_telemetry_interval=10,
        default_heartbeat_interval=30,
    ),
    "smart_home": DeviceTypeConfig(
        name="smart_home",
        description="Smart home monitoring device",
        sensors={
            "indoor_temperature": SensorConfig(16.0, 30.0, "°C"),
            "indoor_humidity": SensorConfig(30.0, 80.0, "%"),
            "motion_detected": SensorConfig(0, 1, "bool", precision=0, noise_factor=0),
            "light_level": SensorConfig(0, 1000, "lux", precision=0),
            "sound_level": SensorConfig(30.0, 100.0, "dB"),
            "door_open": SensorConfig(0, 1, "bool", precision=0, noise_factor=0),
        },
        default_telemetry_interval=45,
        default_heartbeat_interval=90,
    ),
}


# Default simulation settings
DEFAULT_SETTINGS = {
    "api_base_url": "http://localhost:5000/api/v1",
    "mqtt_host": "localhost",
    "mqtt_port": 1883,
    "user_id": "default_user_123",
    "max_devices": 50,
    "log_level": "INFO",
    "startup_delay": 2.0,  # seconds between device startups
    "reconnect_delay": 5.0,  # seconds to wait before reconnecting
    "max_reconnect_attempts": 5,
}


# Sample device configurations
SAMPLE_DEVICES = [
    {
        "name": "Office Environment Monitor",
        "device_type": "environmental",
        "location": "Office Building A, Floor 3, Room 301",
        "telemetry_interval": 30,
        "heartbeat_interval": 60,
    },
    {
        "name": "Factory Machine Monitor",
        "device_type": "industrial",
        "location": "Manufacturing Plant, Line 2, Station 5",
        "telemetry_interval": 15,
        "heartbeat_interval": 30,
    },
    {
        "name": "Greenhouse Sensor Array",
        "device_type": "agricultural",
        "location": "Greenhouse Complex, Section B",
        "telemetry_interval": 120,
        "heartbeat_interval": 300,
    },
    {
        "name": "Home Energy Monitor",
        "device_type": "energy",
        "location": "Residential Home, Main Panel",
        "telemetry_interval": 30,
        "heartbeat_interval": 60,
    },
    {
        "name": "Vehicle Diagnostics Unit",
        "device_type": "automotive",
        "location": "Fleet Vehicle ID: VH-2024-001",
        "telemetry_interval": 10,
        "heartbeat_interval": 30,
    },
    {
        "name": "Smart Home Hub",
        "device_type": "smart_home",
        "location": "Living Room, Central Unit",
        "telemetry_interval": 60,
        "heartbeat_interval": 120,
    },
]


def get_device_type_config(device_type: str) -> DeviceTypeConfig:
    """Get configuration for a device type"""
    return DEVICE_TYPES.get(device_type, DEVICE_TYPES["environmental"])


def get_available_device_types() -> List[str]:
    """Get list of available device types"""
    return list(DEVICE_TYPES.keys())


def get_sample_device_config(index: int = 0) -> Dict[str, Any]:
    """Get a sample device configuration"""
    if 0 <= index < len(SAMPLE_DEVICES):
        return SAMPLE_DEVICES[index].copy()
    return SAMPLE_DEVICES[0].copy()


def save_config_to_file(config: Dict[str, Any], filename: str):
    """Save configuration to JSON file"""
    with open(filename, "w") as f:
        json.dump(config, f, indent=2, default=str)


def load_config_from_file(filename: str) -> Dict[str, Any]:
    """Load configuration from JSON file"""
    with open(filename, "r") as f:
        return json.load(f)


def create_custom_device_config(
    name: str,
    device_type: str,
    location: str,
    telemetry_interval: int = None,
    heartbeat_interval: int = None,
) -> Dict[str, Any]:
    """Create a custom device configuration"""
    type_config = get_device_type_config(device_type)

    return {
        "name": name,
        "device_type": device_type,
        "location": location,
        "telemetry_interval": telemetry_interval
        or type_config.default_telemetry_interval,
        "heartbeat_interval": heartbeat_interval
        or type_config.default_heartbeat_interval,
    }


if __name__ == "__main__":
    # Example usage: print available device types and their sensors
    print("Available Device Types:")
    print("=" * 50)

    for device_type, config in DEVICE_TYPES.items():
        print(f"\n{device_type.upper()}: {config.description}")
        print(
            f"  Default intervals: Telemetry={config.default_telemetry_interval}s, Heartbeat={config.default_heartbeat_interval}s"
        )
        print("  Sensors:")
        for sensor_name, sensor_config in config.sensors.items():
            print(
                f"    - {sensor_name}: {sensor_config.min_value}-{sensor_config.max_value} {sensor_config.unit}"
            )

    print(
        f"\nSample Devices: {len(SAMPLE_DEVICES)} predefined configurations available"
    )
