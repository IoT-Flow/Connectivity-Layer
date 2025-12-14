"""
Example: How to use the Device Status Tracker in your application

This demonstrates how to integrate the DeviceStatusTracker into your Flask app
for automatic device online/offline tracking.
"""

from flask import Flask
from src.services.device_status_tracker import DeviceStatusTracker
from src.services.mqtt_auth import MQTTAuthService
from src.services.iotdb import IoTDBService
from src.utils.redis_util import get_redis_util
from src.models import db

# Example 1: Basic Setup in Flask App
def create_app():
    """Create and configure the Flask application with device status tracking."""
    app = Flask(__name__)
    
    # Configure database and Redis
    app.config['SQLALCHEMY_DATABASE_URI'] = 'postgresql://...'
    db.init_app(app)
    
    # Initialize Redis
    redis_util = get_redis_util()
    redis_client = redis_util._redis_client if redis_util.available else None
    
    # Initialize Device Status Tracker
    status_tracker = DeviceStatusTracker(
        redis_client=redis_client,
        db=db,
        enable_db_sync=True,
        timeout_seconds=60  # 60 seconds = 1 minute
    )
    
    # Store on app for easy access
    app.device_status_tracker = status_tracker
    
    # Initialize MQTT Auth Service with status tracker
    iotdb_service = IoTDBService()
    mqtt_auth = MQTTAuthService(
        iotdb_service=iotdb_service,
        app=app,
        status_tracker=status_tracker
    )
    
    # Store on app
    app.mqtt_auth_service = mqtt_auth
    
    return app


# Example 2: Check Device Status in API Endpoint
def get_device_status_endpoint(device_id: int):
    """
    API endpoint to check if a device is online.
    
    GET /api/v1/devices/<device_id>/status
    """
    from flask import current_app, jsonify
    
    tracker = current_app.device_status_tracker
    
    # Get device status
    status = tracker.get_device_status(device_id)
    last_seen = tracker.get_last_seen(device_id)
    is_online = tracker.is_device_online(device_id)
    
    return jsonify({
        'device_id': device_id,
        'status': status,
        'is_online': is_online,
        'last_seen': last_seen.isoformat() if last_seen else None
    })


# Example 3: Background Task to Monitor Devices
def monitor_device_status():
    """
    Background task that runs periodically to check device statuses.
    Can be run with Celery, APScheduler, or similar.
    """
    from flask import current_app
    from src.models import Device
    
    tracker = current_app.device_status_tracker
    
    # Get all devices
    devices = Device.query.all()
    
    offline_devices = []
    online_devices = []
    
    for device in devices:
        # Check and update status
        status = tracker.check_and_update_status(device.id)
        
        if status == "offline":
            offline_devices.append(device)
        else:
            online_devices.append(device)
    
    # Log results
    print(f"Online devices: {len(online_devices)}")
    print(f"Offline devices: {len(offline_devices)}")
    
    # Send alerts for offline devices
    for device in offline_devices:
        send_offline_alert(device)


# Example 4: Send Alerts for Offline Devices
def send_offline_alert(device):
    """Send alert when device goes offline."""
    from datetime import datetime, timezone, timedelta
    from flask import current_app
    
    tracker = current_app.device_status_tracker
    last_seen = tracker.get_last_seen(device.id)
    
    if last_seen:
        offline_duration = datetime.now(timezone.utc) - last_seen
        
        # Only send alert if offline for more than 5 minutes
        if offline_duration > timedelta(minutes=5):
            print(f"ALERT: Device {device.name} (ID: {device.id}) has been offline for {offline_duration}")
            # Send email, SMS, or webhook notification
            # send_notification(device, offline_duration)


# Example 5: Get All Device Statuses
def get_all_device_statuses():
    """
    Get status for all devices.
    Useful for dashboard or monitoring.
    """
    from flask import current_app
    from src.models import Device
    
    tracker = current_app.device_status_tracker
    devices = Device.query.all()
    
    statuses = []
    for device in devices:
        status = tracker.get_device_status(device.id)
        last_seen = tracker.get_last_seen(device.id)
        
        statuses.append({
            'device_id': device.id,
            'device_name': device.name,
            'device_type': device.device_type,
            'status': status,
            'last_seen': last_seen.isoformat() if last_seen else None
        })
    
    return statuses


