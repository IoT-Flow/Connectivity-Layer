#!/usr/bin/env python3
"""
MQTT Device Simulator for IoTFlow
Simulates IoT devices sending telemetry data via MQTT protocol

Features:
- Multiple device simulation
- Various sensor types (temperature, humidity, pressure, etc.)
- Configurable send intervals
- MQTT connection with retry logic
- Device registration via API
- Real-time telemetry generation
- Status reporting (online/offline/heartbeat)
- Configurable timestamp formats
"""

import json
import time
import random
import logging
import argparse
import signal
import sys
import math
import os
from datetime import datetime, timezone
from typing import Dict, List, Optional, Any
from dataclasses import dataclass
import requests

# Import MQTT library with fallback
try:
    import paho.mqtt.client as mqtt

    MQTT_AVAILABLE = True
except ImportError:
    print("Warning: paho-mqtt not installed. Install with: pip install paho-mqtt")
    MQTT_AVAILABLE = False

from concurrent.futures import ThreadPoolExecutor

# Import timestamp utilities
try:
    sys.path.append("../src")  # Add src to path for imports
    # Note: TimestampFormatter and format_timestamp_for_storage are not used
    # Using local timestamp functions instead
    TIMESTAMP_UTIL_AVAILABLE = True
except ImportError:
    print("Warning: Timestamp utility not available. Using basic timestamps.")
    TIMESTAMP_UTIL_AVAILABLE = False

# Import local configuration
try:
    from simulator_config import (
        DEVICE_TYPES,
        DEFAULT_SETTINGS,
        SAMPLE_DEVICES,
    )
except ImportError:
    # Fallback if config file not available
    DEVICE_TYPES = {}
    DEFAULT_SETTINGS = {
        "api_base_url": "http://localhost:5000/api/v1",
        "mqtt_host": "localhost",
        "mqtt_port": 1883,
        "user_id": "default_user_123",
    }
    SAMPLE_DEVICES = []


# Configure logging
logging.basicConfig(
    level=logging.INFO, format="%(asctime)s - %(name)s - %(levelname)s - %(message)s"
)
logger = logging.getLogger(__name__)


# Device name generation utilities
def generate_random_device_name(device_type: str = "generic") -> str:
    """
    Generate a random device name based on device type

    Args:
        device_type: Type of device to generate name for

    Returns:
        Random device name string
    """
    # Device type specific prefixes and suffixes
    device_name_templates = {
        "environmental": {
            "prefixes": [
                "Environment",
                "Climate",
                "Weather",
                "Temp",
                "Humidity",
                "Air",
            ],
            "suffixes": ["Monitor", "Sensor", "Station", "Probe", "Detector", "Meter"],
        },
        "industrial": {
            "prefixes": [
                "Industrial",
                "Factory",
                "Machine",
                "Motor",
                "Pump",
                "Conveyor",
            ],
            "suffixes": ["Monitor", "Controller", "Sensor", "Unit", "System", "Device"],
        },
        "energy": {
            "prefixes": ["Energy", "Power", "Electric", "Smart", "Grid", "Voltage"],
            "suffixes": ["Meter", "Monitor", "Sensor", "Controller", "Gateway", "Hub"],
        },
        "agricultural": {
            "prefixes": ["Farm", "Crop", "Soil", "Irrigation", "Greenhouse", "Field"],
            "suffixes": ["Monitor", "Sensor", "Controller", "Station", "System", "Hub"],
        },
        "automotive": {
            "prefixes": ["Vehicle", "Car", "Engine", "Fleet", "GPS", "OBD"],
            "suffixes": ["Tracker", "Monitor", "Sensor", "Unit", "Device", "System"],
        },
        "smart_home": {
            "prefixes": [
                "Smart",
                "Home",
                "Living Room",
                "Kitchen",
                "Bedroom",
                "Garage",
            ],
            "suffixes": [
                "Hub",
                "Controller",
                "Sensor",
                "Monitor",
                "Device",
                "Assistant",
            ],
        },
    }

    # Fallback for unknown device types
    default_template = {
        "prefixes": ["IoT", "Smart", "Connected", "Wireless", "Remote", "Digital"],
        "suffixes": ["Device", "Sensor", "Monitor", "Controller", "Unit", "Hub"],
    }

    template = device_name_templates.get(device_type, default_template)

    # Generate random components
    prefix = random.choice(template["prefixes"])
    suffix = random.choice(template["suffixes"])

    # Add random number/identifier
    identifier_options = [
        f"{random.randint(1, 999)}",
        f"Unit-{random.randint(10, 99)}",
        f"#{random.randint(100, 999)}",
        f"{chr(65 + random.randint(0, 25))}{random.randint(1, 99)}",  # Like A23, B45
        f"Zone-{random.randint(1, 20)}",
    ]

    identifier = random.choice(identifier_options)

    # Combine components
    name_formats = [
        f"{prefix} {suffix} {identifier}",
        f"{prefix}-{suffix}-{identifier}",
        f"{prefix} {suffix} ({identifier})",
        f"{identifier} {prefix} {suffix}",
        f"{suffix} {identifier} - {prefix}",
    ]

    return random.choice(name_formats)


