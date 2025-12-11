"""
Pytest configuration and shared fixtures for IoTFlow Connectivity Layer tests
"""

import pytest
import os
import tempfile
from flask import Flask, request, Response
from datetime import datetime, timezone

# Set test environment before importing app
os.environ["FLASK_ENV"] = "testing"
os.environ["TESTING"] = "True"

from src.models import db, User, Device, DeviceAuth, DeviceConfiguration
from src.config.config import config


@pytest.fixture(scope="session")
def app():
    """Create Flask application for testing"""
    app = Flask(__name__)

    # Load test configuration
    app.config.from_object(config["testing"])

    # Use in-memory SQLite for tests
    app.config["SQLALCHEMY_DATABASE_URI"] = "sqlite:///:memory:"
    app.config["TESTING"] = True
    app.config["WTF_CSRF_ENABLED"] = False
    app.config["SECRET_KEY"] = "test-secret-key"

    # Initialize database
    db.init_app(app)

    # Register blueprints
    from src.routes.devices import device_bp
    from src.routes.telemetry import telemetry_bp
    from src.routes.admin import admin_bp
    from src.routes.mqtt import mqtt_bp
    from src.routes.control import control_bp

    app.register_blueprint(device_bp)
    app.register_blueprint(telemetry_bp)
    app.register_blueprint(admin_bp)
    app.register_blueprint(mqtt_bp)
    app.register_blueprint(control_bp)

    # Add health endpoint for testing
    @app.route("/health", methods=["GET"])
    def health_check():
        detailed = request.args.get("detailed", "false").lower() == "true"
        if detailed:
            return {
                "status": "healthy",
                "message": "Test app running",
                "version": "1.0.0",
                "database": "connected",
                "redis": "available",
            }, 200
        return {"status": "healthy", "message": "Test app running", "version": "1.0.0"}, 200

    # Add metrics endpoint for testing
    @app.route("/metrics", methods=["GET"])
    def metrics():
        from flask import Response

        # Return simple Prometheus-format metrics
        metrics_data = """# HELP http_requests_total Total HTTP requests
# TYPE http_requests_total counter
http_requests_total 100
"""
        return Response(metrics_data, mimetype="text/plain; version=0.0.4")

    # Add root endpoint for testing
    @app.route("/", methods=["GET"])
    def root():
        return {
            "name": "IoT Device Connectivity Layer",
            "version": "1.0.0",
            "description": "REST API for IoT device connectivity",
            "endpoints": {
                "health": "/health",
                "devices": "/api/v1/devices",
                "admin": "/api/v1/admin",
                "mqtt": "/api/v1/mqtt",
            },
            "documentation": "See README.md",
        }, 200

    # Add status endpoint for testing
    @app.route("/status", methods=["GET"])
    def system_status():
        return {
            "status": "healthy",
            "message": "System operational",
            "components": {"database": "connected", "redis": "available", "mqtt": "connected"},
        }, 200

    # Add test endpoint for middleware testing
    @app.route("/test", methods=["GET", "POST"])
    def test_endpoint():
        return {"message": "test"}, 200

    # Create application context
    with app.app_context():
        db.create_all()
        yield app
        db.drop_all()


@pytest.fixture
def client(app):
    """Create test client"""
    return app.test_client()


@pytest.fixture
def runner(app):
    """Create test CLI runner"""
    return app.test_cli_runner()


@pytest.fixture
def db_session(app):
    """Create database session for tests"""
    with app.app_context():
        # Start a transaction
        connection = db.engine.connect()
        transaction = connection.begin()

        # Bind session to connection
        session = db.create_scoped_session(options={"bind": connection, "binds": {}})
        db.session = session

        yield session

        # Rollback transaction
        transaction.rollback()
        connection.close()
        session.remove()


@pytest.fixture
def test_user(app):
    """Create a test user"""
    with app.app_context():
        user = User(
            username="testuser",
            email="test@example.com",
            password_hash="hashed_password_for_testing",
            is_active=True,
            is_admin=False,
        )
        db.session.add(user)
        db.session.commit()

        # Refresh to get the ID
        db.session.refresh(user)

        yield user

        # Cleanup
        db.session.delete(user)
        db.session.commit()


@pytest.fixture
def test_admin_user(app):
    """Create a test admin user"""
    with app.app_context():
        admin = User(
            username="adminuser",
            email="admin@example.com",
            password_hash="hashed_password_for_testing",
            is_active=True,
            is_admin=True,
        )
        db.session.add(admin)
        db.session.commit()

        db.session.refresh(admin)

        yield admin

        db.session.delete(admin)
        db.session.commit()


