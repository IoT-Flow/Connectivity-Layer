from flask import Blueprint, request, jsonify, current_app
from src.models import Device, db
from src.middleware.auth import require_admin_token
from datetime import datetime, timezone, timedelta

# Create blueprint for admin routes
admin_bp = Blueprint("admin", __name__, url_prefix="/api/v1/admin")


@admin_bp.route("/devices", methods=["GET"])
@require_admin_token
def list_all_devices():
    """List all devices with basic information
    ---
    tags:
      - Admin
    summary: List all devices (admin)
    description: Get list of all devices with admin privileges
    security:
      - BearerAuth: []
    responses:
      200:
        description: List of all devices
      401:
        description: Unauthorized - admin token required
    """
    try:
        # Get all devices with their basic info
        devices = Device.query.all()

        device_list = []
        for device in devices:
            device_dict = device.to_dict()
            # Hide API key in admin listing for security
            device_dict.pop("api_key", None)
            device_list.append(device_dict)

        return (
            jsonify(
                {
                    "status": "success",
                    "total_devices": len(device_list),
                    "devices": device_list,
                }
            ),
            200,
        )

    except Exception as e:
        current_app.logger.error(f"Error listing devices: {str(e)}")
        return (
            jsonify(
                {
                    "error": "Failed to list devices",
                    "message": "An error occurred while retrieving device list",
                }
            ),
            500,
        )


@admin_bp.route("/devices/<int:device_id>", methods=["GET"])
@require_admin_token
def get_device_details(device_id):
    """Get detailed device information including auth and config
    ---
    tags:
      - Admin
    summary: Get device details (admin)
    description: Get detailed device information with admin privileges
    security:
      - BearerAuth: []
    parameters:
      - name: device_id
        in: path
        required: true
        schema:
          type: integer
    responses:
      200:
        description: Device details
      404:
        description: Device not found
    """
    try:
        device = Device.query.get(device_id)
        
        if not device:
            return jsonify({
                "error": "Device not found",
                "message": f"No device found with ID: {device_id}"
            }), 404

        device_dict = device.to_dict()
        # Hide API key for security
        device_dict.pop("api_key", None)

        return (
            jsonify(
                {
                    "status": "success",
                    "device": device_dict,
                }
            ),
            200,
        )

    except Exception as e:
        current_app.logger.error(f"Error getting device details: {str(e)}")
        return (
            jsonify(
                {
                    "error": "Failed to get device details",
                    "message": "An error occurred while retrieving device information",
                }
            ),
            500,
        )


@admin_bp.route("/devices/<int:device_id>/status", methods=["PUT"])
@require_admin_token
def update_device_status(device_id):
    """Update device status (active/inactive/maintenance)"""
    try:
        device = Device.query.get(device_id)
        
        if not device:
            return jsonify({
                "error": "Device not found",
                "message": f"No device found with ID: {device_id}"
            }), 404
        
        data = request.get_json()

        if not data or "status" not in data:
            return (
                jsonify({"error": "Missing status", "message": "Status field is required"}),
                400,
            )

        new_status = data["status"]
        if new_status not in ["active", "inactive", "maintenance"]:
            return (
                jsonify(
                    {
                        "error": "Invalid status",
                        "message": "Status must be active, inactive, or maintenance",
                    }
                ),
                400,
            )

        old_status = device.status
        device.status = new_status
        device.updated_at = datetime.now(timezone.utc)

        db.session.commit()

        current_app.logger.info(f"Device {device.name} status changed from {old_status} to {new_status}")

        return (
            jsonify(
                {
                    "status": "success",
                    "message": f"Device status updated from {old_status} to {new_status}",
                    "device_id": device_id,
                    "old_status": old_status,
                    "new_status": new_status,
                }
            ),
            200,
        )

    except Exception as e:
        db.session.rollback()
        current_app.logger.error(f"Error updating device status: {str(e)}")
        return (
            jsonify(
                {
                    "error": "Failed to update device status",
                    "message": "An error occurred while updating device status",
                }
            ),
            500,
        )