def generate_random_location(device_type: str = "generic") -> str:
    """
    Generate a random location based on device type

    Args:
        device_type: Type of device to generate location for

    Returns:
        Random location string
    """
    location_templates = {
        "environmental": [
            "Office Building {}, Floor {}",
            "Warehouse {}, Zone {}",
            "Laboratory {}, Room {}",
            "Data Center {}, Rack {}",
            "Campus Building {}, Wing {}",
        ],
        "industrial": [
            "Factory Floor {}, Line {}",
            "Production Area {}, Station {}",
            "Manufacturing Plant {}, Unit {}",
            "Assembly Line {}, Position {}",
            "Industrial Complex {}, Building {}",
        ],
        "energy": [
            "Electrical Panel {}, Circuit {}",
            "Power Station {}, Unit {}",
            "Substation {}, Bay {}",
            "Distribution Center {}, Zone {}",
            "Grid Station {}, Section {}",
        ],
        "agricultural": [
            "Greenhouse {}, Section {}",
            "Field {}, Zone {}",
            "Barn {}, Area {}",
            "Farm Sector {}, Plot {}",
            "Irrigation Zone {}, Block {}",
        ],
        "automotive": [
            "Vehicle Fleet {}, Unit {}",
            "Parking Garage {}, Level {}",
            "Service Bay {}, Station {}",
            "Transport Hub {}, Dock {}",
            "Maintenance Area {}, Bay {}",
        ],
        "smart_home": [
            "Residential Unit {}, Room {}",
            "Apartment {}, {} Area",
            "House {}, {} Zone",
            "Smart Home {}, {} Section",
            "Living Space {}, {} Corner",
        ],
    }

    # Room/area names for smart home
    home_areas = [
        "Living Room",
        "Kitchen",
        "Bedroom",
        "Bathroom",
        "Garage",
        "Basement",
        "Attic",
    ]

    templates = location_templates.get(device_type, location_templates["environmental"])
    template = random.choice(templates)

    # Generate location components
    if device_type == "smart_home" and "{}" in template:
        # Special handling for smart home locations
        building_num = random.randint(101, 999)
        area = random.choice(home_areas)
        return template.format(building_num, area)
    else:
        # Standard two-component locations
        component1 = random.choice(
            ["A", "B", "C", "1", "2", "3", "North", "South", "Main"]
        )
        component2 = random.randint(1, 20)
        return template.format(component1, component2)


