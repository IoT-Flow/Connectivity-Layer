"""
Logic-based tests for IoTDB Service
Tests validate business requirements for time-series data storage
"""

import pytest
from unittest.mock import Mock, patch, MagicMock
from datetime import datetime, timezone, timedelta
from iotdb.utils.IoTDBConstants import TSDataType

from src.services.iotdb import IoTDBService


class TestIoTDBServiceRequirements:
    """Test business requirements for IoTDB time-series storage"""

    def test_data_type_mapping_requirements(self):
        """
        REQUIREMENT: Map Python types to correct IoTDB data types
        BUSINESS LOGIC: Ensure data integrity in time-series database
        DATA TYPES: int→INT64, float→DOUBLE, bool→BOOLEAN, str→TEXT
        """
        service = IoTDBService()

        # REQUIREMENT: Boolean values map to BOOLEAN
        assert service._get_data_type(True) == TSDataType.BOOLEAN
        assert service._get_data_type(False) == TSDataType.BOOLEAN

        # REQUIREMENT: Integer values map to INT64
        assert service._get_data_type(42) == TSDataType.INT64
        assert service._get_data_type(0) == TSDataType.INT64
        assert service._get_data_type(-100) == TSDataType.INT64

        # REQUIREMENT: Float values map to DOUBLE
        assert service._get_data_type(3.14) == TSDataType.DOUBLE
        assert service._get_data_type(0.0) == TSDataType.DOUBLE
        assert service._get_data_type(-99.99) == TSDataType.DOUBLE

        # REQUIREMENT: String values map to TEXT
        assert service._get_data_type("hello") == TSDataType.TEXT
        assert service._get_data_type("") == TSDataType.TEXT

        # REQUIREMENT: Complex types default to TEXT (for JSON serialization)
        assert service._get_data_type({"key": "value"}) == TSDataType.TEXT
        assert service._get_data_type([1, 2, 3]) == TSDataType.TEXT
        assert service._get_data_type(None) == TSDataType.TEXT

    def test_telemetry_storage_requirements(self):
        """
        REQUIREMENT: Store telemetry data with timestamp
        BUSINESS LOGIC: Each data point must have timestamp
        DEFAULT: Use current time if not provided
        """
        service = IoTDBService()
        service.session = Mock()
        service.session.create_time_series = Mock()
        service.session.insert_str_record = Mock()

        with patch.object(service, "is_available", return_value=True):
            # REQUIREMENT: Store data with explicit timestamp
            timestamp = datetime(2024, 1, 15, 10, 30, 0, tzinfo=timezone.utc)
            result = service.write_telemetry_data(
                device_id="123",
                data={"temperature": 25.5, "humidity": 60},
                timestamp=timestamp,
                user_id="user1",
            )

            assert result is True, "Must successfully store telemetry"
            service.session.insert_str_record.assert_called_once()

            # Verify timestamp was converted to milliseconds
            call_args = service.session.insert_str_record.call_args
            timestamp_ms = call_args[0][1]
            expected_ms = int(timestamp.timestamp() * 1000)
            assert timestamp_ms == expected_ms, "Timestamp must be in milliseconds"

    def test_telemetry_storage_default_timestamp(self):
        """
        REQUIREMENT: Default to current time if timestamp not provided
        BUSINESS LOGIC: All data points must have timestamp
        """
        service = IoTDBService()
        service.session = Mock()
        service.session.create_time_series = Mock()
        service.session.insert_str_record = Mock()

        with patch.object(service, "is_available", return_value=True):
            before_ms = int(datetime.now(timezone.utc).timestamp() * 1000)

            result = service.write_telemetry_data(device_id="123", data={"temperature": 25.5}, user_id="user1")

            after_ms = int(datetime.now(timezone.utc).timestamp() * 1000)

            assert result is True
            call_args = service.session.insert_str_record.call_args
            timestamp_ms = call_args[0][1]

            # Verify timestamp is between before and after (with 1 second tolerance)
            assert before_ms - 1000 <= timestamp_ms <= after_ms + 1000, "Must use current time as default"

    def test_data_isolation_by_user(self):
        """
        REQUIREMENT: Data must be isolated by user
        SECURITY: Users can only access their own device data
        BUSINESS LOGIC: Device paths include user_id
        """
        service = IoTDBService()
        service.session = Mock()
        service.session.create_time_series = Mock()
        service.session.insert_str_record = Mock()

        with patch.object(service, "is_available", return_value=True):
            with patch("src.services.iotdb.iotdb_config") as mock_config:
                # REQUIREMENT: User 1's data stored in user1 path
                mock_config.get_device_path.return_value = "root.user1.device123"

                service.write_telemetry_data(device_id="123", data={"temp": 25}, user_id="user1")

                # Verify user_id was used in path
                mock_config.get_device_path.assert_called_with("123", "user1")

                # REQUIREMENT: User 2's data stored in separate path
                mock_config.get_device_path.return_value = "root.user2.device123"

                service.write_telemetry_data(device_id="123", data={"temp": 30}, user_id="user2")

                mock_config.get_device_path.assert_called_with("123", "user2")

    def test_metadata_storage_requirements(self):
        """
        REQUIREMENT: Store metadata alongside telemetry
        BUSINESS LOGIC: Metadata prefixed with 'meta_'
        USE CASE: Device type, firmware version, location
        """
        service = IoTDBService()
        service.session = Mock()
        service.session.create_time_series = Mock()
        service.session.insert_str_record = Mock()

        with patch.object(service, "is_available", return_value=True):
            metadata = {"firmware": "v1.2.3", "location": "warehouse"}

            result = service.write_telemetry_data(
                device_id="123",
                data={"temperature": 25.5},
                metadata=metadata,
                user_id="user1",
            )

            assert result is True

            # Verify metadata was included
            call_args = service.session.insert_str_record.call_args
            measurements = call_args[0][2]

            # Should have: temperature, meta_firmware, meta_location, meta_device_type, meta_user_id
            assert "temperature" in measurements
            assert "meta_firmware" in measurements
            assert "meta_location" in measurements

    def test_complex_data_serialization(self):
        """
        REQUIREMENT: Handle complex data types (dict, list)
        BUSINESS LOGIC: Serialize to JSON for storage
        USE CASE: Nested sensor data, arrays of readings
        """
        service = IoTDBService()

        # REQUIREMENT: Dict values serialized to JSON
        measurements, data_types, values = service._prepare_time_series(
            "root.device123", {"config": {"mode": "auto", "threshold": 50}}
        )

        assert len(measurements) == 1
        assert data_types[0] == TSDataType.TEXT
        assert '{"mode": "auto"' in values[0], "Dict must be JSON serialized"

        # REQUIREMENT: List values serialized to JSON
        measurements, data_types, values = service._prepare_time_series("root.device123", {"readings": [1, 2, 3, 4, 5]})

        assert len(measurements) == 1
        assert data_types[0] == TSDataType.TEXT
        assert "[1, 2, 3, 4, 5]" in values[0], "List must be JSON serialized"


