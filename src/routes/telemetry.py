from flask import Blueprint, request, jsonify, current_app
from datetime import datetime, timezone
from src.services.iotdb import IoTDBService
from src.models import Device
from src.metrics import TELEMETRY_MESSAGES
import logging

# Create blueprint for telemetry routes
telemetry_bp = Blueprint("telemetry", __name__, url_prefix="/api/v1/telemetry")

# Initialize IoTDB service
iotdb_service = IoTDBService()

# Logger
logger = logging.getLogger(__name__)


# Helper to get device by API key and check access
def get_authenticated_device(device_id=None):
    api_key = request.headers.get("X-API-Key")
    if not api_key:
        return None, jsonify({"error": "API key required"}), 401
    device = Device.query.filter_by(api_key=api_key).first()
    if not device:
        return None, jsonify({"error": "Invalid API key"}), 401

    # If device_id is specified, check if it exists first
    if device_id is not None:
        target_device = Device.query.get(device_id)
        if not target_device:
            return None, jsonify({"error": "Device not found"}), 404
        if int(device.id) != int(device_id):
            return None, jsonify({"error": "Forbidden: device mismatch"}), 403

    return device, None, None


@telemetry_bp.route("", methods=["POST"])
def store_telemetry():
    """Store telemetry data in IoTDB"""
    try:
        data = request.get_json()

        if not data:
            return jsonify({"error": "No data provided"}), 400

        # Get API key from headers
        api_key = request.headers.get("X-API-Key")
        if not api_key:
            return jsonify({"error": "API key required"}), 401

        # Find device by API key
        device = Device.query.filter_by(api_key=api_key).first()
        if not device:
            return jsonify({"error": "Invalid API key"}), 401

        telemetry_data = data.get("data", {})
        metadata = data.get("metadata", {})
        timestamp_str = data.get("timestamp")

        if not telemetry_data:
            return jsonify({"error": "Telemetry data is required"}), 400

        # Parse timestamp if provided
        timestamp = None
        if timestamp_str:
            try:
                # Handle different timestamp formats
                if timestamp_str.endswith("Z"):
                    timestamp = datetime.fromisoformat(timestamp_str.replace("Z", "+00:00"))
                else:
                    timestamp = datetime.fromisoformat(timestamp_str)
            except ValueError:
                return (
                    jsonify({"error": "Invalid timestamp format. Use ISO 8601 format."}),
                    400,
                )

        # Store in IoTDB
        success = iotdb_service.write_telemetry_data(
            device_id=str(device.id),
            data=telemetry_data,
            device_type=device.device_type,
            metadata=metadata,
            timestamp=timestamp,
            user_id=device.user_id,
        )

        if success:
            # Increment telemetry messages counter
            TELEMETRY_MESSAGES.inc()
            # Update device last_seen
            device.update_last_seen()

            current_app.logger.info(f"Telemetry stored for device {device.name} (ID: {device.id})")

            return (
                jsonify(
                    {
                        "message": "Telemetry data stored successfully",
                        "device_id": device.id,
                        "device_name": device.name,
                        "timestamp": (timestamp.isoformat() if timestamp else datetime.now(timezone.utc).isoformat()),
                    }
                ),
                201,
            )
        else:
            return (
                jsonify(
                    {
                        "error": "Failed to store telemetry data",
                        "message": "IoTDB may not be available. Check logs for details.",
                    }
                ),
                500,
            )

    except Exception as e:
        current_app.logger.error(f"Error storing telemetry: {str(e)}")
        return jsonify({"error": f"Internal server error: {str(e)}"}), 500


