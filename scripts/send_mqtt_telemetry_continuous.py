#!/usr/bin/env python3
"""
Send Continuous MQTT Telemetry Messages

Enhanced script to send continuous telemetry messages via MQTT with random values.
Sends one telemetry message every second with random temperature values between 10-30°C.

Usage:
    python scripts/send_mqtt_telemetry_continuous.py <device_id> <api_key> [duration_seconds] [mqtt_host] [mqtt_port]
    
Examples:
    # Send for 60 seconds (default)
    python scripts/send_mqtt_telemetry_continuous.py 1 08ee241945400107854d1fb32a04773b6de6e3e12b26c6457ea2e4f2da4d91a2
    
    # Send for 120 seconds
    python scripts/send_mqtt_telemetry_continuous.py 1 08ee241945400107854d1fb32a04773b6de6e3e12b26c6457ea2e4f2da4d91a2 120
    
    # Send indefinitely (use Ctrl+C to stop)
    python scripts/send_mqtt_telemetry_continuous.py 1 08ee241945400107854d1fb32a04773b6de6e3e12b26c6457ea2e4f2da4d91a2 0
"""

import sys
import json
import time
import random
import signal
from datetime import datetime, timezone

try:
    import paho.mqtt.client as mqtt
    MQTT_AVAILABLE = True
except ImportError:
    print("❌ Error: paho-mqtt not installed")
    print("Install with: pip install paho-mqtt")
    sys.exit(1)


class ContinuousTelemetrySender:
    def __init__(self, device_id, api_key, mqtt_host="4.251.155.59", mqtt_port=1883):
        self.device_id = device_id
        self.api_key = api_key
        self.mqtt_host = mqtt_host
        self.mqtt_port = mqtt_port
        self.connected = False
        self.running = True
        self.message_count = 0
        self.failed_count = 0
        
        # Setup signal handler for graceful shutdown
        signal.signal(signal.SIGINT, self.signal_handler)
        signal.signal(signal.SIGTERM, self.signal_handler)
        
        # Create MQTT client
        self.client = mqtt.Client(client_id=f"continuous_sender_{device_id}_{int(time.time())}")
        self.client.on_connect = self.on_connect
        self.client.on_publish = self.on_publish
        self.client.on_disconnect = self.on_disconnect
        
    def signal_handler(self, signum, frame):
        """Handle Ctrl+C gracefully"""
        print(f"\n🛑 Received signal {signum}, shutting down gracefully...")
        self.running = False
        
    def on_connect(self, client, userdata, flags, rc):
        if rc == 0:
            print("✅ Connected to MQTT broker")
            self.connected = True
        else:
            print(f"❌ Connection failed with code {rc}")
    
    def on_publish(self, client, userdata, mid):
        # Don't print for every message to avoid spam
        pass
    
    def on_disconnect(self, client, userdata, rc):
        print(f"📡 Disconnected from MQTT broker (code: {rc})")
        self.connected = False
    
    def generate_random_telemetry(self):
        """Generate random telemetry data with integer temperature values between 10-30°C"""
        current_time = datetime.now(timezone.utc)
        
        telemetry_data = {
            "data": {
                "temperature": random.randint(10, 30)
            },
            "metadata": {
                "source": "continuous_mqtt_sender",
                "message_id": self.message_count + 1,
                "api_key": self.api_key
            },
            "timestamp": current_time.isoformat(),
            "api_key": self.api_key
        }
        
        return telemetry_data
    
    def connect(self):
        """Connect to MQTT broker"""
        try:
            print("🔌 Connecting to MQTT broker...")
            self.client.connect(self.mqtt_host, self.mqtt_port, 60)
            self.client.loop_start()
            
            # Wait for connection
            timeout = 10
            start = time.time()
            while not self.connected and (time.time() - start) < timeout and self.running:
                time.sleep(0.1)
            
            if not self.connected:
                print("❌ Connection timeout")
                return False
                
            return True
            
        except Exception as e:
            print(f"❌ Connection error: {e}")
            return False
    
    def send_continuous_telemetry(self, duration_seconds=60):
        """Send continuous telemetry messages"""
        
        print("🚀 Continuous MQTT Telemetry Sender")
        print("=" * 60)
        print(f"📡 Device ID: {self.device_id}")
        print(f"🔑 API Key: {self.api_key[:20]}...")
        print(f"🌐 MQTT Broker: {self.mqtt_host}:{self.mqtt_port}")
        print(f"⏱️  Duration: {'Indefinite (Ctrl+C to stop)' if duration_seconds == 0 else f'{duration_seconds} seconds'}")
        print(f"📊 Temperature Range: 10°C - 30°C (integers)")
        print(f"🔄 Interval: 1 second")
        print("=" * 60)
        print()
        
        if not self.connect():
            return False
        
        topic = f"iotflow/devices/{self.device_id}/telemetry"
        start_time = time.time()
        last_message_time = 0
        
        print("📤 Starting telemetry transmission...")
        print("Press Ctrl+C to stop")
        print()
        
        try:
            while self.running:
                current_time = time.time()
                
                # Check if we should stop (duration limit)
                if duration_seconds > 0 and (current_time - start_time) >= duration_seconds:
                    print(f"\n⏰ Duration limit reached ({duration_seconds}s)")
                    break
                
                # Send message every second
                if current_time - last_message_time >= 1.0:
                    if not self.connected:
                        print("⚠️  Connection lost, attempting to reconnect...")
                        if not self.connect():
                            print("❌ Reconnection failed")
                            break
                    
                    # Generate and send telemetry
                    telemetry_data = self.generate_random_telemetry()
                    
                    try:
                        result = self.client.publish(
                            topic,
                            json.dumps(telemetry_data),
                            qos=1
                        )
                        
                        if result.rc == mqtt.MQTT_ERR_SUCCESS:
                            self.message_count += 1
                            temp = telemetry_data['data']['temperature']
                            timestamp = datetime.now().strftime("%H:%M:%S")
                            
                            # Print progress every 10 messages or show individual messages for first 5
                            if self.message_count <= 5 or self.message_count % 10 == 0:
                                print(f"📊 [{timestamp}] Message #{self.message_count}: T={temp}°C")
                            elif self.message_count % 10 == 1 and self.message_count > 5:
                                print(f"📊 [{timestamp}] Messages #{self.message_count}-{self.message_count+9}...")
                        else:
                            self.failed_count += 1
                            print(f"❌ Failed to publish message #{self.message_count + 1}")
                            
                    except Exception as e:
                        self.failed_count += 1
                        print(f"❌ Error publishing message: {e}")
                    
                    last_message_time = current_time
                
                # Small sleep to prevent busy waiting
                time.sleep(0.1)
                
        except KeyboardInterrupt:
            print(f"\n🛑 Interrupted by user")
        
        # Cleanup
        print(f"\n📊 Stopping telemetry transmission...")
        self.client.loop_stop()
        self.client.disconnect()
        
        # Summary
        total_time = time.time() - start_time
        print("\n" + "=" * 60)
        print("📈 TRANSMISSION SUMMARY")
        print("=" * 60)
        print(f"⏱️  Total Duration: {total_time:.1f} seconds")
        print(f"✅ Messages Sent: {self.message_count}")
        print(f"❌ Failed Messages: {self.failed_count}")
        print(f"📊 Success Rate: {(self.message_count/(self.message_count + self.failed_count)*100) if (self.message_count + self.failed_count) > 0 else 0:.1f}%")
        print(f"🔄 Average Rate: {self.message_count/total_time:.2f} messages/second")
        print("=" * 60)
        
        return self.message_count > 0


