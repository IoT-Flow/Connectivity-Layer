#!/usr/bin/env python3
"""
TDD Test for Device Data Summary API

This test implements a comprehensive device data retrieval API using Test-Driven Development.
The API will provide device information, status, configuration, and recent telemetry in one endpoint.

API Endpoint: GET /api/v1/devices/<device_id>/summary
"""

import pytest
import requests
import json
from datetime import datetime, timezone
import sys
import os

# Add src to path for imports
sys.path.insert(0, os.path.join(os.path.dirname(__file__), 'src'))

class TestDeviceDataSummaryAPI:
    """TDD tests for device data summary API - Temperature Only"""
    
    BASE_URL = "http://localhost:5000"
    API_KEY = "mZAziGMCmjDmfrOATJxGWqJX1vL4VgkR"  # Default from previous test
    DEVICE_ID = 11  # Device from previous test
    
    @classmethod
    def send_measurement_data(cls, measurement_type="temperature", value=23.5):
        """Helper method to send measurement data with type and value structure"""
        telemetry_data = {
            "data": {
                "measurement_type": measurement_type,
                "value": value,
                "unit": cls._get_unit_for_measurement(measurement_type)
            },
            "metadata": {
                "test_type": "tdd_measurement_test",
                "source": "test_device_data_api_tdd.py",
                "measurement_category": measurement_type
            }
        }
        
        try:
            response = requests.post(
                f"{cls.BASE_URL}/api/v1/telemetry",
                json=telemetry_data,
                headers={
                    "Content-Type": "application/json",
                    "X-API-Key": cls.API_KEY
                },
                timeout=10
            )
            return response.status_code == 201
        except Exception:
            return False
    
    @classmethod
    def _get_unit_for_measurement(cls, measurement_type):
        """Get the appropriate unit for a measurement type"""
        units = {
            "temperature": "°C",
            "pressure": "hPa",
            "humidity": "%",
            "voltage": "V",
            "current": "A",
            "power": "W",
            "speed": "m/s",
            "distance": "m"
        }
        return units.get(measurement_type, "unit")
    
    @classmethod
    def send_temperature_data(cls, temperature_value=23.5):
        """Backward compatibility method for temperature data"""
        return cls.send_measurement_data("temperature", temperature_value)
    
    def test_01_device_summary_endpoint_exists(self):
        """Test 1: Device summary endpoint should exist and be accessible"""
        print("🔍 Test 1: Testing device summary endpoint existence")
        
        url = f"{self.BASE_URL}/api/v1/devices/{self.DEVICE_ID}/summary"
        
        response = requests.get(
            url,
            headers={"X-API-Key": self.API_KEY},
            timeout=10
        )
        
        # Should not return 404 (endpoint exists)
        assert response.status_code != 404, f"Endpoint should exist, got 404"
        print("✅ Device summary endpoint exists")
    
    def test_02_device_summary_requires_authentication(self):
        """Test 2: Device summary should require API key authentication"""
        print("🔍 Test 2: Testing authentication requirement")
        
        url = f"{self.BASE_URL}/api/v1/devices/{self.DEVICE_ID}/summary"
        
        # Request without API key
        response = requests.get(url, timeout=10)
        
        assert response.status_code == 401, f"Should require authentication, got {response.status_code}"
        
        response_data = response.json()
        assert "error" in response_data, "Should return error message"
        print("✅ Authentication required")
    
    def test_03_device_summary_validates_api_key(self):
        """Test 3: Device summary should validate API key"""
        print("🔍 Test 3: Testing API key validation")
        
        url = f"{self.BASE_URL}/api/v1/devices/{self.DEVICE_ID}/summary"
        
        # Request with invalid API key
        response = requests.get(
            url,
            headers={"X-API-Key": "invalid_api_key"},
            timeout=10
        )
        
        assert response.status_code == 401, f"Should reject invalid API key, got {response.status_code}"
        print("✅ API key validation works")
    
    def test_04_device_summary_returns_device_info(self):
        """Test 4: Device summary should return basic device information"""
        print("🔍 Test 4: Testing device information in summary")
        
        url = f"{self.BASE_URL}/api/v1/devices/{self.DEVICE_ID}/summary"
        
        response = requests.get(
            url,
            headers={"X-API-Key": self.API_KEY},
            timeout=10
        )
        
        assert response.status_code == 200, f"Should return success, got {response.status_code}"
        
        data = response.json()
        
        # Check required device fields
        assert "device" in data, "Should contain device information"
        device = data["device"]
        
        required_fields = ["id", "name", "device_type", "status", "created_at"]
        for field in required_fields:
            assert field in device, f"Device should contain {field}"
        
        assert device["id"] == self.DEVICE_ID, f"Device ID should match requested ID"
        print("✅ Device information included in summary")
    
    def test_05_device_summary_returns_status_info(self):
        """Test 5: Device summary should return device status information"""
        print("🔍 Test 5: Testing device status in summary")
        
        url = f"{self.BASE_URL}/api/v1/devices/{self.DEVICE_ID}/summary"
        
        response = requests.get(
            url,
            headers={"X-API-Key": self.API_KEY},
            timeout=10
        )
        
        assert response.status_code == 200, f"Should return success, got {response.status_code}"
        
        data = response.json()
        
        # Check status fields
        assert "status" in data, "Should contain status information"
        status = data["status"]
        
        status_fields = ["is_online", "last_seen"]
        for field in status_fields:
            assert field in status, f"Status should contain {field}"
        
        assert isinstance(status["is_online"], bool), "is_online should be boolean"
        print("✅ Device status included in summary")
    
    def test_06_device_summary_returns_recent_telemetry(self):
        """Test 6: Device summary should return recent telemetry data (measurement structure)"""
        print("🔍 Test 6: Testing recent telemetry in summary (measurement structure)")
        
        # First, send a temperature measurement to ensure we have data
        print("   📊 Sending temperature measurement: 24.8°C")
        success = self.send_measurement_data("temperature", 24.8)
        assert success, "Should successfully send temperature measurement"
        
        url = f"{self.BASE_URL}/api/v1/devices/{self.DEVICE_ID}/summary"
        
        response = requests.get(
            url,
            headers={"X-API-Key": self.API_KEY},
            timeout=10
        )
        
        assert response.status_code == 200, f"Should return success, got {response.status_code}"
        
        data = response.json()
        
        # Check telemetry fields
        assert "telemetry" in data, "Should contain telemetry information"
        telemetry = data["telemetry"]
        
        assert "recent_data" in telemetry, "Should contain recent telemetry data"
        assert "count" in telemetry, "Should contain telemetry count"
        assert "iotdb_available" in telemetry, "Should indicate IoTDB availability"
        
        # Check that we have measurement data with proper structure
        if telemetry["recent_data"]:
            recent = telemetry["recent_data"][0]
            assert "timestamp" in recent, "Recent data should have timestamp"
            # Look for measurement structure
            found_test_measurement = any(
                record.get("measurement_type") == "temperature" and record.get("value") == 24.8
                for record in telemetry["recent_data"]
            )
            assert found_test_measurement, "Should find our test measurement (temperature: 24.8°C) in recent data"
        
        print("✅ Recent telemetry (measurement structure) included in summary")
    
    def test_07_device_summary_returns_configuration(self):
        """Test 7: Device summary should return device configuration"""
        print("🔍 Test 7: Testing device configuration in summary")
        
        url = f"{self.BASE_URL}/api/v1/devices/{self.DEVICE_ID}/summary"
        
        response = requests.get(
            url,
            headers={"X-API-Key": self.API_KEY},
            timeout=10
        )
        
        assert response.status_code == 200, f"Should return success, got {response.status_code}"
        
        data = response.json()
        
        # Check configuration fields
        assert "configuration" in data, "Should contain configuration information"
        config = data["configuration"]
        
        # Configuration can be empty, but should be a dict
        assert isinstance(config, dict), "Configuration should be a dictionary"
        print("✅ Device configuration included in summary")
    
    def test_08_device_summary_handles_nonexistent_device(self):
        """Test 8: Device summary should handle requests for non-existent devices"""
        print("🔍 Test 8: Testing non-existent device handling")
        
        nonexistent_device_id = 99999
        url = f"{self.BASE_URL}/api/v1/devices/{nonexistent_device_id}/summary"
        
        response = requests.get(
            url,
            headers={"X-API-Key": self.API_KEY},
            timeout=10
        )
        
        assert response.status_code == 404, f"Should return 404 for non-existent device, got {response.status_code}"
        
        data = response.json()
        assert "error" in data, "Should return error message"
        print("✅ Non-existent device handled correctly")
    
    def test_09_device_summary_handles_device_access_control(self):
        """Test 9: Device summary should enforce device access control"""
        print("🔍 Test 9: Testing device access control")
        
        # Try to access a different device with current API key
        different_device_id = 10  # Different device
        url = f"{self.BASE_URL}/api/v1/devices/{different_device_id}/summary"
        
        response = requests.get(
            url,
            headers={"X-API-Key": self.API_KEY},
            timeout=10
        )
        
        # Should either return 403 (forbidden) or only allow access to own device
        assert response.status_code in [403, 404], f"Should restrict access to other devices, got {response.status_code}"
        print("✅ Device access control enforced")
    
    def test_10_device_summary_supports_query_parameters(self):
        """Test 10: Device summary should support query parameters for customization (measurement data)"""
        print("🔍 Test 10: Testing query parameters support with measurement data")
        
        # Send multiple different measurements to test limit
        print("   📊 Sending multiple measurements...")
        measurements = [
            ("temperature", 21.0),
            ("pressure", 1013.25),
            ("humidity", 65.5),
            ("temperature", 22.0),
            ("voltage", 3.3),
            ("current", 0.5)
        ]
        for measurement_type, value in measurements:
            self.send_measurement_data(measurement_type, value)
        
        url = f"{self.BASE_URL}/api/v1/devices/{self.DEVICE_ID}/summary"
        
        # Test with telemetry limit parameter
        response = requests.get(
            url,
            headers={"X-API-Key": self.API_KEY},
            params={"telemetry_limit": 3},
            timeout=10
        )
        
        assert response.status_code == 200, f"Should handle query parameters, got {response.status_code}"
        
        data = response.json()
        
        # Check that telemetry limit is respected
        if data["telemetry"]["recent_data"]:
            assert len(data["telemetry"]["recent_data"]) <= 3, "Should respect telemetry limit of 3"
            # Verify we have measurement structure
            for record in data["telemetry"]["recent_data"]:
                # Should have measurement structure or be legacy data
                has_measurement_structure = "measurement_type" in record and "value" in record
                has_legacy_structure = any(key in record for key in ["temperature", "pressure", "humidity"])
                assert has_measurement_structure or has_legacy_structure, "Each record should have measurement or legacy structure"
        
        print("✅ Query parameters supported with measurement data")
    
    def test_11_measurement_structure_telemetry_storage(self):
        """Test 11: Verify measurement structure telemetry is properly stored and retrieved"""
        print("🔍 Test 11: Testing measurement structure telemetry storage")
        
        # Send different types of measurements
        measurements_to_test = [
            ("temperature", 27.3),
            ("pressure", 1015.2),
            ("humidity", 68.5)
        ]
        
        for measurement_type, value in measurements_to_test:
            print(f"   📊 Sending {measurement_type}: {value}")
            success = self.send_measurement_data(measurement_type, value)
            assert success, f"Should successfully send {measurement_type} measurement"
        
        # Retrieve via telemetry API
        telemetry_url = f"{self.BASE_URL}/api/v1/telemetry/{self.DEVICE_ID}"
        response = requests.get(
            telemetry_url,
            headers={"X-API-Key": self.API_KEY},
            params={"limit": 3},
            timeout=10
        )
        
        assert response.status_code == 200, f"Should retrieve telemetry, got {response.status_code}"
        
        data = response.json()
        assert "data" in data, "Should contain telemetry data"
        
        if data["data"]:
            # Check that we have measurement structure data
            measurement_records = [
                record for record in data["data"] 
                if record.get("meta_test_type") == "tdd_measurement_test"
            ]
            
            assert len(measurement_records) >= 3, "Should have at least 3 measurement records"
            
            # Verify measurement structure
            for record in measurement_records[:3]:  # Check first 3
                assert "measurement_type" in record, "Should have measurement_type field"
                assert "value" in record, "Should have value field"
                assert "unit" in record, "Should have unit field"
                assert record.get("meta_test_type") == "tdd_measurement_test", "Should have correct test type"
                
                # Verify measurement type and unit consistency
                measurement_type = record.get("measurement_type")
                unit = record.get("unit")
                expected_unit = self._get_unit_for_measurement(measurement_type)
                assert unit == expected_unit, f"Unit {unit} should match expected {expected_unit} for {measurement_type}"
        
        print("✅ Measurement structure telemetry properly stored and retrieved")


