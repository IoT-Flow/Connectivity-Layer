"""
Fixtures for End-to-End Tests
Adapts to available services (CI vs local environment)
"""

import pytest
import os
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

    if is_ci_mode:
        print(f"\n✅ E2E Testing Mode: CI Environment")
        print("   - Database: SQLite (in-memory)")
        print("   - Redis: localhost:6379")
        print("   - MQTT: localhost:1883")
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
            print("   - MQTT: localhost:1883")
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

    # Cleanup
    if is_ci_mode:
        print("\n🧹 E2E test completed (SQLite cleaned up automatically)")
    else:
        print("\n💾 E2E test data persisted for inspection")


@pytest.fixture(scope="function")
def client(app):
    """Create test client for making HTTP requests"""
    return app.test_client()


@pytest.fixture(scope="function")
def runner(app):
    """Create test CLI runner"""
    return app.test_cli_runner()
