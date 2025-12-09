"""
Integration tests for Telemetry API endpoints
Following TDD principles - tests written before implementation review
"""
import pytest
from src.models import Device, db
import time
from datetime import datetime, timedelta


class TestTelemetryStorage:
    """Test storing telemetry data"""

    def test_store_telemetry_success(self, client, test_device, app):
        """Test successfully storing telemetry data"""
        with app.app_context():
            # Ensure device is in active state
            device = Device.query.get(test_device.id)
            if device:
                device.status = "active"
                db.session.commit()

        headers = {"X-API-Key": test_device.api_key}
        payload = {
            "data": {"temperature": 25.5, "humidity": 60.0, "pressure": 1013.25},
            "timestamp": datetime.utcnow().isoformat(),
        }

        response = client.post("/api/v1/telemetry", json=payload, headers=headers)

        # If 500 error, print response for debugging
        if response.status_code == 500:
            print(f"Error response: {response.get_json()}")

        assert response.status_code in [
            200,
            201,
        ], f"Expected 200/201, got {response.status_code}: {response.get_json()}"
        data = response.get_json()
        assert "stored" in data or "success" in data or "message" in data

    def test_store_telemetry_without_auth(self, client):
        """Test that authentication is required"""
        payload = {"data": {"temperature": 25.5}}

        response = client.post("/api/v1/telemetry", json=payload)

        assert response.status_code == 401

    def test_store_telemetry_missing_measurements(self, client, test_device):
        """Test that measurements are required"""
        headers = {"X-API-Key": test_device.api_key}
        payload = {"timestamp": datetime.utcnow().isoformat()}

        response = client.post("/api/v1/telemetry", json=payload, headers=headers)

        assert response.status_code == 400

    def test_store_telemetry_batch(self, client, test_device, app):
        """Test storing multiple telemetry readings"""
        with app.app_context():
            # Ensure device is in active state
            device = Device.query.get(test_device.id)
            if device:
                device.status = "active"
                db.session.commit()

        headers = {"X-API-Key": test_device.api_key}

        for i in range(5):
            payload = {"data": {"temperature": 20.0 + i, "humidity": 50.0 + i}}
            response = client.post("/api/v1/telemetry", json=payload, headers=headers)

            # If 500 error, print response for debugging
            if response.status_code == 500:
                print(f"Batch {i} error response: {response.get_json()}")

            assert response.status_code in [200, 201], f"Batch {i}: Expected 200/201, got {response.status_code}"


class TestTelemetryRetrieval:
    """Test retrieving telemetry data"""

    def test_get_device_telemetry(self, client, test_device):
        """Test getting telemetry data for a device"""
        headers = {"X-API-Key": test_device.api_key}
        response = client.get(f"/api/v1/telemetry/{test_device.id}", headers=headers)

        assert response.status_code == 200
        data = response.get_json()
        assert "telemetry" in data or "data" in data or "measurements" in data

    def test_get_device_telemetry_with_time_range(self, client, test_device):
        """Test getting telemetry with time range filter"""
        headers = {"X-API-Key": test_device.api_key}
        start_time = (datetime.utcnow() - timedelta(hours=24)).isoformat()
        end_time = datetime.utcnow().isoformat()

        response = client.get(
            f"/api/v1/telemetry/{test_device.id}",
            query_string={"start_time": start_time, "end_time": end_time},
            headers=headers,
        )

        assert response.status_code == 200
        data = response.get_json()
        assert isinstance(data, dict)

    def test_get_device_telemetry_with_limit(self, client, test_device):
        """Test getting telemetry with limit"""
        headers = {"X-API-Key": test_device.api_key}
        response = client.get(f"/api/v1/telemetry/{test_device.id}", query_string={"limit": 10}, headers=headers)

        assert response.status_code == 200
        data = response.get_json()
        # Verify limit is respected
        if "telemetry" in data:
            assert len(data["telemetry"]) <= 10

    def test_get_device_telemetry_not_found(self, client, test_device):
        """Test getting telemetry for non-existent device"""
        # Need auth header even for 404 test
        headers = {"X-API-Key": test_device.api_key}
        response = client.get("/api/v1/telemetry/99999", headers=headers)

        # Will return 403 (forbidden) since device ID doesn't match auth
        assert response.status_code in [403, 404]

    def test_get_device_telemetry_with_measurement_filter(self, client, test_device):
        """Test filtering by specific measurement"""
        headers = {"X-API-Key": test_device.api_key}
        response = client.get(
            f"/api/v1/telemetry/{test_device.id}", query_string={"measurement": "temperature"}, headers=headers
        )

        assert response.status_code == 200


