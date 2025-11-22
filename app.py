import os
from flask import Flask, jsonify, request
from flask_cors import CORS
from flask_migrate import Migrate
from flasgger import Swagger

from src.config.config import config
from src.models import db
from src.routes.devices import device_bp
from src.routes.admin import admin_bp
from src.routes.users import user_bp
from src.routes.auth import auth_bp
from src.routes.charts import chart_bp

# Import PostgreSQL telemetry routes
from src.routes.telemetry_postgres import telemetry_bp
from src.utils.logging import setup_logging
from src.middleware.monitoring import HealthMonitor
from src.middleware.security import comprehensive_error_handler, security_headers_middleware

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
    CORS(app, 
         origins=["http://localhost:3000", "http://127.0.0.1:3000"],
         methods=["GET", "POST", "PUT", "DELETE", "OPTIONS"],
         allow_headers=["Content-Type", "Authorization", "X-API-Key", "X-User-ID"],
         expose_headers=["X-Request-ID", "X-RateLimit-Limit", "X-RateLimit-Remaining"]
    )
    
    # Initialize Swagger/OpenAPI documentation
    swagger_config = {
        "headers": [],
        "specs": [
            {
                "endpoint": 'apispec',
                "route": '/apispec.json',
                "rule_filter": lambda rule: True,
                "model_filter": lambda tag: True,
            }
        ],
        "static_url_path": "/flasgger_static",
        "swagger_ui": True,
        "specs_route": "/docs"
    }
    
    swagger_template = {
        "swagger": "2.0",
        "info": {
            "title": "IoTFlow Connectivity Layer API",
            "description": "REST API for IoT device connectivity and telemetry data management",
            "version": "1.0.0",
            "contact": {
                "name": "IoTFlow Team",
                "url": "https://github.com/IoT-Flow/Connectivity-Layer"
            }
        },
        "host": "localhost:5000",
        "basePath": "/",
        "schemes": ["http", "https"],
        "securityDefinitions": {
            "ApiKeyAuth": {
                "type": "apiKey",
                "name": "X-API-Key",
                "in": "header",
                "description": "Device API key for authentication"
            },
            "BearerAuth": {
                "type": "apiKey",
                "name": "Authorization",
                "in": "header",
                "description": "JWT token (format: Bearer <token>)"
            }
        }
    }
    
    Swagger(app, config=swagger_config, template=swagger_template)

    migrate = Migrate(app, db)
    
    # Register error handlers
    comprehensive_error_handler(app)
    
    # Register blueprints
    app.register_blueprint(device_bp)
    app.register_blueprint(admin_bp)
    app.register_blueprint(user_bp)
    app.register_blueprint(auth_bp)
    app.register_blueprint(chart_bp)
    app.register_blueprint(telemetry_bp)
    
    # Enhanced health check endpoint
    @app.route('/health', methods=['GET'])
    @security_headers_middleware()
    def health_check():
        """Health check endpoint
        ---
        tags:
          - Health
        summary: Health check
        description: Basic health check endpoint with optional detailed information
        parameters:
          - name: detailed
            in: query
            schema:
              type: boolean
              default: false
            description: Return detailed health information including database status and metrics
        responses:
          200:
            description: System is healthy
            content:
              application/json:
                schema:
                  type: object
                  properties:
                    status:
                      type: string
                      example: healthy
                    message:
                      type: string
                    version:
                      type: string
        """
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
        """Detailed system status and metrics
        ---
        tags:
          - Health
        summary: System status
        description: Get detailed system status including database, metrics, and device statistics
        responses:
          200:
            description: Detailed system status
        """
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
                'telemetry': '/api/v1/telemetry'
            },
            'documentation': 'See README.md for API documentation'
        }), 200
    
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
    
    return app

# Create app instance
app = create_app()

if __name__ == '__main__':
    port = int(os.environ.get('PORT', 5000))
    host = os.environ.get('HOST', '0.0.0.0')
    debug = os.environ.get('DEBUG', 'False').lower() == 'true'
    
    app.logger.info(f"Starting IoT Connectivity Layer on {host}:{port}")
    app.run(host=host, port=port, debug=debug)
