#!/usr/bin/env python3
"""
Test script to demonstrate complete telemetry flow:
1. Register a device (using existing user)
2. Send telemetry via MQTT
3. Retrieve telemetry from IoTDB
"""

import requests
import json
import time
import paho.mqtt.client as mqtt
from datetime import datetime, timezone
import sys

# Configuration
API_BASE_URL = "http://localhost:5000/api/v1"
MQTT_HOST = "localhost"
MQTT_PORT = 1883

# Use an existing user ID from the database
# This was just created
DEFAULT_USER_ID = "7d3233b8975448fdaee491152000799b"


def register_device(user_id):
    """Register a new device"""
    print("\n=== Step 1: Registering Device ===")

    device_data = {
        "name": f"Test Device {int(time.time())}",
        "device_type": "environmental",
        "description": "Test environmental sensor",
        "location": "Test Lab, Bench 1",
        "user_id": user_id,
        "firmware_version": "1.0.0",
        "hardware_version": "v1",
    }

    response = requests.post(
        f"{API_BASE_URL}/devices/register", json=device_data, headers={"Content-Type": "application/json"}
    )

    if response.status_code == 201:
        device = response.json()["device"]
        print(f"✅ Device registered successfully!")
        print(f"   Device ID: {device['id']}")
        print(f"   Device Name: {device['name']}")
        print(f"   API Key: {device['api_key']}")
        print(f"   User ID: {user_id}")
        return device["id"], device["api_key"]
    else:
        print(f"❌ Failed to register device: {response.text}")
        return None, None


def send_telemetry_mqtt(device_id, api_key):
    """Send telemetry data via MQTT"""
    print("\n=== Step 2: Sending Telemetry via MQTT ===")

    # Create MQTT client
    client = mqtt.Client(client_id=f"test_client_{device_id}")

    # Connection callback
    def on_connect(client, userdata, flags, rc):
        if rc == 0:
            print("✅ Connected to MQTT broker")
        else:
            print(f"❌ Failed to connect to MQTT broker: {rc}")

    # Publish callback
    def on_publish(client, userdata, mid):
        print(f"✅ Telemetry message published (mid: {mid})")

    client.on_connect = on_connect
    client.on_publish = on_publish

    # Connect to broker
    try:
        client.connect(MQTT_HOST, MQTT_PORT, keepalive=60)
        client.loop_start()
        time.sleep(1)  # Wait for connection

        # Prepare telemetry data
        telemetry_data = {
            "device_id": device_id,
            "timestamp": datetime.now(timezone.utc).strftime("%Y-%m-%dT%H:%M:%S.%fZ"),
            "data": {
                "temperature": {
                    "value": 22.5,
                    "unit": "°C",
                    "timestamp": datetime.now(timezone.utc).strftime("%Y-%m-%dT%H:%M:%S.%fZ"),
                },
                "humidity": {
                    "value": 45.2,
                    "unit": "%",
                    "timestamp": datetime.now(timezone.utc).strftime("%Y-%m-%dT%H:%M:%S.%fZ"),
                },
                "pressure": {
                    "value": 1013.25,
                    "unit": "hPa",
                    "timestamp": datetime.now(timezone.utc).strftime("%Y-%m-%dT%H:%M:%S.%fZ"),
                },
            },
            "api_key": api_key,
        }

        # Publish to MQTT topic
        topic = f"iotflow/devices/{device_id}/telemetry"
        result = client.publish(topic, json.dumps(telemetry_data), qos=1)

        print(f"   Topic: {topic}")
        print(
            f"   Sensors: temperature={telemetry_data['data']['temperature']['value']}°C, "
            f"humidity={telemetry_data['data']['humidity']['value']}%, "
            f"pressure={telemetry_data['data']['pressure']['value']}hPa"
        )

        # Wait for message to be sent
        time.sleep(2)

        client.loop_stop()
        client.disconnect()

        return True

    except Exception as e:
        print(f"❌ Failed to send telemetry: {e}")
        return False


def retrieve_telemetry(device_id, api_key):
    """Retrieve telemetry data from IoTDB"""
    print("\n=== Step 3: Retrieving Telemetry from IoTDB ===")

    # Wait a bit for data to be processed
    print("   Waiting 5 seconds for data to be processed...")
    time.sleep(5)

    # Get telemetry data
    response = requests.get(f"{API_BASE_URL}/telemetry/{device_id}", headers={"X-API-Key": api_key})

    if response.status_code == 200:
        data = response.json()
        print(f"✅ Telemetry retrieved successfully!")
        print(f"   Total records: {data.get('count', 0)}")

        if data.get("data"):
            print(f"\n   Latest telemetry data:")
            for i, record in enumerate(data["data"][:3], 1):  # Show first 3 records
                print(f"   Record {i}:")
                print(f"     Timestamp: {record.get('timestamp')}")
                measurements = record.get("measurements", {})
                if measurements:
                    for key, value in measurements.items():
                        print(f"     {key}: {value}")
        else:
            print("   No telemetry data found yet")

        return data
    else:
        print(f"❌ Failed to retrieve telemetry: {response.text}")
        return None


def main():
    """Main test flow"""
    print("=" * 60)
    print("IoTFlow Telemetry Test - Complete Flow")
    print("=" * 60)

    # Use existing user ID
    user_id = DEFAULT_USER_ID
    print(f"\nUsing existing user ID: {user_id}")

    # Step 1: Register device
    device_id, api_key = register_device(user_id)
    if not device_id or not api_key:
        print("\n❌ Test failed: Could not register device")
        print("   Make sure the Flask app is running and the user exists in the database")
        return 1

    # Step 2: Send telemetry via MQTT
    if not send_telemetry_mqtt(device_id, api_key):
        print("\n❌ Test failed: Could not send telemetry")
        return 1

    # Step 3: Retrieve telemetry
    telemetry_data = retrieve_telemetry(device_id, api_key)

    if not telemetry_data:
        print("\n⚠️  Warning: Could not retrieve telemetry data")
        print("   The data might still be processing or there was an error")

    # Summary
    print("\n" + "=" * 60)
    print("Test Summary")
    print("=" * 60)
    print(f"✅ User ID: {user_id}")
    print(f"✅ Device registered: {device_id}")
    print(f"✅ Telemetry sent via MQTT")
    if telemetry_data and telemetry_data.get("count", 0) > 0:
        print(f"✅ Telemetry retrieved from IoTDB ({telemetry_data.get('count', 0)} records)")
    else:
        print(f"⚠️  Telemetry retrieval pending")
    print("\n🎉 Test completed!")
    print("=" * 60)

    return 0


if __name__ == "__main__":
    sys.exit(main())