# Timestamp utility functions for simulator
def get_simulator_timestamp(format_type: str = "auto") -> str:
    """
    Get timestamp for simulator data with configurable format
    Simulates various timestamp formats that real devices might send

    Args:
        format_type: 'auto', 'iso', 'epoch', 'epoch_ms', 'readable', 'compact', 'us_format', 'european'

    Returns:
        Formatted timestamp string (as devices would send)
    """
    now = datetime.now(timezone.utc)

    # Use environment setting if auto
    if format_type == "auto":
        format_type = os.environ.get("SIMULATOR_TIMESTAMP_FORMAT", "random").lower()

    # If random, pick a random format to simulate diverse devices
    if format_type == "random":
        formats = [
            "iso",
            "epoch",
            "epoch_ms",
            "readable",
            "us_format",
            "european",
            "iso_no_z",
            "iso_simple",
            "epoch_float",
        ]
        format_type = random.choice(formats)

    # Generate timestamp in various formats (as real devices would send)
    if format_type == "iso":
        # Proper ISO format with Z suffix (UTC)
        return now.strftime("%Y-%m-%dT%H:%M:%S.%fZ")
    elif format_type == "iso_no_z":
        # ISO format without timezone indicator
        return now.strftime("%Y-%m-%dT%H:%M:%S.%f")
    elif format_type == "iso_simple":
        # Simple ISO format without microseconds
        return now.strftime("%Y-%m-%dT%H:%M:%SZ")
    elif format_type == "epoch":
        return str(int(now.timestamp()))
    elif format_type == "epoch_ms":
        return str(int(now.timestamp() * 1000))
    elif format_type == "epoch_float":
        # Some devices send epoch as float with decimal
        return f"{now.timestamp():.3f}"
    elif format_type == "readable":
        return now.strftime("%Y-%m-%d %H:%M:%S")
    elif format_type == "compact":
        return now.strftime("%Y%m%d_%H%M%S")
    elif format_type == "us_format":
        return now.strftime("%m/%d/%Y %H:%M:%S")
    elif format_type == "european":
        return now.strftime("%d/%m/%Y %H:%M:%S")
    else:
        return now.strftime("%Y-%m-%dT%H:%M:%S.%fZ")


def get_device_specific_timestamp(device_type: str) -> str:
    """
    Get timestamp in format typical for specific device types
    Simulates how different types of devices might send timestamps
    """
    # Different devices send different timestamp formats (realistic simulation)
    device_timestamp_formats = {
        "industrial": [
            "epoch_ms",
            "epoch",
            "epoch_float",
        ],  # Industrial devices often use epoch
        "energy": ["epoch", "readable", "epoch_float"],  # Energy meters vary
        "environmental": [
            "iso",
            "iso_no_z",
            "iso_simple",
        ],  # Environmental sensors often use ISO
        "agricultural": ["readable", "us_format"],  # Agricultural sensors vary
        "automotive": [
            "epoch_ms",
            "epoch_float",
        ],  # Automotive systems use milliseconds
        "smart_home": ["readable", "compact", "iso_simple"],  # Smart home devices vary
    }

    # Pick a random format from the device type's typical formats
    possible_formats = device_timestamp_formats.get(device_type, ["iso", "epoch"])
    chosen_format = random.choice(possible_formats)

    return get_simulator_timestamp(chosen_format)


@dataclass
class SimulatedDevice:
    """Configuration for a simulated device"""

    name: str
    device_type: str
    location: str
    api_key: Optional[str] = None
    device_id: Optional[int] = None
    user_id: str = "default_user_123"
    telemetry_interval: int = 30  # seconds
    heartbeat_interval: int = 60  # seconds
    sensor_config: Dict[str, Any] = None

    def __post_init__(self):
        if self.sensor_config is None:
            self.sensor_config = self._get_sensor_config()

    def _get_sensor_config(self) -> Dict[str, Any]:
        """Get sensor configuration based on device type"""
        if self.device_type in DEVICE_TYPES:
            # Use predefined configuration
            type_config = DEVICE_TYPES[self.device_type]
            sensor_config = {}

            for sensor_name, sensor_config_obj in type_config.sensors.items():
                sensor_config[sensor_name] = {
                    "min": sensor_config_obj.min_value,
                    "max": sensor_config_obj.max_value,
                    "unit": sensor_config_obj.unit,
                    "precision": sensor_config_obj.precision,
                    "noise_factor": sensor_config_obj.noise_factor,
                }

            return sensor_config
        else:
            # Fallback to default environmental sensors
            return {
                "temperature": {
                    "min": 15.0,
                    "max": 35.0,
                    "unit": "°C",
                    "precision": 2,
                    "noise_factor": 0.05,
                },
                "humidity": {
                    "min": 30.0,
                    "max": 90.0,
                    "unit": "%",
                    "precision": 2,
                    "noise_factor": 0.05,
                },
                "pressure": {
                    "min": 980.0,
                    "max": 1030.0,
                    "unit": "hPa",
                    "precision": 2,
                    "noise_factor": 0.05,
                },
            }


