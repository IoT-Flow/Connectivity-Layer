from flask import Blueprint, request, jsonify
from src.models import db, Device, DeviceControl
from src.mqtt.mqtt_client import publish_device_command

control_bp = Blueprint("control", __name__, url_prefix="/api/v1/devices")


@control_bp.route("/<int:device_id>/control", methods=["POST"])
def control_device(device_id):
    data = request.get_json()
    command = data.get("command")
    parameters = data.get("parameters", {})

    device = Device.query.get(device_id)
    if not device:
        return jsonify({"error": "Device not found"}), 404

    # Store command in DB for tracking
    control = DeviceControl(
        device_id=device_id, command=command, parameters=parameters, status="pending"
    )
    db.session.add(control)
    db.session.commit()
    publish_device_command(device_id, command, parameters)
    return jsonify({"message": "Command sent via MQTT", "control_id": control.id}), 201


@control_bp.route("/<int:device_id>/control/<int:control_id>/status", methods=["POST"])
def update_control_status(device_id, control_id):
    data = request.get_json()
    status = data.get("status")
    if status not in ["acknowledged", "failed"]:
        return jsonify({"error": "Invalid status"}), 400
    control = DeviceControl.query.filter_by(id=control_id, device_id=device_id).first()
    if not control:
        return jsonify({"error": "Control command not found"}), 404
    control.status = status
    db.session.commit()
    return jsonify({"message": "Status updated"}), 200


@control_bp.route("/<int:device_id>/control/pending", methods=["GET"])
def get_pending_controls(device_id):
    controls = DeviceControl.query.filter_by(device_id=device_id, status="pending").all()
    result = [
        {
            "id": c.id,
            "command": c.command,
            "parameters": c.parameters,
            "created_at": c.created_at.isoformat(),
        }
        for c in controls
    ]
    return jsonify(result), 200