def run_tdd_tests():
    """Run all TDD tests for device data summary API"""
    print("🚀 TDD Tests for Device Data Summary API")
    print("=" * 60)
    
    test_instance = TestDeviceDataSummaryAPI()
    
    tests = [
        ("Endpoint Exists", test_instance.test_01_device_summary_endpoint_exists),
        ("Authentication Required", test_instance.test_02_device_summary_requires_authentication),
        ("API Key Validation", test_instance.test_03_device_summary_validates_api_key),
        ("Device Information", test_instance.test_04_device_summary_returns_device_info),
        ("Status Information", test_instance.test_05_device_summary_returns_status_info),
        ("Recent Telemetry", test_instance.test_06_device_summary_returns_recent_telemetry),
        ("Configuration", test_instance.test_07_device_summary_returns_configuration),
        ("Non-existent Device", test_instance.test_08_device_summary_handles_nonexistent_device),
        ("Access Control", test_instance.test_09_device_summary_handles_device_access_control),
        ("Query Parameters", test_instance.test_10_device_summary_supports_query_parameters),
        ("Measurement Structure Storage", test_instance.test_11_measurement_structure_telemetry_storage),
    ]
    
    results = []
    
    for test_name, test_func in tests:
        try:
            test_func()
            results.append((test_name, True, None))
            print(f"✅ {test_name}: PASSED")
        except Exception as e:
            results.append((test_name, False, str(e)))
            print(f"❌ {test_name}: FAILED - {e}")
        print()
    
    # Summary
    print("=" * 60)
    print("📊 TDD Test Results Summary")
    print("=" * 60)
    
    passed = sum(1 for _, success, _ in results if success)
    total = len(results)
    
    for test_name, success, error in results:
        status = "✅ PASS" if success else "❌ FAIL"
        print(f"   {status}: {test_name}")
        if not success and error:
            print(f"      Error: {error}")
    
    print(f"\n📈 Results: {passed}/{total} tests passed")
    
    if passed == total:
        print("🎉 All TDD tests passed! Ready to implement the API.")
        return 0
    else:
        print("⚠️  Some tests failed. API needs to be implemented/fixed.")
        return 1


if __name__ == "__main__":
    exit(run_tdd_tests())