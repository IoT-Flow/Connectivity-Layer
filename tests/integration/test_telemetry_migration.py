"""
TDD Tests for Telemetry Migration Requirements
Following the migration document specifications
"""

import pytest
import json
from datetime import datetime, timezone, timedelta


class TestTelemetryDataRetrieval:
    """Test GET /api/v1/telemetry/device/<device_id> endpoint"""

    def test_get_telemetry_basic(self, client, test_user, test_device):
        """Test basic telemetry retrieval"""
        # Store some test data first
        from src.services.iotdb import IoTDBService

        iotdb = IoTDBService()

        iotdb.write_telemetry_data(
            device_id=test_device.id,
            user_id=test_user.id,
            data={"temperature": 25.5, "humidity": 60.0},
            device_type=test_device.device_type,
        )

        # Retrieve data
        response = client.get(f"/api/v1/telemetry/device/{test_device.id}", headers={"X-API-Key": test_device.api_key})

        assert response.status_code == 200
        data = response.json
        assert data["success"] is True
        assert data["device_id"] == test_device.id
        assert "telemetry" in data
        assert "pagination" in data

    def test_get_telemetry_with_data_type_filter(self, client, test_user, test_device):
        """Test filtering by data_type parameter"""
        from src.services.iotdb import IoTDBService

        iotdb = IoTDBService()

        # Store data with multiple measurements
        iotdb.write_telemetry_data(
            device_id=test_device.id,
            user_id=test_user.id,
            data={"temperature": 25.5, "humidity": 60.0, "pressure": 1013.25},
            device_type=test_device.device_type,
        )

        # Filter by temperature only
        response = client.get(
            f"/api/v1/telemetry/device/{test_device.id}?data_type=temperature",
            headers={"X-API-Key": test_device.api_key},
        )

        assert response.status_code == 200
        data = response.json
        assert data["success"] is True
        assert "filters" in data
        assert data["filters"]["data_type"] == "temperature"

    def test_get_telemetry_with_date_range(self, client, test_user, test_device):
        """Test filtering by start_date and end_date"""
        start_date = datetime.now(timezone.utc) - timedelta(hours=2)
        end_date = datetime.now(timezone.utc)

        response = client.get(
            f"/api/v1/telemetry/device/{test_device.id}"
            f"?start_date={start_date.isoformat()}"
            f"&end_date={end_date.isoformat()}",
            headers={"X-API-Key": test_device.api_key},
        )

        assert response.status_code == 200
        data = response.json
        assert "filters" in data
        assert "start_date" in data["filters"]
        assert "end_date" in data["filters"]

    def test_get_telemetry_with_pagination(self, client, test_user, test_device):
        """Test pagination with limit and page parameters"""
        response = client.get(
            f"/api/v1/telemetry/device/{test_device.id}?limit=50&page=1", headers={"X-API-Key": test_device.api_key}
        )

        assert response.status_code == 200
        data = response.json
        assert "pagination" in data
        assert data["pagination"]["limit"] == 50
        assert data["pagination"]["currentPage"] == 1
        assert "totalPages" in data["pagination"]
        assert "total" in data["pagination"]

    def test_get_telemetry_unauthorized(self, client, test_device):
        """Test that authentication is required"""
        response = client.get(f"/api/v1/telemetry/device/{test_device.id}")

        assert response.status_code == 401
        data = response.json
        assert data["success"] is False
        assert "error" in data

    def test_get_telemetry_forbidden_different_device(self, client, test_user, test_device):
        """Test that device cannot access other device's data"""
        # Create another device
        from src.models import Device
        from app import db

        other_device = Device(
            name="Other Device", device_type="sensor", user_id=test_user.id, api_key="other_api_key_123"
        )
        db.session.add(other_device)
        db.session.commit()

        # Try to access other device's data
        response = client.get(f"/api/v1/telemetry/device/{other_device.id}", headers={"X-API-Key": test_device.api_key})

        assert response.status_code == 403
        data = response.json
        assert data["success"] is False

    def test_get_telemetry_device_not_found(self, client, test_device):
        """Test 404 when device doesn't exist"""
        response = client.get("/api/v1/telemetry/device/99999", headers={"X-API-Key": test_device.api_key})

        assert response.status_code == 404
        data = response.json
        assert data["success"] is False