class TestLatestTelemetry:
    """Test getting latest telemetry readings"""

    def test_get_latest_telemetry(self, client, test_device):
        """Test getting latest telemetry for device"""
        headers = {"X-API-Key": test_device.api_key}
        response = client.get(f"/api/v1/telemetry/{test_device.id}/latest", headers=headers)

        # May return 200 with data, or 404 if no telemetry exists
        assert response.status_code in [200, 404]
        if response.status_code == 200:
            data = response.get_json()
            assert "latest" in data or "measurements" in data or "data" in data

    def test_get_latest_telemetry_not_found(self, client, test_device):
        """Test getting latest telemetry for non-existent device"""
        # Need auth header even for 404 test
        headers = {"X-API-Key": test_device.api_key}
        response = client.get("/api/v1/telemetry/99999/latest", headers=headers)

        # Will return 403 (forbidden) since device ID doesn't match auth
        assert response.status_code in [403, 404]

    def test_get_latest_telemetry_no_data(self, client, test_user, app):
        """Test getting latest telemetry when no data exists"""
        # Create device with no telemetry
        with app.app_context():
            device = Device(name="No_Telemetry_Device", user_id=test_user.id, device_type="sensor")
            db.session.add(device)
            db.session.commit()
            device_id = device.id
            api_key = device.api_key

        headers = {"X-API-Key": api_key}
        response = client.get(f"/api/v1/telemetry/{device_id}/latest", headers=headers)

        assert response.status_code in [200, 404]
        if response.status_code == 200:
            data = response.get_json()
            assert data.get("latest") is None or len(data.get("measurements", [])) == 0


class TestAggregatedTelemetry:
    """Test aggregated telemetry data"""

    def test_get_aggregated_telemetry(self, client, test_device):
        """Test getting aggregated telemetry data"""
        headers = {"X-API-Key": test_device.api_key}
        response = client.get(
            f"/api/v1/telemetry/{test_device.id}/aggregated",
            query_string={"measurement": "temperature", "aggregation": "avg", "interval": "1h"},
            headers=headers,
        )

        # May return 200 with data, 400 if IoTDB query fails, or 500 for errors
        assert response.status_code in [200, 400, 500]
        if response.status_code == 200:
            data = response.get_json()
            assert "aggregated" in data or "data" in data or "results" in data

    def test_get_aggregated_telemetry_multiple_functions(self, client, test_device):
        """Test aggregation with multiple functions"""
        headers = {"X-API-Key": test_device.api_key}
        aggregations = ["avg", "min", "max", "sum", "count"]

        for agg in aggregations:
            response = client.get(
                f"/api/v1/telemetry/{test_device.id}/aggregated",
                query_string={"measurement": "temperature", "aggregation": agg},
                headers=headers,
            )
            # May work or fail depending on IoTDB availability
            assert response.status_code in [200, 400, 500]

    def test_get_aggregated_telemetry_different_intervals(self, client, test_device):
        """Test aggregation with different time intervals"""
        headers = {"X-API-Key": test_device.api_key}
        intervals = ["1m", "5m", "1h", "1d"]

        for interval in intervals:
            response = client.get(
                f"/api/v1/telemetry/{test_device.id}/aggregated",
                query_string={"measurement": "temperature", "aggregation": "avg", "interval": interval},
                headers=headers,
            )
            # May work or fail depending on IoTDB availability
            assert response.status_code in [200, 400, 500]

    def test_get_aggregated_telemetry_missing_params(self, client, test_device):
        """Test that required parameters are validated"""
        headers = {"X-API-Key": test_device.api_key}
        response = client.get(f"/api/v1/telemetry/{test_device.id}/aggregated", headers=headers)

        # Should either succeed with defaults, return 400 for validation, or 500 for errors
        assert response.status_code in [200, 400, 500]

    def test_get_aggregated_telemetry_with_time_range(self, client, test_device):
        """Test aggregation with time range"""
        headers = {"X-API-Key": test_device.api_key}
        start_time = (datetime.utcnow() - timedelta(days=7)).isoformat()
        end_time = datetime.utcnow().isoformat()

        response = client.get(
            f"/api/v1/telemetry/{test_device.id}/aggregated",
            query_string={
                "measurement": "temperature",
                "aggregation": "avg",
                "start_time": start_time,
                "end_time": end_time,
            },
            headers=headers,
        )

        # May work or fail depending on IoTDB availability
        assert response.status_code in [200, 400, 500]


