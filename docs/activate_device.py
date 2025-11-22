#!/usr/bin/env python3
"""
Activate a device by updating its status to 'active'
"""
import requests

# Configuration
BASE_URL = "http://localhost:5000/api/v1"
API_KEY = "JVpok9Vp4jCOTyHJ9eHsNteXY3bfkJZv"

# Headers
headers = {
    "X-API-Key": API_KEY,
    "Content-Type": "application/json"
}

print("=" * 60)
print("🔧 Activating Device")
print("=" * 60)
print(f"API Key: {API_KEY}")
print("=" * 60)
print()

# Update device status to active
payload = {
    "status": "active"
}

try:
    response = requests.put(
        f"{BASE_URL}/devices/config",
        headers=headers,
        json=payload,
        timeout=5
    )
    
    if response.status_code == 200:
        result = response.json()
        device = result.get('device', {})
        print("✅ Device activated successfully!")
        print()
        print(f"Device Name: {device.get('name', 'N/A')}")
        print(f"Device Type: {device.get('device_type', 'N/A')}")
        print(f"Status: {device.get('status', 'N/A')}")
        print(f"Location: {device.get('location', 'N/A')}")
        print()
        print("🎉 You can now send telemetry data!")
    else:
        print(f"❌ Failed to activate device - Status: {response.status_code}")
        print(f"Response: {response.text}")

except requests.exceptions.RequestException as e:
    print(f"❌ Error: {str(e)}")
    print()
    print("Make sure:")
    print("  - The server is running")
    print("  - The API key is correct")