class TestTelemetryAggregation:
    """Test GET /api/v1/telemetry/device/<device_id>/aggregated endpoint"""

    def test_get_aggregated_avg(self, client, test_user, test_device):
        """Test average aggregation"""
        from src.services.iotdb import IoTDBService

        iotdb = IoTDBService()

        # Store multiple data points
        for temp in [20.0, 22.0, 24.0, 26.0, 28.0]:
            iotdb.write_telemetry_data(
                device_id=test_device.id,
                user_id=test_user.id,
                data={"temperature": temp},
                device_type=test_device.device_type,
            )

        response = client.get(
            f"/api/v1/telemetry/device/{test_device.id}/aggregated" f"?data_type=temperature&aggregation=avg",
            headers={"X-API-Key": test_device.api_key},
        )

        assert response.status_code == 200
        data = response.json
        assert data["success"] is True
        assert "aggregation" in data
        assert data["aggregation"]["type"] == "avg"
        assert data["aggregation"]["data_type"] == "temperature"
        assert "value" in data["aggregation"]
        assert "count" in data["aggregation"]

    def test_get_aggregated_all_functions(self, client, test_user, test_device):
        """Test all aggregation functions: avg, sum, min, max, count"""
        from src.services.iotdb import IoTDBService

        iotdb = IoTDBService()

        # Store test data
        iotdb.write_telemetry_data(
            device_id=test_device.id,
            user_id=test_user.id,
            data={"temperature": 25.0},
            device_type=test_device.device_type,
        )

        for agg_func in ["avg", "sum", "min", "max", "count"]:
            response = client.get(
                f"/api/v1/telemetry/device/{test_device.id}/aggregated"
                f"?data_type=temperature&aggregation={agg_func}",
                headers={"X-API-Key": test_device.api_key},
            )

            assert response.status_code == 200, f"Failed for {agg_func}"
            data = response.json
            assert data["success"] is True
            assert data["aggregation"]["type"] == agg_func

    def test_get_aggregated_missing_required_params(self, client, test_device):
        """Test 400 when required parameters are missing"""
        # Missing data_type
        response = client.get(
            f"/api/v1/telemetry/device/{test_device.id}/aggregated?aggregation=avg",
            headers={"X-API-Key": test_device.api_key},
        )
        assert response.status_code == 400

        # Missing aggregation
        response = client.get(
            f"/api/v1/telemetry/device/{test_device.id}/aggregated?data_type=temperature",
            headers={"X-API-Key": test_device.api_key},
        )
        assert response.status_code == 400

    def test_get_aggregated_invalid_function(self, client, test_device):
        """Test 400 when aggregation function is invalid"""
        response = client.get(
            f"/api/v1/telemetry/device/{test_device.id}/aggregated" f"?data_type=temperature&aggregation=invalid",
            headers={"X-API-Key": test_device.api_key},
        )

        assert response.status_code == 400
        data = response.json
        assert data["success"] is False
        assert "error" in data

    def test_get_aggregated_with_date_range(self, client, test_user, test_device):
        """Test aggregation with date range filter"""
        start_date = datetime.now(timezone.utc) - timedelta(hours=1)
        end_date = datetime.now(timezone.utc)

        response = client.get(
            f"/api/v1/telemetry/device/{test_device.id}/aggregated"
            f"?data_type=temperature&aggregation=avg"
            f"&start_date={start_date.isoformat()}"
            f"&end_date={end_date.isoformat()}",
            headers={"X-API-Key": test_device.api_key},
        )

        assert response.status_code == 200
        data = response.json
        assert "aggregation" in data
        assert "start_date" in data["aggregation"]
        assert "end_date" in data["aggregation"]


class TestIoTDBServiceEnhancements:
    """Test enhanced IoTDB service methods"""

    def test_query_telemetry_data_with_filters(self, test_user, test_device):
        """Test query_telemetry_data method with all filters"""
        from src.services.iotdb import IoTDBService

        iotdb = IoTDBService()

        # Store test data
        iotdb.write_telemetry_data(
            device_id=test_device.id,
            user_id=test_user.id,
            data={"temperature": 25.5, "humidity": 60.0},
            device_type=test_device.device_type,
        )

        # Query with filters
        result = iotdb.query_telemetry_data(
            device_id=str(test_device.id), user_id=str(test_user.id), data_type="temperature", limit=50, page=1
        )

        assert "records" in result
        assert "total" in result
        assert "page" in result
        assert "pages" in result
        assert result["page"] == 1

    def test_query_telemetry_data_pagination(self, test_user, test_device):
        """Test pagination logic in query_telemetry_data"""
        from src.services.iotdb import IoTDBService

        iotdb = IoTDBService()

        # Store multiple records
        for i in range(10):
            iotdb.write_telemetry_data(
                device_id=test_device.id,
                user_id=test_user.id,
                data={"temperature": 20.0 + i},
                device_type=test_device.device_type,
            )

        # Get page 1 with limit 5
        result = iotdb.query_telemetry_data(device_id=str(test_device.id), user_id=str(test_user.id), limit=5, page=1)

        assert len(result["records"]) <= 5
        assert result["page"] == 1

    def test_aggregate_telemetry_data(self, test_user, test_device):
        """Test aggregate_telemetry_data method"""
        from src.services.iotdb import IoTDBService

        iotdb = IoTDBService()

        # Store test data
        iotdb.write_telemetry_data(
            device_id=test_device.id,
            user_id=test_user.id,
            data={"temperature": 25.0},
            device_type=test_device.device_type,
        )

        # Test aggregation
        result = iotdb.aggregate_telemetry_data(
            device_id=str(test_device.id), user_id=str(test_user.id), data_type="temperature", aggregation="avg"
        )

        assert "value" in result
        assert "count" in result
        assert "aggregation" in result
        assert "data_type" in result
        assert result["aggregation"] == "avg"
        assert result["data_type"] == "temperature"

    def test_aggregate_invalid_function(self, test_user, test_device):
        """Test that invalid aggregation function raises error"""
        from src.services.iotdb import IoTDBService

        iotdb = IoTDBService()

        with pytest.raises(ValueError, match="Invalid aggregation"):
            iotdb.aggregate_telemetry_data(
                device_id=str(test_device.id),
                user_id=str(test_user.id),
                data_type="temperature",
                aggregation="invalid_func",
            )


