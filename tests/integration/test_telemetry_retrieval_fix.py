"""
Test for telemetry retrieval fix - TDD approach
This test verifies that telemetry data can be retrieved after being stored
"""

import pytest
import json
import time
from datetime import datetime, timezone


class TestTelemetryRetrievalFix:
    """Test telemetry data retrieval after storage"""

    def test_retrieve_telemetry_after_storage(self, client, test_user, test_device):
        """
        Test that telemetry data stored can be retrieved via API

        Steps:
        1. Store telemetry data directly via IoTDB service
        2. Wait for data to be written to IoTDB
        3. Retrieve telemetry data via API
        4. Verify data is returned correctly
        """
        from src.services.iotdb import IoTDBService

        iotdb_service = IoTDBService()

        # Store telemetry data
        measurements = {"temperature": 25.5, "humidity": 60.0, "pressure": 1013.25}

        success = iotdb_service.write_telemetry_data(
            device_id=test_device.id, user_id=test_user.id, data=measurements, device_type=test_device.device_type
        )

        assert success, "Failed to write telemetry data"

        # Wait for IoTDB to process
        time.sleep(2)

        # Retrieve telemetry via API
        response = client.get(f"/api/v1/telemetry/{test_device.id}", headers={"X-API-Key": test_device.api_key})

        # Assertions
        assert response.status_code == 200
        data = response.json

        # Should have data structure
        assert "data" in data
        assert "iotdb_available" in data

        # If IoTDB is available, we should have data
        if data.get("iotdb_available", True):
            assert len(data["data"]) > 0, f"Expected telemetry data to be returned when IoTDB is available, got: {data}"
            # Verify the data content
            record = data["data"][0]
            assert "timestamp" in record
            assert "device_id" in record
        else:
            # If IoTDB is disabled (testing mode), we expect empty data
            assert len(data["data"]) == 0, f"Expected empty data when IoTDB is disabled, got: {data}"

    def test_retrieve_telemetry_with_user_id(self, client, test_user, test_device):
        """
        Test that telemetry retrieval works when user_id is provided

        The issue might be that user_id is not being passed correctly
        """
        from src.services.iotdb import IoTDBService

        iotdb_service = IoTDBService()

        # Store some test data first
        measurements = {"temperature": 22.5, "humidity": 45.0}

        success = iotdb_service.write_telemetry_data(
            device_id=test_device.id, user_id=test_user.id, data=measurements, device_type=test_device.device_type
        )

        assert success, "Failed to store telemetry data"

        # Wait for data to be written
        time.sleep(2)

        # Retrieve with user_id
        results = iotdb_service.get_device_telemetry(device_id=test_device.id, user_id=test_user.id, limit=10)

        # Should return data if IoTDB is available, empty if disabled
        from src.config.iotdb_config import iotdb_config

        if iotdb_config.enabled:
            assert (
                len(results) > 0
            ), f"Expected telemetry data for device {test_device.id}, user {test_user.id} when IoTDB is enabled"
            # Verify data structure only if we have results
            record = results[0]
            assert "timestamp" in record
            assert "device_id" in record
        else:
            assert len(results) == 0, f"Expected empty results when IoTDB is disabled, got {len(results)} results"

    def test_iotdb_path_construction(self, test_user, test_device):
        """
        Test that IoTDB path is constructed correctly

        This might be the root cause - path mismatch between storage and retrieval
        """
        from src.config.iotdb_config import iotdb_config

        # Test path with user_id
        path_with_user = iotdb_config.get_device_path(test_device.id, test_user.id)

        # Test path without user_id (might be the issue)
        path_without_user = iotdb_config.get_device_path(test_device.id, None)

        # Paths should be consistent
        # If user_id is required, both should use it
        print(f"Path with user_id: {path_with_user}")
        print(f"Path without user_id: {path_without_user}")

        # The path should include user information
        assert "user" in path_with_user.lower(), "Path should include user information"

        # Paths are different - this could be the issue!
        assert path_with_user != path_without_user, "Paths should be different when user_id is provided"
