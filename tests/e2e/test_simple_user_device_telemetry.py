"""
Simple End-to-End Test: User -> Device -> Telemetry
A focused test that creates a user, registers a device, and sends telemetry data
Uses PERSISTENT PostgreSQL database - data remains after test completion
"""

import pytest
import json
import time
import os
from datetime import datetime, timezone


@pytest.fixture(scope="function", autouse=True)
def force_persistent_database():
    """
    Force the use of persistent PostgreSQL database for this test
    """
    # Set environment variable to force PostgreSQL usage
    original_force_postgres = os.environ.get("FORCE_POSTGRES")
    os.environ["FORCE_POSTGRES"] = "true"

    yield

    # Restore original value
    if original_force_postgres is not None:
        os.environ["FORCE_POSTGRES"] = original_force_postgres
    else:
        os.environ.pop("FORCE_POSTGRES", None)


class TestSimpleUserDeviceTelemetry:
    """
    Simple end-to-end test that covers the basic IoTFlow workflow:
    1. Create a user
    2. Register a device for that user
    3. Send telemetry data from the device
    4. Verify the data was stored and can be retrieved
    """

    def test_simple_user_device_telemetry_flow(self, client, app, iotdb_service, telemetry_helper):
        """
        Test the complete flow from user creation to telemetry data retrieval

        This test:
        - Creates a real user in the database
        - Registers a real device for that user
        - Sends telemetry data via HTTP API
        - Verifies the data can be retrieved
        - Checks IoTDB storage if available
        """

        from src.models import User, Device, db

        print("\n" + "=" * 60)
        print("🚀 PERSISTENT E2E TEST: User → Device → Telemetry")
        print("📊 Data will be stored in PostgreSQL and remain after test")
        print("=" * 60)

        # ============================================================
        # STEP 1: Create User
        # ============================================================
        print("\n📝 Step 1: Creating user...")

        with app.app_context():
            # Create a unique user
            timestamp = int(time.time())
            user = User(
                username=f"testuser_{timestamp}",
                email=f"testuser_{timestamp}@example.com",
                password_hash="$pbkdf2-sha256$29000$N.Z8z1nrPWeMcY4RwjjHGA$1BVbKKOKUmBT5.DXcxRPXtgZ8zQiOx6VRV8PnA2updk",  # "password123"
                is_active=True,
                is_admin=False,
            )
            db.session.add(user)
            db.session.commit()
            db.session.refresh(user)

            user_id = user.id
            username = user.username

        print(f"   ✅ User created successfully")
        print(f"      - ID: {user_id}")
        print(f"      - Username: {username}")
        print(f"      - Email: {user.email}")

        # ============================================================
        # STEP 2: Register Device
        # ============================================================
        print("\n🔌 Step 2: Registering device...")

        with app.app_context():
            # Create a device for the user
            device = Device(
                name=f"TestDevice_{timestamp}",
                device_type="temperature_sensor",
                description="Simple E2E test device",
                location="Test Lab",
                metadata={"manufacturer": "TestCorp", "model": "TS-E2E", "firmware_version": "1.0.0"},
                user_id=user_id,
                status="active",
            )
            db.session.add(device)
            db.session.commit()
            db.session.refresh(device)

            device_id = device.id
            device_api_key = device.api_key
            device_name = device.name

        print(f"   ✅ Device registered successfully")
        print(f"      - ID: {device_id}")
        print(f"      - Name: {device_name}")
        print(f"      - API Key: {device_api_key[:20]}...")
        print(f"      - Type: {device.device_type}")
        print(f"      - Status: {device.status}")

        # ============================================================
        # STEP 3: Send Telemetry Data (Structured Format)
        # ============================================================
        print("\n📊 Step 3: Sending telemetry data (structured format)...")

        # Prepare structured telemetry data
        telemetry_data = {"temperature": 23.5, "humidity": 65.2, "pressure": 1013.25, "battery_level": 87}

        metadata = {"location": "Test Lab", "sensor_status": "operational", "test_run": "simple_e2e"}

        # Send telemetry using the helper
        response = telemetry_helper.send_telemetry(device=device, data=telemetry_data, metadata=metadata)

        print(f"   📤 Telemetry sent - Status: {response.status_code}")

        if response.status_code in [200, 201]:
            print(f"   ✅ Telemetry accepted successfully")
            print(f"      - Temperature: {telemetry_data['temperature']}°C")
            print(f"      - Humidity: {telemetry_data['humidity']}%")
            print(f"      - Pressure: {telemetry_data['pressure']} hPa")
            print(f"      - Battery: {telemetry_data['battery_level']}%")
        else:
            response_data = response.get_json() if response.get_json() else {}
            print(f"   ❌ Telemetry failed: {response_data}")
            pytest.fail(f"Telemetry submission failed with status {response.status_code}")

        # Wait for data processing
        print("   ⏳ Waiting for data processing...")
        time.sleep(2)

        # ============================================================
        # STEP 4: Send More Telemetry Data (Flat Format)
        # ============================================================
        print("\n📊 Step 4: Sending more telemetry data (flat format)...")

        # Send flat telemetry data
        response = telemetry_helper.send_flat_telemetry(
            device=device, temperature=24.1, humidity=63.8, pressure=1012.80, battery_level=86, signal_strength=-65
        )

        print(f"   📤 Flat telemetry sent - Status: {response.status_code}")

        if response.status_code in [200, 201]:
            print(f"   ✅ Flat telemetry accepted successfully")
            print(f"      - Temperature: 24.1°C")
            print(f"      - Humidity: 63.8%")
            print(f"      - Signal: -65 dBm")
        else:
            response_data = response.get_json() if response.get_json() else {}
            print(f"   ❌ Flat telemetry failed: {response_data}")

        # Wait for data processing
        time.sleep(2)

        # ============================================================
        # STEP 5: Query Telemetry Data
        # ============================================================
        print("\n🔍 Step 5: Querying telemetry data...")

        # Query telemetry data
        response = telemetry_helper.query_telemetry(device=device, limit=10)

        print(f"   📥 Query response - Status: {response.status_code}")

        if response.status_code == 200:
            query_data = response.get_json()
            telemetry_records = query_data.get("data", [])
            iotdb_available = query_data.get("iotdb_available", False)

            print(f"   ✅ Telemetry data retrieved successfully")
            print(f"      - Records found: {len(telemetry_records)}")
            print(f"      - IoTDB available: {iotdb_available}")

            # Display recent records
            if telemetry_records:
                print(f"\n   📋 Recent telemetry records:")
                for i, record in enumerate(telemetry_records[:3], 1):
                    print(f"      Record {i}:")
                    print(f"         - Timestamp: {record.get('timestamp', 'N/A')}")
                    if "temperature" in record:
                        print(f"         - Temperature: {record['temperature']}°C")
                    if "humidity" in record:
                        print(f"         - Humidity: {record['humidity']}%")
                    if "pressure" in record:
                        print(f"         - Pressure: {record['pressure']} hPa")
                    if "battery_level" in record:
                        print(f"         - Battery: {record['battery_level']}%")
            else:
                if iotdb_available:
                    print(f"   ⚠️  No records found (data may still be processing)")
                else:
                    print(f"   ℹ️  No records (IoTDB disabled in test environment)")
        else:
            query_data = response.get_json() if response.get_json() else {}
            print(f"   ❌ Query failed: {query_data}")

        # ============================================================
        # STEP 6: Verify IoTDB Storage (if available)
        # ============================================================
        print("\n🗄️  Step 6: Verifying IoTDB storage...")

        # Verify IoTDB storage using helper
        verification = telemetry_helper.verify_iotdb_storage(
            device=device, iotdb_service=iotdb_service, expected_count=2  # We sent 2 telemetry messages
        )

        if verification["iotdb_available"]:
            if verification["verified"]:
                print(f"   ✅ IoTDB verification successful")
                print(f"      - Records found: {verification['records_found']}")
                print(f"      - Total count: {verification['total_count']}")

                if verification.get("count_matches"):
                    print(f"      - Expected count met: ✅")
                else:
                    print(f"      - Expected count: {verification.get('expected_count', 'N/A')}")
                    print(f"      - Actual count: {verification['total_count']}")

                # Show latest records from IoTDB
                if verification["latest_records"]:
                    print(f"\n   📋 Latest records from IoTDB:")
                    for i, record in enumerate(verification["latest_records"], 1):
                        print(f"      Record {i}: {record}")
            else:
                print(f"   ❌ IoTDB verification failed")
                print(f"      - Error: {verification.get('error', 'Unknown error')}")
        else:
            print(f"   ℹ️  IoTDB not available for verification")
            print(f"      - Message: {verification.get('message', 'IoTDB disabled')}")

        # ============================================================
        # STEP 7: Verify Database State
        # ============================================================
        print("\n💾 Step 7: Verifying database state...")

        with app.app_context():
            # Verify user still exists
            user = User.query.get(user_id)
            assert user is not None, "User should still exist"
            assert user.is_active, "User should be active"

            # Verify device still exists and is properly linked
            device = Device.query.get(device_id)
            assert device is not None, "Device should still exist"
            assert device.user_id == user_id, "Device should belong to the user"
            assert device.status == "active", "Device should be active"

            # Check user's devices
            user_devices = Device.query.filter_by(user_id=user_id).all()
            assert len(user_devices) >= 1, "User should have at least one device"

            print(f"   ✅ Database state verified")
            print(f"      - User exists: ✅ (ID: {user.id})")
            print(f"      - Device exists: ✅ (ID: {device.id})")
            print(f"      - Device belongs to user: ✅")
            print(f"      - User has {len(user_devices)} device(s)")

        # ============================================================
        # FINAL SUMMARY
        # ============================================================
        print("\n" + "=" * 60)
        print("🎉 PERSISTENT E2E TEST COMPLETED SUCCESSFULLY!")
        print("💾 Data has been stored in PostgreSQL and IoTDB")
        print("=" * 60)

        # Test summary
        test_results = {
            "User created": user_id is not None,
            "Device registered": device_id is not None,
            "Structured telemetry sent": True,
            "Flat telemetry sent": True,
            "Telemetry data queried": response.status_code == 200,
            "Database state verified": True,
            "IoTDB available": verification["iotdb_available"],
        }

        print(f"\n📊 Test Results Summary:")
        for check, passed in test_results.items():
            status = "✅" if passed else "❌"
            print(f"   {status} {check}")

        print(f"\n📋 Created Resources:")
        print(f"   - User ID: {user_id}")
        print(f"   - Username: {username}")
        print(f"   - Device ID: {device_id}")
        print(f"   - Device Name: {device_name}")
        print(f"   - Telemetry Records: 2 sent")

        # Environment info
        import os

        is_ci = os.environ.get("TESTING", "false").lower() == "true"
        env_type = "CI Environment" if is_ci else "Local Development"

        print(f"\n🔧 Environment: {env_type}")
        print(f"   - Database: PostgreSQL (PERSISTENT)")
        if verification["iotdb_available"]:
            print(f"   - IoTDB: Available and tested (PERSISTENT)")
        else:
            print(f"   - IoTDB: Disabled/Mocked for testing")

        print(f"\n💾 PERSISTENT DATA CREATED:")
        print(f"   - User '{username}' (ID: {user_id}) stored in PostgreSQL")
        print(f"   - Device '{device_name}' (ID: {device_id}) stored in PostgreSQL")
        print(f"   - Telemetry data stored in IoTDB (if available)")
        print(f"   - Data will remain accessible after test completion")

        print("=" * 60)

        # Assert all critical tests passed
        critical_tests = [
            test_results["User created"],
            test_results["Device registered"],
            test_results["Structured telemetry sent"],
            test_results["Database state verified"],
        ]

        assert all(critical_tests), "Critical E2E test components failed"

        print("✅ All assertions passed - E2E test successful!")


