from flask import Blueprint, request, jsonify, current_app
from src.models import Device, DeviceConfiguration, User, db
from src.middleware.auth import (
    authenticate_device,
    validate_json_payload,
    rate_limit_device,
)
from src.middleware.monitoring import (
    device_heartbeat_monitor,
    request_metrics_middleware,
)
from src.middleware.security import (
    security_headers_middleware,
    input_sanitization_middleware,
)
from src.services.iotdb import IoTDBService
from datetime import datetime, timezone
import json

# Create blueprint for device routes
device_bp = Blueprint("devices", __name__, url_prefix="/api/v1/devices")

# Initialize IoTDB service for telemetry queries
iotdb_service = IoTDBService()


@device_bp.route("/register", methods=["POST"])
@security_headers_middleware()
@request_metrics_middleware()
@rate_limit_device(max_requests=10, window=300, per_device=False)  # 10 registrations per 5 minutes per IP
@validate_json_payload(["name", "device_type", "user_id"])
@input_sanitization_middleware()
def register_device():
    """Register a new IoT device with user_id authentication"""
    try:
        data = request.validated_json

        # Verify user by user_id
        user_id = data["user_id"]

        user = User.query.filter_by(user_id=user_id, is_active=True).first()
        if not user:
            return (
                jsonify(
                    {
                        "error": "Authentication failed",
                        "message": "Invalid user_id or user is not active",
                    }
                ),
                401,
            )

        # Check if device name already exists
        existing_device = Device.query.filter_by(name=data["name"]).first()
        if existing_device:
            return (
                jsonify(
                    {
                        "error": "Device name already exists",
                        "message": "Please choose a different device name",
                    }
                ),
                409,
            )

        # Create new device associated with the authenticated user
        device = Device(
            name=data["name"],
            description=data.get("description", ""),
            device_type=data["device_type"],
            location=data.get("location", ""),
            firmware_version=data.get("firmware_version", ""),
            hardware_version=data.get("hardware_version", ""),
            user_id=user.id,  # Associate device with authenticated user
        )

        db.session.add(device)
        db.session.commit()

        current_app.logger.info(f"New device registered: {device.name} (ID: {device.id}) by user: {user.username}")

        response_data = device.to_dict()
        response_data["api_key"] = device.api_key  # Include API key in registration response
        response_data["owner"] = {"username": user.username, "email": user.email}

        return (
            jsonify({"message": "Device registered successfully", "device": response_data}),
            201,
        )

    except Exception as e:
        db.session.rollback()
        current_app.logger.error(f"Error registering device: {str(e)}")
        return (
            jsonify(
                {
                    "error": "Registration failed",
                    "message": "An error occurred while registering the device",
                }
            ),
            500,
        )


@device_bp.route("/status", methods=["GET"])
@security_headers_middleware()
@request_metrics_middleware()
@authenticate_device
@device_heartbeat_monitor()
def get_device_status():
    """Get current device status"""
    try:
        device = request.device

        # Get telemetry count from IoTDB
        telemetry_count = 0
        try:
            # Query IoTDB for telemetry count (simplified)
            telemetry_data = iotdb_service.get_device_telemetry(
                device_id=str(device.id),
                start_time="-30d",  # Last 30 days
                limit=1,
                user_id=str(device.user_id) if device.user_id else None,
            )
            # This is a simplified count - in practice you might want a proper count query
            telemetry_count = len(telemetry_data) if telemetry_data else 0
        except Exception as e:
            current_app.logger.warning(f"Failed to get telemetry count from IoTDB: {e}")

        response = device.to_dict()
        response["telemetry_count"] = telemetry_count

        # Check Redis cache for online/offline status first
        is_online = False

        # Try to get status from Redis cache
        if hasattr(current_app, "device_status_cache") and current_app.device_status_cache:
            cached_status = current_app.device_status_cache.get_device_status(device.id)
            if cached_status == "online":
                is_online = True
            elif cached_status == "offline":
                is_online = False
            else:
                # Fall back to database check if not in cache
                if device.last_seen:
                    # Ensure both datetimes are timezone-aware for comparison
                    now = datetime.now(timezone.utc)
                    last_seen = device.last_seen
                    if last_seen.tzinfo is None:
                        # If last_seen is naive, assume it's UTC
                        last_seen = last_seen.replace(tzinfo=timezone.utc)
                    is_online = (now - last_seen).total_seconds() < 300  # 5 minutes
        else:
            # Fall back to database check if Redis not available
            if device.last_seen:
                # Ensure both datetimes are timezone-aware for comparison
                now = datetime.now(timezone.utc)
                last_seen = device.last_seen
                if last_seen.tzinfo is None:
                    # If last_seen is naive, assume it's UTC
                    last_seen = last_seen.replace(tzinfo=timezone.utc)
                is_online = (now - last_seen).total_seconds() < 300  # 5 minutes

        response["is_online"] = is_online

        return jsonify({"status": "success", "device": response}), 200

    except Exception as e:
        current_app.logger.error(f"Error getting device status: {str(e)}")
        return (
            jsonify(
                {
                    "error": "Status retrieval failed",
                    "message": "An error occurred while retrieving device status",
                }
            ),
            500,
        )


