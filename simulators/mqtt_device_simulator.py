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
"""

import json
import time
import random
import logging
import argparse
import threading
import signal
import sys
import math
from datetime import datetime, timezone
from typing import Dict, List, Optional, Any
from dataclasses import dataclass, asdict
import requests

# Import MQTT library with fallback
try:
    import paho.mqtt.client as mqtt
    MQTT_AVAILABLE = True
except ImportError:
    print("Warning: paho-mqtt not installed. Install with: pip install paho-mqtt")
    MQTT_AVAILABLE = False
    
from concurrent.futures import ThreadPoolExecutor

# Import local configuration
try:
    from simulator_config import DEVICE_TYPES, DEFAULT_SETTINGS, SAMPLE_DEVICES, get_device_type_config
except ImportError:
    # Fallback if config file not available
    DEVICE_TYPES = {}
    DEFAULT_SETTINGS = {
        'api_base_url': 'http://localhost:5000/api/v1',
        'mqtt_host': 'localhost',
        'mqtt_port': 1883,
        'user_id': 'default_user_123'
    }
    SAMPLE_DEVICES = []


# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)


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
                    'min': sensor_config_obj.min_value,
                    'max': sensor_config_obj.max_value,
                    'unit': sensor_config_obj.unit,
                    'precision': sensor_config_obj.precision,
                    'noise_factor': sensor_config_obj.noise_factor
                }
            
            return sensor_config
        else:
            # Fallback to default environmental sensors
            return {
                'temperature': {'min': 15.0, 'max': 35.0, 'unit': '°C', 'precision': 2, 'noise_factor': 0.05},
                'humidity': {'min': 30.0, 'max': 90.0, 'unit': '%', 'precision': 2, 'noise_factor': 0.05},
                'pressure': {'min': 980.0, 'max': 1030.0, 'unit': 'hPa', 'precision': 2, 'noise_factor': 0.05}
            }


class MQTTDeviceSimulator:
    """MQTT Device Simulator"""
    
    def __init__(self, 
                 api_base_url: str = "http://localhost:5000/api/v1",
                 mqtt_host: str = "localhost", 
                 mqtt_port: int = 1883):
        
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
                "hardware_version": "SIM-v1"
            }
            
            response = requests.post(
                f"{self.api_base_url}/devices/register",
                json=payload,
                headers={"Content-Type": "application/json"},
                timeout=10
            )
            
            if response.status_code == 201:
                data = response.json()
                device.device_id = data['device']['id']
                device.api_key = data['device']['api_key']
                logger.info(f"Device {device.name} registered with ID: {device.device_id}")
                return True
            else:
                logger.error(f"Failed to register device {device.name}: {response.text}")
                return False
                
        except requests.RequestException as e:
            logger.error(f"API request failed for device {device.name}: {e}")
            return False
    
    def _setup_mqtt_client(self, device: SimulatedDevice) -> bool:
        """Setup MQTT client for device"""
        if not MQTT_AVAILABLE:
            logger.error("MQTT library not available. Please install paho-mqtt: pip install paho-mqtt")
            return False
            
        try:
            client_id = f"sim_{device.device_id}_{device.name.replace(' ', '_')}"
            client = mqtt.Client(client_id=client_id)
            
            # Set callbacks
            client.on_connect = lambda client, userdata, flags, rc: self._on_connect(client, userdata, flags, rc, device)
            client.on_disconnect = lambda client, userdata, rc: self._on_disconnect(client, userdata, rc, device)
            client.on_publish = lambda client, userdata, mid: self._on_publish(client, userdata, mid, device)
            
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
                "timestamp": datetime.now(timezone.utc).isoformat(),
                "api_key": device.api_key
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
                "timestamp": datetime.now(timezone.utc).isoformat(),
                "uptime_seconds": int(time.time()),
                "api_key": device.api_key
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
            min_val = config.get('min', 0.0)
            max_val = config.get('max', 100.0)
            unit = config.get('unit', '')
            precision = config.get('precision', 2)
            noise_factor = config.get('noise_factor', 0.05)
            
            # Generate base value
            base_value = random.uniform(min_val, max_val)
            
            # Add time-based patterns for realistic behavior
            if 'temperature' in sensor_name.lower():
                hour = datetime.now().hour
                # Simulate daily temperature cycle
                daily_factor = 0.8 + 0.4 * (1 + math.cos((hour - 14) * math.pi / 12)) / 2
                base_value *= daily_factor
            
            # Add realistic noise
            if noise_factor > 0:
                noise = random.uniform(-noise_factor, noise_factor) * base_value
                base_value += noise
            
            # Clamp to bounds
            final_value = max(min_val, min(max_val, base_value))
            
            # Handle boolean sensors (for door_open, motion_detected, etc.)
            if unit == 'bool':
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
                "timestamp": datetime.now(timezone.utc).isoformat()
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
                "timestamp": datetime.now(timezone.utc).isoformat(),
                "data": sensor_data,
                "metadata": {
                    "firmware_version": "1.0.0-sim",
                    "signal_strength": random.randint(-80, -30),
                    "battery_level": random.randint(15, 100)
                },
                "api_key": device.api_key
            }
            
            # Publish to main telemetry topic
            main_topic = f"iotflow/devices/{device.device_id}/telemetry"
            client.publish(main_topic, json.dumps(payload), qos=1)
            
            # Also publish to sensors subtopic
            sensors_topic = f"iotflow/devices/{device.device_id}/telemetry/sensors"
            client.publish(sensors_topic, json.dumps(payload), qos=1)
            
            logger.info(f"Published telemetry for device {device.name}: {len(sensor_data)} sensors")
            
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


def create_sample_devices() -> List[SimulatedDevice]:
    """Create sample devices for testing"""
    devices = []
    
    # Use predefined sample devices if available
    if SAMPLE_DEVICES:
        for sample in SAMPLE_DEVICES[:6]:  # Limit to 6 devices
            device = SimulatedDevice(
                name=sample['name'],
                device_type=sample['device_type'],
                location=sample['location'],
                telemetry_interval=sample.get('telemetry_interval', 30),
                heartbeat_interval=sample.get('heartbeat_interval', 60)
            )
            devices.append(device)
    else:
        # Fallback to basic devices if config not available
        devices = [
            SimulatedDevice(
                name="Environment Monitor 1",
                device_type="environmental",
                location="Office Building A, Floor 3",
                telemetry_interval=15,
                heartbeat_interval=45
            ),
            SimulatedDevice(
                name="Industrial Sensor Array",
                device_type="industrial", 
                location="Factory Floor 1, Zone B",
                telemetry_interval=10,
                heartbeat_interval=30
            ),
            SimulatedDevice(
                name="Smart Farm Sensor",
                device_type="agricultural",
                location="Greenhouse Section 2",
                telemetry_interval=60,
                heartbeat_interval=120
            ),
            SimulatedDevice(
                name="Energy Monitor Home",
                device_type="energy",
                location="Residential Unit 101",
                telemetry_interval=20,
                heartbeat_interval=60
            )
        ]
    
    return devices


def main():
    """Main function"""
    parser = argparse.ArgumentParser(description="MQTT Device Simulator for IoTFlow")
    parser.add_argument("--api-url", default="http://localhost:5000/api/v1", 
                       help="Base URL for IoTFlow API")
    parser.add_argument("--mqtt-host", default="localhost", 
                       help="MQTT broker hostname")
    parser.add_argument("--mqtt-port", type=int, default=1883, 
                       help="MQTT broker port")
    parser.add_argument("--devices", type=int, default=4, 
                       help="Number of devices to simulate")
    parser.add_argument("--user-id", default="default_user_123",
                       help="User ID for device registration")
    parser.add_argument("--verbose", "-v", action="store_true",
                       help="Enable verbose logging")
    
    args = parser.parse_args()
    
    if args.verbose:
        logging.getLogger().setLevel(logging.DEBUG)  
    
    # Create simulator
    simulator = MQTTDeviceSimulator(
        api_base_url=args.api_url,
        mqtt_host=args.mqtt_host,
        mqtt_port=args.mqtt_port
    )
    
    # Create and add sample devices
    sample_devices = create_sample_devices()[:args.devices]
    
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
    import math  # Import needed for temperature calculations
    sys.exit(main())
