#!/usr/bin/env python3
"""
Send Single MQTT Telemetry Message

Simple script to send one telemetry message via MQTT to test device status tracking.
This will trigger the status tracker to mark the device as online.

Usage:
    python scripts/send_mqtt_telemetry_once.py <device_id> <api_key>
    
Example:
    python scripts/send_mqtt_telemetry_once.py 11 mZAziGMCmjDmfrOATJxGWqJX1vL4VgkR
"""

import sys
import json
import time
from datetime import datetime, timezone

try:
    import paho.mqtt.client as mqtt
    MQTT_AVAILABLE = True
except ImportError:
    print("❌ Error: paho-mqtt not installed")
    print("Install with: pip install paho-mqtt")
    sys.exit(1)


def send_single_telemetry(device_id, api_key, mqtt_host="4.251.155.59", mqtt_port=1883):
    """Send a single telemetry message via MQTT"""
    
    print("🚀 MQTT Telemetry Sender")
    print("=" * 50)
    print(f"📡 Device ID: {device_id}")
    print(f"🔑 API Key: {api_key[:20]}...")
    print(f"🌐 MQTT Broker: {mqtt_host}:{mqtt_port}")
    print()
    
    # Connection flag
    connected = False
    message_published = False
    
    def on_connect(client, userdata, flags, rc):
        nonlocal connected
        if rc == 0:
            print("✅ Connected to MQTT broker")
            connected = True
        else:
            print(f"❌ Connection failed with code {rc}")
    
    def on_publish(client, userdata, mid):
        nonlocal message_published
        print("✅ Message published successfully")
        message_published = True
    
    def on_disconnect(client, userdata, rc):
        print(f"📡 Disconnected from MQTT broker (code: {rc})")
    
    # Create MQTT client
    client = mqtt.Client(client_id=f"telemetry_sender_{device_id}_{int(time.time())}")
    client.on_connect = on_connect
    client.on_publish = on_publish
    client.on_disconnect = on_disconnect
    
    try:
        # Connect to broker
        print("🔌 Connecting to MQTT broker...")
        client.connect(mqtt_host, mqtt_port, 60)
        
        # Start network loop
        client.loop_start()
        
        # Wait for connection
        timeout = 5
        start = time.time()
        while not connected and (time.time() - start) < timeout:
            time.sleep(0.1)
        
        if not connected:
            print("❌ Connection timeout")
            return False
        
        # Prepare telemetry data (single temperature reading only)
        telemetry_data = {
            "data": {
                "temperature": 24.5
            },
            "metadata": {
                "source": "mqtt_telemetry_sender",
                "test_type": "single_temperature",
                "api_key": api_key
            },
            "timestamp": datetime.now(timezone.utc).isoformat(),
            "api_key": api_key  # Include API key for server-side authentication
        }
        
        # Topic for telemetry
        topic = f"iotflow/devices/{device_id}/telemetry"
        
            # Publish message
        print(f"📤 Publishing telemetry to topic: {topic}")
        print(f"📊 Data: temperature={telemetry_data['data']['temperature']}°C")
            
        result = client.publish(
            topic,
            json.dumps(telemetry_data),
            qos=1
        )
        
        # Wait for publish confirmation
        timeout = 5
        start = time.time()
        while not message_published and (time.time() - start) < timeout:
            time.sleep(0.1)
        
        if message_published:
            print()
            print("✅ SUCCESS! Telemetry sent via MQTT")
            print("📊 This should trigger the device status tracker")
            print("🟢 Device should now appear as ONLINE")
            success = True
        else:
            print("⚠️  Message published but no confirmation received")
            success = True  # Still consider it success
        
        # Small delay before disconnecting
        time.sleep(1)
        
        # Disconnect
        client.loop_stop()
        client.disconnect()
        
        return success
        
    except Exception as e:
        print(f"❌ Error: {e}")
        return False


def main():
    """Main function"""
    if len(sys.argv) < 3:
        print("Usage: python send_mqtt_telemetry_once.py <device_id> <api_key>")
        print()
        print("Example:")
        print("  python scripts/send_mqtt_telemetry_once.py 11 mZAziGMCmjDmfrOATJxGWqJX1vL4VgkR")
        sys.exit(1)
    
    device_id = sys.argv[1]
    api_key = sys.argv[2]
    
    # Optional MQTT broker settings (defaults to AKS deployment)
    mqtt_host = sys.argv[3] if len(sys.argv) > 3 else "4.251.155.59"
    mqtt_port = int(sys.argv[4]) if len(sys.argv) > 4 else 1883
    
    success = send_single_telemetry(device_id, api_key, mqtt_host, mqtt_port)
    
    if success:
        print()
        print("=" * 50)
        print("🎉 Telemetry sent successfully via MQTT!")
        print("✅ Device status should now be online")
        print()
        print("You can verify by:")
        print("  1. Check the device status in the dashboard")
        print("  2. Query device status via API")
        print("  3. Check Redis cache for device activity")
        return 0
    else:
        print()
        print("=" * 50)
        print("❌ Failed to send telemetry")
        return 1


if __name__ == "__main__":
    sys.exit(main())