@device_bp.route("/telemetry", methods=["POST"])
@security_headers_middleware()
@request_metrics_middleware()
@authenticate_device
@device_heartbeat_monitor()
@rate_limit_device(max_requests=100, window=60)  # 100 telemetry submissions per minute
@validate_json_payload(["data"])
@input_sanitization_middleware()
def submit_telemetry():
    """Submit telemetry data from device"""
    try:
        device = request.device
        data = request.validated_json

        # Validate payload structure
        telemetry_payload = data["data"]
        if not isinstance(telemetry_payload, dict):
            return (
                jsonify(
                    {
                        "error": "Invalid data format",
                        "message": "Telemetry data must be a JSON object",
                    }
                ),
                400,
            )

        # Store only in IoTDB
        timestamp = datetime.now(timezone.utc)

        # Store in IoTDB for time-series analysis
        iotdb_success = iotdb_service.write_telemetry_data(
            device_id=str(device.id),
            data=telemetry_payload,
            device_type=device.device_type,
            metadata=data.get("metadata", {}),
            timestamp=timestamp,
            user_id=str(device.user_id) if device.user_id else None,
        )

        if not iotdb_success:
            return (
                jsonify(
                    {
                        "error": "Telemetry storage failed",
                        "message": "Failed to store telemetry data in IoTDB",
                    }
                ),
                500,
            )

        # Update device last_seen
        device.update_last_seen()

        current_app.logger.info(f"Telemetry received from device {device.name} (ID: {device.id}) - " f"IoTDB: ✓")

        return (
            jsonify(
                {
                    "message": "Telemetry data received successfully",
                    "device_id": device.id,
                    "device_name": device.name,
                    "timestamp": timestamp.isoformat(),
                    "stored_in_iotdb": iotdb_success,
                }
            ),
            201,
        )

    except Exception as e:
        current_app.logger.error(f"Error submitting telemetry: {str(e)}")
        return (
            jsonify(
                {
                    "error": "Telemetry submission failed",
                    "message": "An error occurred while processing telemetry data",
                }
            ),
            500,
        )


@device_bp.route("/telemetry", methods=["GET"])
@authenticate_device
def get_telemetry():
    """Get telemetry data for device"""
    try:
        device = request.device

        # Parse query parameters
        limit = min(int(request.args.get("limit", 100)), 1000)  # Max 1000 records
        start_time = request.args.get("start_time", "-24h")  # Default to last 24 hours
        data_type = request.args.get("type")

        # Get telemetry data from IoTDB
        try:
            telemetry_data = iotdb_service.get_device_telemetry(
                device_id=str(device.id),
                start_time=start_time,
                limit=limit,
                user_id=str(device.user_id) if device.user_id else None,
            )

            # Filter by data type if specified (this would need to be implemented in IoTDB service)
            if data_type and telemetry_data:
                # Simple filtering - in practice this should be done in the IoTDB query
                telemetry_data = [record for record in telemetry_data if record.get("data_type") == data_type]

        except Exception as e:
            current_app.logger.error(f"Error querying IoTDB: {str(e)}")
            telemetry_data = []

        return (
            jsonify(
                {
                    "status": "success",
                    "telemetry": telemetry_data,
                    "count": len(telemetry_data),
                    "limit": limit,
                    "start_time": start_time,
                }
            ),
            200,
        )

    except Exception as e:
        current_app.logger.error(f"Error retrieving telemetry: {str(e)}")
        return (
            jsonify(
                {
                    "error": "Telemetry retrieval failed",
                    "message": "An error occurred while retrieving telemetry data",
                }
            ),
            500,
        )


