"""
Charts API Routes
Provides endpoints for creating, managing, and retrieving chart configurations
"""

from flask import Blueprint, request, jsonify, current_app
from src.models import Chart, ChartDevice, ChartMeasurement, Device, User, db
from src.middleware.security import security_headers_middleware
from datetime import datetime, timezone
from sqlalchemy import text
import uuid

# Create blueprint for chart routes
chart_bp = Blueprint("charts", __name__, url_prefix="/api/v1/charts")


@chart_bp.route("", methods=["POST"])
@security_headers_middleware()
def create_chart():
    """Create a new chart"""
    try:
        data = request.get_json()
        
        # Validate required fields
        if not data:
            return jsonify({"error": "No data provided"}), 400
        
        name = data.get('name')
        chart_type = data.get('type')
        user_id = data.get('user_id')
        
        if not name or not chart_type or not user_id:
            return jsonify({
                "error": "Missing required fields",
                "message": "name, type, and user_id are required"
            }), 400
        
        # Validate chart type
        valid_types = ['line', 'bar', 'pie', 'scatter', 'area']
        if chart_type not in valid_types:
            return jsonify({
                "error": "Invalid chart type",
                "message": f"type must be one of: {', '.join(valid_types)}"
            }), 400
        
        # Check if user exists
        user = User.query.filter_by(user_id=user_id).first()
        if not user:
            return jsonify({
                "error": "User not found",
                "message": f"No user found with ID: {user_id}"
            }), 404
        
        # Create new chart
        chart = Chart(
            id=str(uuid.uuid4()),
            name=name,
            title=data.get('title', name),
            description=data.get('description', ''),
            type=chart_type,
            user_id=user.id,
            time_range=data.get('time_range', '24h'),
            refresh_interval=data.get('refresh_interval', 30),
            aggregation=data.get('aggregation', 'none'),
            group_by=data.get('group_by', 'device'),
            appearance_config=data.get('appearance_config', {}),
            is_active=True
        )
        
        db.session.add(chart)
        db.session.commit()
        
        current_app.logger.info(f"Chart created: {name} (ID: {chart.id})")
        
        return jsonify({
            "status": "success",
            "message": "Chart created successfully",
            "chart": chart.to_dict()
        }), 201
    
    except Exception as e:
        db.session.rollback()
        current_app.logger.error(f"Error creating chart: {str(e)}")
        return jsonify({
            "error": "Chart creation failed",
            "message": "An error occurred while creating the chart"
        }), 500


@chart_bp.route("", methods=["GET"])
@security_headers_middleware()
def list_charts():
    """List all charts"""
    try:
        # Get pagination parameters
        limit = request.args.get('limit', 100, type=int)
        offset = request.args.get('offset', 0, type=int)
        user_id = request.args.get('user_id')
        
        # Build query
        query = Chart.query.filter_by(is_active=True)
        
        # Filter by user if specified
        if user_id:
            user = User.query.filter_by(user_id=user_id).first()
            if user:
                query = query.filter_by(user_id=user.id)
        
        # Get charts
        charts = query.limit(limit).offset(offset).all()
        
        return jsonify({
            "status": "success",
            "charts": [chart.to_dict() for chart in charts],
            "meta": {
                "total": Chart.query.filter_by(is_active=True).count(),
                "limit": limit,
                "offset": offset
            }
        }), 200
    
    except Exception as e:
        current_app.logger.error(f"Error listing charts: {str(e)}")
        return jsonify({
            "error": "Failed to list charts",
            "message": "An error occurred while retrieving charts"
        }), 500