@admin_bp.route("/stats", methods=["GET"])
@require_admin_token
def get_system_stats():
    """Get system statistics
    ---
    tags:
      - Admin
    summary: Get system statistics
    description: Get comprehensive system statistics (admin only)
    security:
      - BearerAuth: []
    responses:
      200:
        description: System statistics
    """
    try:
        # Device statistics
        total_devices = Device.query.count()
        active_devices = Device.query.filter_by(status="active").count()
        inactive_devices = Device.query.filter_by(status="inactive").count()
        maintenance_devices = Device.query.filter_by(status="maintenance").count()

        # Online/offline statistics (devices seen in last 5 minutes)
        five_minutes_ago = datetime.now(timezone.utc) - timedelta(minutes=5)
        online_devices = Device.query.filter(Device.last_seen >= five_minutes_ago, Device.status == "active").count()

        return (
            jsonify(
                {
                    "status": "success",
                    "timestamp": datetime.now(timezone.utc).isoformat(),
                    "device_stats": {
                        "total": total_devices,
                        "active": active_devices,
                        "inactive": inactive_devices,
                        "maintenance": maintenance_devices,
                        "online": online_devices,
                        "offline": active_devices - online_devices,
                    },
                    "total_devices": total_devices,
                }
            ),
            200,
        )

    except Exception as e:
        current_app.logger.error(f"Error getting system stats: {str(e)}")
        return (
            jsonify(
                {
                    "error": "Failed to get system statistics",
                    "message": "An error occurred while retrieving system statistics",
                }
            ),
            500,
        )


@admin_bp.route("/devices/<int:device_id>", methods=["DELETE"])
@require_admin_token
def delete_device(device_id):
    """Delete a device and all related data"""
    try:
        device = Device.query.get(device_id)
        
        if not device:
            return jsonify({
                "error": "Device not found",
                "message": f"No device found with ID: {device_id}"
            }), 404
        
        device_name = device.name

        # Delete device
        db.session.delete(device)
        db.session.commit()

        current_app.logger.info(f"Device {device_name} (ID: {device_id}) deleted")

        return (
            jsonify(
                {
                    "status": "success",
                    "message": f"Device {device_name} deleted successfully",
                    "device_id": device_id,
                }
            ),
            200,
        )

    except Exception as e:
        db.session.rollback()
        current_app.logger.error(f"Error deleting device: {str(e)}")
        return (
            jsonify(
                {
                    "error": "Failed to delete device",
                    "message": "An error occurred while deleting the device",
                }
            ),
            500,
        )


@admin_bp.route("/devices/statuses", methods=["GET"])
@require_admin_token
def get_all_device_statuses():
    """
    Get status of all devices (Admin only)
    Returns condensed device info with online/offline status for dashboard display
    ---
    tags:
      - Admin
    summary: Get all device statuses (Admin)
    description: Get status of all devices in the system (requires admin authentication)
    security:
      - AdminAuth: []
    parameters:
      - name: limit
        in: query
        schema:
          type: integer
          default: 100
      - name: offset
        in: query
        schema:
          type: integer
          default: 0
    responses:
      200:
        description: List of all device statuses
      401:
        description: Admin token required
    """
    try:
        # Get optional limit/offset parameters
        limit = request.args.get("limit", default=100, type=int)
        offset = request.args.get("offset", default=0, type=int)

        # Query devices from database
        devices = Device.query.order_by(Device.id).offset(offset).limit(limit).all()
        device_statuses = []

        for device in devices:
            # Build condensed device info
            device_info = {
                "id": device.id,
                "name": device.name,
                "device_type": device.device_type,
                "status": device.status,
            }

            # Check online status from database
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


def is_device_online(device):
    """
    Helper function to check if device is online based on last_seen timestamp
    """
    if not device.last_seen:
        # Device has never been seen
        return False

    # Ensure both datetimes are timezone-aware for comparison
    now = datetime.now(timezone.utc)
    last_seen = device.last_seen
    if last_seen.tzinfo is None:
        # If last_seen is naive, assume it's UTC
        last_seen = last_seen.replace(tzinfo=timezone.utc)

    # Consider device online if last seen in the last 5 minutes
    time_since_last_seen = (now - last_seen).total_seconds()
    is_online = time_since_last_seen < 300  # 5 minutes (300 seconds)

    return is_online