@device_bp.route("/config", methods=["PUT"])
@authenticate_device
@validate_json_payload(["status"])
def update_device_info():
    """Update device information (status, location, versions)"""
    try:
        device = request.device
        data = request.validated_json

        # Update allowed fields
        if "status" in data and data["status"] in ["active", "inactive", "maintenance"]:
            device.status = data["status"]

        if "location" in data:
            device.location = data["location"]

        if "firmware_version" in data:
            device.firmware_version = data["firmware_version"]

        if "hardware_version" in data:
            device.hardware_version = data["hardware_version"]

        device.updated_at = datetime.now(timezone.utc)
        db.session.commit()

        current_app.logger.info(f"Device configuration updated: {device.name} (ID: {device.id})")

        return (
            jsonify(
                {
                    "message": "Device configuration updated successfully",
                    "device": device.to_dict(),
                }
            ),
            200,
        )

    except Exception as e:
        db.session.rollback()
        current_app.logger.error(f"Error updating device config: {str(e)}")
        return (
            jsonify(
                {
                    "error": "Configuration update failed",
                    "message": "An error occurred while updating device configuration",
                }
            ),
            500,
        )


@device_bp.route("/credentials", methods=["GET"])
@security_headers_middleware()
@request_metrics_middleware()
@rate_limit_device(max_requests=10, window=60, per_device=False)  # 10 requests per minute per IP
def get_device_credentials():
    """Get device credentials using API key authentication"""
    try:
        # Get API key from headers
        api_key = request.headers.get("X-API-Key")
        if not api_key:
            return (
                jsonify(
                    {
                        "error": "API key required",
                        "message": "X-API-Key header is required",
                    }
                ),
                401,
            )

        # Find device by API key (allow inactive devices for credentials lookup)
        device = Device.query.filter_by(api_key=api_key).first()
        if not device:
            return (
                jsonify({"error": "Invalid API key", "message": "Device not found"}),
                404,
            )

        # Check if device is active
        # if device.status != 'active':
        #     return jsonify({
        #         'error': 'Device inactive',
        #         'message': f'Device status is {device.status}. Please contact administrator to activate device.',
        #         'device_status': device.status
        #     }), 403

        # Update device last_seen
        device.update_last_seen()

        # Get user information
        user = User.query.filter_by(id=device.user_id).first()

        # Return device credentials
        credentials = {
            "id": device.id,
            "name": device.name,
            "device_type": device.device_type,
            "user_id": str(device.user_id) if device.user_id else None,
            "status": device.status,
            "mqtt_topics": {
                "telemetry": f"iotflow/devices/{device.id}/telemetry/sensors",
                "status": f"iotflow/devices/{device.id}/status",
                "commands": f"iotflow/devices/{device.id}/commands/control",
                "heartbeat": f"iotflow/devices/{device.id}/status/heartbeat",
            },
        }

        # Add user info if available
        if user:
            credentials["owner"] = {"username": user.username, "user_id": user.user_id}

        current_app.logger.info(f"Credentials retrieved for device {device.name} (ID: {device.id})")

        return jsonify({"status": "success", "device": credentials}), 200

    except Exception as e:
        current_app.logger.error(f"Error getting device credentials: {str(e)}")
        return (
            jsonify(
                {
                    "error": "Credentials retrieval failed",
                    "message": "An error occurred while retrieving device credentials",
                }
            ),
            500,
        )


