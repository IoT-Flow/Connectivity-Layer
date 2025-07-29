import json
import paho.mqtt.client as mqtt

MQTT_BROKER = 'localhost'  # Change to your broker address if needed
MQTT_PORT = 1883

mqtt_client = mqtt.Client()

# Connect to the MQTT broker (call this once at app startup)
def connect_mqtt():
    mqtt_client.connect(MQTT_BROKER, MQTT_PORT)
    mqtt_client.loop_start()

# Publish a control command to a device's MQTT topic
def publish_device_command(device_id, command, parameters=None):
    topic = f"devices/{device_id}/control"
    payload = {
        "command": command,
        "parameters": parameters or {}
    }
    mqtt_client.publish(topic, json.dumps(payload))
