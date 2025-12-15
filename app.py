import os
import redis
from flask import Flask, jsonify, request, Response  # add Response for Prometheus metrics
from flask_cors import CORS
from flask_migrate import Migrate
from prometheus_client import generate_latest, CONTENT_TYPE_LATEST

from src.config.config import config
from src.models import db
from src.routes.devices import device_bp
from src.routes.admin import admin_bp
from src.routes.mqtt import mqtt_bp
from src.routes.telemetry import telemetry_bp
from src.routes.control import control_bp
from src.utils.logging import setup_logging
from src.middleware.monitoring import HealthMonitor
from src.middleware.security import comprehensive_error_handler, security_headers_middleware
from src.middleware.auth import require_admin_token
from src.mqtt.client import create_mqtt_service
from src.services.mqtt_auth import MQTTAuthService
from src.services.device_status_cache import DeviceStatusCache
from src.services.device_status_tracker import DeviceStatusTracker

def create_app(config_name=None):
    """Application factory pattern"""
    
    # Create Flask app
    app = Flask(__name__)
    
    # Load configuration
    config_name = config_name or os.environ.get('FLASK_ENV', 'development')
    app.config.from_object(config[config_name])
    
    # Setup logging
    setup_logging(app)
    
    # Initialize extensions
    db.init_app(app)
    
    # Enhanced CORS configuration
    allowed_origins = os.environ.get('ALLOWED_ORIGINS', 'http://localhost:3000,http://localhost:3001').split(',')
    CORS(app, 
         origins=allowed_origins,
         methods=["GET", "POST", "PUT", "DELETE", "OPTIONS"],
         allow_headers=["Content-Type", "Authorization", "X-API-Key", "X-User-ID"],
         expose_headers=["X-Request-ID", "X-RateLimit-Limit", "X-RateLimit-Remaining"]
    )

    # Instrument HTTP request metrics
    from src.metrics import HTTP_REQUEST_COUNT, HTTP_REQUEST_LATENCY, HTTP_REQUEST_COUNT_ALL
    import time

    @app.before_request
    def _start_timer():
        request._start_time = time.time()

    @app.after_request
    def _record_request_data(response):
        try:
            latency = time.time() - getattr(request, '_start_time', time.time())
            # Per-endpoint counter
            HTTP_REQUEST_COUNT.labels(request.method, request.path, response.status_code).inc()
            # Global counter for all requests
            HTTP_REQUEST_COUNT_ALL.inc()
            HTTP_REQUEST_LATENCY.labels(request.method, request.path).observe(latency)
        except Exception:
            pass
        return response

    migrate = Migrate(app, db)
    
    # Initialize Redis client
    try:
        redis_client = redis.from_url(app.config['REDIS_URL'], decode_responses=True)
        redis_client.ping()  # Test connection
        app.redis_client = redis_client
        app.logger.info("Redis connection established")
    except Exception as e:
        app.logger.warning(f"Redis connection failed: {str(e)}")
        app.redis_client = None
    
    # Register error handlers
    comprehensive_error_handler(app)
    
    # Register blueprints
    app.register_blueprint(device_bp)
    app.register_blueprint(admin_bp)
    app.register_blueprint(mqtt_bp)
    app.register_blueprint(telemetry_bp)
    app.register_blueprint(control_bp)
    
    # Initialize MQTT service with authentication (skip in testing mode)
    if not os.environ.get('TESTING', 'false').lower() == 'true':
        try:
            # Get MQTT config from the config object
            config_obj = config[config_name or 'development']()
            
            # Initialize Device Status Tracker with Redis and DB
            redis_client = app.redis_client  # Use the Redis client we initialized earlier
            app.logger.info(f"Initializing DeviceStatusTracker with Redis client: {redis_client is not None}")
            status_tracker = DeviceStatusTracker(
                redis_client=redis_client,
                db=db,
                timeout_seconds=60,
                enable_db_sync=True
            )
            app.status_tracker = status_tracker
            app.logger.info(f"DeviceStatusTracker initialized - Available: {status_tracker.available}")
            
            # Initialize MQTT authentication service with app context and status tracker
            mqtt_auth_service = MQTTAuthService(app=app, status_tracker=status_tracker)
            
            # Create MQTT service with authentication and app reference for Redis cache
            mqtt_service = create_mqtt_service(config_obj.mqtt_config, mqtt_auth_service, app)
            app.mqtt_service = mqtt_service
            app.mqtt_auth_service = mqtt_auth_service
            
            # Connect to MQTT broker
            if mqtt_service.connect():
                app.logger.info("MQTT service initialized and connected successfully")
                
                # Subscribe to device topics for server-side processing
                mqtt_service.subscribe_to_system_topics()
                
                app.logger.info("MQTT authentication service initialized")
            else:
                app.logger.error("Failed to connect to MQTT broker")
                
        except Exception as e:
            app.logger.error(f"MQTT service initialization failed: {str(e)}")
            app.mqtt_service = None
            app.mqtt_auth_service = None
    else:
        app.logger.info("Skipping MQTT service initialization in testing mode")
        app.mqtt_service = None
        app.mqtt_auth_service = None
    
    # Initialize Device Status Cache
    try:
        # Use Redis client for device status caching
        device_status_cache = DeviceStatusCache(redis_client=app.redis_client)
        app.device_status_cache = device_status_cache
        app.logger.info("Device Status Cache initialized successfully")
    except Exception as e:
        app.logger.error(f"Failed to initialize Device Status Cache: {str(e)}")
        app.device_status_cache = None
    
    # Enhanced health check endpoint
    @app.route('/health', methods=['GET'])
    @security_headers_middleware()
    def health_check():
        """Comprehensive health check endpoint"""
        detailed = request.args.get('detailed', 'false').lower() == 'true'
        
        if detailed:
            return jsonify(HealthMonitor.get_system_health())
        else:
            return jsonify({
                'status': 'healthy',
                'message': 'IoT Connectivity Layer is running',
                'version': '1.0.0'
            }), 200
    
    # Detailed system status endpoint
    @app.route('/status', methods=['GET'])
    @security_headers_middleware()
    def system_status():
        """Detailed system status and metrics"""
        return jsonify(HealthMonitor.get_system_health())
    
    # Root endpoint
    @app.route('/', methods=['GET'])
    def root():
        """Root endpoint with API information"""
        return jsonify({
            'name': 'IoT Device Connectivity Layer',
            'version': '1.0.0',
            'description': 'REST API for IoT device connectivity and telemetry data management',
            'endpoints': {
                'health': '/health',
                'devices': '/api/v1/devices',
                'admin': '/api/v1/admin',
                'mqtt': '/api/v1/mqtt'
            },
            'documentation': 'See README.md for API documentation'
        }), 200
    
    # Prometheus metrics endpoint (admin only)
    @app.route('/metrics')
    @require_admin_token
    def metrics():
        """Prometheus metrics endpoint (admin authentication required)"""
        # Collect fresh metrics before returning
        from src.services.system_metrics import SystemMetricsCollector
        from src.services.redis_metrics import RedisMetricsCollector
        from src.services.mqtt_metrics import MQTTMetricsCollector
        from src.services.iotdb_metrics import IoTDBMetricsCollector
        
        # Collect all service metrics
        system_collector = SystemMetricsCollector()
        system_collector.collect_all_metrics()
        
        redis_collector = RedisMetricsCollector()
        redis_collector.collect_all_metrics()
        
        mqtt_collector = MQTTMetricsCollector()
        mqtt_collector.collect_all_metrics()
        
        iotdb_collector = IoTDBMetricsCollector()
        iotdb_collector.collect_all_metrics()
        
        return Response(generate_latest(), mimetype=CONTENT_TYPE_LATEST)

    # Error handlers
    @app.errorhandler(404)
    def not_found(error):
        return jsonify({
            'error': 'Not Found',
            'message': 'The requested resource was not found'
        }), 404
    
    @app.errorhandler(500)
    def internal_error(error):
        db.session.rollback()
        app.logger.error(f"Internal server error: {str(error)}")
        return jsonify({
            'error': 'Internal Server Error',
            'message': 'An unexpected error occurred'
        }), 500
    
    @app.errorhandler(400)
    def bad_request(error):
        return jsonify({
            'error': 'Bad Request',
            'message': 'The request was invalid'
        }), 400
    
    # Create database tables
    with app.app_context():
        try:
            db.create_all()
            app.logger.info("Database tables created successfully")
        except Exception as e:
            app.logger.error(f"Error creating database tables: {str(e)}")
    
    # MQTT connection is handled by the main MQTT service above
    
    return app

# Create app instance
app = create_app()

if __name__ == '__main__':
    port = int(os.environ.get('PORT', 5000))
    host = os.environ.get('HOST', '0.0.0.0')
    debug = os.environ.get('DEBUG', 'False').lower() == 'true'
    
    app.logger.info(f"Starting IoT Connectivity Layer on {host}:{port}")
    app.run(host=host, port=port, debug=debug)