@device_bp.route("/heartbeat", methods=["POST"])
@security_headers_middleware()
@request_metrics_middleware()
@authenticate_device
@device_heartbeat_monitor()
@rate_limit_device(max_requests=30, window=60)  # 30 heartbeats per minute
def device_heartbeat():
    """Simple heartbeat endpoint to check device connectivity"""
    try:
        device = request.device

        # Device last_seen is already updated by authenticate_device decorator

        return (
            jsonify(
                {
                    "message": "Heartbeat received",
                    "device_id": device.id,
                    "timestamp": datetime.now(timezone.utc).isoformat(),
                    "status": "online",
                }
            ),
            200,
        )

    except Exception as e:
        current_app.logger.error(f"Error processing heartbeat: {str(e)}")
        return (
            jsonify(
                {
                    "error": "Heartbeat failed",
                    "message": "An error occurred while processing heartbeat",
                }
            ),
            500,
        )


@device_bp.route("/mqtt-credentials", methods=["GET"])
@authenticate_device
@security_headers_middleware()
@request_metrics_middleware()
def get_mqtt_credentials():
    """Get MQTT connection details for device"""
    try:
        device = request.device

        # Return MQTT connection details for anonymous connection
        # Note: Authentication is handled server-side using API key
        credentials = {
            "mqtt_host": current_app.config.get("MQTT_HOST", "localhost"),
            "mqtt_port": current_app.config.get("MQTT_PORT", 1883),
            "client_id": f"device_{device.id}_{device.name.replace(' ', '_')}",
            "api_key": device.api_key,  # API key for server-side authentication
            "anonymous_connection": True,  # MQTT broker allows anonymous connections
            "authentication_note": "Use API key for server-side authentication, not MQTT broker auth",
            "topics": {
                "telemetry_publish": f"iotflow/devices/{device.id}/telemetry",
                "status_publish": f"iotflow/devices/{device.id}/status",
                "commands_subscribe": f"iotflow/devices/{device.id}/commands",
                "config_subscribe": f"iotflow/devices/{device.id}/config",
            },
        }

        return jsonify({"status": "success", "credentials": credentials}), 200

    except Exception as e:
        current_app.logger.error(f"Error getting MQTT credentials: {str(e)}")
        return (
            jsonify(
                {
                    "error": "Failed to get MQTT credentials",
                    "message": "An error occurred while retrieving MQTT credentials",
                }
            ),
            500,
        )


@device_bp.route("/config", methods=["GET"])
@authenticate_device
@security_headers_middleware()
@request_metrics_middleware()
def get_device_config():
    """Get device configuration"""
    try:
        device = request.device

        # Get all active configurations for the device
        configs = DeviceConfiguration.query.filter_by(device_id=device.id, is_active=True).all()

        config_dict = {}
        for config in configs:
            # Convert value based on data type
            value = config.config_value
            if config.data_type == "integer":
                value = int(value) if value else 0
            elif config.data_type == "float":
                value = float(value) if value else 0.0
            elif config.data_type == "boolean":
                value = value.lower() in ("true", "1", "yes") if value else False
            elif config.data_type == "json":
                try:
                    value = json.loads(value) if value else {}
                except json.JSONDecodeError:
                    value = {}

            config_dict[config.config_key] = {
                "value": value,
                "data_type": config.data_type,
                "updated_at": (config.updated_at.isoformat() if config.updated_at else None),
            }

        return (
            jsonify(
                {
                    "status": "success",
                    "device_id": device.id,
                    "configuration": config_dict,
                }
            ),
            200,
        )

    except Exception as e:
        current_app.logger.error(f"Error getting device config: {str(e)}")
        return (
            jsonify(
                {
                    "error": "Failed to get device configuration",
                    "message": "An error occurred while retrieving device configuration",
                }
            ),
            500,
        )


