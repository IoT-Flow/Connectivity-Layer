import json
import os
import paho.mqtt.client as mqtt
import logging
import time
from src.config.config import Config

# Use configuration values instead of hardcoded ones
MQTT_BROKER = Config.MQTT_HOST
MQTT_PORT = Config.MQTT_PORT

mqtt_client = mqtt.Client()
logger = logging.getLogger(__name__)


# Connect to the MQTT broker (call this once at app startup)
def connect_mqtt():
    """Connect to MQTT broker with retry logic for containerized environments"""
    # Skip connection in testing mode
    if os.getenv('TESTING', 'false').lower() == 'true':
        logger.info("Skipping MQTT connection in testing mode")
        return
        
    max_retries = 10
    retry_delay = 2

    for attempt in range(max_retries):
        try:
            logger.info(
                f"Attempting to connect to MQTT broker {MQTT_BROKER}:{MQTT_PORT} (attempt {attempt + 1}/{max_retries})"
            )
            mqtt_client.connect(MQTT_BROKER, MQTT_PORT)
            mqtt_client.loop_start()
            logger.info("Successfully connected to MQTT broker")
            return
        except Exception as e:
            logger.warning(f"Failed to connect to MQTT broker: {e}")
            if attempt < max_retries - 1:
                logger.info(f"Retrying in {retry_delay} seconds...")
                time.sleep(retry_delay)
                retry_delay = min(retry_delay * 2, 30)  # Exponential backoff, max 30s
            else:
                logger.error("Max retries exceeded. MQTT connection failed.")
                raise


# Publish a control command to a device's MQTT topic
def publish_device_command(device_id, command, parameters=None):
    topic = f"devices/{device_id}/control"
    payload = {"command": command, "parameters": parameters or {}}
    mqtt_client.publish(topic, json.dumps(payload))
