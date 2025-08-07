"""
MQTT Authentication Service
Handles server-side device authentication for MQTT connections and message authorization
Note: MQTT broker allows anonymous connections, all authentication happens server-side
"""

import logging
import hashlib
import json
from typing import Optional, Dict, Any
from datetime import datetime, timezone

from ..models import Device, DeviceAuth, db
from ..services.iotdb import IoTDBService
from ..utils.time_util import TimestampFormatter, parse_device_timestamp, format_timestamp_for_storage

logger = logging.getLogger(__name__)


class MQTTAuthService:
    """Service for handling server-side MQTT device authentication and authorization"""
    
    def __init__(self, iotdb_service: Optional[IoTDBService] = None, app=None):
        self.iotdb_service = iotdb_service or IoTDBService()
        self.authenticated_devices = {}  # Cache for authenticated devices
        self.app = app  # Flask app instance for context
        
    def authenticate_device_by_api_key(self, api_key: str) -> Optional[Device]:
        """
        Authenticate device using API key for server-side validation
        This is called when processing MQTT messages server-side
        """
        if not self.app:
            logger.error("No Flask app instance available for database operations")
            return None
            
        try:
            with self.app.app_context():
                # Find device by API key (allow inactive devices for now)
                device = Device.query.filter_by(api_key=api_key).first()
                
                if not device:
                    logger.warning("Device not found for API key: %s...", api_key[:8])
                    return None
                
                # Log device status for debugging
                logger.info("Authenticating device %d (%s) with status: %s", device.id, device.name, device.status)
                    
                # Update last seen (this also updates Redis cache via the device model)
                device.update_last_seen()
                
                # Cache authenticated device
                self.authenticated_devices[device.id] = device
                
                # Also update device status in Redis directly
                if hasattr(self.app, 'device_status_cache') and self.app.device_status_cache:
                    self.app.device_status_cache.set_device_status(device.id, 'online')
                
                logger.info("Device authenticated successfully: %s (ID: %d)", device.name, device.id)
                return device
                
        except Exception as e:
            logger.error("Error authenticating device by API key: %s", e)
            return None
    
    def validate_device_message(self, device_id: int, api_key: str, topic: str) -> Optional[Device]:
        """
        Validate that a device is authorized to publish to a specific topic
        Returns the device if validation passes, None otherwise
        """
        try:
            # First authenticate the device by API key
            device = self.authenticate_device_by_api_key(api_key)
            if not device or device.id != device_id:
                logger.warning("API key validation failed for device_id %d", device_id)
                return None
            
            # Check topic authorization
            if not self.is_device_authorized(device_id, topic):
                logger.warning("Device %d not authorized for topic: %s", device_id, topic)
                return None
                
            return device
            
        except Exception as e:
            logger.error("Error validating device message: %s", e)
            return None
    
    def is_device_authorized(self, device_id: int, topic: str) -> bool:
        """
        Check if device is authorized to publish/subscribe to a topic
        """
        try:
            # Check if device is authenticated (allow inactive devices for now)
            device = self.authenticated_devices.get(device_id)
            if not device:
                device = Device.query.filter_by(id=device_id).first()  # Remove status='active' filter
                if not device:
                    return False
                self.authenticated_devices[device_id] = device
                logger.info("Device %d (%s) authorized for topic: %s", device_id, device.name, topic)
            
            # Basic topic authorization rules
            # Devices can publish to their own telemetry topics
            allowed_publish_topics = [
                f"iotflow/devices/{device_id}/telemetry",
                f"iotflow/devices/{device_id}/status",
                f"iotflow/devices/{device_id}/heartbeat"
            ]
            
            # Devices can subscribe to their own command topics
            allowed_subscribe_topics = [
                f"iotflow/devices/{device_id}/commands",
                f"iotflow/devices/{device_id}/config"
            ]
            
            # Check if exact match
            if topic in allowed_publish_topics or topic in allowed_subscribe_topics:
                return True
                
            # Check for telemetry subtopics (like telemetry/sensors)
            if topic.startswith(f"iotflow/devices/{device_id}/telemetry/"):
                return True
                
            # Check for status subtopics (like status/online)
            if topic.startswith(f"iotflow/devices/{device_id}/status/"):
                return True
                
            return False
        except Exception as e:
            logger.error(f"Error checking device authorization: {e}")
            return False
    
    def handle_telemetry_message(self, device_id: int, api_key: str, topic: str, payload: str) -> bool:
        """
        Handle incoming telemetry message from device with server-side authentication
        Store data only in IoTDB
        """
        if not self.app:
            logger.error("No Flask app instance available for telemetry processing")
            return False
            
        try:
            with self.app.app_context():
                # First, validate device registration
                is_registered, reg_message = self.validate_device_registration(device_id, api_key)
                if not is_registered:
                    logger.warning(f"Device registration validation failed for device {device_id}: {reg_message}")
                    return False
                
                # Parse JSON payload
                try:
                    data = json.loads(payload)
                except json.JSONDecodeError:
                    logger.error("Invalid JSON payload from device %d: %s", device_id, payload)
                    return False
                
                # Validate device and authorization using payload data
                is_authorized, auth_message, device = self.is_device_registered_for_mqtt(data)
                if not is_authorized:
                    logger.warning(f"Device MQTT authorization failed for device {device_id}: {auth_message}")
                    return False
                
                # Validate device and authorization
                device = self.validate_device_message(device_id, api_key, topic)
                if not device:
                    logger.warning("Unauthorized telemetry attempt from device_id %d", device_id)
                    return False
                
                # Handle both structured and flat data formats
                telemetry_data = {}
                metadata = {}
                timestamp = None
                timestamp_str = None
                
                # Check if data has the expected structure with 'data' field
                if 'data' in data:
                    # Structured format
                    telemetry_data = data.get('data', {})
                    metadata = data.get('metadata', {})
                    timestamp_str = data.get('timestamp')
                else:
                    # Flat format (all fields at root level)
                    # Copy payload data excluding api_key
                    telemetry_data = {k: v for k, v in data.items() if k != 'api_key'}
                    
                    # Look for timestamp in ts or timestamp fields
                    timestamp_str = data.get('timestamp') or data.get('ts')
                    
                    # Include device_type in metadata
                    metadata = {'device_type': device.device_type}
                
                # Check if we have any telemetry data
                if not telemetry_data:
                    logger.warning("No telemetry data extracted from message for device %d", device_id)
                    return False
                
                # Parse timestamp if provided
                # The timestamp formatter handles various formats from different devices:
                # - ISO: "2025-08-07T14:30:15Z", "2025-08-07T14:30:15"
                # - Epoch: "1723034415", 1723034415123 (seconds/milliseconds)
                # - Readable: "2025-08-07 14:30:15", "08/07/2025 14:30:15"
                # - And more formats that real IoT devices might send
                if timestamp_str:
                    timestamp = parse_device_timestamp(timestamp_str)
                    if timestamp:
                        logger.debug(f"Parsed timestamp for device {device_id}: {format_timestamp_for_storage(timestamp)}")
                    else:
                        logger.warning(f"Failed to parse timestamp from device {device_id}: {timestamp_str}")
                        # Use current time as fallback
                        timestamp = TimestampFormatter.get_current_utc()
                
                # Log what we're processing
                logger.debug(f"Processing telemetry for device {device_id}: {telemetry_data}")
                
                # Store in IoTDB
                success = self.iotdb_service.write_telemetry_data(
                    device_id=str(device_id),
                    data=telemetry_data,
                    device_type=device.device_type,
                    metadata=metadata,
                    timestamp=timestamp,
                    user_id=device.user_id
                )
                
                if success:                # Update device last seen and also update Redis cache
                    device.update_last_seen()
                
                # Update device status in Redis cache directly if available
                if hasattr(self.app, 'device_status_cache') and self.app.device_status_cache:
                    self.app.device_status_cache.update_device_last_seen(device_id)
                    self.app.device_status_cache.set_device_status(device_id, 'online')
                
                    logger.info("Telemetry stored in IoTDB for device %s (ID: %d)", device.name, device_id)
                    return True
                else:
                    logger.error("Failed to store telemetry in IoTDB for device %d", device_id)
                    return False
                    
        except Exception as e:
            logger.error("Error handling telemetry message: %s", e)
            return False
    
    def get_device_credentials(self, device_id: int) -> Optional[Dict[str, str]]:
        """
        Get MQTT credentials for a device
        Returns dict with username (device_id) and password (api_key)
        """
        try:
            device = Device.query.filter_by(id=device_id, status='active').first()
            if device:
                return {
                    'username': str(device.id),
                    'password': device.api_key,
                    'client_id': f"device_{device.id}_{device.name.replace(' ', '_')}"
                }
            return None
        except Exception as e:
            logger.error(f"Error getting device credentials: {e}")
            return None
    
    def revoke_device_access(self, device_id: int):
        """
        Revoke access for a device (remove from authenticated devices cache)
        """
        if device_id in self.authenticated_devices:
            del self.authenticated_devices[device_id]
            logger.info(f"Revoked access for device {device_id}")
    
    def cleanup_inactive_devices(self):
        """
        Clean up authenticated devices cache for inactive devices
        """
        try:
            active_device_ids = set()
            for device_id in list(self.authenticated_devices.keys()):
                device = Device.query.filter_by(id=device_id, status='active').first()
                if device:
                    active_device_ids.add(device_id)
                else:
                    del self.authenticated_devices[device_id]
            
            logger.info(f"Cleaned up inactive devices. Active: {len(active_device_ids)}")
            
        except Exception as e:
            logger.error(f"Error cleaning up inactive devices: {e}")
    
    def validate_device_registration(self, device_id: int, api_key: str) -> tuple[bool, str]:
        """
        Validate that device is properly registered before allowing MQTT communication
        Returns (is_valid, message)
        """
        if not self.app:
            return False, "No Flask app context available"
        
        try:
            with self.app.app_context():
                # Check if device exists (allow inactive devices for now)
                device = Device.query.filter_by(id=device_id, api_key=api_key).first()
                
                if not device:
                    logger.warning(f"Device registration validation failed: Device {device_id} not found with provided API key")
                    return False, "Device not found or invalid API key"
                
                # Log device status but don't reject inactive devices
                if device.status != 'active':
                    logger.info(f"Device {device_id} has status '{device.status}' but allowing MQTT communication")
                
                # Update last seen timestamp
                device.update_last_seen()
                
                logger.info(f"Device registration validation successful for device {device_id} (status: {device.status})")
                return True, "Device validated successfully"
                
        except Exception as e:
            logger.error(f"Error validating device registration: {e}")
            return False, f"Validation error: {str(e)}"
    
    def is_device_registered_for_mqtt(self, payload: dict) -> tuple[bool, str, Optional[Device]]:
        """
        Check if device is registered and authorized to send MQTT data
        Returns (is_authorized, message, device)
        """
        try:
            # Extract device info from payload
            api_key = payload.get('api_key')
            if not api_key:
                return False, "Missing API key in message payload", None
            
            # Get device from database
            device = self.authenticate_device_by_api_key(api_key)
            if not device:
                return False, "Invalid API key or device not found", None
            
            # No additional validation needed since authenticate_device_by_api_key already validates
            logger.info(f"Device {device.id} ({device.name}) authorized for MQTT communication")
            return True, "Device authorized for MQTT communication", device
            
        except Exception as e:
            logger.error(f"Error checking device MQTT authorization: {e}")
            return False, f"Authorization check failed: {str(e)}", None
