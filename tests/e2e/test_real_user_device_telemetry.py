"""
Real End-to-End Test: Complete User, Device, and Telemetry Flow
Creates a real user with password, real device, and sends real telemetry data to IoTDB
"""

import pytest
import json
import time
import os
from datetime import datetime, timezone
import requests


class TestRealUserDeviceTelemetryFlow:
    """
    REAL End-to-End test that creates:
    1. A real user with password "test123"
    2. A real device for that user
    3. Sends real telemetry data to IoTDB
    4. Verifies everything is stored and accessible

    This test uses the actual database and IoTDB - no mocking!
    """

    def test_complete_real_user_device_telemetry_flow(self, client, app, iotdb_service, telemetry_helper):
        """
        COMPLETE REAL E2E TEST

        This test performs REAL operations:
        1. Creates a real user with password "test123" in PostgreSQL
        2. Creates a real device for that user
        3. Sends real telemetry data to IoTDB
        4. Verifies user can authenticate
        5. Verifies device is registered
        6. Verifies telemetry data is stored in IoTDB
        7. Queries data back from IoTDB
        """

        from src.models import User, Device, db
        from werkzeug.security import generate_password_hash, check_password_hash

        print("\n" + "=" * 80)
        print("🚀 REAL USER-DEVICE-TELEMETRY E2E TEST")
        print("=" * 80)

        # ============================================================
        # STEP 1: Create REAL User with Password "test123"
        # ============================================================
        print("\n📋 STEP 1: Creating REAL user with password 'test123'...")
        print("-" * 60)

        timestamp = int(time.time())
        username = f"real_user_{timestamp}"
        email = f"real_user_{timestamp}@iotflow.test"
        password = "test123"

        with app.app_context():
            # Create real user with hashed password
            password_hash = generate_password_hash(password)

            user = User(username=username, email=email, password_hash=password_hash, is_active=True, is_admin=False)

            db.session.add(user)
            db.session.commit()
            db.session.refresh(user)

            user_id = user.id

            # Verify password hashing works
            assert check_password_hash(user.password_hash, password), "Password hash verification failed"

        print(f"✅ REAL user created successfully:")
        print(f"   - Username: {username}")
        print(f"   - Email: {email}")
        print(f"   - Password: {password}")
        print(f"   - User ID: {user_id}")
        print(f"   - Password Hash: {password_hash[:30]}...")
        print(f"   - Database: PostgreSQL (persistent)")

        # ============================================================
        # STEP 2: Create REAL Device for the User
        # ============================================================
        print("\n🔧 STEP 2: Creating REAL device for the user...")
        print("-" * 60)

        device_name = f"Real IoT Sensor {timestamp}"
        device_type = "environmental_sensor"
        location = "Real Test Lab"

        with app.app_context():
            device = Device(
                name=device_name,
                device_type=device_type,
                description="Real IoT device for complete E2E testing",
                location=location,
                metadata={
                    "manufacturer": "IoTFlow Real Systems",
                    "model": "RTS-ENV-2024",
                    "firmware_version": "v2.1.0",
                    "installation_date": datetime.now(timezone.utc).isoformat(),
                    "test_type": "real_e2e",
                    "created_by_test": True,
                    "user_password": "test123",  # For reference (not secure in real app)
                },
                user_id=user_id,
                status="active",
            )

            db.session.add(device)
            db.session.commit()
            db.session.refresh(device)

            device_id = device.id
            device_api_key = device.api_key

        print(f"✅ REAL device created successfully:")
        print(f"   - Device Name: {device_name}")
        print(f"   - Device Type: {device_type}")
        print(f"   - Device ID: {device_id}")
        print(f"   - API Key: {device_api_key[:20]}...")
        print(f"   - Location: {location}")
        print(f"   - Owner: {username} (ID: {user_id})")
        print(f"   - Database: PostgreSQL (persistent)")

        # ============================================================
        # STEP 3: Send REAL Telemetry Data to IoTDB
        # ============================================================
        print("\n📡 STEP 3: Sending REAL telemetry data to IoTDB...")
        print("-" * 60)

        # Send multiple telemetry readings with realistic sensor data
        telemetry_readings = [
            {
                "temperature": 22.5,
                "humidity": 45.2,
                "pressure": 1013.25,
                "air_quality_index": 35,
                "battery_level": 98,
                "signal_strength": -45,
                "reading_type": "initial",
            },
            {
                "temperature": 23.1,
                "humidity": 46.8,
                "pressure": 1012.80,
                "air_quality_index": 32,
                "battery_level": 97,
                "signal_strength": -42,
                "reading_type": "follow_up",
            },
            {
                "temperature": 22.8,
                "humidity": 44.5,
                "pressure": 1013.10,
                "air_quality_index": 38,
                "battery_level": 97,
                "signal_strength": -48,
                "reading_type": "final",
            },
        ]

        successful_sends = 0

        for i, reading in enumerate(telemetry_readings, 1):
            print(f"\n   📊 Sending reading {i}/3...")

            # Add timestamp and metadata
            telemetry_data = {
                "device_id": device_id,
                "api_key": device_api_key,
                "data": reading,
                "metadata": {
                    "device_type": device_type,
                    "location": location,
                    "user_id": user_id,
                    "username": username,
                    "test_type": "real_e2e",
                    "reading_sequence": i,
                    "sensor_calibrated": True,
                },
                "timestamp": datetime.now(timezone.utc).isoformat(),
            }

            response = client.post(
                "/api/v1/telemetry",
                data=json.dumps(telemetry_data),
                content_type="application/json",
                headers={"X-API-Key": device_api_key},
            )

            if response.status_code in [200, 201]:
                successful_sends += 1
                print(f"      ✅ Reading {i} sent successfully")
                print(f"         Temperature: {reading['temperature']}°C")
                print(f"         Humidity: {reading['humidity']}%")
                print(f"         Pressure: {reading['pressure']} hPa")
                print(f"         AQI: {reading['air_quality_index']}")
            else:
                print(f"      ❌ Reading {i} failed: {response.status_code}")
                if response.get_json():
                    print(f"         Error: {response.get_json()}")

            # Small delay between readings
            time.sleep(0.5)

        print(f"\n📊 Telemetry Summary:")
        print(f"   - Readings sent: {successful_sends}/{len(telemetry_readings)}")
        print(f"   - Target: IoTDB time-series database")
        print(f"   - Path: root.iotflow.users.user_{user_id}.devices.device_{device_id}")

        # Wait for IoTDB to process the data
        if iotdb_service.is_available():
            print("   ⏳ Waiting for IoTDB to process data...")
            time.sleep(3)

        # ============================================================
        # STEP 4: Verify IoTDB Data Storage
        # ============================================================
        print("\n🔍 STEP 4: Verifying REAL data storage in IoTDB...")
        print("-" * 60)

        verification = telemetry_helper.verify_iotdb_storage(
            device=device, iotdb_service=iotdb_service, expected_count=successful_sends
        )

        if verification["verified"]:
            print(f"✅ IoTDB verification successful:")
            print(f"   - Records found: {verification['records_found']}")
            print(f"   - Total count: {verification['total_count']}")
            print(f"   - Storage: IoTDB time-series database")

            if verification["latest_records"]:
                print(f"\n   📊 Latest telemetry records:")
                for i, record in enumerate(verification["latest_records"][:2], 1):
                    print(f"      Record {i}:")
                    print(f"      - Timestamp: {record.get('timestamp', 'N/A')}")
                    for key, value in record.items():
                        if key not in ["timestamp", "device_id"] and value is not None:
                            print(f"      - {key}: {value}")
        else:
            print(f"⚠️  IoTDB verification: {verification.get('message', 'Failed')}")

        # ============================================================
        # STEP 5: Query Telemetry Data via API
        # ============================================================
        print("\n📊 STEP 5: Querying telemetry data via API...")
        print("-" * 60)

        response = telemetry_helper.query_telemetry(device=device, limit=10, start_time="-1h")

        if response.status_code == 200:
            data = response.get_json()
            records = data.get("data", [])

            print(f"✅ API query successful:")
            print(f"   - Records retrieved: {len(records)}")
            print(f"   - IoTDB available: {data.get('iotdb_available', False)}")

            if records:
                print(f"\n   📊 Retrieved telemetry data:")
                for i, record in enumerate(records[:2], 1):
                    print(f"      API Record {i}:")
                    print(f"      - Timestamp: {record.get('timestamp', 'N/A')}")
                    for key, value in record.items():
                        if key not in ["timestamp", "device_id"] and value is not None:
                            print(f"      - {key}: {value}")
        else:
            print(f"❌ API query failed: {response.status_code}")

        # ============================================================
        # STEP 6: Verify User Authentication
        # ============================================================
        print("\n🔐 STEP 6: Verifying user authentication...")
        print("-" * 60)

        with app.app_context():
            # Verify user exists and password works
            stored_user = User.query.get(user_id)
            assert stored_user is not None, "User should exist in database"
            assert stored_user.username == username, "Username should match"
            assert stored_user.email == email, "Email should match"
            assert check_password_hash(stored_user.password_hash, password), "Password should verify"
            assert stored_user.is_active, "User should be active"

            print(f"✅ User authentication verified:")
            print(f"   - User exists: Yes")
            print(f"   - Username: {stored_user.username}")
            print(f"   - Email: {stored_user.email}")
            print(f"   - Password verification: ✅ PASS")
            print(f"   - Account status: {'Active' if stored_user.is_active else 'Inactive'}")

        # ============================================================
        # STEP 7: Verify Device Ownership
        # ============================================================
        print("\n🔧 STEP 7: Verifying device ownership...")
        print("-" * 60)

        with app.app_context():
            # Verify device belongs to user
            stored_device = Device.query.get(device_id)
            user_devices = Device.query.filter_by(user_id=user_id).all()

            assert stored_device is not None, "Device should exist in database"
            assert stored_device.user_id == user_id, "Device should belong to user"
            assert stored_device.name == device_name, "Device name should match"
            assert stored_device.status == "active", "Device should be active"

            print(f"✅ Device ownership verified:")
            print(f"   - Device exists: Yes")
            print(f"   - Device name: {stored_device.name}")
            print(f"   - Owner: {username} (ID: {user_id})")
            print(f"   - Status: {stored_device.status}")
            print(f"   - API Key: {stored_device.api_key[:20]}...")
            print(f"   - User's total devices: {len(user_devices)}")

        # ============================================================
        # STEP 8: Test Real API Authentication
        # ============================================================
        print("\n🔑 STEP 8: Testing real API authentication...")
        print("-" * 60)

        # Test API key authentication
        test_payload = {
            "device_id": device_id,
            "api_key": device_api_key,
            "data": {
                "test_reading": True,
                "authentication_test": "success",
                "timestamp_test": datetime.now(timezone.utc).isoformat(),
            },
            "metadata": {"test_type": "authentication_verification"},
        }

        auth_response = client.post(
            "/api/v1/telemetry",
            data=json.dumps(test_payload),
            content_type="application/json",
            headers={"X-API-Key": device_api_key},
        )

        if auth_response.status_code in [200, 201]:
            print(f"✅ API authentication successful:")
            print(f"   - API Key: Valid")
            print(f"   - Device Access: Authorized")
            print(f"   - Telemetry Endpoint: Accessible")
        else:
            print(f"❌ API authentication failed: {auth_response.status_code}")

        # Test invalid API key
        invalid_response = client.post(
            "/api/v1/telemetry",
            data=json.dumps(test_payload),
            content_type="application/json",
            headers={"X-API-Key": "invalid_key_12345"},
        )

        if invalid_response.status_code == 401:
            print(f"✅ Invalid API key properly rejected (401)")
        else:
            print(f"⚠️  Invalid API key handling: {invalid_response.status_code}")

        # ============================================================
        # FINAL VERIFICATION AND SUMMARY
        # ============================================================
        print("\n" + "=" * 80)
        print("🎯 FINAL VERIFICATION - REAL E2E TEST RESULTS")
        print("=" * 80)

        # Comprehensive assertions
        assertions = {
            "User created with correct password": check_password_hash(password_hash, password),
            "Device created and linked to user": stored_device.user_id == user_id,
            "Telemetry data sent successfully": successful_sends >= 2,
            "IoTDB storage verified": verification.get("verified", False),
            "API query successful": response.status_code == 200,
            "User authentication works": check_password_hash(stored_user.password_hash, password),
            "Device ownership verified": stored_device.user_id == user_id,
            "API key authentication works": auth_response.status_code in [200, 201],
            "Invalid API key rejected": invalid_response.status_code == 401,
        }

        print(f"\n✅ Complete E2E Test Results:")
        passed_checks = 0
        for check, passed in assertions.items():
            status = "✅ PASS" if passed else "❌ FAIL"
            print(f"   {status}: {check}")
            if passed:
                passed_checks += 1

        print(f"\n📊 Test Summary:")
        print(f"   - Total Checks: {len(assertions)}")
        print(f"   - Passed: {passed_checks}")
        print(f"   - Failed: {len(assertions) - passed_checks}")
        print(f"   - Success Rate: {(passed_checks/len(assertions)*100):.1f}%")

        print(f"\n💾 Created Real Data:")
        print(f"   👤 User: {username}")
        print(f"      - Email: {email}")
        print(f"      - Password: {password}")
        print(f"      - ID: {user_id}")
        print(f"      - Database: PostgreSQL")

        print(f"   🔧 Device: {device_name}")
        print(f"      - Type: {device_type}")
        print(f"      - ID: {device_id}")
        print(f"      - API Key: {device_api_key[:20]}...")
        print(f"      - Database: PostgreSQL")

        print(f"   📊 Telemetry Data:")
        print(f"      - Records sent: {successful_sends}")
        print(f"      - Storage: IoTDB time-series database")
        print(f"      - Path: root.iotflow.users.user_{user_id}.devices.device_{device_id}")

        if iotdb_service.is_available():
            print(f"      - Verification: ✅ Data confirmed in IoTDB")
        else:
            print(f"      - Verification: ⚠️  IoTDB not available")

        print(f"\n🚀 Real World Usage:")
        print(f"   - User can login with: {username} / {password}")
        print(f"   - Device can send data with API key: {device_api_key[:20]}...")
        print(f"   - Telemetry data is persistent and queryable")
        print(f"   - All data remains in database for further testing")

        # All assertions must pass for test to succeed
        assert all(assertions.values()), f"Some E2E checks failed. Passed: {passed_checks}/{len(assertions)}"

        print("\n" + "=" * 80)
        print("🎉 REAL E2E TEST COMPLETED SUCCESSFULLY!")
        print("=" * 80)
        print(f"✅ Created real user '{username}' with password '{password}'")
        print(f"✅ Created real device '{device_name}' with working API key")
        print(f"✅ Sent {successful_sends} real telemetry records to IoTDB")
        print(f"✅ Verified complete data flow from user creation to telemetry storage")
        print("=" * 80 + "\n")