class TestIoTDBServiceErrorHandling:
    """Test error handling and edge cases"""

    def test_graceful_degradation_when_unavailable(self):
        """
        REQUIREMENT: Gracefully handle IoTDB unavailability
        ERROR HANDLING: Return False, don't crash
        BUSINESS LOGIC: System continues without time-series storage
        """
        service = IoTDBService()

        with patch.object(service, "is_available", return_value=False):
            # REQUIREMENT: Write fails gracefully when unavailable
            result = service.write_telemetry_data(device_id="123", data={"temp": 25}, user_id="user1")

            assert result is False, "Must return False when unavailable"

            # REQUIREMENT: Query returns empty when unavailable
            results = service.get_device_telemetry(device_id="123", user_id="user1")

            assert results == [], "Must return empty list when unavailable"

    def test_empty_data_handling(self):
        """
        REQUIREMENT: Handle empty data gracefully
        EDGE CASE: Empty dict, no measurements
        """
        service = IoTDBService()
        service.session = Mock()
        service.session.create_time_series = Mock()
        service.session.insert_str_record = Mock()

        with patch.object(service, "is_available", return_value=True):
            # EDGE CASE: Empty data dict
            result = service.write_telemetry_data(device_id="123", data={}, user_id="user1")

            # Should still succeed (metadata will be stored)
            assert result is True

    def test_null_value_handling(self):
        """
        REQUIREMENT: Handle null/None values
        EDGE CASE: Missing sensor readings
        """
        service = IoTDBService()

        # EDGE CASE: None value maps to TEXT
        data_type = service._get_data_type(None)
        assert data_type == TSDataType.TEXT

        # EDGE CASE: None in data dict
        measurements, data_types, values = service._prepare_time_series(
            "root.device123", {"sensor1": 25, "sensor2": None}
        )

        assert len(measurements) == 2
        assert None in values or "None" in [str(v) for v in values]

    def test_connection_error_handling(self):
        """
        REQUIREMENT: Handle connection errors gracefully
        ERROR HANDLING: Log error, return False
        RESILIENCE: Don't crash application
        """
        service = IoTDBService()
        service.session = Mock()
        service.session.insert_str_record.side_effect = Exception("Connection lost")

        with patch.object(service, "is_available", return_value=True):
            result = service.write_telemetry_data(device_id="123", data={"temp": 25}, user_id="user1")

            assert result is False, "Must return False on connection error"

    def test_time_series_creation_idempotency(self):
        """
        REQUIREMENT: Handle existing time series gracefully
        BUSINESS LOGIC: Time series creation is idempotent
        EDGE CASE: Time series already exists
        """
        service = IoTDBService()
        service.session = Mock()
        service.session.create_time_series.side_effect = Exception("Time series already exists")
        service.session.insert_str_record = Mock()

        with patch.object(service, "is_available", return_value=True):
            # REQUIREMENT: Should succeed even if time series exists
            result = service.write_telemetry_data(device_id="123", data={"temp": 25}, user_id="user1")

            assert result is True, "Must succeed even if time series exists"
            service.session.insert_str_record.assert_called_once()