# Example 6: Custom Timeout for Different Device Types
def create_device_type_trackers():
    """
    Create different trackers for different device types.
    Some devices may need different timeout periods.
    """
    from flask import current_app
    
    redis_util = get_redis_util()
    redis_client = redis_util._redis_client
    
    # Fast sensors (30 second timeout)
    fast_tracker = DeviceStatusTracker(
        redis_client=redis_client,
        db=db,
        timeout_seconds=30
    )
    
    # Normal devices (60 second timeout)
    normal_tracker = DeviceStatusTracker(
        redis_client=redis_client,
        db=db,
        timeout_seconds=60
    )
    
    # Low-power devices (5 minute timeout)
    slow_tracker = DeviceStatusTracker(
        redis_client=redis_client,
        db=db,
        timeout_seconds=300
    )
    
    # Store on app
    current_app.device_trackers = {
        'fast': fast_tracker,
        'normal': normal_tracker,
        'slow': slow_tracker
    }


# Example 7: WebSocket Integration for Real-Time Updates
def emit_device_status_update(device_id: int):
    """
    Emit device status updates via WebSocket.
    Integrates with Flask-SocketIO or similar.
    """
    from flask import current_app
    from flask_socketio import emit
    
    tracker = current_app.device_status_tracker
    
    status = tracker.get_device_status(device_id)
    last_seen = tracker.get_last_seen(device_id)
    
    # Emit to all connected clients
    emit('device_status_update', {
        'device_id': device_id,
        'status': status,
        'last_seen': last_seen.isoformat() if last_seen else None
    }, broadcast=True)


# Example 8: Integration with Celery for Periodic Monitoring
"""
# In celery_tasks.py

from celery import Celery
from datetime import timedelta

celery = Celery('tasks', broker='redis://localhost:6379/0')

@celery.task
def check_device_statuses():
    '''Periodic task to check all device statuses.'''
    from flask import current_app
    with app.app_context():
        monitor_device_status()

# Schedule task to run every 5 minutes
celery.conf.beat_schedule = {
    'check-device-statuses': {
        'task': 'tasks.check_device_statuses',
        'schedule': timedelta(minutes=5),
    },
}
"""


# Example 9: REST API Endpoints
"""
# In routes/devices.py

@devices_bp.route('/<int:device_id>/status', methods=['GET'])
def get_device_status(device_id):
    '''Get device online/offline status.'''
    tracker = current_app.device_status_tracker
    
    status = tracker.get_device_status(device_id)
    last_seen = tracker.get_last_seen(device_id)
    is_online = tracker.is_device_online(device_id)
    
    return jsonify({
        'device_id': device_id,
        'status': status,
        'is_online': is_online,
        'last_seen': last_seen.isoformat() if last_seen else None
    })


@devices_bp.route('/status/all', methods=['GET'])
def get_all_statuses():
    '''Get status for all devices.'''
    statuses = get_all_device_statuses()
    return jsonify(statuses)


@devices_bp.route('/status/online', methods=['GET'])
def get_online_devices():
    '''Get all online devices.'''
    from src.models import Device
    
    tracker = current_app.device_status_tracker
    devices = Device.query.all()
    
    online_devices = [
        {
            'device_id': d.id,
            'device_name': d.name,
            'last_seen': tracker.get_last_seen(d.id).isoformat()
        }
        for d in devices
        if tracker.is_device_online(d.id)
    ]
    
    return jsonify(online_devices)


@devices_bp.route('/status/offline', methods=['GET'])
def get_offline_devices():
    '''Get all offline devices.'''
    from src.models import Device
    
    tracker = current_app.device_status_tracker
    devices = Device.query.all()
    
    offline_devices = [
        {
            'device_id': d.id,
            'device_name': d.name,
            'last_seen': tracker.get_last_seen(d.id).isoformat() if tracker.get_last_seen(d.id) else None
        }
        for d in devices
        if not tracker.is_device_online(d.id)
    ]
    
    return jsonify(offline_devices)
"""


# Example 10: Prometheus Metrics Integration
"""
from prometheus_client import Gauge

# Define metrics
devices_online = Gauge('iot_devices_online', 'Number of online devices')
devices_offline = Gauge('iot_devices_offline', 'Number of offline devices')

def update_device_metrics():
    '''Update Prometheus metrics for device status.'''
    from flask import current_app
    from src.models import Device
    
    tracker = current_app.device_status_tracker
    devices = Device.query.all()
    
    online_count = sum(1 for d in devices if tracker.is_device_online(d.id))
    offline_count = len(devices) - online_count
    
    devices_online.set(online_count)
    devices_offline.set(offline_count)

# Call this in your metrics collection routine
"""


if __name__ == '__main__':
    # Example usage
    app = create_app()
    
    with app.app_context():
        # Get status for device 123
        tracker = app.device_status_tracker
        
        status = tracker.get_device_status(123)
        print(f"Device 123 status: {status}")
        
        last_seen = tracker.get_last_seen(123)
        print(f"Device 123 last seen: {last_seen}")
        
        is_online = tracker.is_device_online(123)
        print(f"Device 123 online: {is_online}")