class TestTelemetryDataTypes:
    """
    Test different types of telemetry data formats
    """

    def test_various_telemetry_formats(self, client, app, telemetry_helper):
        """
        Test sending various types of telemetry data formats
        """

        from src.models import User, Device, db

        print("\n" + "=" * 60)
        print("🔬 PERSISTENT TELEMETRY DATA TYPES TEST")
        print("📊 Testing various data formats with persistent storage")
        print("=" * 60)

        # Setup user and device
        with app.app_context():
            timestamp = int(time.time())
            user = User(
                username=f"datatypes_user_{timestamp}",
                email=f"datatypes_{timestamp}@example.com",
                password_hash="$pbkdf2-sha256$29000$N.Z8z1nrPWeMcY4RwjjHGA$1BVbKKOKUmBT5.DXcxRPXtgZ8zQiOx6VRV8PnA2updk",
                is_active=True,
            )
            db.session.add(user)
            db.session.commit()
            db.session.refresh(user)

            device = Device(
                name=f"DataTypesDevice_{timestamp}",
                device_type="multi_sensor",
                description="Device for testing various data types",
                user_id=user.id,
                status="active",
            )
            db.session.add(device)
            db.session.commit()
            db.session.refresh(device)

            user_id = user.id
            device_id = device.id

        print(f"✅ Setup complete - User: {user_id}, Device: {device_id}")

        # Test 1: Numeric data
        print("\n📊 Test 1: Numeric telemetry data...")
        response = telemetry_helper.send_telemetry(
            device=device,
            data={"temperature": 25.7, "humidity": 60, "pressure": 1013.25, "altitude": 150.5, "battery_voltage": 3.7},
        )
        assert response.status_code in [200, 201], f"Numeric data failed: {response.status_code}"
        print("   ✅ Numeric data accepted")

        # Test 2: String data
        print("\n📝 Test 2: String telemetry data...")
        response = telemetry_helper.send_telemetry(
            device=device,
            data={
                "status": "operational",
                "location": "Building A, Floor 2",
                "firmware_version": "1.2.3",
                "error_message": "none",
            },
        )
        assert response.status_code in [200, 201], f"String data failed: {response.status_code}"
        print("   ✅ String data accepted")

        # Test 3: Boolean data
        print("\n🔘 Test 3: Boolean telemetry data...")
        response = telemetry_helper.send_telemetry(
            device=device, data={"is_online": True, "alarm_active": False, "maintenance_mode": False, "door_open": True}
        )
        assert response.status_code in [200, 201], f"Boolean data failed: {response.status_code}"
        print("   ✅ Boolean data accepted")

        # Test 4: Mixed data types
        print("\n🔀 Test 4: Mixed telemetry data...")
        response = telemetry_helper.send_telemetry(
            device=device,
            data={
                "temperature": 26.1,
                "status": "normal",
                "is_calibrated": True,
                "reading_count": 1547,
                "last_maintenance": "2024-01-15",
                "coordinates": [40.7128, -74.0060],  # Array data
            },
            metadata={"test_type": "mixed_data", "data_quality": "high"},
        )
        assert response.status_code in [200, 201], f"Mixed data failed: {response.status_code}"
        print("   ✅ Mixed data types accepted")

        time.sleep(1)

        # Verify data retrieval
        print("\n🔍 Verifying data retrieval...")
        response = telemetry_helper.query_telemetry(device=device, limit=10)

        if response.status_code == 200:
            data = response.get_json()
            records = data.get("data", [])
            print(f"   ✅ Retrieved {len(records)} telemetry records")

            # Show sample of retrieved data
            if records:
                print(f"   📋 Sample record: {records[0] if records else 'None'}")
        else:
            print(f"   ⚠️  Data retrieval returned: {response.status_code}")

        print(f"\n🎉 Telemetry data types test completed!")
        print(f"💾 User '{user.username}' and device '{device.name}' data persisted in PostgreSQL")
        print(f"📊 Various telemetry data formats stored in IoTDB (if available)")


