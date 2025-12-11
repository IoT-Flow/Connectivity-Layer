"""
Fixtures for End-to-End Tests
Adapts to available services (CI vs local environment)
"""

import pytest
import os
import time
from app import create_app
from src.models import db


@pytest.fixture(scope="function")
def app():
    """
    Create application for E2E testing with available services

    In CI: Uses SQLite + Redis + MQTT (IoTDB disabled)
    Locally: Can use PostgreSQL + IoTDB if available
    """
    # Check if we're in CI/testing mode
    is_ci_mode = os.environ.get("TESTING", "false").lower() == "true"

    # Force PostgreSQL for real e2e tests
    force_postgres = os.environ.get("FORCE_POSTGRES", "false").lower() == "true"

    # Set TESTING environment variable to disable MQTT during E2E tests
    original_testing = os.environ.get("TESTING")
    os.environ["TESTING"] = "true"

    if is_ci_mode and not force_postgres:
        print(f"\n✅ E2E Testing Mode: CI Environment")
        print("   - Database: SQLite (in-memory)")
        print("   - Redis: localhost:6379")
        print("   - MQTT: Disabled (testing mode)")
        print("   - IoTDB: Disabled (mocked)")

        # Use testing config for CI
        app = create_app("testing")

        # Override config for E2E testing in CI
        app.config.update(
            {
                "TESTING": True,
                "WTF_CSRF_ENABLED": False,
                "SQLALCHEMY_ECHO": False,
            }
        )

    else:
        # Local development mode - try to use real services
        database_url = os.environ.get("DATABASE_URL")

        if not database_url:
            # Use localhost PostgreSQL (assumes PostgreSQL is running locally)
            database_url = "postgresql://iotflow:iotflowpass@localhost:5432/iotflow"
            print(f"\n✅ E2E Testing Mode: Local Development")
            print("   - Database: PostgreSQL localhost:5432/iotflow")
            print("   - IoTDB: localhost:6667 (if available)")
            print("   - MQTT: Disabled (testing mode)")
        else:
            # Replace 'postgres' hostname with 'localhost' if needed (for local testing)
            if "postgres:5432" in database_url:
                database_url = database_url.replace("postgres:5432", "localhost:5432")
            print(f"\n✅ E2E Testing Mode: Custom Database")
            print(f"   - Database: {database_url.split('@')[1] if '@' in database_url else 'configured'}")

        # Set the DATABASE_URL environment variable BEFORE creating the app
        original_db_url = os.environ.get("DATABASE_URL")
        os.environ["DATABASE_URL"] = database_url

        try:
            # Use development config
            app = create_app("development")

            # Override config for E2E testing
            app.config.update(
                {
                    "TESTING": True,
                    "WTF_CSRF_ENABLED": False,
                    "SQLALCHEMY_ECHO": False,
                }
            )

        finally:
            # Restore original DATABASE_URL
            if original_db_url:
                os.environ["DATABASE_URL"] = original_db_url
            elif "DATABASE_URL" in os.environ:
                del os.environ["DATABASE_URL"]

    # Ensure database tables exist
    with app.app_context():
        try:
            db.create_all()
            if is_ci_mode:
                print("✅ Database tables created in SQLite")
            else:
                print("✅ Database tables created/verified")
        except Exception as e:
            print(f"⚠️  Database setup error: {e}")
            raise

    yield app

    # Cleanup and restore environment
    try:
        # Clean up any MQTT connections if they exist
        if hasattr(app, "mqtt_service") and app.mqtt_service:
            try:
                app.mqtt_service.disconnect()
            except:
                pass
    except:
        pass

    # Restore original TESTING environment variable
    if original_testing is not None:
        os.environ["TESTING"] = original_testing
    else:
        os.environ.pop("TESTING", None)

    if is_ci_mode:
        print("\n🧹 E2E test completed (SQLite cleaned up automatically)")
    else:
        print("\n💾 E2E test data persisted for inspection")


@pytest.fixture(scope="function")
def iotdb_service(app):
    """
    Fixture to provide IoTDB service for testing telemetry data sending
    """
    with app.app_context():
        from src.services.iotdb import IoTDBService
        from src.config.iotdb_config import iotdb_config

        service = IoTDBService()

        # Check IoTDB availability and log status
        is_available = service.is_available()
        print(f"\n🔗 IoTDB Service Status:")
        print(f"   - Enabled: {iotdb_config.enabled}")
        print(f"   - Host: {iotdb_config.host}:{iotdb_config.port}")
        print(f"   - Database: {iotdb_config.database}")
        print(f"   - Available: {is_available}")

        if is_available:
            print("   ✅ IoTDB is ready for telemetry data")
        else:
            print("   ⚠️  IoTDB not available - telemetry will be mocked")

        yield service


