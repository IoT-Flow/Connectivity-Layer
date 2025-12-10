"""
Fixtures for End-to-End Tests
Uses the real application with actual database and IoTDB
"""

import pytest
import os
from app import create_app
from src.models import db


@pytest.fixture(scope="function")
def app():
    """
    Create application for E2E testing with real services
    Uses actual PostgreSQL database and IoTDB

    Set DATABASE_URL environment variable to use PostgreSQL:
    export DATABASE_URL="postgresql://user:password@localhost/iotflow"

    Or it will use the default PostgreSQL configuration
    """
    # Use PostgreSQL for E2E tests (real database)
    # Default to localhost PostgreSQL with same credentials as docker-compose
    database_url = os.environ.get("DATABASE_URL")

    if not database_url:
        # Use localhost PostgreSQL (assumes PostgreSQL is running locally)
        database_url = "postgresql://iotflow:iotflowpass@localhost:5432/iotflow"
        print(f"\n✅ Using PostgreSQL database: localhost:5432/iotflow")
        print("   (Using default credentials from .env.example)")
    else:
        # Replace 'postgres' hostname with 'localhost' if needed (for local testing)
        if "postgres:5432" in database_url:
            database_url = database_url.replace("postgres:5432", "localhost:5432")
        print(
            f"\n✅ Using PostgreSQL from DATABASE_URL: {database_url.split('@')[1] if '@' in database_url else 'configured'}"
        )

    # Set the DATABASE_URL environment variable BEFORE creating the app
    # This ensures the app uses PostgreSQL from the start
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
                "SQLALCHEMY_ECHO": False,  # Reduce noise in tests
            }
        )

        # Ensure database tables exist
        with app.app_context():
            try:
                db.create_all()
                print("✅ Database tables created/verified in PostgreSQL")
            except Exception as e:
                print(f"⚠️  Database setup error: {e}")
                raise

        yield app

        # Note: We don't drop tables in E2E tests as we want to inspect the data
        # Cleanup can be done manually if needed
        print("\n💾 E2E test data persisted in PostgreSQL for inspection")

    finally:
        # Restore original DATABASE_URL
        if original_db_url:
            os.environ["DATABASE_URL"] = original_db_url
        elif "DATABASE_URL" in os.environ:
            del os.environ["DATABASE_URL"]


@pytest.fixture(scope="function")
def client(app):
    """Create test client for making HTTP requests"""
    return app.test_client()


@pytest.fixture(scope="function")
def runner(app):
    """Create test CLI runner"""
    return app.test_cli_runner()