@device_bp.route("/config", methods=["POST"])
@authenticate_device
@security_headers_middleware()
@request_metrics_middleware()
@validate_json_payload(["config_key", "config_value"])
@input_sanitization_middleware()
def update_device_config():
    """Update device configuration"""
    try:
        device = request.device
        data = request.validated_json

        config_key = data["config_key"]
        config_value = str(data["config_value"])
        data_type = data.get("data_type", "string")

        # Check if configuration already exists
        existing_config = DeviceConfiguration.query.filter_by(device_id=device.id, config_key=config_key).first()

        if existing_config:
            # Update existing configuration
            existing_config.config_value = config_value
            existing_config.data_type = data_type
            existing_config.updated_at = datetime.now(timezone.utc)
            existing_config.is_active = True
        else:
            # Create new configuration
            new_config = DeviceConfiguration(
                device_id=device.id,
                config_key=config_key,
                config_value=config_value,
                data_type=data_type,
            )
            db.session.add(new_config)

        db.session.commit()

        current_app.logger.info(f"Configuration updated for device {device.name}: {config_key}")

        return (
            jsonify(
                {
                    "status": "success",
                    "message": "Configuration updated successfully",
                    "config_key": config_key,
                    "config_value": config_value,
                    "data_type": data_type,
                }
            ),
            200,
        )

    except Exception as e:
        db.session.rollback()
        current_app.logger.error(f"Error updating device config: {str(e)}")
        return (
            jsonify(
                {
                    "error": "Failed to update configuration",
                    "message": "An error occurred while updating device configuration",
                }
            ),
            500,
        )


@device_bp.route("/statuses", methods=["GET"])
@security_headers_middleware()
@request_metrics_middleware()
def get_all_device_statuses():
    """
    Get status of all devices using Redis cache for better performance
    Returns condensed device info with online/offline status for dashboard display
    """
    try:
        # Get optional limit/offset parameters
        limit = request.args.get("limit", default=100, type=int)
        offset = request.args.get("offset", default=0, type=int)

        # Query devices from database
        devices = Device.query.order_by(Device.id).offset(offset).limit(limit).all()
        device_statuses = []

        # Check if Redis cache is available
        redis_available = (
            hasattr(current_app, "device_status_cache")
            and current_app.device_status_cache
            and current_app.device_status_cache.available
        )

        for device in devices:
            # Build condensed device info
            device_info = {
                "id": device.id,
                "name": device.name,
                "device_type": device.device_type,
                "status": device.status,
            }

            # Try to get online/offline status from Redis cache first
            if redis_available:
                cached_status = current_app.device_status_cache.get_device_status(device.id)
                if cached_status:
                    device_info["is_online"] = cached_status == "online"
                else:
                    # Fall back to database check if not in cache
                    device_info["is_online"] = is_device_online(device)
            else:
                # Fall back to database check if Redis not available
                device_info["is_online"] = is_device_online(device)

            device_statuses.append(device_info)

        # Return response
        return (
            jsonify(
                {
                    "status": "success",
                    "devices": device_statuses,
                    "meta": {
                        "total": Device.query.count(),
                        "limit": limit,
                        "offset": offset,
                        "cache_used": redis_available,
                    },
                }
            ),
            200,
        )

    except Exception as e:
        current_app.logger.error(f"Error getting device statuses: {str(e)}")
        return (
            jsonify(
                {
                    "error": "Status retrieval failed",
                    "message": "An error occurred while retrieving device statuses",
                }
            ),
            500,
        )


