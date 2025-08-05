# MQTT Device Simulator for IoTFlow

This directory contains a comprehensive MQTT device simulator that can simulate multiple IoT devices sending telemetry data to your IoTFlow system.

## Features

- 🔄 **Multiple Device Types**: Environmental, Industrial, Agricultural, Energy, Automotive, and Smart Home sensors
- 📡 **MQTT Protocol**: Uses MQTT for efficient IoT communication
- 🎛️ **Configurable Sensors**: Each device type has realistic sensor configurations
- ⏱️ **Flexible Intervals**: Customizable telemetry and heartbeat intervals
- 🔐 **API Integration**: Automatic device registration via IoTFlow API
- 📊 **Realistic Data**: Time-based patterns, noise, and realistic sensor ranges
- 🔄 **Status Reporting**: Online/offline status and heartbeat messages
- 🛠️ **Easy Configuration**: Modify device types and sensors in `simulator_config.py`

## Files

- `mqtt_device_simulator.py` - Main simulator script
- `simulator_config.py` - Device types and sensor configurations  
- `requirements.txt` - Python dependencies
- `setup.sh` - Setup script for easy installation
- `README.md` - This documentation

## Quick Start

### 1. Install Dependencies

```bash
# Option A: Use the setup script
chmod +x setup.sh
./setup.sh

# Option B: Install manually
pip3 install -r requirements.txt
```

### 2. Start IoTFlow Services

Make sure your IoTFlow server and MQTT broker are running:

```bash
# Start Redis (if not running)
redis-server

# Start MQTT broker (Mosquitto)
mosquitto -c mqtt/config/mosquitto.conf

# Start IoTFlow API server
poetry run python app.py
```

### 3. Run the Simulator

```bash
# Basic usage (4 devices)
python3 mqtt_device_simulator.py

# Custom number of devices
python3 mqtt_device_simulator.py --devices 8

# Custom MQTT broker and API URL
python3 mqtt_device_simulator.py --mqtt-host localhost --api-url http://localhost:5000/api/v1

# Verbose output
python3 mqtt_device_simulator.py --verbose

# Custom user ID for device registration
python3 mqtt_device_simulator.py --user-id "your_user_id_here"
```

## Command Line Options

```
Options:
  --api-url URL         IoTFlow API base URL (default: http://localhost:5000/api/v1)
  --mqtt-host HOST      MQTT broker hostname (default: localhost)
  --mqtt-port PORT      MQTT broker port (default: 1883)
  --devices N           Number of devices to simulate (default: 4)
  --user-id ID          User ID for device registration (default: default_user_123)
  --verbose, -v         Enable verbose logging
  --help, -h            Show help message
```

## Device Types

The simulator supports the following device types:

### Environmental Sensors
- **Sensors**: Temperature, Humidity, Pressure, Light, Air Quality
- **Use Case**: Office buildings, weather stations
- **Telemetry Interval**: 30 seconds

### Industrial Monitors  
- **Sensors**: Temperature, Vibration, Pressure, Current, Voltage, RPM
- **Use Case**: Manufacturing equipment monitoring
- **Telemetry Interval**: 15 seconds

### Agricultural Devices
- **Sensors**: Soil temperature/moisture/pH, Light intensity, Ambient conditions
- **Use Case**: Smart farming, greenhouse monitoring
- **Telemetry Interval**: 60 seconds

### Energy Meters
- **Sensors**: Voltage, Current, Power, Energy, Frequency, Power Factor
- **Use Case**: Smart grid, home energy monitoring
- **Telemetry Interval**: 20 seconds

### Automotive Sensors
- **Sensors**: Engine temperature, RPM, Speed, Fuel level, Battery, Oil pressure
- **Use Case**: Fleet management, vehicle diagnostics
- **Telemetry Interval**: 10 seconds

### Smart Home Devices
- **Sensors**: Indoor climate, Motion, Light level, Sound, Door status
- **Use Case**: Home automation, security systems
- **Telemetry Interval**: 45 seconds

## MQTT Topics

The simulator publishes to these MQTT topics:

```
# Telemetry data
iotflow/devices/{device_id}/telemetry
iotflow/devices/{device_id}/telemetry/sensors

# Device status
iotflow/devices/{device_id}/status/online
iotflow/devices/{device_id}/status/offline
iotflow/devices/{device_id}/status/heartbeat
```