@telemetry_bp.route("/device/<int:device_id>", methods=["GET"])
def get_device_telemetry_new(device_id):
    """Get telemetry data for a specific device - Migration Requirements Format"""
    device, err, code = get_authenticated_device(device_id)
    if err:
        return {"success": False, "error": err.get_json().get("error", "Authentication failed")}, code

    try:
        # Parse query parameters
        data_type = request.args.get("data_type")
        start_date = request.args.get("start_date")
        end_date = request.args.get("end_date")
        limit = min(int(request.args.get("limit", 100)), 1000)
        page = int(request.args.get("page", 1))

        # Query telemetry data using new method
        result = iotdb_service.query_telemetry_data(
            device_id=str(device_id),
            user_id=str(device.user_id),
            data_type=data_type,
            start_date=start_date,
            end_date=end_date,
            limit=limit,
            page=page,
        )

        # Build response according to migration requirements
        response = {
            "success": True,
            "device_id": device_id,
            "device_name": device.name,
            "device_type": device.device_type,
            "telemetry": result["records"],
            "pagination": {
                "total": result["total"],
                "currentPage": result["page"],
                "totalPages": result["pages"],
                "limit": limit,
            },
            "iotdb_available": iotdb_service.is_available(),
        }

        # Add filters if applied
        filters = {}
        if data_type:
            filters["data_type"] = data_type
        if start_date:
            filters["start_date"] = start_date
        if end_date:
            filters["end_date"] = end_date
        if filters:
            response["filters"] = filters

        return response, 200

    except Exception as e:
        logger.error(f"Error retrieving telemetry for device {device_id}: {e}")
        return {"success": False, "error": "Failed to retrieve telemetry data"}, 500


@telemetry_bp.route("/<int:device_id>", methods=["GET"])
def get_device_telemetry(device_id):
    """Get telemetry data for a specific device - Legacy endpoint"""
    device, err, code = get_authenticated_device(device_id)
    if err:
        return err, code
    try:
        telemetry_data = iotdb_service.get_device_telemetry(
            device_id=str(device_id),
            user_id=str(device.user_id),  # FIX: Pass user_id for correct path
            start_time=request.args.get("start_time", "-1h"),
            limit=min(int(request.args.get("limit", 1000)), 10000),
        )
        return (
            jsonify(
                {
                    "device_id": device_id,
                    "device_name": device.name,
                    "device_type": device.device_type,
                    "start_time": request.args.get("start_time", "-1h"),
                    "data": telemetry_data,
                    "count": len(telemetry_data),
                    "iotdb_available": iotdb_service.is_available(),
                }
            ),
            200,
        )
    except Exception as e:
        current_app.logger.error(f"Error getting telemetry: {str(e)}")
        return jsonify({"error": f"Internal server error: {str(e)}"}), 500


@telemetry_bp.route("/<int:device_id>/latest", methods=["GET"])
def get_device_latest_telemetry(device_id):
    """Get the latest telemetry data for a device"""
    device, err, code = get_authenticated_device(device_id)
    if err:
        return err, code
    try:
        latest_data = iotdb_service.get_device_latest_telemetry(
            device_id=str(device_id), user_id=str(device.user_id)  # FIX: Pass user_id for correct path
        )
        if latest_data:
            return (
                jsonify(
                    {
                        "device_id": device_id,
                        "device_name": device.name,
                        "device_type": device.device_type,
                        "latest_data": latest_data,
                        "data": latest_data,  # Backward compatibility
                        "iotdb_available": iotdb_service.is_available(),
                    }
                ),
                200,
            )
        else:
            return (
                jsonify(
                    {
                        "device_id": device_id,
                        "device_name": device.name,
                        "message": "No telemetry data found",
                        "iotdb_available": iotdb_service.is_available(),
                    }
                ),
                404,
            )
    except Exception as e:
        current_app.logger.error(f"Error getting latest telemetry: {str(e)}")
        return jsonify({"error": f"Internal server error: {str(e)}"}), 500