class MQTTDeviceSimulator:
    """MQTT Device Simulator"""

    def __init__(
        self,
        api_base_url: str = "http://localhost:5000/api/v1",
        mqtt_host: str = "localhost",
        mqtt_port: int = 1883,
    ):
        self.api_base_url = api_base_url
        self.mqtt_host = mqtt_host
        self.mqtt_port = mqtt_port
        self.devices: List[SimulatedDevice] = []
        self.mqtt_clients: Dict[int, mqtt.Client] = {}
        self.running = False
        self.executor = ThreadPoolExecutor(max_workers=10)

        # Setup signal handlers for graceful shutdown
        signal.signal(signal.SIGINT, self._signal_handler)
        signal.signal(signal.SIGTERM, self._signal_handler)

    def _signal_handler(self, signum, frame):
        """Handle shutdown signals"""
        logger.info(f"Received signal {signum}, shutting down gracefully...")
        self.stop_simulation()
        sys.exit(0)

    def add_device(self, device: SimulatedDevice) -> bool:
        """Add a device to simulate"""
        try:
            # Register device via API
            if not self._register_device_api(device):
                return False

            # Setup MQTT client for the device
            if not self._setup_mqtt_client(device):
                return False

            self.devices.append(device)
            logger.info(f"Added device: {device.name} (ID: {device.device_id})")
            return True

        except Exception as e:
            logger.error(f"Failed to add device {device.name}: {e}")
            return False

    def _register_device_api(self, device: SimulatedDevice) -> bool:
        """Register device via HTTP API"""
        try:
            payload = {
                "name": device.name,
                "device_type": device.device_type,
                "description": f"Simulated {device.device_type} device",
                "location": device.location,
                "user_id": device.user_id,
                "firmware_version": "1.0.0-sim",
                "hardware_version": "SIM-v1",
            }

            response = requests.post(
                f"{self.api_base_url}/devices/register",
                json=payload,
                headers={"Content-Type": "application/json"},
                timeout=10,
            )

            if response.status_code == 201:
                data = response.json()
                device.device_id = data["device"]["id"]
                device.api_key = data["device"]["api_key"]
                logger.info(
                    f"Device {device.name} registered with ID: {device.device_id}"
                )
                return True
            else:
                logger.error(
                    f"Failed to register device {device.name}: {response.text}"
                )
                return False

        except requests.RequestException as e:
            logger.error(f"API request failed for device {device.name}: {e}")
            return False

    def _setup_mqtt_client(self, device: SimulatedDevice) -> bool:
        """Setup MQTT client for device"""
        if not MQTT_AVAILABLE:
            logger.error(
                "MQTT library not available. Please install paho-mqtt: pip install paho-mqtt"
            )
            return False

        try:
            client_id = f"sim_{device.device_id}_{device.name.replace(' ', '_')}"
            client = mqtt.Client(client_id=client_id)

            # Set callbacks
            client.on_connect = lambda client, userdata, flags, rc: self._on_connect(
                client, userdata, flags, rc, device
            )
            client.on_disconnect = lambda client, userdata, rc: self._on_disconnect(
                client, userdata, rc, device
            )
            client.on_publish = lambda client, userdata, mid: self._on_publish(
                client, userdata, mid, device
            )

            # Connect to MQTT broker
            client.connect(self.mqtt_host, self.mqtt_port, keepalive=60)
            client.loop_start()

            self.mqtt_clients[device.device_id] = client
            return True

        except Exception as e:
            logger.error(f"Failed to setup MQTT client for device {device.name}: {e}")
            return False

    def _on_connect(self, client, userdata, flags, rc, device):
        """MQTT connection callback"""
        if rc == 0:
            logger.info(f"Device {device.name} connected to MQTT broker")
            # Publish online status
            self._publish_status(device, "online")
        else:
            logger.error(f"Device {device.name} failed to connect to MQTT broker: {rc}")

    def _on_disconnect(self, client, userdata, rc, device):
        """MQTT disconnection callback"""
        logger.warning(f"Device {device.name} disconnected from MQTT broker: {rc}")

    def _on_publish(self, client, userdata, mid, device):
        """MQTT publish callback"""
        logger.debug(f"Message {mid} published for device {device.name}")

    def _publish_status(self, device: SimulatedDevice, status: str):
        """Publish device status"""
        try:
            client = self.mqtt_clients.get(device.device_id)
            if not client:
                return

            topic = f"iotflow/devices/{device.device_id}/status/{status}"
            payload = {
                "device_id": device.device_id,
                "device_name": device.name,
                "status": status,
                "timestamp": get_device_specific_timestamp(device.device_type),
                "api_key": device.api_key,
            }

            client.publish(topic, json.dumps(payload), qos=1, retain=True)
            logger.debug(f"Published {status} status for device {device.name}")

        except Exception as e:
            logger.error(f"Failed to publish status for device {device.name}: {e}")

    def _publish_heartbeat(self, device: SimulatedDevice):
        """Publish device heartbeat"""
        try:
            client = self.mqtt_clients.get(device.device_id)
            if not client:
                return

            topic = f"iotflow/devices/{device.device_id}/status/heartbeat"
            payload = {
                "device_id": device.device_id,
                "device_name": device.name,
                "timestamp": get_device_specific_timestamp(device.device_type),
                "uptime_seconds": int(time.time()),
                "api_key": device.api_key,
            }

            client.publish(topic, json.dumps(payload), qos=0)
            logger.debug(f"Published heartbeat for device {device.name}")

        except Exception as e:
            logger.error(f"Failed to publish heartbeat for device {device.name}: {e}")

    def _generate_sensor_data(self, device: SimulatedDevice) -> Dict[str, Any]:
        """Generate simulated sensor data"""
        sensor_data = {}

        for sensor_name, config in device.sensor_config.items():
            # Get configuration values with defaults
            min_val = config.get("min", 0.0)
            max_val = config.get("max", 100.0)
            unit = config.get("unit", "")
            precision = config.get("precision", 2)
            noise_factor = config.get("noise_factor", 0.05)

            # Generate base value
            base_value = random.uniform(min_val, max_val)

            # Add time-based patterns for realistic behavior
            if "temperature" in sensor_name.lower():
                hour = datetime.now().hour
                # Simulate daily temperature cycle
                daily_factor = (
                    0.8 + 0.4 * (1 + math.cos((hour - 14) * math.pi / 12)) / 2
                )
                base_value *= daily_factor

            # Add realistic noise
            if noise_factor > 0:
                noise = random.uniform(-noise_factor, noise_factor) * base_value
                base_value += noise

            # Clamp to bounds
            final_value = max(min_val, min(max_val, base_value))

            # Handle boolean sensors (for door_open, motion_detected, etc.)
            if unit == "bool":
                final_value = 1 if random.random() > 0.7 else 0
                precision = 0

            # Apply precision
            if precision == 0:
                final_value = int(final_value)
            else:
                final_value = round(final_value, precision)

            sensor_data[sensor_name] = {
                "value": final_value,
                "unit": unit,
                "timestamp": get_device_specific_timestamp(device.device_type),
            }

        return sensor_data

    def _publish_telemetry(self, device: SimulatedDevice):
        """Publish telemetry data for device"""
        try:
            client = self.mqtt_clients.get(device.device_id)
            if not client:
                return

            # Generate sensor data
            sensor_data = self._generate_sensor_data(device)

            # Create telemetry payload
            payload = {
                "device_id": device.device_id,
                "device_name": device.name,
                "device_type": device.device_type,
                "location": device.location,
                "timestamp": get_device_specific_timestamp(device.device_type),
                "data": sensor_data,
                "metadata": {
                    "firmware_version": "1.0.0-sim",
                    "signal_strength": random.randint(-80, -30),
                    "battery_level": random.randint(15, 100),
                },
                "api_key": device.api_key,
            }

            # Publish to main telemetry topic
            main_topic = f"iotflow/devices/{device.device_id}/telemetry"
            client.publish(main_topic, json.dumps(payload), qos=1)

            # Also publish to sensors subtopic
            sensors_topic = f"iotflow/devices/{device.device_id}/telemetry/sensors"
            client.publish(sensors_topic, json.dumps(payload), qos=1)

            logger.info(
                f"Published telemetry for device {device.name}: {len(sensor_data)} sensors"
            )

        except Exception as e:
            logger.error(f"Failed to publish telemetry for device {device.name}: {e}")

    def _device_loop(self, device: SimulatedDevice):
        """Main loop for a device"""
        last_telemetry = 0
        last_heartbeat = 0

        while self.running:
            try:
                current_time = time.time()

                # Send telemetry
                if current_time - last_telemetry >= device.telemetry_interval:
                    self._publish_telemetry(device)
                    last_telemetry = current_time

                # Send heartbeat
                if current_time - last_heartbeat >= device.heartbeat_interval:
                    self._publish_heartbeat(device)
                    last_heartbeat = current_time

                time.sleep(1)  # Short sleep to prevent busy waiting

            except Exception as e:
                logger.error(f"Error in device loop for {device.name}: {e}")
                time.sleep(5)  # Longer sleep on error

    def start_simulation(self):
        """Start the device simulation"""
        if not self.devices:
            logger.error("No devices to simulate")
            return

        logger.info(f"Starting simulation for {len(self.devices)} devices")
        self.running = True

        # Start device loops in separate threads
        for device in self.devices:
            self.executor.submit(self._device_loop, device)

        logger.info("Device simulation started")

    def stop_simulation(self):
        """Stop the device simulation"""
        logger.info("Stopping device simulation...")
        self.running = False

        # Publish offline status for all devices
        for device in self.devices:
            self._publish_status(device, "offline")

        # Disconnect MQTT clients
        for client in self.mqtt_clients.values():
            client.loop_stop()
            client.disconnect()

        # Shutdown executor
        self.executor.shutdown(wait=True)
        logger.info("Device simulation stopped")