@device_bp.route("/<int:device_id>/status", methods=["GET"])
@security_headers_middleware()
@request_metrics_middleware()
def get_device_status_by_id(device_id):
    """
    Get status of a specific device using Redis cache for better performance
    """
    try:
        # Get device from database
        device = Device.query.filter_by(id=device_id).first_or_404()

        # Build response with basic device info
        response = {
            "id": device.id,
            "name": device.name,
            "device_type": device.device_type,
            "status": device.status,
        }

        # Try to get additional data from Redis cache
        if hasattr(current_app, "device_status_cache") and current_app.device_status_cache:
            # Check if Redis cache is available
            if current_app.device_status_cache.available:
                # Get online/offline status from cache, but verify against last_seen time
                cached_status = current_app.device_status_cache.get_device_status(device.id)

                # Always check if the device should be online based on last_seen
                actual_online_status = is_device_online(device)

                # Use actual status, but record where we initially checked
                response["is_online"] = actual_online_status
                if cached_status:
                    response["status_source"] = "redis_cache_verified"
                else:
                    response["status_source"] = "database"

                # Get last seen timestamp from cache
                last_seen = current_app.device_status_cache.get_device_last_seen(device.id)
                if last_seen:
                    response["last_seen"] = last_seen.isoformat()
                    response["last_seen_source"] = "redis_cache"
                else:
                    response["last_seen"] = device.last_seen.isoformat() if device.last_seen else None
                    response["last_seen_source"] = "database"
            else:
                # Redis not available
                response["is_online"] = is_device_online(device)
                response["last_seen"] = device.last_seen.isoformat() if device.last_seen else None
                response["status_source"] = "database"
                response["last_seen_source"] = "database"
        else:
            # Redis not configured
            response["is_online"] = is_device_online(device)
            response["last_seen"] = device.last_seen.isoformat() if device.last_seen else None
            response["status_source"] = "database"
            response["last_seen_source"] = "database"

        return jsonify({"status": "success", "device": response}), 200

    except Exception as e:
        current_app.logger.error(f"Error getting device status for ID {device_id}: {str(e)}")
        return (
            jsonify(
                {
                    "error": "Status retrieval failed",
                    "message": f"An error occurred while retrieving status for device {device_id}",
                }
            ),
            500,
        )


def is_device_online(device):
    """
    Helper function to check if device is online based on last_seen timestamp
    and update Redis cache if the status has changed
    """
    if not device.last_seen:
        # Device has never been seen
        sync_device_status_to_redis(device, False)
        return False

    # Ensure both datetimes are timezone-aware for comparison
    now = datetime.now(timezone.utc)
    last_seen = device.last_seen
    if last_seen.tzinfo is None:
        # If last_seen is naive, assume it's UTC
        last_seen = last_seen.replace(tzinfo=timezone.utc)

    # Consider device online if last seen in the last 5 minutes
    time_since_last_seen = (now - last_seen).total_seconds()
    is_online = time_since_last_seen < 5  # 5 minutes

    # Update Redis cache if needed
    sync_device_status_to_redis(device, is_online, time_since_last_seen)

    return is_online


def sync_device_status_to_redis(device, is_online, time_since_last_seen=None):
    """
    Sync the device status to Redis cache if it doesn't match
    Uses safe Redis utility that works both inside and outside Flask application context
    """
    try:
        # First try to use the Flask app context if available
        try:
            # Check if we have Flask app context available
            cache_available = (
                hasattr(current_app, "device_status_cache")
                and current_app.device_status_cache
                and current_app.device_status_cache.available
            )

            if cache_available:
                # Use the Flask app's Redis cache
                redis_status = current_app.device_status_cache.get_device_status(device.id)

                if (is_online and redis_status != "online") or (not is_online and redis_status != "offline"):
                    new_status = "online" if is_online else "offline"
                    current_app.device_status_cache.set_device_status(device.id, new_status)

                    if time_since_last_seen is not None:
                        current_app.logger.info(
                            f"Updated device {device.id} status in Redis: {new_status} "
                            f"(last seen {time_since_last_seen:.1f}s ago)"
                        )
                    else:
                        current_app.logger.info(f"Updated device {device.id} status in Redis: {new_status}")
                return

        except RuntimeError:
            # We're outside Flask application context, use the safe Redis utility
            pass

        # Fall back to safe Redis utility
        from src.utils.redis_util import sync_device_status_safe

        sync_device_status_safe(device.id, is_online, time_since_last_seen)

    except Exception as e:
        # Use a basic logger if we can't get the app logger
        import logging

        logger = logging.getLogger(__name__)
        logger.error(f"Error syncing device {device.id} status to Redis: {e}")