class TestIoTDBServiceDataIntegrity:
    """Test data integrity and validation"""

    def test_timestamp_precision(self):
        """
        REQUIREMENT: Maintain timestamp precision
        BUSINESS LOGIC: Millisecond precision for time-series
        DATA INTEGRITY: No precision loss
        """
        service = IoTDBService()
        service.session = Mock()
        service.session.create_time_series = Mock()
        service.session.insert_str_record = Mock()

        with patch.object(service, "is_available", return_value=True):
            # Test with microsecond precision
            timestamp = datetime(2024, 1, 15, 10, 30, 45, 123456, tzinfo=timezone.utc)

            service.write_telemetry_data(device_id="123", data={"temp": 25}, timestamp=timestamp, user_id="user1")

            call_args = service.session.insert_str_record.call_args
            timestamp_ms = call_args[0][1]

            # Verify millisecond precision maintained
            expected_ms = int(timestamp.timestamp() * 1000)
            assert timestamp_ms == expected_ms

    def test_measurement_name_sanitization(self):
        """
        REQUIREMENT: Measurement names must be valid
        BUSINESS LOGIC: Extract measurement names from full paths
        DATA INTEGRITY: Consistent naming
        """
        service = IoTDBService()

        measurements, _, _ = service._prepare_time_series(
            "root.user1.device123",
            {"temperature": 25, "humidity": 60, "pressure": 1013},
        )

        # Verify full paths are created
        assert all("root.user1.device123." in m for m in measurements)
        assert any("temperature" in m for m in measurements)
        assert any("humidity" in m for m in measurements)
        assert any("pressure" in m for m in measurements)

    def test_value_type_consistency(self):
        """
        REQUIREMENT: Values must match declared data types
        DATA INTEGRITY: Type consistency in time-series
        """
        service = IoTDBService()

        # Test integer consistency
        measurements, data_types, values = service._prepare_time_series("root.device123", {"count": 42})
        assert data_types[0] == TSDataType.INT64
        assert isinstance(values[0], int)

        # Test float consistency
        measurements, data_types, values = service._prepare_time_series("root.device123", {"temperature": 25.5})
        assert data_types[0] == TSDataType.DOUBLE
        assert isinstance(values[0], float)

        # Test boolean consistency
        measurements, data_types, values = service._prepare_time_series("root.device123", {"active": True})
        assert data_types[0] == TSDataType.BOOLEAN
        assert isinstance(values[0], bool)