@chart_bp.route("/<chart_id>", methods=["GET"])
@security_headers_middleware()
def get_chart(chart_id):
    """Get chart by ID"""
    try:
        chart = Chart.query.filter_by(id=chart_id, is_active=True).first()
        
        if not chart:
            return jsonify({
                "error": "Chart not found",
                "message": f"No chart found with ID: {chart_id}"
            }), 404
        
        # Get associated devices
        chart_devices = ChartDevice.query.filter_by(chart_id=chart_id).all()
        device_ids = [cd.device_id for cd in chart_devices]
        devices = Device.query.filter(Device.id.in_(device_ids)).all() if device_ids else []
        
        # Get associated measurements
        chart_measurements = ChartMeasurement.query.filter_by(chart_id=chart_id).all()
        
        chart_dict = chart.to_dict()
        chart_dict['devices'] = [device.to_dict() for device in devices]
        chart_dict['measurements'] = [{
            'id': cm.id,
            'measurement_name': cm.measurement_name,
            'display_name': cm.display_name,
            'color': cm.color
        } for cm in chart_measurements]
        
        return jsonify({
            "status": "success",
            "chart": chart_dict
        }), 200
    
    except Exception as e:
        current_app.logger.error(f"Error getting chart: {str(e)}")
        return jsonify({
            "error": "Failed to retrieve chart",
            "message": "An error occurred while retrieving the chart"
        }), 500


@chart_bp.route("/<chart_id>", methods=["PUT"])
@security_headers_middleware()
def update_chart(chart_id):
    """Update chart"""
    try:
        chart = Chart.query.filter_by(id=chart_id, is_active=True).first()
        
        if not chart:
            return jsonify({
                "error": "Chart not found",
                "message": f"No chart found with ID: {chart_id}"
            }), 404
        
        data = request.get_json()
        if not data:
            return jsonify({"error": "No data provided"}), 400
        
        # Update allowed fields
        if 'name' in data:
            chart.name = data['name']
        
        if 'title' in data:
            chart.title = data['title']
        
        if 'description' in data:
            chart.description = data['description']
        
        if 'type' in data:
            valid_types = ['line', 'bar', 'pie', 'scatter', 'area']
            if data['type'] not in valid_types:
                return jsonify({
                    "error": "Invalid chart type",
                    "message": f"type must be one of: {', '.join(valid_types)}"
                }), 400
            chart.type = data['type']
        
        if 'time_range' in data:
            chart.time_range = data['time_range']
        
        if 'refresh_interval' in data:
            chart.refresh_interval = data['refresh_interval']
        
        if 'aggregation' in data:
            chart.aggregation = data['aggregation']
        
        if 'appearance_config' in data:
            chart.appearance_config = data['appearance_config']
        
        chart.updated_at = datetime.now(timezone.utc)
        db.session.commit()
        
        current_app.logger.info(f"Chart updated: {chart.name} (ID: {chart.id})")
        
        return jsonify({
            "status": "success",
            "message": "Chart updated successfully",
            "chart": chart.to_dict()
        }), 200
    
    except Exception as e:
        db.session.rollback()
        current_app.logger.error(f"Error updating chart: {str(e)}")
        return jsonify({
            "error": "Chart update failed",
            "message": "An error occurred while updating the chart"
        }), 500


@chart_bp.route("/<chart_id>", methods=["DELETE"])
@security_headers_middleware()
def delete_chart(chart_id):
    """Delete chart"""
    try:
        chart = Chart.query.filter_by(id=chart_id, is_active=True).first()
        
        if not chart:
            return jsonify({
                "error": "Chart not found",
                "message": f"No chart found with ID: {chart_id}"
            }), 404
        
        chart_name = chart.name
        
        # Soft delete - mark as inactive
        chart.is_active = False
        chart.updated_at = datetime.now(timezone.utc)
        db.session.commit()
        
        current_app.logger.info(f"Chart deleted: {chart_name} (ID: {chart_id})")
        
        return jsonify({
            "status": "success",
            "message": f"Chart '{chart_name}' deleted successfully"
        }), 200
    
    except Exception as e:
        db.session.rollback()
        current_app.logger.error(f"Error deleting chart: {str(e)}")
        return jsonify({
            "error": "Chart deletion failed",
            "message": "An error occurred while deleting the chart"
        }), 500