## Sample Data Format

### Telemetry Message
```json
{
  "device_id": 123,
  "device_name": "Office Environment Monitor",
  "device_type": "environmental",
  "location": "Office Building A, Floor 3",
  "timestamp": "2025-01-15T10:30:00.000Z",
  "data": {
    "temperature": {
      "value": 22.5,
      "unit": "°C",
      "timestamp": "2025-01-15T10:30:00.000Z"
    },
    "humidity": {
      "value": 45.2,
      "unit": "%",
      "timestamp": "2025-01-15T10:30:00.000Z"
    },
    "pressure": {
      "value": 1013.25,
      "unit": "hPa", 
      "timestamp": "2025-01-15T10:30:00.000Z"
    }
  },
  "metadata": {
    "firmware_version": "1.0.0-sim",
    "signal_strength": -65,
    "battery_level": 87
  },
  "api_key": "device_api_key_here"
}
```

### Status Message
```json
{
  "device_id": 123,
  "device_name": "Office Environment Monitor",
  "status": "online",
  "timestamp": "2025-01-15T10:30:00.000Z",
  "api_key": "device_api_key_here"
}
```

## Customization

### Adding New Device Types

Edit `simulator_config.py` to add new device types:

```python
DEVICE_TYPES['custom_type'] = DeviceTypeConfig(
    name='custom_type',
    description='My custom device type',
    sensors={
        'custom_sensor': SensorConfig(0.0, 100.0, 'units'),
        'another_sensor': SensorConfig(-50.0, 50.0, 'other_units')
    },
    default_telemetry_interval=30,
    default_heartbeat_interval=60
)
```

### Modifying Sensor Ranges

Update sensor configurations in `simulator_config.py`:

```python
'temperature': SensorConfig(
    min_value=-10.0,    # Minimum value
    max_value=50.0,     # Maximum value
    unit='°C',          # Unit of measurement
    precision=2,        # Decimal places
    noise_factor=0.05   # 5% random noise
)
```

## Troubleshooting

### MQTT Connection Issues
- Ensure MQTT broker (Mosquitto) is running on the specified host/port
- Check firewall settings
- Verify MQTT broker configuration allows anonymous connections

### API Registration Failures
- Ensure IoTFlow API server is running
- Check the API URL is correct
- Verify the user_id exists in the database (run `init_db.py` if needed)

### Missing Dependencies
```bash
pip3 install paho-mqtt requests
```

### Permission Issues
```bash
chmod +x mqtt_device_simulator.py
chmod +x setup.sh
```

## Monitoring

While the simulator is running, you can monitor:

1. **Simulator Logs**: Watch the console output for device status
2. **MQTT Messages**: Use MQTT client to subscribe to `iotflow/#`
3. **IoTFlow Logs**: Check IoTFlow server logs for received messages
4. **Redis Cache**: Monitor device status in Redis
5. **Database**: Check telemetry data in IoTDB

### MQTT Monitoring Commands

```bash
# Subscribe to all topics
mosquitto_sub -h localhost -t "iotflow/#" -v

# Subscribe to specific device
mosquitto_sub -h localhost -t "iotflow/devices/+/telemetry" -v

# Subscribe to status messages
mosquitto_sub -h localhost -t "iotflow/devices/+/status/+" -v
```

## Advanced Usage

### Running Multiple Simulators
You can run multiple simulator instances with different configurations:

```bash
# Terminal 1: Environmental devices
python3 mqtt_device_simulator.py --devices 3 --user-id "user1"

# Terminal 2: Industrial devices  
python3 mqtt_device_simulator.py --devices 2 --user-id "user2"
```

### Custom Device Configuration
Create custom device configurations by modifying the `SAMPLE_DEVICES` list in `simulator_config.py`.

### Integration Testing
The simulator is perfect for:
- Testing MQTT message handling
- Validating telemetry data processing
- Load testing the IoTFlow system
- Demonstrating real-time data flows

## Support

For issues or questions:
1. Check the troubleshooting section above
2. Review IoTFlow server logs
3. Verify MQTT broker connectivity
4. Ensure all dependencies are installed