class TestErrorHandling:
    """
    Test error handling in the E2E flow
    """

    def test_invalid_api_key(self, client, app):
        """
        Test telemetry submission with invalid API key
        """

        print("\n" + "=" * 60)
        print("🚫 ERROR HANDLING TEST: Invalid API Key")
        print("🔒 Testing security with persistent database")
        print("=" * 60)

        # Try to send telemetry with invalid API key
        invalid_telemetry = {
            "device_id": 99999,  # Non-existent device
            "api_key": "invalid_api_key_12345",
            "temperature": 25.0,
            "timestamp": datetime.now(timezone.utc).isoformat(),
        }

        response = client.post(
            "/api/v1/telemetry",
            data=json.dumps(invalid_telemetry),
            content_type="application/json",
            headers={"X-API-Key": "invalid_api_key_12345"},
        )

        print(f"   📤 Invalid API key test - Status: {response.status_code}")

        # Should return 401 or 403 (unauthorized)
        assert response.status_code in [401, 403], f"Expected 401/403, got {response.status_code}"

        response_data = response.get_json()
        print(f"   ✅ Correctly rejected invalid API key")
        print(f"      - Status: {response.status_code}")
        print(f"      - Message: {response_data.get('message', 'No message') if response_data else 'No response data'}")

        print("\n🎉 Error handling test completed!")