@chart_bp.route("/<chart_id>/devices", methods=["POST"])
@security_headers_middleware()
def add_device_to_chart(chart_id):
    """Add device to chart"""
    try:
        chart = Chart.query.filter_by(id=chart_id, is_active=True).first()
        if not chart:
            return jsonify({"error": "Chart not found"}), 404
        
        data = request.get_json()
        device_id = data.get('device_id')
        
        if not device_id:
            return jsonify({"error": "device_id is required"}), 400
        
        # Check if device exists
        device = Device.query.get(device_id)
        if not device:
            return jsonify({"error": "Device not found"}), 404
        
        # Check if already associated
        existing = ChartDevice.query.filter_by(
            chart_id=chart_id,
            device_id=device_id
        ).first()
        
        if existing:
            return jsonify({"error": "Device already associated with chart"}), 400
        
        # Create association
        chart_device = ChartDevice(chart_id=chart_id, device_id=device_id)
        db.session.add(chart_device)
        db.session.commit()
        
        return jsonify({
            "status": "success",
            "message": "Device added to chart successfully"
        }), 201
    
    except Exception as e:
        db.session.rollback()
        current_app.logger.error(f"Error adding device to chart: {str(e)}")
        return jsonify({"error": "Failed to add device to chart"}), 500


@chart_bp.route("/<chart_id>/devices/<int:device_id>", methods=["DELETE"])
@security_headers_middleware()
def remove_device_from_chart(chart_id, device_id):
    """Remove device from chart"""
    try:
        chart_device = ChartDevice.query.filter_by(
            chart_id=chart_id,
            device_id=device_id
        ).first()
        
        if not chart_device:
            return jsonify({"error": "Device not associated with chart"}), 404
        
        db.session.delete(chart_device)
        db.session.commit()
        
        return jsonify({
            "status": "success",
            "message": "Device removed from chart successfully"
        }), 200
    
    except Exception as e:
        db.session.rollback()
        current_app.logger.error(f"Error removing device from chart: {str(e)}")
        return jsonify({"error": "Failed to remove device from chart"}), 500


@chart_bp.route("/<chart_id>/measurements", methods=["POST"])
@security_headers_middleware()
def add_measurement_to_chart(chart_id):
    """Add measurement to chart"""
    try:
        chart = Chart.query.filter_by(id=chart_id, is_active=True).first()
        if not chart:
            return jsonify({"error": "Chart not found"}), 404
        
        data = request.get_json()
        measurement_name = data.get('measurement_name')
        
        if not measurement_name:
            return jsonify({"error": "measurement_name is required"}), 400
        
        # Check if already exists
        existing = ChartMeasurement.query.filter_by(
            chart_id=chart_id,
            measurement_name=measurement_name
        ).first()
        
        if existing:
            return jsonify({"error": "Measurement already associated with chart"}), 400
        
        # Create measurement
        chart_measurement = ChartMeasurement(
            chart_id=chart_id,
            measurement_name=measurement_name,
            display_name=data.get('display_name', measurement_name),
            color=data.get('color', '#000000')
        )
        db.session.add(chart_measurement)
        db.session.commit()
        
        return jsonify({
            "status": "success",
            "message": "Measurement added to chart successfully",
            "measurement": {
                'id': chart_measurement.id,
                'measurement_name': chart_measurement.measurement_name,
                'display_name': chart_measurement.display_name,
                'color': chart_measurement.color
            }
        }), 201
    
    except Exception as e:
        db.session.rollback()
        current_app.logger.error(f"Error adding measurement to chart: {str(e)}")
        return jsonify({"error": "Failed to add measurement to chart"}), 500