@device_bp.route("/<int:device_id>/summary", methods=["GET"])
@security_headers_middleware()
@request_metrics_middleware()
@rate_limit_device(max_requests=30, window=60, per_device=False)  # 30 requests per minute per IP
def get_device_summary(device_id):
    """
    Get comprehensive device summary including device info, status, configuration, and recent telemetry

    TDD Implementation: Device Data Summary API
    Endpoint: GET /api/v1/devices/<device_id>/summary

    Query Parameters:
    - telemetry_limit: Number of recent telemetry records to include (default: 10, max: 100)
    - include_config: Whether to include device configuration (default: true)
    """
    try:
        # Get API key from headers
        api_key = request.headers.get("X-API-Key")
        if not api_key:
            return (
                jsonify({"error": "API key required", "message": "X-API-Key header is required"}),
                401,
            )

        # Find device by API key
        device = Device.query.filter_by(api_key=api_key).first()
        if not device:
            return (
                jsonify({"error": "Invalid API key", "message": "Device not found"}),
                401,
            )

        # Check if requested device exists
        target_device = Device.query.get(device_id)
        if not target_device:
            return (
                jsonify({"error": "Device not found", "message": f"Device with ID {device_id} does not exist"}),
                404,
            )

        # Enforce access control - device can only access its own data
        if device.id != device_id:
            return (
                jsonify({"error": "Access denied", "message": "You can only access your own device data"}),
                403,
            )

        # Parse query parameters
        telemetry_limit = min(int(request.args.get("telemetry_limit", 10)), 100)
        include_config = request.args.get("include_config", "true").lower() in ("true", "1", "yes")

        # 1. Get basic device information
        device_info = {
            "id": device.id,
            "name": device.name,
            "description": device.description,
            "device_type": device.device_type,
            "status": device.status,
            "location": device.location,
            "firmware_version": device.firmware_version,
            "hardware_version": device.hardware_version,
            "created_at": device.created_at.isoformat() if device.created_at else None,
            "updated_at": device.updated_at.isoformat() if device.updated_at else None,
        }

        # 2. Get device status information
        status_info = {
            "is_online": is_device_online(device),
            "last_seen": device.last_seen.isoformat() if device.last_seen else None,
            "status": device.status,
        }

        # 3. Get recent telemetry data
        telemetry_info = {
            "recent_data": [],
            "count": 0,
            "iotdb_available": False,
        }

        try:
            # Get recent telemetry from IoTDB
            recent_telemetry = iotdb_service.get_device_telemetry(
                device_id=str(device.id),
                user_id=str(device.user_id) if device.user_id else None,
                start_time="-24h",  # Last 24 hours
                limit=telemetry_limit,
            )

            telemetry_info["recent_data"] = recent_telemetry or []
            telemetry_info["count"] = len(recent_telemetry) if recent_telemetry else 0
            telemetry_info["iotdb_available"] = iotdb_service.is_available()

        except Exception as e:
            current_app.logger.warning(f"Failed to get telemetry data for device {device.id}: {e}")
            telemetry_info["iotdb_available"] = False

        # 4. Get device configuration (if requested)
        configuration_info = {}

        if include_config:
            try:
                # Get all active configurations for the device
                configs = DeviceConfiguration.query.filter_by(device_id=device.id, is_active=True).all()

                for config in configs:
                    # Convert value based on data type
                    value = config.config_value
                    if config.data_type == "integer":
                        value = int(value) if value else 0
                    elif config.data_type == "float":
                        value = float(value) if value else 0.0
                    elif config.data_type == "boolean":
                        value = value.lower() in ("true", "1", "yes") if value else False
                    elif config.data_type == "json":
                        try:
                            value = json.loads(value) if value else {}
                        except json.JSONDecodeError:
                            value = {}

                    configuration_info[config.config_key] = {
                        "value": value,
                        "data_type": config.data_type,
                        "updated_at": config.updated_at.isoformat() if config.updated_at else None,
                    }

            except Exception as e:
                current_app.logger.warning(f"Failed to get configuration for device {device.id}: {e}")

        # 5. Build comprehensive response
        summary_response = {
            "device": device_info,
            "status": status_info,
            "telemetry": telemetry_info,
            "configuration": configuration_info,
            "summary_generated_at": datetime.now(timezone.utc).isoformat(),
        }

        current_app.logger.info(f"Device summary generated for device {device.name} (ID: {device.id})")

        return jsonify(summary_response), 200

    except Exception as e:
        current_app.logger.error(f"Error generating device summary for ID {device_id}: {str(e)}")
        return (
            jsonify(
                {"error": "Summary generation failed", "message": "An error occurred while generating device summary"}
            ),
            500,
        )