def create_sample_devices(
    use_random_names: bool = False, custom_names: List[str] = None
) -> List[SimulatedDevice]:
    """Create sample devices for testing

    Args:
        use_random_names: If True, generate random device names
        custom_names: List of custom names to use (overrides random names)

    Returns:
        List of SimulatedDevice objects
    """
    devices = []

    # Define device types and base configurations
    device_configs = [
        {
            "device_type": "environmental",
            "telemetry_interval": 15,
            "heartbeat_interval": 45,
        },
        {
            "device_type": "industrial",
            "telemetry_interval": 10,
            "heartbeat_interval": 30,
        },
        {
            "device_type": "agricultural",
            "telemetry_interval": 60,
            "heartbeat_interval": 120,
        },
        {"device_type": "energy", "telemetry_interval": 20, "heartbeat_interval": 60},
        {
            "device_type": "automotive",
            "telemetry_interval": 5,
            "heartbeat_interval": 30,
        },
        {
            "device_type": "smart_home",
            "telemetry_interval": 30,
            "heartbeat_interval": 90,
        },
    ]

    # Use predefined sample devices if available and not using random names
    if SAMPLE_DEVICES and not use_random_names and not custom_names:
        for sample in SAMPLE_DEVICES[:6]:  # Limit to 6 devices
            device = SimulatedDevice(
                name=sample["name"],
                device_type=sample["device_type"],
                location=sample["location"],
                telemetry_interval=sample.get("telemetry_interval", 30),
                heartbeat_interval=sample.get("heartbeat_interval", 60),
            )
            devices.append(device)
    else:
        # Generate devices with custom, random, or fallback names
        for i, config in enumerate(device_configs):
            device_type = config["device_type"]

            # Determine device name
            if custom_names and i < len(custom_names):
                # Use custom name provided
                device_name = custom_names[i]
            elif use_random_names:
                # Generate random name
                device_name = generate_random_device_name(device_type)
            else:
                # Use fallback names
                fallback_names = {
                    "environmental": "Environment Monitor",
                    "industrial": "Industrial Sensor Array",
                    "agricultural": "Smart Farm Sensor",
                    "energy": "Energy Monitor",
                    "automotive": "Vehicle Tracker",
                    "smart_home": "Smart Home Hub",
                }
                device_name = f"{fallback_names.get(device_type, 'IoT Device')} {i+1}"

            # Generate location (always random for variety)
            location = generate_random_location(device_type)

            device = SimulatedDevice(
                name=device_name,
                device_type=device_type,
                location=location,
                telemetry_interval=config["telemetry_interval"],
                heartbeat_interval=config["heartbeat_interval"],
            )
            devices.append(device)

    return devices