@pytest.fixture(scope="function")
def telemetry_helper(app, client):
    """
    Helper fixture for sending telemetry data in tests
    """

    class TelemetryHelper:
        def __init__(self, app, client):
            self.app = app
            self.client = client

        def send_telemetry(self, device, data, metadata=None, timestamp=None):
            """
            Send telemetry data to the API endpoint

            Args:
                device: Device model instance
                data: Dictionary of telemetry data
                metadata: Optional metadata dictionary
                timestamp: Optional timestamp (ISO format)

            Returns:
                Response object from the API call
            """
            import json
            from datetime import datetime, timezone

            payload = {"device_id": device.id, "api_key": device.api_key, "data": data}

            if metadata:
                payload["metadata"] = metadata

            if timestamp:
                payload["timestamp"] = timestamp
            else:
                payload["timestamp"] = datetime.now(timezone.utc).isoformat()

            response = self.client.post(
                "/api/v1/telemetry",
                data=json.dumps(payload),
                content_type="application/json",
                headers={"X-API-Key": device.api_key},
            )

            return response

        def send_flat_telemetry(self, device, **kwargs):
            """
            Send flat telemetry data (direct key-value pairs)

            Args:
                device: Device model instance
                **kwargs: Telemetry data as keyword arguments

            Returns:
                Response object from the API call
            """
            import json
            from datetime import datetime, timezone

            payload = {
                "device_id": device.id,
                "api_key": device.api_key,
                "timestamp": datetime.now(timezone.utc).isoformat(),
            }

            # Add all telemetry data directly to payload
            for key, value in kwargs.items():
                if key not in ["device_id", "api_key", "timestamp"]:
                    payload[key] = value

            response = self.client.post(
                "/api/v1/telemetry",
                data=json.dumps(payload),
                content_type="application/json",
                headers={"X-API-Key": device.api_key},
            )

            return response

        def query_telemetry(self, device, limit=10, start_time=None):
            """
            Query telemetry data for a device

            Args:
                device: Device model instance
                limit: Number of records to retrieve
                start_time: Optional start time filter

            Returns:
                Response object from the API call
            """
            params = {"limit": limit}
            if start_time:
                params["start_time"] = start_time

            query_string = "&".join([f"{k}={v}" for k, v in params.items()])

            response = self.client.get(
                f"/api/v1/telemetry/{device.id}?{query_string}", headers={"X-API-Key": device.api_key}
            )

            return response

        def verify_iotdb_storage(self, device, iotdb_service, expected_count=None):
            """
            Verify that telemetry data was actually stored in IoTDB

            Args:
                device: Device model instance
                iotdb_service: IoTDB service instance
                expected_count: Expected number of records (optional)

            Returns:
                Dictionary with verification results
            """
            if not iotdb_service.is_available():
                return {"iotdb_available": False, "verified": False, "message": "IoTDB not available for verification"}

            try:
                # Query recent telemetry data
                telemetry_data = iotdb_service.get_device_telemetry(
                    device_id=str(device.id), user_id=str(device.user_id), start_time="-1h", limit=100
                )

                # Get telemetry count
                count = iotdb_service.get_telemetry_count(device_id=str(device.id), start_time="-1h")

                result = {
                    "iotdb_available": True,
                    "verified": True,
                    "records_found": len(telemetry_data),
                    "total_count": count,
                    "latest_records": telemetry_data[:3] if telemetry_data else [],
                }

                if expected_count is not None:
                    result["count_matches"] = count >= expected_count
                    result["expected_count"] = expected_count

                return result

            except Exception as e:
                return {
                    "iotdb_available": True,
                    "verified": False,
                    "error": str(e),
                    "message": "Error verifying IoTDB storage",
                }

    yield TelemetryHelper(app, client)


@pytest.fixture(scope="function")
def client(app):
    """Create test client for making HTTP requests"""
    return app.test_client()


@pytest.fixture(scope="function")
def runner(app):
    """Create test CLI runner"""
    return app.test_cli_runner()


@pytest.fixture(scope="function", autouse=True)
def cleanup_mqtt_connections():
    """
    Automatically cleanup MQTT connections before and after each test
    to prevent connection conflicts
    """
    # Before test - ensure clean state
    import os
    import time

    # Set testing mode to prevent MQTT connections
    original_testing = os.environ.get("TESTING")
    os.environ["TESTING"] = "true"

    yield

    # After test - cleanup any remaining connections
    try:
        # Give time for any background threads to finish
        time.sleep(0.1)

        # Force cleanup of any MQTT client instances
        import gc

        gc.collect()

    except Exception as e:
        # Log cleanup errors but don't fail the test
        print(f"⚠️  MQTT cleanup warning: {e}")

    # Restore original TESTING environment variable
    if original_testing is not None:
        os.environ["TESTING"] = original_testing
    else:
        os.environ.pop("TESTING", None)