@pytest.fixture
def test_device(app, test_user):
    """Create a test device"""
    with app.app_context():
        device = Device(
            name="Test Device",
            description="Test device for unit tests",
            device_type="sensor",
            status="active",
            location="Test Lab",
            firmware_version="1.0.0",
            hardware_version="v1.0",
            user_id=test_user.id,
        )
        db.session.add(device)
        db.session.commit()

        db.session.refresh(device)

        yield device

        # Cleanup
        db.session.delete(device)
        db.session.commit()


@pytest.fixture
def auth_headers(test_device):
    """Create authentication headers with device API key"""
    return {"X-API-Key": test_device.api_key, "Content-Type": "application/json"}


@pytest.fixture
def admin_headers():
    """Create admin authentication headers"""
    return {"Authorization": "admin test", "Content-Type": "application/json"}


@pytest.fixture
def admin_token():
    """Create admin token for testing"""
    return "test"


@pytest.fixture
def multiple_devices(app, test_user):
    """Create multiple test devices"""
    with app.app_context():
        devices = []
        for i in range(3):
            device = Device(
                name=f"Test Device {i+1}",
                description=f"Test device {i+1}",
                device_type="sensor" if i % 2 == 0 else "actuator",
                status="active" if i < 2 else "inactive",
                user_id=test_user.id,
            )
            db.session.add(device)
            devices.append(device)

        db.session.commit()

        for device in devices:
            db.session.refresh(device)

        yield devices

        # Cleanup
        for device in devices:
            db.session.delete(device)
        db.session.commit()


@pytest.fixture
def mock_redis(monkeypatch):
    """Mock Redis client for testing"""

    class MockPipeline:
        def __init__(self, redis_client):
            self.redis_client = redis_client
            self.commands = []

        def delete(self, *keys):
            self.commands.append(("delete", keys))
            return self

        def execute(self):
            for cmd, args in self.commands:
                if cmd == "delete":
                    for key in args:
                        self.redis_client.delete(key)
            self.commands = []
            return [True] * len(self.commands)

    class MockRedis:
        def __init__(self):
            self.data = {}

        def get(self, key):
            return self.data.get(key)

        def set(self, key, value, ex=None):
            self.data[key] = value
            return True

        def delete(self, key):
            if key in self.data:
                del self.data[key]
            return True

        def ping(self):
            return True

        def keys(self, pattern):
            return list(self.data.keys())

        def pipeline(self):
            return MockPipeline(self)

    mock = MockRedis()
    return mock


@pytest.fixture
def mock_iotdb(monkeypatch):
    """Mock IoTDB client for testing"""

    class MockIoTDB:
        def __init__(self):
            self.data = {}

        def write_telemetry_data(self, device_id, data, **kwargs):
            if device_id not in self.data:
                self.data[device_id] = []
            self.data[device_id].append({"timestamp": datetime.now(timezone.utc), "data": data, **kwargs})
            return True

        def get_device_telemetry(self, device_id, **kwargs):
            return self.data.get(device_id, [])

        def is_available(self):
            return True

    mock = MockIoTDB()
    return mock


# Helper functions for tests
def create_test_user(username="testuser", email="test@example.com", is_admin=False):
    """Helper to create a test user"""
    user = User(
        username=username,
        email=email,
        password_hash="hashed_password",
        is_active=True,
        is_admin=is_admin,
    )
    db.session.add(user)
    db.session.commit()
    return user


def create_test_device(user_id, name="Test Device", device_type="sensor"):
    """Helper to create a test device"""
    device = Device(name=name, device_type=device_type, user_id=user_id, status="active")
    db.session.add(device)
    db.session.commit()
    return device


@pytest.fixture
def mock_mqtt_client(monkeypatch):
    """Mock MQTT client for testing"""
    from unittest.mock import MagicMock

    mock = MagicMock()
    mock.connect.return_value = True
    mock.publish.return_value = True
    mock.subscribe.return_value = True
    mock.is_connected.return_value = True

    # Mock the mqtt_client module functions
    monkeypatch.setattr("src.mqtt.mqtt_client.publish_device_command", mock.publish)

    return mock


@pytest.fixture
def mock_mqtt_service(app, monkeypatch):
    """Mock MQTT service for testing"""
    from unittest.mock import MagicMock

    mock_service = MagicMock()
    mock_service.connect.return_value = True
    mock_service.publish.return_value = True
    mock_service.subscribe.return_value = True
    mock_service.is_connected.return_value = True
    mock_service.client = MagicMock()

    # Mock the get_connection_status method to return serializable data
    mock_service.get_connection_status.return_value = {
        "host": "localhost",
        "port": 1883,
        "connected": True,
        "use_tls": False,
        "client_id": "test_client",
        "status": "connected",
    }

    app.mqtt_service = mock_service

    return mock_service