@telemetry_bp.route("/device/<int:device_id>/aggregated", methods=["GET"])
def get_device_aggregated_telemetry_new(device_id):
    """Get aggregated telemetry data for a device - Migration Requirements Format"""
    device, err, code = get_authenticated_device(device_id)
    if err:
        return {"success": False, "error": err.get_json().get("error", "Authentication failed")}, code

    try:
        # Parse required parameters
        data_type = request.args.get("data_type")
        aggregation = request.args.get("aggregation")

        if not data_type:
            return {"success": False, "error": "data_type parameter is required"}, 400

        if not aggregation:
            return {"success": False, "error": "aggregation parameter is required"}, 400

        # Validate aggregation function
        valid_aggregations = ["avg", "sum", "min", "max", "count"]
        if aggregation not in valid_aggregations:
            return {
                "success": False,
                "error": f"Invalid aggregation function. Must be one of: {', '.join(valid_aggregations)}",
            }, 400

        # Parse optional parameters
        start_date = request.args.get("start_date")
        end_date = request.args.get("end_date")

        # Get aggregated data using new method
        result = iotdb_service.aggregate_telemetry_data(
            device_id=str(device_id),
            user_id=str(device.user_id),
            data_type=data_type,
            aggregation=aggregation,
            start_date=start_date,
            end_date=end_date,
        )

        # Build response according to migration requirements
        response = {
            "success": True,
            "device_id": device_id,
            "device_name": device.name,
            "device_type": device.device_type,
            "aggregation": {
                "type": aggregation,
                "data_type": data_type,
                "value": result["value"],
                "count": result["count"],
            },
            "iotdb_available": iotdb_service.is_available(),
        }

        # Add date range if provided
        if start_date:
            response["aggregation"]["start_date"] = start_date
        if end_date:
            response["aggregation"]["end_date"] = end_date

        return response, 200

    except ValueError as e:
        return {"success": False, "error": str(e)}, 400
    except Exception as e:
        logger.error(f"Error getting aggregated telemetry for device {device_id}: {e}")
        return {"success": False, "error": "Failed to retrieve aggregated telemetry data"}, 500


@telemetry_bp.route("/<int:device_id>/aggregated", methods=["GET"])
def get_device_aggregated_telemetry(device_id):
    """Get aggregated telemetry data for a device - Legacy endpoint"""
    device, err, code = get_authenticated_device(device_id)
    if err:
        return err, code
    try:
        field = request.args.get("field", "temperature")
        aggregation = request.args.get("aggregation", "mean")
        window = request.args.get("window", "1h")
        start_time = request.args.get("start_time", "-24h")
        valid_aggregations = [
            "mean",
            "sum",
            "count",
            "min",
            "max",
            "first",
            "last",
            "median",
        ]
        if aggregation not in valid_aggregations:
            return (
                jsonify(
                    {
                        "error": "Invalid aggregation function",
                        "valid_functions": valid_aggregations,
                    }
                ),
                400,
            )
        aggregated_data = iotdb_service.get_device_aggregated_data(
            device_id=str(device_id),
            user_id=str(device.user_id),  # FIX: Pass user_id for correct path
            field=field,
            aggregation=aggregation,
            window=window,
            start_time=start_time,
        )
        return (
            jsonify(
                {
                    "device_id": device_id,
                    "device_name": device.name,
                    "device_type": device.device_type,
                    "field": field,
                    "aggregation": aggregation,
                    "window": window,
                    "start_time": start_time,
                    "data": aggregated_data,
                    "count": len(aggregated_data),
                    "iotdb_available": iotdb_service.is_available(),
                }
            ),
            200,
        )
    except Exception as e:
        current_app.logger.error(f"Error getting aggregated telemetry: {str(e)}")
        return jsonify({"error": f"Internal server error: {str(e)}"}), 500