@chart_bp.route("/<chart_id>/measurements/<int:measurement_id>", methods=["DELETE"])
@security_headers_middleware()
def remove_measurement_from_chart(chart_id, measurement_id):
    """Remove measurement from chart"""
    try:
        chart_measurement = ChartMeasurement.query.filter_by(
            id=measurement_id,
            chart_id=chart_id
        ).first()
        
        if not chart_measurement:
            return jsonify({"error": "Measurement not found in chart"}), 404
        
        db.session.delete(chart_measurement)
        db.session.commit()
        
        return jsonify({
            "status": "success",
            "message": "Measurement removed from chart successfully"
        }), 200
    
    except Exception as e:
        db.session.rollback()
        current_app.logger.error(f"Error removing measurement from chart: {str(e)}")
        return jsonify({"error": "Failed to remove measurement from chart"}), 500


@chart_bp.route("/<chart_id>/data", methods=["GET"])
@security_headers_middleware()
def get_chart_data(chart_id):
    """Get chart data"""
    try:
        chart = Chart.query.filter_by(id=chart_id, is_active=True).first()
        
        if not chart:
            return jsonify({
                "error": "Chart not found",
                "message": f"No chart found with ID: {chart_id}"
            }), 404
        
        # Get time range parameters
        start_time = request.args.get('start')
        end_time = request.args.get('end')
        limit = request.args.get('limit', 1000, type=int)
        
        # Get associated devices and measurements
        chart_devices = ChartDevice.query.filter_by(chart_id=chart_id).all()
        chart_measurements = ChartMeasurement.query.filter_by(chart_id=chart_id).all()
        
        if not chart_devices or not chart_measurements:
            return jsonify({
                "status": "success",
                "chart_id": chart_id,
                "chart_name": chart.name,
                "chart_type": chart.type,
                "data": [],
                "series": [],
                "message": "No devices or measurements configured for this chart"
            }), 200
        
        device_ids = [cd.device_id for cd in chart_devices]
        measurement_names = [cm.measurement_name for cm in chart_measurements]
        
        # Build telemetry query
        query = """
            SELECT device_id, measurement_name, timestamp, numeric_value
            FROM telemetry_data
            WHERE device_id IN :device_ids
            AND measurement_name IN :measurement_names
        """
        
        params = {
            'device_ids': tuple(device_ids),
            'measurement_names': tuple(measurement_names)
        }
        
        # Add time range if specified
        if start_time:
            query += " AND timestamp >= :start_time"
            params['start_time'] = start_time
        
        if end_time:
            query += " AND timestamp <= :end_time"
            params['end_time'] = end_time
        
        query += " ORDER BY timestamp DESC LIMIT :limit"
        params['limit'] = limit
        
        # Execute query
        result = db.session.execute(text(query), params)
        rows = result.fetchall()
        
        # Format data for chart
        data = []
        series = {}
        
        for row in rows:
            device_id, measurement_name, timestamp, value = row
            
            # Add to data array
            data.append({
                'device_id': device_id,
                'measurement_name': measurement_name,
                'timestamp': timestamp.isoformat() if timestamp else None,
                'value': value
            })
            
            # Group by measurement for series
            if measurement_name not in series:
                # Find display name and color from chart measurements
                chart_measurement = next(
                    (cm for cm in chart_measurements if cm.measurement_name == measurement_name),
                    None
                )
                series[measurement_name] = {
                    'name': chart_measurement.display_name if chart_measurement else measurement_name,
                    'color': chart_measurement.color if chart_measurement else '#000000',
                    'data': []
                }
            
            series[measurement_name]['data'].append({
                'x': timestamp.isoformat() if timestamp else None,
                'y': value
            })
        
        return jsonify({
            "status": "success",
            "chart_id": chart_id,
            "chart_name": chart.name,
            "chart_type": chart.type,
            "data": data,
            "series": list(series.values()),
            "count": len(data)
        }), 200
    
    except Exception as e:
        current_app.logger.error(f"Error getting chart data: {str(e)}")
        return jsonify({
            "error": "Failed to retrieve chart data",
            "message": "An error occurred while retrieving chart data"
        }), 500