class TestAuthenticationEnhancements:
    """Test dual authentication (API Key + JWT)"""

    def test_api_key_authentication(self, client, test_device):
        """Test API key authentication works"""
        response = client.get(f"/api/v1/telemetry/device/{test_device.id}", headers={"X-API-Key": test_device.api_key})

        # Should not be 401 (may be 200 or 404 depending on data)
        assert response.status_code != 401

    @pytest.mark.skip(reason="JWT authentication requires PyJWT library - future enhancement")
    def test_jwt_authentication(self, client, test_user, test_device):
        """Test JWT token authentication works"""
        # Generate JWT token
        import jwt
        import os

        token = jwt.encode(
            {"user_id": test_user.id, "exp": datetime.now(timezone.utc) + timedelta(hours=1)},
            os.getenv("JWT_SECRET", "test_secret"),
            algorithm="HS256",
        )

        response = client.get(
            f"/api/v1/telemetry/device/{test_device.id}", headers={"Authorization": f"Bearer {token}"}
        )

        # Should not be 401
        assert response.status_code != 401

    def test_no_authentication_fails(self, client, test_device):
        """Test that no authentication returns 401"""
        response = client.get(f"/api/v1/telemetry/device/{test_device.id}")

        assert response.status_code == 401
        data = response.json
        assert data["success"] is False

    def test_invalid_api_key_fails(self, client, test_device):
        """Test that invalid API key returns 401"""
        response = client.get(f"/api/v1/telemetry/device/{test_device.id}", headers={"X-API-Key": "invalid_key_123"})

        assert response.status_code == 401

    @pytest.mark.skip(reason="JWT authentication requires PyJWT library - future enhancement")
    def test_expired_jwt_fails(self, client, test_user, test_device):
        """Test that expired JWT token returns 401"""
        import jwt
        import os

        # Create expired token
        token = jwt.encode(
            {"user_id": test_user.id, "exp": datetime.now(timezone.utc) - timedelta(hours=1)},
            os.getenv("JWT_SECRET", "test_secret"),
            algorithm="HS256",
        )

        response = client.get(
            f"/api/v1/telemetry/device/{test_device.id}", headers={"Authorization": f"Bearer {token}"}
        )

        assert response.status_code == 401


class TestResponseFormat:
    """Test response format matches migration requirements"""

    def test_success_response_structure(self, client, test_user, test_device):
        """Test that success response has correct structure"""
        from src.services.iotdb import IoTDBService

        iotdb = IoTDBService()

        iotdb.write_telemetry_data(
            device_id=test_device.id,
            user_id=test_user.id,
            data={"temperature": 25.0},
            device_type=test_device.device_type,
        )

        response = client.get(f"/api/v1/telemetry/device/{test_device.id}", headers={"X-API-Key": test_device.api_key})

        assert response.status_code == 200
        data = response.json

        # Required fields
        assert "success" in data
        assert "device_id" in data
        assert "device_name" in data
        assert "device_type" in data
        assert "telemetry" in data
        assert "pagination" in data
        assert "iotdb_available" in data

        # Pagination structure
        pagination = data["pagination"]
        assert "total" in pagination
        assert "currentPage" in pagination
        assert "totalPages" in pagination
        assert "limit" in pagination

    def test_error_response_structure(self, client, test_device):
        """Test that error response has correct structure"""
        response = client.get(f"/api/v1/telemetry/device/{test_device.id}")

        assert response.status_code == 401
        data = response.json

        # Required error fields
        assert "success" in data
        assert data["success"] is False
        assert "error" in data
        assert isinstance(data["error"], str)
