"""
Device Groups Routes
API endpoints for managing device groups
"""

from flask import Blueprint, request, jsonify, current_app
from sqlalchemy.exc import IntegrityError
from src.models import db, User, Device, DeviceGroup, DeviceGroupMember

# Create blueprint
groups_bp = Blueprint("groups", __name__, url_prefix="/api/v1/groups")


def get_user_from_header():
    """Get user from X-User-ID header"""
    user_id = request.headers.get("X-User-ID")
    if not user_id:
        return None, (jsonify({"error": "X-User-ID header required"}), 401)
    
    user = User.query.filter_by(user_id=user_id).first()
    if not user:
        return None, (jsonify({"error": "Invalid user ID"}), 401)
    
    return user, None


@groups_bp.route("", methods=["POST"])
def create_group():
    """Create a new device group
    ---
    tags:
      - Device Groups
    summary: Create device group
    description: Create a new device group for organizing devices
    parameters:
      - name: X-User-ID
        in: header
        required: true
        schema:
          type: string
        description: User identifier
    requestBody:
      required: true
      content:
        application/json:
          schema:
            type: object
            required:
              - name
            properties:
              name:
                type: string
                example: Living Room
                description: Group name (must be unique per user)
              description:
                type: string
                example: All smart devices in the living room
              color:
                type: string
                example: "#FF5733"
                description: Hex color code
    responses:
      201:
        description: Group created successfully
      400:
        description: Bad request - missing required fields
      401:
        description: Unauthorized - invalid user ID
      409:
        description: Conflict - group name already exists
    """
    user, error = get_user_from_header()
    if error:
        return error
    
    data = request.get_json()
    if not data:
        return jsonify({"error": "Request body required"}), 400
    
    name = data.get("name")
    if not name:
        return jsonify({"error": "Group name is required"}), 400
    
    # Check for duplicate name for this user
    existing = DeviceGroup.query.filter_by(user_id=user.id, name=name).first()
    if existing:
        return jsonify({"error": "Group with this name already exists"}), 409
    
    # Create group
    group = DeviceGroup(
        name=name,
        description=data.get("description"),
        user_id=user.id,
        color=data.get("color")
    )
    
    try:
        db.session.add(group)
        db.session.commit()
        
        current_app.logger.info(f"Group '{name}' created by user {user.username}")
        
        return jsonify({
            "status": "success",
            "message": "Group created successfully",
            "group": group.to_dict()
        }), 201
        
    except Exception as e:
        db.session.rollback()
        current_app.logger.error(f"Error creating group: {str(e)}")
        return jsonify({"error": "Failed to create group"}), 500


@groups_bp.route("", methods=["GET"])
def list_groups():
    """List all groups for the authenticated user
    ---
    tags:
      - Device Groups
    summary: List user's groups
    description: Get all device groups belonging to the authenticated user
    parameters:
      - name: X-User-ID
        in: header
        required: true
        schema:
          type: string
      - name: include_devices
        in: query
        schema:
          type: boolean
          default: false
        description: Include device list in response
      - name: limit
        in: query
        schema:
          type: integer
          default: 100
          maximum: 1000
        description: Maximum number of results
      - name: offset
        in: query
        schema:
          type: integer
          default: 0
        description: Pagination offset
    responses:
      200:
        description: List of groups retrieved successfully
      401:
        description: Unauthorized - invalid user ID
    """
    user, error = get_user_from_header()
    if error:
        return error
    
    include_devices = request.args.get("include_devices", "false").lower() == "true"
    limit = min(int(request.args.get("limit", 100)), 1000)
    offset = int(request.args.get("offset", 0))
    
    groups = DeviceGroup.query.filter_by(user_id=user.id).limit(limit).offset(offset).all()
    total = DeviceGroup.query.filter_by(user_id=user.id).count()
    
    return jsonify({
        "status": "success",
        "groups": [g.to_dict(include_devices=include_devices) for g in groups],
        "meta": {
            "total": total,
            "limit": limit,
            "offset": offset
        }
    }), 200