def main():
    """Main function"""
    if len(sys.argv) < 3:
        print("Usage: python send_mqtt_telemetry_continuous.py <device_id> <api_key> [duration_seconds] [mqtt_host] [mqtt_port]")
        print()
        print("Parameters:")
        print("  device_id        - Device ID to send telemetry for")
        print("  api_key          - Device API key for authentication")
        print("  duration_seconds - Duration in seconds (default: 60, use 0 for indefinite)")
        print("  mqtt_host        - MQTT broker host (default: 4.251.155.59)")
        print("  mqtt_port        - MQTT broker port (default: 1883)")
        print()
        print("Examples:")
        print("  # Send for 60 seconds (default)")
        print("  python scripts/send_mqtt_telemetry_continuous.py 1 08ee241945400107854d1fb32a04773b6de6e3e12b26c6457ea2e4f2da4d91a2")
        print()
        print("  # Send for 120 seconds")
        print("  python scripts/send_mqtt_telemetry_continuous.py 1 08ee241945400107854d1fb32a04773b6de6e3e12b26c6457ea2e4f2da4d91a2 120")
        print()
        print("  # Send indefinitely (Ctrl+C to stop)")
        print("  python scripts/send_mqtt_telemetry_continuous.py 1 08ee241945400107854d1fb32a04773b6de6e3e12b26c6457ea2e4f2da4d91a2 0")
        sys.exit(1)
    
    device_id = sys.argv[1]
    api_key = sys.argv[2]
    duration_seconds = int(sys.argv[3]) if len(sys.argv) > 3 else 60
    mqtt_host = sys.argv[4] if len(sys.argv) > 4 else "4.251.155.59"
    mqtt_port = int(sys.argv[5]) if len(sys.argv) > 5 else 1883
    
    # Create sender and start transmission
    sender = ContinuousTelemetrySender(device_id, api_key, mqtt_host, mqtt_port)
    success = sender.send_continuous_telemetry(duration_seconds)
    
    if success:
        print("🎉 Telemetry transmission completed successfully!")
        print()
        print("You can verify by:")
        print("  1. Check the device status in the dashboard")
        print("  2. Query device status via API")
        print("  3. Check MQTT broker metrics")
        return 0
    else:
        print("❌ Telemetry transmission failed")
        return 1


if __name__ == "__main__":
    sys.exit(main())