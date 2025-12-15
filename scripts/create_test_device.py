#!/usr/bin/env python3
"""
Create a test device with known API key for testing telemetry sender
"""

import requests
import json

def create_test_device(base_url="http://localhost:5000"):
    """Create a test device and return its API key"""
    
    # Device registration data
    device_data = {
        "name": "TDD Test Device",
        "description": "Device created for TDD telemetry testing",
        "device_type": "test_sensor",
        "location": "Test Lab",
        "user_id": "user123",  # Using existing user ID
        "firmware_version": "1.0.0",
        "hardware_version": "v1.0"
    }
    
    try:
        response = requests.post(
            f"{base_url}/api/v1/devices/register",
            headers={"Content-Type": "application/json"},
            json=device_data
        )
        
        if response.status_code == 201:
            data = response.json()
            device_info = data.get("device", {})
            api_key = device_info.get("api_key")
            device_id = device_info.get("id")
            device_name = device_info.get("name")
            
            print(f"✅ Device created successfully!")
            print(f"   Device ID: {device_id}")
            print(f"   Device Name: {device_name}")
            print(f"   API Key: {api_key}")
            
            return api_key, device_id
        else:
            print(f"❌ Failed to create device: {response.status_code}")
            print(f"Response: {response.text}")
            return None, None
            
    except Exception as e:
        print(f"❌ Error creating device: {e}")
        return None, None

def main():
    print("🔧 Creating test device for telemetry testing...")
    
    api_key, device_id = create_test_device()
    
    if api_key:
        print(f"\n📝 You can now test telemetry with:")
        print(f"   API Key: {api_key}")
        print(f"   Device ID: {device_id}")
        print(f"\n🚀 Test command:")
        print(f"   poetry run python send_telemetry_cli.py")
        print(f"   # (Update the API key in the script)")
    else:
        print("❌ Could not create test device")

if __name__ == "__main__":
    main()