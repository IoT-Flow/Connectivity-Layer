"""
Telemetry routes using PostgreSQL
Drop-in replacement for telemetry.py with PostgreSQL backend
"""

from flask import Blueprint, request, jsonify, current_app
from datetime import datetime, timezone
from src.services.postgres_telemetry import PostgresTelemetryService
from src.models import Device

# Create blueprint for telemetry routes
telemetry_bp = Blueprint("telemetry", __name__, url_prefix="/api/v1/telemetry")

# Initialize PostgreSQL telemetry service
postgres_service = PostgresTelemetryService()


# Helper to get device by API key and check access
def get_authenticated_device(device_id=None):
    api_key = request.headers.get("X-API-Key")
    if not api_key:
        return None, jsonify({"error": "API key required"}), 401
    device = Device.query.filter_by(api_key=api_key).first()
    if not device:
        return None, jsonify({"error": "Invalid API key"}), 401
    if device_id is not None and int(device.id) != int(device_id):
        return None, jsonify({"error": "Forbidden: device mismatch"}), 403
    return device, None, None


@telemetry_bp.route("", methods=["POST"])
def store_telemetry():
    """Store telemetry data
    ---
    tags:
      - Telemetry
    summary: Submit telemetry data
    description: Submit telemetry data from an IoT device
    security:
      - ApiKeyAuth: []
    requestBody:
      required: true
      content:
        application/json:
          schema:
            type: object
            required:
              - measurements
            properties:
              measurements:
                type: array
                items:
                  type: object
                  properties:
                    name:
                      type: string
                      example: temperature
                    value:
                      oneOf:
                        - type: number
                        - type: string
                      example: 25.5
                    unit:
                      type: string
                      example: celsius
                    timestamp:
                      type: string
                      format: date-time
    responses:
      201:
        description: Telemetry data stored successfully
      401:
        description: Unauthorized - invalid API key
    """
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

        # Store in PostgreSQL
        success = postgres_service.write_telemetry_data(
            device_id=str(device.id),
            data=telemetry_data,
            device_type=device.device_type,
            metadata=metadata,
            timestamp=timestamp,
            user_id=device.user_id,
        )

        if success:
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
                        "stored_in_postgres": True
                    }
                ),
                201,
            )
        else:
            return (
                jsonify(
                    {
                        "error": "Failed to store telemetry data",
                        "message": "PostgreSQL may not be available. Check logs for details.",
                    }
                ),
                500,
            )

    except Exception as e:
        current_app.logger.error(f"Error storing telemetry: {str(e)}")
        return jsonify({"error": f"Internal server error: {str(e)}"}), 500


@telemetry_bp.route("/<int:device_id>", methods=["GET"])
def get_device_telemetry(device_id):
    """Get telemetry data for a specific device"""
    device, err, code = get_authenticated_device(device_id)
    if err:
        return err, code
    try:
        telemetry_data = postgres_service.get_device_telemetry(
            device_id=str(device_id),
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
                    "postgres_available": postgres_service.is_available(),
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
        latest_data = postgres_service.get_device_latest_telemetry(str(device_id))
        if latest_data:
            return (
                jsonify(
                    {
                        "device_id": device_id,
                        "device_name": device.name,
                        "device_type": device.device_type,
                        "latest_data": latest_data,
                        "postgres_available": postgres_service.is_available(),
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
                        "postgres_available": postgres_service.is_available(),
                    }
                ),
                404,
            )
    except Exception as e:
        current_app.logger.error(f"Error getting latest telemetry: {str(e)}")
        return jsonify({"error": f"Internal server error: {str(e)}"}), 500


@telemetry_bp.route("/<int:device_id>/aggregated", methods=["GET"])
def get_device_aggregated_telemetry(device_id):
    """Get aggregated telemetry data for a device"""
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
        aggregated_data = postgres_service.get_device_aggregated_data(
            device_id=str(device_id),
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
                    "postgres_available": postgres_service.is_available(),
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
        success = postgres_service.delete_device_data(
            device_id=str(device_id), 
            start_time=start_time, 
            stop_time=stop_time
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
                        "message": "PostgreSQL may not be available. Check logs for details.",
                    }
                ),
                500,
            )
    except Exception as e:
        current_app.logger.error(f"Error deleting telemetry: {str(e)}")
        return jsonify({"error": f"Internal server error: {str(e)}"}), 500


@telemetry_bp.route("/status", methods=["GET"])
def get_telemetry_status():
    """Get PostgreSQL telemetry service status and statistics"""
    try:
        postgres_available = postgres_service.is_available()

        # Get basic statistics
        total_devices = Device.query.count()

        return (
            jsonify(
                {
                    "postgres_available": postgres_available,
                    "backend": "PostgreSQL",
                    "total_devices": total_devices,
                    "status": "healthy" if postgres_available else "unavailable",
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
        limit = min(int(request.args.get("limit", 100)), 1000)
        start_time = request.args.get("start_time", "-24h")
        end_time = request.args.get("end_time")

        # Get telemetry data from PostgreSQL for all user's devices
        try:
            telemetry_data = postgres_service.get_user_telemetry(
                user_id=str(user_id),
                start_time=start_time,
                end_time=end_time,
                limit=limit,
            )

            # Get telemetry count for the user
            telemetry_count = postgres_service.get_user_telemetry_count(
                user_id=str(user_id), 
                start_time=start_time
            )

        except Exception as e:
            current_app.logger.error(f"Error querying user telemetry from PostgreSQL: {str(e)}")
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