@groups_bp.route("/<int:group_id>", methods=["GET"])
def get_group(group_id):
    """Get details of a specific group
    ---
    tags:
      - Device Groups
    summary: Get group details
    description: Get detailed information about a specific device group
    parameters:
      - name: X-User-ID
        in: header
        required: true
        schema:
          type: string
      - name: group_id
        in: path
        required: true
        schema:
          type: integer
        description: Group ID
      - name: include_devices
        in: query
        schema:
          type: boolean
          default: true
        description: Include device list in response
    responses:
      200:
        description: Group details retrieved successfully
      401:
        description: Unauthorized - invalid user ID
      403:
        description: Forbidden - group doesn't belong to user
      404:
        description: Not found - group not found
    """
    user, error = get_user_from_header()
    if error:
        return error
    
    group = DeviceGroup.query.get(group_id)
    if not group:
        return jsonify({"error": "Group not found"}), 404
    
    if group.user_id != user.id:
        return jsonify({"error": "Forbidden: group doesn't belong to user"}), 403
    
    include_devices = request.args.get("include_devices", "true").lower() == "true"
    
    return jsonify({
        "status": "success",
        "group": group.to_dict(include_devices=include_devices)
    }), 200


@groups_bp.route("/<int:group_id>", methods=["PUT"])
def update_group(group_id):
    """Update a group
    ---
    tags:
      - Device Groups
    summary: Update group
    description: Update device group information
    parameters:
      - name: X-User-ID
        in: header
        required: true
        schema:
          type: string
      - name: group_id
        in: path
        required: true
        schema:
          type: integer
    requestBody:
      required: true
      content:
        application/json:
          schema:
            type: object
            properties:
              name:
                type: string
                example: Living Room Smart Devices
              description:
                type: string
                example: Updated description
              color:
                type: string
                example: "#33FF57"
    responses:
      200:
        description: Group updated successfully
      401:
        description: Unauthorized - invalid user ID
      403:
        description: Forbidden - group doesn't belong to user
      404:
        description: Not found - group not found
    """
    user, error = get_user_from_header()
    if error:
        return error
    
    group = DeviceGroup.query.get(group_id)
    if not group:
        return jsonify({"error": "Group not found"}), 404
    
    if group.user_id != user.id:
        return jsonify({"error": "Forbidden: group doesn't belong to user"}), 403
    
    data = request.get_json()
    if not data:
        return jsonify({"error": "Request body required"}), 400
    
    # Update fields
    if "name" in data:
        group.name = data["name"]
    if "description" in data:
        group.description = data["description"]
    if "color" in data:
        group.color = data["color"]
    
    try:
        db.session.commit()
        
        return jsonify({
            "status": "success",
            "message": "Group updated successfully",
            "group": group.to_dict()
        }), 200
        
    except Exception as e:
        db.session.rollback()
        current_app.logger.error(f"Error updating group: {str(e)}")
        return jsonify({"error": "Failed to update group"}), 500


@groups_bp.route("/<int:group_id>", methods=["DELETE"])
def delete_group(group_id):
    """Delete a group
    ---
    tags:
      - Device Groups
    summary: Delete group
    description: Delete a device group (devices are not deleted)
    parameters:
      - name: X-User-ID
        in: header
        required: true
        schema:
          type: string
      - name: group_id
        in: path
        required: true
        schema:
          type: integer
    responses:
      200:
        description: Group deleted successfully
      401:
        description: Unauthorized - invalid user ID
      403:
        description: Forbidden - group doesn't belong to user
      404:
        description: Not found - group not found
    """
    user, error = get_user_from_header()
    if error:
        return error
    
    group = DeviceGroup.query.get(group_id)
    if not group:
        return jsonify({"error": "Group not found"}), 404
    
    if group.user_id != user.id:
        return jsonify({"error": "Forbidden: group doesn't belong to user"}), 403
    
    group_name = group.name
    
    try:
        db.session.delete(group)
        db.session.commit()
        
        return jsonify({
            "status": "success",
            "message": f"Group '{group_name}' deleted successfully"
        }), 200
        
    except Exception as e:
        db.session.rollback()
        current_app.logger.error(f"Error deleting group: {str(e)}")
        return jsonify({"error": "Failed to delete group"}), 500


