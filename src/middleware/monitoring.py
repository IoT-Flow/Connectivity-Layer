"""
Advanced monitoring and health check middleware
"""

import time
import psutil
from flask import current_app, jsonify, request
from functools import wraps
from src.models import Device, db
from datetime import datetime, timezone, timedelta


class HealthMonitor:
    """System health monitoring service"""

    @staticmethod
    def get_system_health():
        """Get comprehensive system health status"""
        health_data = {
            "status": "healthy",
            "timestamp": datetime.now(timezone.utc).isoformat(),
            "checks": {},
            "metrics": {},
        }

        try:
            # Database health
            health_data["checks"]["database"] = HealthMonitor._check_database()

            # System metrics
            health_data["metrics"]["system"] = HealthMonitor._get_system_metrics()

            # Application metrics
            health_data["metrics"]["application"] = HealthMonitor._get_app_metrics()

            # Device status summary
            health_data["metrics"]["devices"] = HealthMonitor._get_device_metrics()

            # Determine overall status
            failed_checks = [name for name, check in health_data["checks"].items() if not check.get("healthy", False)]

            if failed_checks:
                health_data["status"] = "degraded" if len(failed_checks) == 1 else "unhealthy"
                health_data["failed_checks"] = failed_checks

        except Exception as e:
            health_data["status"] = "error"
            health_data["error"] = str(e)
            current_app.logger.error(f"Health check error: {str(e)}")

        return health_data

    @staticmethod
    def _check_database():
        """Check database connectivity and performance"""
        try:
            start_time = time.time()
            from sqlalchemy import text

            db.session.execute(text("SELECT 1"))
            db.session.commit()
            response_time = (time.time() - start_time) * 1000  # ms

            return {
                "healthy": True,
                "response_time_ms": round(response_time, 2),
                "status": "connected",
            }
        except Exception as e:
            return {"healthy": False, "error": str(e), "status": "disconnected"}

    @staticmethod
    def _get_system_metrics():
        """Get system performance metrics"""
        try:
            return {
                "cpu_percent": psutil.cpu_percent(interval=1),
                "memory_percent": psutil.virtual_memory().percent,
                "memory_available_mb": round(psutil.virtual_memory().available / 1024 / 1024, 2),
                "disk_usage_percent": psutil.disk_usage("/").percent,
                "load_average": (list(psutil.getloadavg()) if hasattr(psutil, "getloadavg") else None),
            }
        except Exception as e:
            current_app.logger.error(f"System metrics error: {str(e)}")
            return {"error": str(e)}

    @staticmethod
    def _get_app_metrics():
        """Get application-specific metrics"""
        try:
            # Get uptime (approximate)
            return {
                "flask_env": current_app.config.get("ENV"),
                "debug_mode": current_app.debug,
                "testing_mode": current_app.testing,
            }
        except Exception as e:
            current_app.logger.error(f"App metrics error: {str(e)}")
            return {"error": str(e)}

    @staticmethod
    def _get_device_metrics():
        """Get device-related metrics"""
        try:
            now = datetime.now(timezone.utc)
            online_threshold = now - timedelta(minutes=5)

            total_devices = Device.query.count()
            active_devices = Device.query.filter_by(status="active").count()
            online_devices = Device.query.filter(
                Device.last_seen >= online_threshold, Device.status == "active"
            ).count()

            # Telemetry metrics (stored in PostgreSQL)
            telemetry_last_hour = 0  # Can be implemented with PostgreSQL query
            telemetry_last_day = 0  # Can be implemented with PostgreSQL query

            return {
                "total_devices": total_devices,
                "active_devices": active_devices,
                "online_devices": online_devices,
                "offline_devices": active_devices - online_devices,
                "telemetry_last_hour": telemetry_last_hour,
                "telemetry_last_day": telemetry_last_day,
            }
        except Exception as e:
            try:
                current_app.logger.error(f"Device metrics error: {str(e)}")
            except Exception:
                # Fallback if current_app is not available
                print(f"Device metrics error: {str(e)}")
            return {"error": str(e)}




def device_heartbeat_monitor():
    """Monitor device heartbeats and update status"""

    def decorator(f):
        @wraps(f)
        def decorated_function(*args, **kwargs):
            if hasattr(request, "device"):
                device = request.device

                # Device heartbeat managed in database only

                # Update last_seen in database
                device.update_last_seen()

            return f(*args, **kwargs)

        return decorated_function

    return decorator


def request_metrics_middleware():
    """Middleware to collect request metrics"""

    def decorator(f):
        @wraps(f)
        def decorated_function(*args, **kwargs):
            start_time = time.time()

            # Execute request
            try:
                response = f(*args, **kwargs)
                status_code = getattr(response, "status_code", 200)
                success = True
            except Exception as e:
                response = jsonify({"error": "Internal server error"}), 500
                status_code = 500
                success = False
                current_app.logger.error(f"Request error: {str(e)}")

            # Calculate metrics
            duration = time.time() - start_time

            # Log metrics
            current_app.logger.info(
                f"REQUEST_METRICS: {request.method} {request.path} "
                f"status={status_code} duration={duration:.3f}s "
                f"success={success} ip={request.remote_addr}"
            )

            return response

        return decorated_function

    return decorator