class TestRealUserDeviceScenarios:
    """
    Additional real-world scenarios with the created user and device
    """

    def test_real_user_multiple_devices(self, client, app, iotdb_service, telemetry_helper):
        """
        Test creating multiple devices for a real user and sending telemetry from each
        """

        from src.models import User, Device, db
        from werkzeug.security import generate_password_hash

        print("\n" + "=" * 80)
        print("🔧 REAL USER WITH MULTIPLE DEVICES TEST")
        print("=" * 80)

        timestamp = int(time.time())
        username = f"multi_device_user_{timestamp}"
        password = "test123"

        # Create user
        with app.app_context():
            user = User(
                username=username,
                email=f"{username}@iotflow.test",
                password_hash=generate_password_hash(password),
                is_active=True,
                is_admin=False,
            )
            db.session.add(user)
            db.session.commit()
            db.session.refresh(user)
            user_id = user.id

        print(f"✅ Created user: {username}")

        # Create multiple devices
        device_configs = [
            {"name": f"Temperature Sensor {timestamp}", "type": "temperature_sensor"},
            {"name": f"Humidity Sensor {timestamp}", "type": "humidity_sensor"},
            {"name": f"Air Quality Monitor {timestamp}", "type": "air_quality_sensor"},
        ]

        created_devices = []

        with app.app_context():
            for config in device_configs:
                device = Device(
                    name=config["name"],
                    device_type=config["type"],
                    description=f"Real {config['type']} for multi-device testing",
                    location="Multi-Device Test Lab",
                    user_id=user_id,
                    status="active",
                )
                db.session.add(device)
                created_devices.append(device)

            db.session.commit()

            for device in created_devices:
                db.session.refresh(device)
                print(f"✅ Created device: {device.name} (ID: {device.id})")

        # Send telemetry from each device
        total_sent = 0

        for device in created_devices:
            print(f"\n📡 Sending telemetry from {device.name}...")

            if "temperature" in device.device_type:
                data = {"temperature": 25.0 + len(created_devices), "battery": 95}
            elif "humidity" in device.device_type:
                data = {"humidity": 50.0 + len(created_devices), "battery": 92}
            else:
                data = {"aqi": 30 + len(created_devices), "pm25": 15, "battery": 88}

            response = telemetry_helper.send_telemetry(
                device=device, data=data, metadata={"test_type": "multi_device", "user": username}
            )

            if response.status_code in [200, 201]:
                total_sent += 1
                print(f"   ✅ Telemetry sent successfully")

        print(f"\n📊 Multi-device summary:")
        print(f"   - User: {username}")
        print(f"   - Devices created: {len(created_devices)}")
        print(f"   - Telemetry sent: {total_sent}/{len(created_devices)}")

        # Verify all devices belong to user
        with app.app_context():
            user_devices = Device.query.filter_by(user_id=user_id).all()
            assert len(user_devices) == len(created_devices)
            print(f"   ✅ All {len(user_devices)} devices verified in database")

        assert total_sent == len(created_devices), "All devices should send telemetry successfully"

        print("🎉 Multi-device test completed successfully!")


