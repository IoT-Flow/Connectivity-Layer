import json
from flask import Blueprint, request, jsonify, current_app
from src.models import db, Device, DeviceControl
from src.middleware.auth import authenticate_device

control_bp = Blueprint("control", __name__, url_prefix="/api/v1/devices")


@control_bp.route("/<int:device_id>/control", methods=["POST"])
@authenticate_device
def control_device(device_id):
    data = request.get_json()

    if not data:
        return jsonify({"error": "Request body is required"}), 400

    command = data.get("command")
    if not command:
        return jsonify({"error": "Command is required"}), 400

    parameters = data.get("parameters", {})

    device = Device.query.get(device_id)
    if not device:
        return jsonify({"error": "Device not found"}), 404

    # Verify the authenticated device matches the requested device
    api_key = request.headers.get("X-API-Key")
    auth_device = Device.query.filter_by(api_key=api_key).first()
    if auth_device.id != device_id:
        return jsonify({"error": "Unauthorized"}), 403

    # Store command in DB for tracking
    control = DeviceControl(device_id=device_id, command=command, parameters=parameters, status="pending")
    db.session.add(control)
    db.session.commit()

    # Publish command via main MQTT service
    try:
        if hasattr(current_app, "mqtt_service") and current_app.mqtt_service:
            topic = f"devices/{device_id}/control"
            payload = {"command": command, "parameters": parameters}
            current_app.mqtt_service.publish(topic, json.dumps(payload))
        else:
            current_app.logger.warning("MQTT service not available for publishing command")
    except Exception as e:
        current_app.logger.error(f"Failed to publish MQTT command: {e}")
        # Log error but don't fail - command is stored in DB

    return (
        jsonify(
            {
                "id": control.id,
                "device_id": control.device_id,
                "command": control.command,
                "parameters": control.parameters,
                "status": control.status,
                "created_at": control.created_at.isoformat(),
            }
        ),
        201,
    )


@control_bp.route("/<int:device_id>/control/<int:control_id>/status", methods=["POST"])
@authenticate_device
def update_control_status(device_id, control_id):
    data = request.get_json()

    if not data:
        return jsonify({"error": "Request body is required"}), 400

    status = data.get("status")
    if not status:
        return jsonify({"error": "Status is required"}), 400

    if status not in ["pending", "completed", "failed", "acknowledged"]:
        return jsonify({"error": "Invalid status"}), 400

    control = DeviceControl.query.filter_by(id=control_id, device_id=device_id).first()
    if not control:
        return jsonify({"error": "Control command not found"}), 404

    # Verify the authenticated device matches the requested device
    api_key = request.headers.get("X-API-Key")
    auth_device = Device.query.filter_by(api_key=api_key).first()
    if auth_device.id != device_id:
        return jsonify({"error": "Unauthorized"}), 403

    control.status = status
    db.session.commit()

    return (
        jsonify(
            {
                "id": control.id,
                "device_id": control.device_id,
                "command": control.command,
                "parameters": control.parameters,
                "status": control.status,
                "updated_at": control.updated_at.isoformat(),
            }
        ),
        200,
    )


@control_bp.route("/<int:device_id>/control/pending", methods=["GET"])
@authenticate_device
def get_pending_controls(device_id):
    # Verify the authenticated device matches the requested device
    api_key = request.headers.get("X-API-Key")
    auth_device = Device.query.filter_by(api_key=api_key).first()
    if auth_device.id != device_id:
        return jsonify({"error": "Unauthorized"}), 403

    controls = DeviceControl.query.filter_by(device_id=device_id, status="pending").all()
    result = [
        {
            "id": c.id,
            "device_id": c.device_id,
            "command": c.command,
            "parameters": c.parameters,
            "status": c.status,
            "created_at": c.created_at.isoformat(),
        }
        for c in controls
    ]
    return jsonify(result), 200