@groups_bp.route("/<int:group_id>/devices", methods=["POST"])
def add_device_to_group(group_id):
    """Add a device to a group
    ---
    tags:
      - Device Groups
    summary: Add device to group
    description: Add a single device to a device group
    parameters:
      - name: X-User-ID
        in: header
        required: true
        schema:
          type: string
      - name: group_id
        in: path
        required: true
        schema:
          type: integer
    requestBody:
      required: true
      content:
        application/json:
          schema:
            type: object
            required:
              - device_id
            properties:
              device_id:
                type: integer
                example: 5
    responses:
      201:
        description: Device added to group successfully
      400:
        description: Bad request - missing device_id
      401:
        description: Unauthorized - invalid user ID
      403:
        description: Forbidden - device doesn't belong to user
      404:
        description: Not found - group or device not found
      409:
        description: Conflict - device already in group
    """
    user, error = get_user_from_header()
    if error:
        return error
    
    group = DeviceGroup.query.get(group_id)
    if not group:
        return jsonify({"error": "Group not found"}), 404
    
    if group.user_id != user.id:
        return jsonify({"error": "Forbidden: group doesn't belong to user"}), 403
    
    data = request.get_json()
    if not data or "device_id" not in data:
        return jsonify({"error": "device_id is required"}), 400
    
    device_id = data["device_id"]
    device = Device.query.get(device_id)
    
    if not device:
        return jsonify({"error": "Device not found"}), 404
    
    if device.user_id != user.id:
        return jsonify({"error": "Forbidden: device doesn't belong to user"}), 403
    
    # Check if already in group
    existing = DeviceGroupMember.query.filter_by(
        group_id=group_id,
        device_id=device_id
    ).first()
    
    if existing:
        return jsonify({"error": "Device already in group"}), 409
    
    # Add device to group
    membership = DeviceGroupMember(
        group_id=group_id,
        device_id=device_id
    )
    
    try:
        db.session.add(membership)
        db.session.commit()
        
        return jsonify({
            "status": "success",
            "message": "Device added to group successfully",
            "membership": membership.to_dict()
        }), 201
        
    except IntegrityError:
        db.session.rollback()
        return jsonify({"error": "Device already in group"}), 409
    except Exception as e:
        db.session.rollback()
        current_app.logger.error(f"Error adding device to group: {str(e)}")
        return jsonify({"error": "Failed to add device to group"}), 500


@groups_bp.route("/<int:group_id>/devices/<int:device_id>", methods=["DELETE"])
def remove_device_from_group(group_id, device_id):
    """Remove a device from a group
    ---
    tags:
      - Device Groups
    summary: Remove device from group
    description: Remove a device from a device group
    parameters:
      - name: X-User-ID
        in: header
        required: true
        schema:
          type: string
      - name: group_id
        in: path
        required: true
        schema:
          type: integer
      - name: device_id
        in: path
        required: true
        schema:
          type: integer
    responses:
      200:
        description: Device removed from group successfully
      401:
        description: Unauthorized - invalid user ID
      403:
        description: Forbidden - group doesn't belong to user
      404:
        description: Not found - device not in group
    """
    user, error = get_user_from_header()
    if error:
        return error
    
    group = DeviceGroup.query.get(group_id)
    if not group:
        return jsonify({"error": "Group not found"}), 404
    
    if group.user_id != user.id:
        return jsonify({"error": "Forbidden: group doesn't belong to user"}), 403
    
    membership = DeviceGroupMember.query.filter_by(
        group_id=group_id,
        device_id=device_id
    ).first()
    
    if not membership:
        return jsonify({"error": "Device not in group"}), 404
    
    try:
        db.session.delete(membership)
        db.session.commit()
        
        return jsonify({
            "status": "success",
            "message": "Device removed from group successfully"
        }), 200
        
    except Exception as e:
        db.session.rollback()
        current_app.logger.error(f"Error removing device from group: {str(e)}")
        return jsonify({"error": "Failed to remove device from group"}), 500


