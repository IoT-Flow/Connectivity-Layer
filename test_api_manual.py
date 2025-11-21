#!/usr/bin/env python3
"""
Manual API Test Script
Tests device registration and telemetry sending for a specific user
"""

import requests
import json
from datetime import datetime

# Configuration
BASE_URL = "http://localhost:5000/api/v1"
USER_ID = "c4a7730602624786bd05a3b145464c85"

def print_section(title):
    """Print a formatted section header"""
    print("\n" + "="*60)
    print(f"  {title}")
    print("="*60)

def print_response(response):
    """Print formatted response"""
    print(f"Status Code: {response.status_code}")
    try:
        print(f"Response: {json.dumps(response.json(), indent=2)}")
    except:
        print(f"Response: {response.text}")

# Step 1: Register a device for the user
print_section("STEP 1: Register Device")

device_data = {
    "name": "Test Temperature Sensor",
    "description": "Manual API test device",
    "device_type": "sensor",
    "location": "Test Lab",
    "firmware_version": "1.0.0",
    "hardware_version": "v1.0",
    "user_id": USER_ID
}

print(f"Registering device for user: {USER_ID}")
print(f"Device data: {json.dumps(device_data, indent=2)}")

response = requests.post(
    f"{BASE_URL}/devices/register",
    json=device_data,
    headers={"Content-Type": "application/json"}
)

print_response(response)

if response.status_code not in [200, 201]:
    print("\n❌ Device registration failed!")
    exit(1)

# Extract device info
device_response = response.json()
device = device_response.get('device', {})
device_id = device.get('id')
device_api_key = device.get('api_key')

print(f"\n✅ Device registered successfully!")
print(f"   Device ID: {device_id}")
print(f"   API Key: {device_api_key}")

# Step 2: Send telemetry data
print_section("STEP 2: Send Telemetry Data")

telemetry_data = {
    "data": {
        "temperature": 23.5,
        "humidity": 65.0,
        "pressure": 1013.25
    },
    "metadata": {
        "sensor_type": "DHT22",
        "location": "room_1"
    }
}

print(f"Sending telemetry data:")
print(f"{json.dumps(telemetry_data, indent=2)}")

response = requests.post(
    f"{BASE_URL}/telemetry",
    json=telemetry_data,
    headers={
        "X-API-Key": device_api_key,
        "Content-Type": "application/json"
    }
)

print_response(response)

if response.status_code != 201:
    print("\n❌ Telemetry send failed!")
    exit(1)

print(f"\n✅ Telemetry sent successfully!")

# Step 3: Retrieve latest telemetry
print_section("STEP 3: Retrieve Latest Telemetry")

response = requests.get(
    f"{BASE_URL}/telemetry/{device_id}/latest",
    headers={"X-API-Key": device_api_key}
)

print_response(response)

if response.status_code != 200:
    print("\n❌ Failed to retrieve telemetry!")
    exit(1)

latest_data = response.json()
print(f"\n✅ Latest telemetry retrieved!")
print(f"   Temperature: {latest_data['latest_data']['temperature']}°C")
print(f"   Humidity: {latest_data['latest_data']['humidity']}%")
print(f"   Pressure: {latest_data['latest_data']['pressure']} hPa")

# Step 4: Get device status
print_section("STEP 4: Get Device Status")

response = requests.get(
    f"{BASE_URL}/devices/status",
    headers={"X-API-Key": device_api_key}
)

print_response(response)

if response.status_code != 200:
    print("\n❌ Failed to get device status!")
    exit(1)

status_data = response.json()
device_info = status_data.get('device', {})
print(f"\n✅ Device status retrieved!")
print(f"   Name: {device_info['name']}")
print(f"   Type: {device_info['device_type']}")
print(f"   Status: {device_info['status']}")
print(f"   Location: {device_info['location']}")
print(f"   Online: {device_info.get('is_online', False)}")

# Step 5: Send more telemetry with different data types
print_section("STEP 5: Send Mixed Data Types")

mixed_telemetry = {
    "data": {
        "temperature": 24.0,
        "status": "online",
        "is_active": True,
        "config": {
            "mode": "auto",
            "threshold": 25
        }
    }
}

print(f"Sending mixed data types:")
print(f"{json.dumps(mixed_telemetry, indent=2)}")

response = requests.post(
    f"{BASE_URL}/telemetry",
    json=mixed_telemetry,
    headers={
        "X-API-Key": device_api_key,
        "Content-Type": "application/json"
    }
)

print_response(response)

if response.status_code != 201:
    print("\n❌ Mixed telemetry send failed!")
    exit(1)

print(f"\n✅ Mixed telemetry sent successfully!")

# Step 6: Retrieve telemetry history
print_section("STEP 6: Retrieve Telemetry History")

response = requests.get(
    f"{BASE_URL}/telemetry/{device_id}?start_time=-1h&limit=10",
    headers={"X-API-Key": device_api_key}
)

print_response(response)

if response.status_code != 200:
    print("\n❌ Failed to retrieve telemetry history!")
    exit(1)

history_data = response.json()
print(f"\n✅ Telemetry history retrieved!")
print(f"   Total readings: {history_data['count']}")
print(f"   Readings in response: {len(history_data['data'])}")

# Final Summary
print_section("✅ ALL TESTS PASSED!")
print(f"""
Summary:
  - User ID: {USER_ID}
  - Device ID: {device_id}
  - Device Name: {device_info['name']}
  - API Key: {device_api_key}
  - Telemetry readings sent: 2
  - All operations successful!

You can use this API key to send more telemetry:
  curl -X POST {BASE_URL}/telemetry \\
    -H "X-API-Key: {device_api_key}" \\
    -H "Content-Type: application/json" \\
    -d '{{"data": {{"temperature": 25.0, "humidity": 60.0}}}}'
""")
print("="*60)
