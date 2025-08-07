#!/usr/bin/env python3
"""
Example usage of the MQTT Device Simulator
Shows how to create custom devices and run simulations
"""

import sys
import time
import logging
from mqtt_device_simulator import MQTTDeviceSimulator, SimulatedDevice

# Setup logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

def example_custom_devices():
    """Example of creating custom devices"""
    
    # Create simulator instance
    simulator = MQTTDeviceSimulator(
        api_base_url="http://localhost:5000/api/v1",
        mqtt_host="localhost",
        mqtt_port=1883
    )
    
    # Create custom devices
    devices = [
        SimulatedDevice(
            name="Office Temperature Sensor",
            device_type="environmental",
            location="Main Office, Desk Area",
            telemetry_interval=20,
            heartbeat_interval=60,
            user_id="office_manager_001"
        ),
        SimulatedDevice(
            name="Production Line Monitor",
            device_type="industrial",
            location="Factory Floor A, Line 3",
            telemetry_interval=5,  # Very frequent for critical monitoring
            heartbeat_interval=15,
            user_id="production_supervisor_002"
        ),
        SimulatedDevice(
            name="Smart Greenhouse Controller",
            device_type="agricultural", 
            location="Greenhouse Bay 2, Section C",
            telemetry_interval=300,  # Every 5 minutes (less critical)
            heartbeat_interval=600,  # Every 10 minutes
            user_id="farm_manager_003"
        )
    ]
    
    # Add devices to simulator
    logger.info("Adding custom devices to simulator...")
    for device in devices:
        if simulator.add_device(device):
            logger.info(f"✅ Added: {device.name}")
        else:
            logger.error(f"❌ Failed to add: {device.name}")
    
    # Start simulation
    if simulator.devices:
        logger.info(f"Starting simulation with {len(simulator.devices)} devices...")
        simulator.start_simulation()
        
        try:
            # Run for a specific duration or until interrupted
            logger.info("Simulation running... Press Ctrl+C to stop")
            while True:
                time.sleep(1)
        except KeyboardInterrupt:
            logger.info("Stopping simulation...")
        finally:
            simulator.stop_simulation()
    else:
        logger.error("No devices were successfully added")

def example_single_device():
    """Example of running a single device simulation"""
    
    simulator = MQTTDeviceSimulator()
    
    # Create a single high-frequency device for testing
    test_device = SimulatedDevice(
        name="Test Device - High Frequencyy",
        device_type="energy",
        location="Test Lab, Bench 1",
        telemetry_interval=5,  # Every 5 seconds
        heartbeat_interval=15,  # Every 15 seconds
        user_id="0fd2aa3103dc49e4b5d92199ea84c79e"
    )
    
    if simulator.add_device(test_device):
        logger.info("Starting single device test simulation...")
        simulator.start_simulation()
        
        try:
            # Run for 2 minutes then stop
            logger.info("Test simulation will run for 2 minutes...")
            time.sleep(120)
        finally:
            simulator.stop_simulation()
            logger.info("Test simulation completed")
    else:
        logger.error("Failed to add test device")

def example_batch_simulation():
    """Example of running multiple devices in batches"""
    
    simulator = MQTTDeviceSimulator()
    
    # Create devices of different types
    device_configs = [
        ("Warehouse Temp Sensor 1", "environmental", "Warehouse A, Zone 1"),
        ("Warehouse Temp Sensor 2", "environmental", "Warehouse A, Zone 2"), 
        ("Warehouse Temp Sensor 3", "environmental", "Warehouse A, Zone 3"),
        ("Motor Monitor 1", "industrial", "Production Line 1"),
        ("Motor Monitor 2", "industrial", "Production Line 2"),
        ("Energy Meter Main", "energy", "Main Electrical Panel"),
        ("Energy Meter Backup", "energy", "Backup Electrical Panel")
    ]
    
    # Create devices with standard intervals
    for name, device_type, location in device_configs:
        device = SimulatedDevice(
            name=name,
            device_type=device_type,
            location=location,
            telemetry_interval=10,
            heartbeat_interval=60,
            user_id="b5b2c0465af84b609e44171e24711fd9"
        )
        
        if not simulator.add_device(device):
            logger.error(f"Failed to add device: {name}")
    
    if simulator.devices:
        logger.info(f"Starting batch simulation with {len(simulator.devices)} devices...")
        simulator.start_simulation()
        
        try:
            logger.info("Batch simulation running... Press Ctrl+C to stop")
            while True:
                # Print status every 30 seconds
                time.sleep(30)
                logger.info(f"Simulation running with {len(simulator.devices)} active devices")
        except KeyboardInterrupt:
            logger.info("Stopping batch simulation...")
        finally:
            simulator.stop_simulation()
    else:
        logger.error("No devices were successfully added to batch simulation")

def main():
    """Main function with example selection"""
    
    if len(sys.argv) < 2:
        print("Usage: python3 example_usage.py [custom|single|batch]")
        print("")
        print("Examples:")
        print("  custom - Run custom devices with different configurations")
        print("  single - Run a single test device")
        print("  batch  - Run multiple devices in batch mode")
        return 1
    
    example_type = sys.argv[1].lower()
    
    try:
        if example_type == "custom":
            example_custom_devices()
        elif example_type == "single":
            example_single_device()
        elif example_type == "batch":
            example_batch_simulation()
        else:
            print(f"Unknown example type: {example_type}")
            return 1
            
    except Exception as e:
        logger.error(f"Example failed: {e}")
        return 1
    
    return 0

if __name__ == "__main__":
    sys.exit(main())