class TestIoTDBServicePerformance:
    """Test performance-related requirements"""

    def test_batch_measurement_preparation(self):
        """
        REQUIREMENT: Efficiently handle multiple measurements
        PERFORMANCE: Batch processing for multiple sensors
        """
        service = IoTDBService()

        # Test with many measurements
        data = {f"sensor_{i}": i * 10.5 for i in range(100)}

        measurements, data_types, values = service._prepare_time_series("root.device123", data)

        # REQUIREMENT: All measurements prepared
        assert len(measurements) == 100
        assert len(data_types) == 100
        assert len(values) == 100

        # PERFORMANCE: Correct types assigned
        assert all(dt == TSDataType.DOUBLE for dt in data_types)

    def test_metadata_overhead(self):
        """
        REQUIREMENT: Metadata doesn't significantly increase storage
        PERFORMANCE: Metadata stored efficiently
        """
        service = IoTDBService()

        # Small data with metadata
        data = {"temp": 25}
        metadata = {"device_type": "sensor", "location": "room1"}

        measurements, data_types, values = service._prepare_time_series("root.device123", data, metadata)

        # Should have: temp + 2 metadata fields
        assert len(measurements) == 3
        assert any("temp" in m for m in measurements)
        assert any("meta_device_type" in m for m in measurements)
        assert any("meta_location" in m for m in measurements)


