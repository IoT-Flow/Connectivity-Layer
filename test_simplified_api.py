#!/usr/bin/env python3
"""
Test API with Simplified Telemetry Table
Only numeric values are stored
"""

import requests
import json

BASE_URL = "http://localhost:5000/api/v1"
USER_ID = "c4a7730602624786bd05a3b145464c85"

print("="*60)
print("Testing Simplified Telemetry Table (Numeric Only)")
print("="*60)

# Step 1: Register a new device
print("\n1. Registering device...")
import time
device_data = {
    "name": f"Simplified Test Sensor {int(time.time())}",
    "description": "Testing simplified telemetry table",
    "device_type": "sensor",
    "location": "Test Lab",
    "user_id": USER_ID
}

response = requests.post(f"{BASE_URL}/devices/register", json=device_data)
print(f"Status: {response.status_code}")

if response.status_code not in [200, 201]:
    print(f"Error: {response.text}")
    exit(1)

device = response.json()['device']
device_id = device['id']
api_key = device['api_key']
print(f"✓ Device ID: {device_id}")
print(f"✓ API Key: {api_key}")

# Step 2: Send numeric telemetry (should work)
print("\n2. Sending numeric telemetry...")
telemetry = {
    "data": {
        "temperature": 23.5,
        "humidity": 65.0,
        "pressure": 1013.25,
        "voltage": 3.3
    }
}

response = requests.post(
    f"{BASE_URL}/telemetry",
    json=telemetry,
    headers={"X-API-Key": api_key}
)
print(f"Status: {response.status_code}")
print(f"Response: {json.dumps(response.json(), indent=2)}")

if response.status_code == 201:
    print("✓ Numeric telemetry stored successfully")
else:
    print("✗ Failed to store telemetry")

# Step 3: Try to send non-numeric data (should be skipped)
print("\n3. Sending mixed data (non-numeric should be skipped)...")
mixed_data = {
    "data": {
        "temperature": 24.0,
        "status": "online",  # This should be skipped
        "is_active": True,   # This should be skipped
        "count": 42
    }
}

response = requests.post(
    f"{BASE_URL}/telemetry",
    json=mixed_data,
    headers={"X-API-Key": api_key}
)
print(f"Status: {response.status_code}")
print(f"Response: {json.dumps(response.json(), indent=2)}")

# Step 4: Retrieve latest telemetry
print("\n4. Retrieving latest telemetry...")
response = requests.get(
    f"{BASE_URL}/telemetry/{device_id}/latest",
    headers={"X-API-Key": api_key}
)
print(f"Status: {response.status_code}")
if response.status_code == 200:
    latest = response.json()
    print(f"Latest data: {json.dumps(latest['latest_data'], indent=2)}")
    print("✓ Only numeric values retrieved")
else:
    print(f"Error: {response.text}")

# Step 5: Get telemetry history
print("\n5. Retrieving telemetry history...")
response = requests.get(
    f"{BASE_URL}/telemetry/{device_id}?start_time=-1h&limit=10",
    headers={"X-API-Key": api_key}
)
print(f"Status: {response.status_code}")
if response.status_code == 200:
    history = response.json()
    print(f"Total readings: {history['count']}")
    print(f"Measurements in latest reading:")
    if history['data']:
        for key, value in history['data'][0]['measurements'].items():
            print(f"  - {key}: {value}")
    print("✓ History retrieved successfully")
else:
    print(f"Error: {response.text}")

print("\n" + "="*60)
print("✓ Test completed!")
print("="*60)
print("\nTable structure:")
print("  - id: BIGSERIAL")
print("  - device_id: INTEGER")
print("  - timestamp: TIMESTAMP WITH TIME ZONE")
print("  - measurement_name: VARCHAR(100)")
print("  - numeric_value: DOUBLE PRECISION")
print("\nOnly numeric values are stored!")
print("="*60)