def main():
    """Main function"""
    parser = argparse.ArgumentParser(description="MQTT Device Simulator for IoTFlow")
    parser.add_argument(
        "--api-url",
        default="http://localhost:5000/api/v1",
        help="Base URL for IoTFlow API",
    )
    parser.add_argument("--mqtt-host", default="localhost", help="MQTT broker hostname")
    parser.add_argument("--mqtt-port", type=int, default=1883, help="MQTT broker port")
    parser.add_argument(
        "--devices", type=int, default=1, help="Number of devices to simulate"
    )
    parser.add_argument(
        "--user-id", default="a78689be04814ac187e0191656ee6fb1", help="User ID for device registration"
    )
    parser.add_argument(
        "--verbose", "-v", action="store_true", help="Enable verbose logging"
    )

    # Device naming options
    naming_group = parser.add_mutually_exclusive_group()
    naming_group.add_argument(
        "--random-names", action="store_true", help="Generate random device names"
    )
    naming_group.add_argument(
        "--device-names",
        nargs="+",
        help="Specify custom device names (space-separated)",
    )

    args = parser.parse_args()

    if args.verbose:
        logging.getLogger().setLevel(logging.DEBUG)

    # Create simulator
    simulator = MQTTDeviceSimulator(
        api_base_url=args.api_url, mqtt_host=args.mqtt_host, mqtt_port=args.mqtt_port
    )

    # Create and add sample devices with naming options
    if args.device_names:
        logger.info(f"Using custom device names: {args.device_names}")
        sample_devices = create_sample_devices(
            use_random_names=False, custom_names=args.device_names
        )[: args.devices]
    elif args.random_names:
        logger.info("Generating random device names")
        sample_devices = create_sample_devices(use_random_names=True)[: args.devices]
    else:
        logger.info("Using default device names")
        sample_devices = create_sample_devices()[: args.devices]

    for device in sample_devices:
        device.user_id = args.user_id
        if not simulator.add_device(device):
            logger.error(f"Failed to add device: {device.name}")
            continue

    if not simulator.devices:
        logger.error("No devices were successfully added")
        return 1

    try:
        # Start simulation
        simulator.start_simulation()

        # Keep running until interrupted
        logger.info("Simulation running... Press Ctrl+C to stop")
        while True:
            time.sleep(1)

    except KeyboardInterrupt:
        logger.info("Simulation interrupted by user")
    finally:
        simulator.stop_simulation()

    return 0


if __name__ == "__main__":
    sys.exit(main())
