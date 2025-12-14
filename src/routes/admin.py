from flask import Blueprint, request, jsonify, current_app
from src.models import Device, DeviceAuth, DeviceConfiguration, db
from src.middleware.auth import require_admin_token
from datetime import datetime, timezone, timedelta
from src.services.device_status_cache import (
    DEVICE_STATUS_PREFIX,
    DEVICE_LASTSEEN_PREFIX,
)

# Create blueprint for admin routes
admin_bp = Blueprint("admin", __name__, url_prefix="/api/v1/admin")


@admin_bp.route("/devices", methods=["GET"])
@require_admin_token
def list_all_devices():
    """Enhanced admin endpoint to list all devices with complete information"""
    try:
        from src.models import User
        from src.services.iotdb import IoTDBService
        from sqlalchemy.orm import joinedload

        # Parse query parameters
        status_filter = request.args.get("status")
        device_type_filter = request.args.get("device_type")
        user_id_filter = request.args.get("user_id")
        search_query = request.args.get("search")
        page = int(request.args.get("page", 1))
        per_page = min(int(request.args.get("per_page", 50)), 100)  # Max 100 per page

        # Build query with filters
        query = Device.query.options(joinedload(Device.owner))

        # Apply filters
        if status_filter:
            query = query.filter(Device.status == status_filter)
        if device_type_filter:
            query = query.filter(Device.device_type == device_type_filter)
        if user_id_filter:
            query = query.filter(Device.user_id == int(user_id_filter))
        if search_query:
            search_pattern = f"%{search_query}%"
            query = query.filter(
                db.or_(
                    Device.name.ilike(search_pattern),
                    Device.description.ilike(search_pattern),
                    Device.location.ilike(search_pattern),
                )
            )

        # Get total count for pagination
        total_devices = query.count()

        # Apply pagination
        devices = query.offset((page - 1) * per_page).limit(per_page).all()

        # Initialize IoTDB service for telemetry stats
        iotdb_service = IoTDBService()
        iotdb_available = iotdb_service.is_available()

        device_list = []
        device_type_counts = {}
        status_counts = {}

        for device in devices:
            # Get complete device information
            device_dict = device.to_dict()

            # Add online/offline status from status tracker
            if hasattr(current_app, "status_tracker") and current_app.status_tracker and current_app.status_tracker.available:
                is_online = current_app.status_tracker.is_device_online(device.id)
                device_dict["is_online"] = is_online
                device_dict["status"] = "online" if is_online else "offline"
                device_dict["registration_status"] = device.status  # Keep original status
            else:
                # Fallback to database status
                device_dict["registration_status"] = device.status
                device_dict["status"] = device.status

            # Note: API key is intentionally excluded for security reasons
            # Admin can see device details but not the actual API key

            # Add owner information
            if device.owner:
                device_dict["owner"] = {
                    "username": device.owner.username,
                    "email": device.owner.email,
                    "user_id": device.owner.user_id,
                    "id": device.owner.id,
                }
            else:
                device_dict["owner"] = None

            # Add configurations
            configurations = DeviceConfiguration.query.filter_by(device_id=device.id, is_active=True).all()
            config_list = []
            for config in configurations:
                config_list.append(
                    {
                        "id": config.id,
                        "config_key": config.config_key,
                        "config_value": config.config_value,
                        "data_type": config.data_type,
                        "created_at": config.created_at.isoformat() if config.created_at else None,
                        "updated_at": config.updated_at.isoformat() if config.updated_at else None,
                    }
                )
            device_dict["configurations"] = config_list

            # Add auth records
            auth_records = DeviceAuth.query.filter_by(device_id=device.id).all()
            auth_list = []
            for auth in auth_records:
                auth_list.append(
                    {
                        "id": auth.id,
                        "api_key_hash": auth.api_key_hash,
                        "is_active": auth.is_active,
                        "expires_at": auth.expires_at.isoformat() if auth.expires_at else None,
                        "created_at": auth.created_at.isoformat() if auth.created_at else None,
                        "last_used": auth.last_used.isoformat() if auth.last_used else None,
                        "usage_count": auth.usage_count,
                    }
                )
            device_dict["auth_records"] = auth_list

            # Add telemetry statistics
            telemetry_stats = {"iotdb_available": iotdb_available, "total_records": 0}

            if iotdb_available:
                try:
                    telemetry_count = iotdb_service.get_telemetry_count(
                        device_id=str(device.id), start_time="-30d"  # Last 30 days
                    )
                    telemetry_stats["total_records"] = telemetry_count
                except Exception as e:
                    current_app.logger.warning(f"Failed to get telemetry count for device {device.id}: {e}")

            device_dict["telemetry_stats"] = telemetry_stats

            # Count device types and statuses for statistics
            device_type_counts[device.device_type] = device_type_counts.get(device.device_type, 0) + 1
            status_counts[device.status] = status_counts.get(device.status, 0) + 1

            device_list.append(device_dict)

        # Calculate pagination info
        total_pages = (total_devices + per_page - 1) // per_page

        # Get additional statistics
        total_users_with_devices = db.session.query(Device.user_id).distinct().count()

        # Build response
        response = {
            "status": "success",
            "devices": device_list,
            "total_devices": total_devices,
            "pagination": {"page": page, "per_page": per_page, "total": total_devices, "pages": total_pages},
            "metadata": {
                "device_types": device_type_counts,
                "status_counts": status_counts,
                "users_with_devices": total_users_with_devices,
                "iotdb_available": iotdb_available,
            },
        }

        return jsonify(response), 200

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
    """Get detailed device information including auth and config"""
    from src.models import User
    from src.services.iotdb import IoTDBService
    from sqlalchemy.orm import joinedload

    device = Device.query.options(joinedload(Device.owner)).get_or_404(device_id)

    try:
        # Get complete device information
        device_dict = device.to_dict()

        # Note: API key is intentionally excluded for security reasons
        # Admin can see device details but not the actual API key

        # Add owner information
        if device.owner:
            device_dict["owner"] = {
                "username": device.owner.username,
                "email": device.owner.email,
                "user_id": device.owner.user_id,
                "id": device.owner.id,
            }
        else:
            device_dict["owner"] = None

        # Get device auth records
        auth_records_query = DeviceAuth.query.filter_by(device_id=device_id).all()
        auth_records = []
        for auth in auth_records_query:
            auth_dict = {
                "id": auth.id,
                "api_key_hash": auth.api_key_hash,
                "is_active": auth.is_active,
                "expires_at": auth.expires_at.isoformat() if auth.expires_at else None,
                "created_at": auth.created_at.isoformat() if auth.created_at else None,
                "last_used": auth.last_used.isoformat() if auth.last_used else None,
                "usage_count": auth.usage_count,
            }
            auth_records.append(auth_dict)

        # Get device configurations
        configurations_query = DeviceConfiguration.query.filter_by(device_id=device_id, is_active=True).all()
        configurations = []
        for config in configurations_query:
            configurations.append(
                {
                    "id": config.id,
                    "config_key": config.config_key,
                    "config_value": config.config_value,
                    "data_type": config.data_type,
                    "created_at": config.created_at.isoformat() if config.created_at else None,
                    "updated_at": config.updated_at.isoformat() if config.updated_at else None,
                }
            )

        # Add telemetry statistics
        iotdb_service = IoTDBService()
        iotdb_available = iotdb_service.is_available()

        telemetry_stats = {
            "iotdb_available": iotdb_available,
            "total_records": 0,
            "last_30_days": 0,
            "last_7_days": 0,
            "last_24_hours": 0,
        }

        if iotdb_available:
            try:
                telemetry_stats["total_records"] = iotdb_service.get_telemetry_count(device_id=str(device_id))
                telemetry_stats["last_30_days"] = iotdb_service.get_telemetry_count(
                    device_id=str(device_id), start_time="-30d"
                )
                telemetry_stats["last_7_days"] = iotdb_service.get_telemetry_count(
                    device_id=str(device_id), start_time="-7d"
                )
                telemetry_stats["last_24_hours"] = iotdb_service.get_telemetry_count(
                    device_id=str(device_id), start_time="-24h"
                )
            except Exception as e:
                current_app.logger.warning(f"Failed to get telemetry stats for device {device_id}: {e}")

        return (
            jsonify(
                {
                    "status": "success",
                    "device": device_dict,
                    "auth_records": auth_records,
                    "configurations": configurations,
                    "telemetry_stats": telemetry_stats,
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
    device = Device.query.get_or_404(device_id)

    try:
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
    """Get system statistics"""
    try:
        # Device statistics
        total_devices = Device.query.count()
        active_devices = Device.query.filter_by(status="active").count()
        inactive_devices = Device.query.filter_by(status="inactive").count()
        maintenance_devices = Device.query.filter_by(status="maintenance").count()

        # Online/offline statistics (devices seen in last 5 minutes)
        five_minutes_ago = datetime.now(timezone.utc) - timedelta(minutes=5)
        online_devices = Device.query.filter(Device.last_seen >= five_minutes_ago, Device.status == "active").count()

        # Auth statistics
        total_auth_records = DeviceAuth.query.count()
        active_auth_records = DeviceAuth.query.filter_by(is_active=True).count()

        # Configuration statistics
        total_configs = DeviceConfiguration.query.count()
        active_configs = DeviceConfiguration.query.filter_by(is_active=True).count()

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
                    "auth_stats": {
                        "total_records": total_auth_records,
                        "active_records": active_auth_records,
                    },
                    "config_stats": {
                        "total_configs": total_configs,
                        "active_configs": active_configs,
                    },
                    "telemetry_note": "Telemetry data is stored in IoTDB, not accessible via this API",
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
    device = Device.query.get_or_404(device_id)

    try:
        device_name = device.name

        # Delete related auth records and configurations (cascaded by relationships)
        db.session.delete(device)
        db.session.commit()

        current_app.logger.info(f"Device {device_name} (ID: {device_id}) deleted")

        return (
            jsonify(
                {
                    "status": "success",
                    "message": f"Device {device_name} deleted successfully",
                    "device_id": device_id,
                    "note": "Telemetry data in IoTDB is not automatically deleted",
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


@admin_bp.route("/cache/device-status", methods=["DELETE"])
@require_admin_token
def clear_device_status_cache():
    """Clear all device status cache data from Redis"""
    try:
        # Check if Redis cache is available
        if not hasattr(current_app, "device_status_cache") or not current_app.device_status_cache:
            return (
                jsonify(
                    {
                        "status": "error",
                        "message": "Device status cache is not available",
                    }
                ),
                503,
            )

        # Clear all device caches
        success = current_app.device_status_cache.clear_all_device_caches()

        if success:
            return (
                jsonify(
                    {
                        "status": "success",
                        "message": "All device status caches cleared successfully",
                    }
                ),
                200,
            )
        else:
            return (
                jsonify(
                    {
                        "status": "error",
                        "message": "Failed to clear device status caches",
                    }
                ),
                500,
            )

    except Exception as e:
        current_app.logger.error(f"Error clearing device status cache: {str(e)}")
        return (
            jsonify(
                {
                    "error": "Cache operation failed",
                    "message": "An error occurred while clearing the device status cache",
                }
            ),
            500,
        )


@admin_bp.route("/cache/devices/<int:device_id>", methods=["DELETE"])
@require_admin_token
def clear_device_cache(device_id):
    """Clear cached data for a specific device"""
    try:
        # Check if device exists
        device = Device.query.filter_by(id=device_id).first()
        if not device:
            return (
                jsonify(
                    {
                        "error": "Device not found",
                        "message": f"No device found with ID {device_id}",
                    }
                ),
                404,
            )

        # Check if Redis cache is available
        if not hasattr(current_app, "device_status_cache") or not current_app.device_status_cache:
            return (
                jsonify(
                    {
                        "status": "error",
                        "message": "Device status cache is not available",
                    }
                ),
                503,
            )

        # Clear device cache
        success = current_app.device_status_cache.clear_device_cache(device_id)

        if success:
            return (
                jsonify(
                    {
                        "status": "success",
                        "message": f"Cache cleared for device {device_id}",
                    }
                ),
                200,
            )
        else:
            return (
                jsonify(
                    {
                        "status": "error",
                        "message": f"Failed to clear cache for device {device_id}",
                    }
                ),
                500,
            )

    except Exception as e:
        current_app.logger.error(f"Error clearing device cache: {str(e)}")
        return (
            jsonify(
                {
                    "error": "Cache operation failed",
                    "message": f"An error occurred while clearing the cache for device {device_id}",
                }
            ),
            500,
        )


@admin_bp.route("/cache/device-status", methods=["GET"])
@require_admin_token
def get_cache_stats():
    """Get statistics about the device status cache"""
    try:
        # Check if Redis cache is available
        if not hasattr(current_app, "device_status_cache") or not current_app.device_status_cache:
            return (
                jsonify(
                    {
                        "status": "error",
                        "message": "Device status cache is not available",
                    }
                ),
                503,
            )

        # Check if Redis client is available
        if not current_app.device_status_cache.available:
            return (
                jsonify({"status": "error", "message": "Redis connection is not available"}),
                503,
            )

        # Get Redis info
        redis_client = current_app.device_status_cache.redis

        # Get all cache keys
        status_keys = redis_client.keys(f"{DEVICE_STATUS_PREFIX}*")
        lastseen_keys = redis_client.keys(f"{DEVICE_LASTSEEN_PREFIX}*")

        # Get Redis info
        redis_info = redis_client.info()

        return (
            jsonify(
                {
                    "status": "success",
                    "cache_stats": {
                        "device_status_count": len(status_keys),
                        "device_lastseen_count": len(lastseen_keys),
                        "redis_memory_used": redis_info.get("used_memory_human", "unknown"),
                        "redis_uptime": redis_info.get("uptime_in_seconds", 0),
                        "redis_version": redis_info.get("redis_version", "unknown"),
                    },
                }
            ),
            200,
        )

    except Exception as e:
        current_app.logger.error(f"Error getting cache stats: {str(e)}")
        return (
            jsonify(
                {
                    "error": "Cache operation failed",
                    "message": "An error occurred while getting cache statistics",
                }
            ),
            500,
        )


# Redis-to-Database Sync Management Endpoints


@admin_bp.route("/redis-db-sync/status", methods=["GET"])
@require_admin_token
def get_redis_db_sync_status():
    """Get Redis-to-Database synchronization status"""
    try:
        if not hasattr(current_app, "device_status_cache") or not current_app.device_status_cache:
            return (
                jsonify(
                    {
                        "status": "not_available",
                        "message": "Device status cache not available",
                    }
                ),
                200,
            )

        cache = current_app.device_status_cache

        return (
            jsonify(
                {
                    "status": "success",
                    "redis_db_sync": {
                        "enabled": cache.is_database_sync_enabled(),
                        "redis_available": cache.available,
                        "callback_count": len(cache.status_change_callbacks),
                    },
                }
            ),
            200,
        )

    except Exception as e:
        current_app.logger.error(f"Error getting Redis-DB sync status: {str(e)}")
        return jsonify({"error": "Failed to get sync status", "message": str(e)}), 500


@admin_bp.route("/redis-db-sync/enable", methods=["POST"])
@require_admin_token
def enable_redis_db_sync():
    """Enable Redis-to-Database synchronization"""
    try:
        if not hasattr(current_app, "device_status_cache") or not current_app.device_status_cache:
            return (
                jsonify(
                    {
                        "error": "Service not available",
                        "message": "Device status cache not available",
                    }
                ),
                400,
            )

        cache = current_app.device_status_cache
        cache.enable_database_sync()

        return (
            jsonify(
                {
                    "status": "success",
                    "message": "Redis-to-Database synchronization enabled",
                }
            ),
            200,
        )

    except Exception as e:
        current_app.logger.error(f"Error enabling Redis-DB sync: {str(e)}")
        return jsonify({"error": "Failed to enable sync", "message": str(e)}), 500


@admin_bp.route("/redis-db-sync/disable", methods=["POST"])
@require_admin_token
def disable_redis_db_sync():
    """Disable Redis-to-Database synchronization"""
    try:
        if not hasattr(current_app, "device_status_cache") or not current_app.device_status_cache:
            return (
                jsonify(
                    {
                        "error": "Service not available",
                        "message": "Device status cache not available",
                    }
                ),
                400,
            )

        cache = current_app.device_status_cache
        cache.disable_database_sync()

        return (
            jsonify(
                {
                    "status": "success",
                    "message": "Redis-to-Database synchronization disabled",
                }
            ),
            200,
        )

    except Exception as e:
        current_app.logger.error(f"Error disabling Redis-DB sync: {str(e)}")
        return jsonify({"error": "Failed to disable sync", "message": str(e)}), 500


@admin_bp.route("/redis-db-sync/force-sync/<int:device_id>", methods=["POST"])
@require_admin_token
def force_sync_device_to_db(device_id):
    """Force synchronization of a specific device status to database"""
    try:
        if not hasattr(current_app, "device_status_cache") or not current_app.device_status_cache:
            return (
                jsonify(
                    {
                        "error": "Service not available",
                        "message": "Device status cache not available",
                    }
                ),
                400,
            )

        cache = current_app.device_status_cache

        # Check if device exists
        device = Device.query.get(device_id)
        if not device:
            return (
                jsonify(
                    {
                        "error": "Device not found",
                        "message": f"Device with ID {device_id} does not exist",
                    }
                ),
                404,
            )

        # Force sync
        success = cache.force_sync_device_to_database(device_id)

        if success:
            # Get updated status
            redis_status = cache.get_device_status(device_id)
            db.session.refresh(device)

            return (
                jsonify(
                    {
                        "status": "success",
                        "message": f"Device {device_id} status synchronized successfully",
                        "sync_result": {
                            "device_id": device_id,
                            "redis_status": redis_status,
                            "database_status": device.status,
                        },
                    }
                ),
                200,
            )
        else:
            return (
                jsonify(
                    {
                        "error": "Sync failed",
                        "message": f"Failed to synchronize device {device_id} status",
                    }
                ),
                500,
            )

    except Exception as e:
        current_app.logger.error(f"Error forcing device sync: {str(e)}")
        return jsonify({"error": "Force sync operation failed", "message": str(e)}), 500


@admin_bp.route("/redis-db-sync/bulk-sync", methods=["POST"])
@require_admin_token
def bulk_sync_devices_to_db():
    """Force synchronization of all devices with Redis status to database"""
    try:
        if not hasattr(current_app, "device_status_cache") or not current_app.device_status_cache:
            return (
                jsonify(
                    {
                        "error": "Service not available",
                        "message": "Device status cache not available",
                    }
                ),
                400,
            )

        cache = current_app.device_status_cache

        # Get all devices
        devices = Device.query.all()

        sync_results = {
            "total_devices": len(devices),
            "synced_devices": 0,
            "failed_devices": 0,
            "skipped_devices": 0,  # Devices without Redis status
            "details": [],
        }

        for device in devices:
            redis_status = cache.get_device_status(device.id)

            if not redis_status:
                sync_results["skipped_devices"] += 1
                continue

            try:
                success = cache.force_sync_device_to_database(device.id)

                if success:
                    sync_results["synced_devices"] += 1
                    db.session.refresh(device)
                    sync_results["details"].append(
                        {
                            "device_id": device.id,
                            "device_name": device.name,
                            "redis_status": redis_status,
                            "database_status": device.status,
                            "result": "success",
                        }
                    )
                else:
                    sync_results["failed_devices"] += 1
                    sync_results["details"].append(
                        {
                            "device_id": device.id,
                            "device_name": device.name,
                            "result": "failed",
                        }
                    )

            except Exception as e:
                sync_results["failed_devices"] += 1
                sync_results["details"].append(
                    {
                        "device_id": device.id,
                        "device_name": device.name,
                        "result": "error",
                        "error": str(e),
                    }
                )

        return (
            jsonify(
                {
                    "status": "success",
                    "message": "Bulk synchronization completed",
                    "sync_results": sync_results,
                }
            ),
            200,
        )

    except Exception as e:
        current_app.logger.error(f"Error in bulk device sync: {str(e)}")
        return jsonify({"error": "Bulk sync operation failed", "message": str(e)}), 500