class TestIoTDBServiceQueryOperations:
    """Test query operations for IoTDB service"""

    def test_get_device_telemetry_with_relative_time(self):
        """Test querying telemetry with relative time ranges"""
        service = IoTDBService()
        service.session = Mock()

        mock_dataset = Mock()
        mock_dataset.has_next.side_effect = [False]
        mock_dataset.close_operation_handle = Mock()
        mock_dataset.get_column_names.return_value = ["Time", "root.device123.temperature"]

        service.session.execute_query_statement.return_value = mock_dataset

        with patch.object(service, "is_available", return_value=True):
            with patch("src.services.iotdb.iotdb_config") as mock_config:
                mock_config.get_device_path.return_value = "root.device123"

                # Test with relative hours
                results = service.get_device_telemetry(device_id="123", start_time="-2h", user_id="user1")
                assert isinstance(results, list)

                # Test with relative days
                results = service.get_device_telemetry(device_id="123", start_time="-7d", user_id="user1")
                assert isinstance(results, list)

    def test_get_device_telemetry_with_absolute_time(self):
        """Test querying telemetry with absolute time ranges"""
        service = IoTDBService()
        service.session = Mock()

        mock_dataset = Mock()
        mock_dataset.has_next.side_effect = [False]
        mock_dataset.close_operation_handle = Mock()
        mock_dataset.get_column_names.return_value = ["Time"]

        service.session.execute_query_statement.return_value = mock_dataset

        with patch.object(service, "is_available", return_value=True):
            with patch("src.services.iotdb.iotdb_config") as mock_config:
                mock_config.get_device_path.return_value = "root.device123"

                results = service.get_device_telemetry(
                    device_id="123",
                    start_time="2024-01-15T10:00:00Z",
                    end_time="2024-01-15T11:00:00Z",
                    user_id="user1",
                )
                assert isinstance(results, list)

    def test_get_device_telemetry_with_data(self):
        """Test querying telemetry with actual data"""
        service = IoTDBService()
        service.session = Mock()

        # Mock record
        mock_record = Mock()
        mock_record.get_timestamp.return_value = 1705318200000  # 2024-01-15 10:30:00
        mock_field = Mock()
        mock_field.get_value.return_value = 25.5
        mock_record.get_fields.return_value = [mock_field]

        mock_dataset = Mock()
        mock_dataset.has_next.side_effect = [True, False]
        mock_dataset.next.return_value = mock_record
        mock_dataset.close_operation_handle = Mock()
        mock_dataset.get_column_names.return_value = ["Time", "root.device123.temperature"]

        service.session.execute_query_statement.return_value = mock_dataset

        with patch.object(service, "is_available", return_value=True):
            with patch("src.services.iotdb.iotdb_config") as mock_config:
                mock_config.get_device_path.return_value = "root.device123"

                results = service.get_device_telemetry(device_id="123", user_id="user1")

                assert len(results) == 1
                assert results[0]["device_id"] == "123"
                assert "timestamp" in results[0]
                assert "temperature" in results[0]

    def test_get_device_telemetry_with_json_values(self):
        """Test querying telemetry with JSON-serialized values"""
        service = IoTDBService()
        service.session = Mock()

        # Mock record with JSON value
        mock_record = Mock()
        mock_record.get_timestamp.return_value = 1705318200000
        mock_field = Mock()
        mock_field.get_value.return_value = '{"mode": "auto", "threshold": 50}'
        mock_record.get_fields.return_value = [mock_field]

        mock_dataset = Mock()
        mock_dataset.has_next.side_effect = [True, False]
        mock_dataset.next.return_value = mock_record
        mock_dataset.close_operation_handle = Mock()
        mock_dataset.get_column_names.return_value = ["Time", "root.device123.config"]

        service.session.execute_query_statement.return_value = mock_dataset

        with patch.object(service, "is_available", return_value=True):
            with patch("src.services.iotdb.iotdb_config") as mock_config:
                mock_config.get_device_path.return_value = "root.device123"

                results = service.get_device_telemetry(device_id="123", user_id="user1")

                assert len(results) == 1
                assert isinstance(results[0]["config"], dict)
                assert results[0]["config"]["mode"] == "auto"

    def test_get_device_telemetry_with_bytes_values(self):
        """Test querying telemetry with bytes values"""
        service = IoTDBService()
        service.session = Mock()

        # Mock record with bytes value
        mock_record = Mock()
        mock_record.get_timestamp.return_value = 1705318200000
        mock_field = Mock()
        mock_field.get_value.return_value = b"test_value"
        mock_record.get_fields.return_value = [mock_field]

        mock_dataset = Mock()
        mock_dataset.has_next.side_effect = [True, False]
        mock_dataset.next.return_value = mock_record
        mock_dataset.close_operation_handle = Mock()
        mock_dataset.get_column_names.return_value = ["Time", "root.device123.data"]

        service.session.execute_query_statement.return_value = mock_dataset

        with patch.object(service, "is_available", return_value=True):
            with patch("src.services.iotdb.iotdb_config") as mock_config:
                mock_config.get_device_path.return_value = "root.device123"

                results = service.get_device_telemetry(device_id="123", user_id="user1")

                assert len(results) == 1
                assert results[0]["data"] == "test_value"

    def test_get_device_telemetry_with_null_values(self):
        """Test querying telemetry with null/NaN values"""
        service = IoTDBService()
        service.session = Mock()

        # Mock record with None value
        mock_record = Mock()
        mock_record.get_timestamp.return_value = 1705318200000
        mock_field = Mock()
        mock_field.get_value.return_value = None
        mock_record.get_fields.return_value = [mock_field]

        mock_dataset = Mock()
        mock_dataset.has_next.side_effect = [True, False]
        mock_dataset.next.return_value = mock_record
        mock_dataset.close_operation_handle = Mock()
        mock_dataset.get_column_names.return_value = ["Time", "root.device123.sensor"]

        service.session.execute_query_statement.return_value = mock_dataset

        with patch.object(service, "is_available", return_value=True):
            with patch("src.services.iotdb.iotdb_config") as mock_config:
                mock_config.get_device_path.return_value = "root.device123"

                results = service.get_device_telemetry(device_id="123", user_id="user1")

                assert len(results) == 1
                assert results[0]["sensor"] is None

    def test_get_telemetry_count(self):
        """Test getting telemetry count"""
        service = IoTDBService()
        service.session = Mock()

        # Mock count result
        mock_record = Mock()
        mock_field = Mock()
        mock_field.get_value.return_value = 42
        mock_record.get_fields.return_value = [mock_field]

        mock_dataset = Mock()
        mock_dataset.has_next.return_value = True
        mock_dataset.next.return_value = mock_record
        mock_dataset.close_operation_handle = Mock()

        service.session.execute_query_statement.return_value = mock_dataset

        with patch.object(service, "is_available", return_value=True):
            with patch("src.services.iotdb.iotdb_config") as mock_config:
                mock_config.get_device_path.return_value = "root.device123"

                count = service.get_telemetry_count(device_id="123")

                assert count == 42

    def test_get_telemetry_count_with_relative_time(self):
        """Test getting telemetry count with relative time"""
        service = IoTDBService()
        service.session = Mock()

        mock_record = Mock()
        mock_field = Mock()
        mock_field.get_value.return_value = 10
        mock_record.get_fields.return_value = [mock_field]

        mock_dataset = Mock()
        mock_dataset.has_next.return_value = True
        mock_dataset.next.return_value = mock_record
        mock_dataset.close_operation_handle = Mock()

        service.session.execute_query_statement.return_value = mock_dataset

        with patch.object(service, "is_available", return_value=True):
            with patch("src.services.iotdb.iotdb_config") as mock_config:
                mock_config.get_device_path.return_value = "root.device123"

                # Test with hours
                count = service.get_telemetry_count(device_id="123", start_time="-1h")
                assert count == 10

                # Test with days
                count = service.get_telemetry_count(device_id="123", start_time="-7d")
                assert count == 10

    def test_delete_device_data(self):
        """Test deleting device data"""
        service = IoTDBService()
        service.session = Mock()
        service.session.delete_data = Mock()

        with patch.object(service, "is_available", return_value=True):
            with patch("src.services.iotdb.iotdb_config") as mock_config:
                mock_config.get_device_path.return_value = "root.device123"

                result = service.delete_device_data(
                    device_id="123",
                    start_time="2024-01-15T10:00:00Z",
                    end_time="2024-01-15T11:00:00Z",
                )

                assert result is True
                service.session.delete_data.assert_called_once()

    def test_delete_device_data_no_time_range(self):
        """Test deleting device data without time range"""
        service = IoTDBService()
        service.session = Mock()
        service.session.delete_data = Mock()

        with patch.object(service, "is_available", return_value=True):
            with patch("src.services.iotdb.iotdb_config") as mock_config:
                mock_config.get_device_path.return_value = "root.device123"

                result = service.delete_device_data(device_id="123")

                assert result is True
                service.session.delete_data.assert_called_once()

    def test_get_device_latest_telemetry(self):
        """Test getting latest telemetry for a device"""
        service = IoTDBService()
        service.session = Mock()

        # Mock record
        mock_record = Mock()
        mock_record.get_timestamp.return_value = 1705318200000
        mock_field = Mock()
        mock_field.get_value.return_value = 25.5
        mock_record.get_fields.return_value = [mock_field]

        mock_dataset = Mock()
        mock_dataset.has_next.return_value = True
        mock_dataset.next.return_value = mock_record
        mock_dataset.close_operation_handle = Mock()
        mock_dataset.get_column_names.return_value = ["Time", "root.device123.temperature"]

        service.session.execute_query_statement.return_value = mock_dataset

        with patch.object(service, "is_available", return_value=True):
            with patch("src.services.iotdb.iotdb_config") as mock_config:
                mock_config.get_device_path.return_value = "root.device123"

                result = service.get_device_latest_telemetry(device_id="123")

                assert result["device_id"] == "123"
                assert "timestamp" in result
                assert "temperature" in result

    def test_get_device_latest_telemetry_no_data(self):
        """Test getting latest telemetry when no data exists"""
        service = IoTDBService()
        service.session = Mock()

        mock_dataset = Mock()
        mock_dataset.has_next.return_value = False
        mock_dataset.close_operation_handle = Mock()
        mock_dataset.get_column_names.return_value = ["Time"]

        service.session.execute_query_statement.return_value = mock_dataset

        with patch.object(service, "is_available", return_value=True):
            with patch("src.services.iotdb.iotdb_config") as mock_config:
                mock_config.get_device_path.return_value = "root.device123"

                result = service.get_device_latest_telemetry(device_id="123")

                assert result == {}

    def test_get_user_telemetry(self):
        """Test getting telemetry for all user devices"""
        service = IoTDBService()
        service.session = Mock()

        # Mock record
        mock_record = Mock()
        mock_record.get_timestamp.return_value = 1705318200000
        mock_field = Mock()
        mock_field.get_value.return_value = 25.5
        mock_record.get_fields.return_value = [mock_field]

        mock_dataset = Mock()
        mock_dataset.has_next.side_effect = [True, False]
        mock_dataset.next.return_value = mock_record
        mock_dataset.close_operation_handle = Mock()
        mock_dataset.get_column_names.return_value = [
            "Time",
            "root.iotflow.users.user_123.devices.device_456.temperature",
        ]

        service.session.execute_query_statement.return_value = mock_dataset

        with patch.object(service, "is_available", return_value=True):
            with patch("src.services.iotdb.iotdb_config") as mock_config:
                mock_config.get_user_devices_path.return_value = "root.iotflow.users.user_123.devices"

                results = service.get_user_telemetry(user_id="user_123")

                assert len(results) == 1
                assert results[0]["user_id"] == "user_123"
                assert results[0]["device_id"] == "456"

    def test_get_user_telemetry_with_time_range(self):
        """Test getting user telemetry with time range"""
        service = IoTDBService()
        service.session = Mock()

        mock_dataset = Mock()
        mock_dataset.has_next.return_value = False
        mock_dataset.close_operation_handle = Mock()
        mock_dataset.get_column_names.return_value = ["Time"]

        service.session.execute_query_statement.return_value = mock_dataset

        with patch.object(service, "is_available", return_value=True):
            with patch("src.services.iotdb.iotdb_config") as mock_config:
                mock_config.get_user_devices_path.return_value = "root.iotflow.users.user_123.devices"

                results = service.get_user_telemetry(
                    user_id="user_123",
                    start_time="-1h",
                    end_time="2024-01-15T11:00:00Z",
                    limit=50,
                )

                assert isinstance(results, list)

    def test_get_user_telemetry_count(self):
        """Test getting user telemetry count"""
        service = IoTDBService()
        service.session = Mock()

        mock_record = Mock()
        mock_field = Mock()
        mock_field.get_value.return_value = 100
        mock_record.get_fields.return_value = [mock_field]

        mock_dataset = Mock()
        mock_dataset.has_next.return_value = True
        mock_dataset.next.return_value = mock_record
        mock_dataset.close_operation_handle = Mock()

        service.session.execute_query_statement.return_value = mock_dataset

        with patch.object(service, "is_available", return_value=True):
            with patch("src.services.iotdb.iotdb_config") as mock_config:
                mock_config.get_user_devices_path.return_value = "root.iotflow.users.user_123.devices"

                count = service.get_user_telemetry_count(user_id="user_123")

                assert count == 100

    def test_get_user_telemetry_count_with_time(self):
        """Test getting user telemetry count with time filter"""
        service = IoTDBService()
        service.session = Mock()

        mock_record = Mock()
        mock_field = Mock()
        mock_field.get_value.return_value = 50
        mock_record.get_fields.return_value = [mock_field]

        mock_dataset = Mock()
        mock_dataset.has_next.return_value = True
        mock_dataset.next.return_value = mock_record
        mock_dataset.close_operation_handle = Mock()

        service.session.execute_query_statement.return_value = mock_dataset

        with patch.object(service, "is_available", return_value=True):
            with patch("src.services.iotdb.iotdb_config") as mock_config:
                mock_config.get_user_devices_path.return_value = "root.iotflow.users.user_123.devices"

                count = service.get_user_telemetry_count(user_id="user_123", start_time="-24h")

                assert count == 50

    def test_close_connection(self):
        """Test closing IoTDB connection"""
        service = IoTDBService()

        with patch("src.services.iotdb.iotdb_config") as mock_config:
            mock_config.close = Mock()

            service.close()

            mock_config.close.assert_called_once()

    def test_query_error_handling(self):
        """Test error handling during query operations"""
        service = IoTDBService()
        service.session = Mock()
        service.session.execute_query_statement.side_effect = Exception("Query failed")

        with patch.object(service, "is_available", return_value=True):
            with patch("src.services.iotdb.iotdb_config") as mock_config:
                mock_config.get_device_path.return_value = "root.device123"

                # Should return empty list on error
                results = service.get_device_telemetry(device_id="123", user_id="user1")
                assert results == []

                # Should return 0 on count error
                count = service.get_telemetry_count(device_id="123")
                assert count == 0

                # Should return empty dict on latest error
                latest = service.get_device_latest_telemetry(device_id="123")
                assert latest == {}

    def test_delete_error_handling(self):
        """Test error handling during delete operations"""
        service = IoTDBService()
        service.session = Mock()
        service.session.delete_data.side_effect = Exception("Delete failed")

        with patch.object(service, "is_available", return_value=True):
            with patch("src.services.iotdb.iotdb_config") as mock_config:
                mock_config.get_device_path.return_value = "root.device123"

                result = service.delete_device_data(device_id="123")

                assert result is False