@telemetry_bp.route("/<int:device_id>", methods=["DELETE"])
def delete_device_telemetry(device_id):
    """Delete telemetry data for a device within a time range"""
    device, err, code = get_authenticated_device(device_id)
    if err:
        return err, code
    try:
        data = request.get_json()
        if not data:
            return (
                jsonify({"error": "Request body required with start_time and stop_time"}),
                400,
            )
        start_time = data.get("start_time")
        stop_time = data.get("stop_time")
        if not start_time or not stop_time:
            return jsonify({"error": "start_time and stop_time are required"}), 400
        success = iotdb_service.delete_device_data(
            device_id=str(device_id),
            user_id=str(device.user_id),  # FIX: Pass user_id for correct path
            start_time=start_time,
            stop_time=stop_time,
        )
        if success:
            current_app.logger.info(f"Telemetry data deleted for device {device.name} (ID: {device_id})")
            return (
                jsonify(
                    {
                        "message": f"Telemetry data deleted for device {device.name}",
                        "device_id": device_id,
                        "start_time": start_time,
                        "stop_time": stop_time,
                    }
                ),
                200,
            )
        else:
            return (
                jsonify(
                    {
                        "error": "Failed to delete telemetry data",
                        "message": "IoTDB may not be available. Check logs for details.",
                    }
                ),
                500,
            )
    except Exception as e:
        current_app.logger.error(f"Error deleting telemetry: {str(e)}")
        return jsonify({"error": f"Internal server error: {str(e)}"}), 500


@telemetry_bp.route("/status", methods=["GET"])
def get_telemetry_status():
    """Get IoTDB service status and statistics"""
    try:
        from src.config.iotdb_config import iotdb_config

        iotdb_available = iotdb_service.is_available()

        # Get basic statistics
        total_devices = Device.query.count()

        return (
            jsonify(
                {
                    "iotdb_available": iotdb_available,
                    "iotdb_host": iotdb_config.host,
                    "iotdb_port": iotdb_config.port,
                    "iotdb_database": iotdb_config.database,
                    "total_devices": total_devices,
                    "status": "healthy" if iotdb_available else "unavailable",
                }
            ),
            200,
        )

    except Exception as e:
        current_app.logger.error(f"Error getting telemetry status: {str(e)}")
        return jsonify({"error": f"Internal server error: {str(e)}"}), 500


@telemetry_bp.route("/user/<int:user_id>", methods=["GET"])
def get_user_telemetry(user_id):
    """Get telemetry data for all devices belonging to a user"""
    try:
        # For now, we'll require authentication via API key from any device owned by the user
        # In a production system, you might want user-level authentication here
        api_key = request.headers.get("X-API-Key")
        if not api_key:
            return jsonify({"error": "API key required"}), 401

        # Find device by API key and verify it belongs to the requested user
        device = Device.query.filter_by(api_key=api_key).first()
        if not device:
            return jsonify({"error": "Invalid API key"}), 401

        if device.user_id != user_id:
            return jsonify({"error": "Forbidden: user mismatch"}), 403

        # Parse query parameters
        limit = min(int(request.args.get("limit", 100)), 1000)  # Max 1000 records
        start_time = request.args.get("start_time", "-24h")  # Default to last 24 hours
        end_time = request.args.get("end_time")

        # Get telemetry data from IoTDB for all user's devices
        try:
            telemetry_data = iotdb_service.get_user_telemetry(
                user_id=str(user_id),
                start_time=start_time,
                end_time=end_time,
                limit=limit,
            )

            # Get telemetry count for the user
            telemetry_count = iotdb_service.get_user_telemetry_count(user_id=str(user_id), start_time=start_time)

        except Exception as e:
            current_app.logger.error(f"Error querying user telemetry from IoTDB: {str(e)}")
            telemetry_data = []
            telemetry_count = 0

        return (
            jsonify(
                {
                    "status": "success",
                    "user_id": user_id,
                    "telemetry": telemetry_data,
                    "count": len(telemetry_data),
                    "total_count": telemetry_count,
                    "limit": limit,
                    "start_time": start_time,
                    "end_time": end_time,
                }
            ),
            200,
        )

    except Exception as e:
        current_app.logger.error(f"Error retrieving user telemetry: {str(e)}")
        return (
            jsonify(
                {
                    "error": "Telemetry retrieval failed",
                    "message": "An error occurred while retrieving user telemetry data",
                }
            ),
            500,
        )