@groups_bp.route("/<int:group_id>/devices", methods=["GET"])
def list_group_devices(group_id):
    """List all devices in a group
    ---
    tags:
      - Device Groups
    summary: List group's devices
    description: Get all devices in a specific group
    parameters:
      - name: X-User-ID
        in: header
        required: true
        schema:
          type: string
      - name: group_id
        in: path
        required: true
        schema:
          type: integer
      - name: status
        in: query
        schema:
          type: string
          enum: [active, inactive, maintenance]
        description: Filter by device status
      - name: device_type
        in: query
        schema:
          type: string
        description: Filter by device type
      - name: limit
        in: query
        schema:
          type: integer
          default: 100
          maximum: 1000
      - name: offset
        in: query
        schema:
          type: integer
          default: 0
    responses:
      200:
        description: List of devices retrieved successfully
      401:
        description: Unauthorized - invalid user ID
      403:
        description: Forbidden - group doesn't belong to user
      404:
        description: Not found - group not found
    """
    user, error = get_user_from_header()
    if error:
        return error
    
    group = DeviceGroup.query.get(group_id)
    if not group:
        return jsonify({"error": "Group not found"}), 404
    
    if group.user_id != user.id:
        return jsonify({"error": "Forbidden: group doesn't belong to user"}), 403
    
    limit = min(int(request.args.get("limit", 100)), 1000)
    offset = int(request.args.get("offset", 0))
    
    memberships = DeviceGroupMember.query.filter_by(group_id=group_id).limit(limit).offset(offset).all()
    total = DeviceGroupMember.query.filter_by(group_id=group_id).count()
    
    devices = []
    for membership in memberships:
        device_dict = membership.device.to_dict()
        device_dict['added_to_group_at'] = membership.added_at.isoformat() if membership.added_at else None
        devices.append(device_dict)
    
    return jsonify({
        "status": "success",
        "group_id": group_id,
        "group_name": group.name,
        "devices": devices,
        "meta": {
            "total": total,
            "limit": limit,
            "offset": offset
        }
    }), 200


@groups_bp.route("/<int:group_id>/devices/bulk", methods=["POST"])
def bulk_add_devices(group_id):
    """Add multiple devices to a group
    ---
    tags:
      - Device Groups
    summary: Bulk add devices
    description: Add multiple devices to a group in a single request
    parameters:
      - name: X-User-ID
        in: header
        required: true
        schema:
          type: string
      - name: group_id
        in: path
        required: true
        schema:
          type: integer
    requestBody:
      required: true
      content:
        application/json:
          schema:
            type: object
            required:
              - device_ids
            properties:
              device_ids:
                type: array
                items:
                  type: integer
                example: [1, 2, 3, 4, 5]
    responses:
      201:
        description: Devices added successfully (returns counts)
      400:
        description: Bad request - missing or invalid device_ids
      401:
        description: Unauthorized - invalid user ID
      403:
        description: Forbidden - group doesn't belong to user
      404:
        description: Not found - group not found
    """
    user, error = get_user_from_header()
    if error:
        return error
    
    group = DeviceGroup.query.get(group_id)
    if not group:
        return jsonify({"error": "Group not found"}), 404
    
    if group.user_id != user.id:
        return jsonify({"error": "Forbidden: group doesn't belong to user"}), 403
    
    data = request.get_json()
    if not data or "device_ids" not in data:
        return jsonify({"error": "device_ids array is required"}), 400
    
    device_ids = data["device_ids"]
    if not isinstance(device_ids, list):
        return jsonify({"error": "device_ids must be an array"}), 400
    
    added = []
    skipped = []
    
    for device_id in device_ids:
        device = Device.query.get(device_id)
        
        if not device or device.user_id != user.id:
            skipped.append(device_id)
            continue
        
        # Check if already in group
        existing = DeviceGroupMember.query.filter_by(
            group_id=group_id,
            device_id=device_id
        ).first()
        
        if existing:
            skipped.append(device_id)
            continue
        
        # Add device to group
        membership = DeviceGroupMember(
            group_id=group_id,
            device_id=device_id
        )
        db.session.add(membership)
        added.append(device_id)
    
    try:
        db.session.commit()
        
        return jsonify({
            "status": "success",
            "message": f"{len(added)} devices added to group",
            "added": len(added),
            "skipped": len(skipped),
            "details": {
                "added_device_ids": added,
                "skipped_device_ids": skipped
            }
        }), 201
        
    except Exception as e:
        db.session.rollback()
        current_app.logger.error(f"Error bulk adding devices: {str(e)}")
        return jsonify({"error": "Failed to add devices to group"}), 500