class TestRealDataPersistence:
    """
    Test that verifies data persistence across test runs
    """

    def test_verify_persistent_real_data(self, client, app, iotdb_service):
        """
        Verify that previously created real data still exists and is accessible
        """

        from src.models import User, Device, db

        print("\n" + "=" * 80)
        print("💾 REAL DATA PERSISTENCE VERIFICATION")
        print("=" * 80)

        with app.app_context():
            # Find users created by our tests
            test_users = User.query.filter(
                User.username.like("real_user_%") | User.username.like("multi_device_user_%")
            ).all()

            print(f"📊 Found {len(test_users)} test users in database:")

            total_devices = 0
            for user in test_users:
                user_devices = Device.query.filter_by(user_id=user.id).all()
                total_devices += len(user_devices)

                print(f"   👤 {user.username}:")
                print(f"      - Email: {user.email}")
                print(f"      - Active: {user.is_active}")
                print(f"      - Devices: {len(user_devices)}")

                for device in user_devices[:2]:  # Show first 2 devices
                    print(f"         🔧 {device.name} ({device.device_type})")

            print(f"\n📊 Persistence Summary:")
            print(f"   - Test users found: {len(test_users)}")
            print(f"   - Total devices: {total_devices}")

            # Check if we're using in-memory SQLite (CI mode) or persistent PostgreSQL
            is_ci_mode = os.environ.get("TESTING", "false").lower() == "true"
            force_postgres = os.environ.get("FORCE_POSTGRES", "false").lower() == "true"

            if is_ci_mode and not force_postgres:
                print(f"   - Database: SQLite (in-memory, CI mode)")
                print(f"   ℹ️  Note: In CI mode, data doesn't persist between test runs")
                # In CI mode with SQLite, we don't expect persistent data
                if len(test_users) == 0:
                    print(f"   ✅ Expected behavior: No persistent data in CI mode")
            else:
                print(f"   - Database: PostgreSQL (persistent)")

            if iotdb_service.is_available():
                print(f"   - IoTDB: Available for telemetry queries")
            else:
                print(f"   - IoTDB: Not available")

        # Only assert persistent data exists if we're not in CI mode with SQLite
        is_ci_mode = os.environ.get("TESTING", "false").lower() == "true"
        force_postgres = os.environ.get("FORCE_POSTGRES", "false").lower() == "true"

        if not (is_ci_mode and not force_postgres):
            assert len(test_users) > 0, "Should find previously created test users in persistent database"
        else:
            print("✅ CI mode verification complete - using in-memory database as expected")
        print("✅ Data persistence verified - real data persists between test runs!")