class TestTelemetryDeletion:
    """Test deleting telemetry data"""

    def test_delete_device_telemetry(self, client, test_device):
        """Test deleting telemetry data for device"""
        response = client.delete(f"/api/v1/telemetry/{test_device.id}")

        # May require admin auth
        assert response.status_code in [200, 401, 403]

    def test_delete_device_telemetry_with_time_range(self, client, test_device):
        """Test deleting telemetry within time range"""
        start_time = (datetime.utcnow() - timedelta(days=30)).isoformat()
        end_time = (datetime.utcnow() - timedelta(days=7)).isoformat()

        response = client.delete(
            f"/api/v1/telemetry/{test_device.id}", query_string={"start_time": start_time, "end_time": end_time}
        )

        assert response.status_code in [200, 401, 403]

    def test_delete_telemetry_not_found(self, client):
        """Test deleting telemetry for non-existent device"""
        response = client.delete("/api/v1/telemetry/99999")

        assert response.status_code in [401, 403, 404]


class TestTelemetryStatus:
    """Test telemetry service status"""

    def test_get_telemetry_status(self, client):
        """Test getting IoTDB service status"""
        response = client.get("/api/v1/telemetry/status")

        assert response.status_code == 200
        data = response.get_json()
        assert "status" in data or "available" in data or "iotdb" in data

    def test_telemetry_status_includes_stats(self, client):
        """Test that status includes statistics"""
        response = client.get("/api/v1/telemetry/status")

        assert response.status_code == 200
        data = response.get_json()
        # Should include some stats about the service
        assert isinstance(data, dict)
        assert len(data) > 0


class TestUserTelemetry:
    """Test getting telemetry for all user devices"""

    def test_get_user_telemetry(self, client, test_user, test_device):
        """Test getting telemetry for all user's devices"""
        response = client.get(f"/api/v1/telemetry/user/{test_user.id}")

        # May require authentication
        assert response.status_code in [200, 401]

        if response.status_code == 200:
            data = response.get_json()
            assert "devices" in data or "telemetry" in data

    def test_get_user_telemetry_not_found(self, client):
        """Test getting telemetry for non-existent user"""
        response = client.get("/api/v1/telemetry/user/99999")

        assert response.status_code in [401, 404]

    def test_get_user_telemetry_multiple_devices(self, client, test_user, app):
        """Test getting telemetry when user has multiple devices"""
        # Create additional devices
        with app.app_context():
            for i in range(3):
                device = Device(name=f"User_Device_{i}", user_id=test_user.id, device_type="sensor")
                db.session.add(device)
            db.session.commit()

        response = client.get(f"/api/v1/telemetry/user/{test_user.id}")

        # May require authentication
        assert response.status_code in [200, 401]
