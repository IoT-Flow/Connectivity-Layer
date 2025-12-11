"""
Persistent Data Creation Test
Creates test users, devices, and telemetry data that remains in the database
for development, testing, and demonstration purposes.
"""

import pytest
import json
import time
import math
from datetime import datetime, timezone, timedelta
import random


class TestPersistentDataCreation:
    """
    Creates persistent test data in the database for development and testing.

    This test creates:
    - Multiple test users with different roles
    - Various device types for each user
    - Sample telemetry data with realistic patterns
    - Data remains in database after test completion
    """

    def test_create_persistent_test_data(self, client, app):
        """
        Creates comprehensive test data that persists in the database.

        This includes:
        - Admin and regular users
        - Multiple device types per user
        - Historical telemetry data with realistic patterns
        - Various device statuses and configurations
        """

        from src.models import User, Device, db

        print("\n" + "=" * 80)
        print("🏗️  CREATING PERSISTENT TEST DATA FOR DEVELOPMENT")
        print("=" * 80)

        created_users = []
        created_devices = []

        # ============================================================
        # STEP 1: Create Test Users
        # ============================================================
        print("\n📋 STEP 1: Creating test users...")
        print("-" * 50)

        test_users_config = [
            {
                "username": "admin_user",
                "email": "admin@iotflow.dev",
                "is_admin": True,
                "description": "System administrator",
            },
            {
                "username": "demo_user",
                "email": "demo@iotflow.dev",
                "is_admin": False,
                "description": "Demo user for presentations",
            },
            {
                "username": "test_user_1",
                "email": "test1@iotflow.dev",
                "is_admin": False,
                "description": "Test user with temperature sensors",
            },
            {
                "username": "test_user_2",
                "email": "test2@iotflow.dev",
                "is_admin": False,
                "description": "Test user with environmental sensors",
            },
            {
                "username": "industrial_user",
                "email": "industrial@iotflow.dev",
                "is_admin": False,
                "description": "Industrial monitoring user",
            },
        ]

        with app.app_context():
            for user_config in test_users_config:
                # Check if user already exists
                existing_user = User.query.filter_by(username=user_config["username"]).first()
                if existing_user:
                    print(f"   ♻️  User '{user_config['username']}' already exists (ID: {existing_user.id})")
                    created_users.append(existing_user)
                    continue

                user = User(
                    username=user_config["username"],
                    email=user_config["email"],
                    password_hash="$2b$12$LQv3c1yqBWVHxkd0LHAkCOYz6TtxMQJqhN8/LewdBPj3bp.Gm.F5W",  # "password123"
                    is_active=True,
                    is_admin=user_config["is_admin"],
                )

                db.session.add(user)
                db.session.flush()  # Get ID without committing
                created_users.append(user)

                role = "Admin" if user.is_admin else "User"
                print(f"   ✅ Created {role}: {user.username} (ID: {user.id}) - {user_config['description']}")

            # Store user info before committing to avoid detached instance errors
            user_info = []
            for user in created_users:
                user_info.append({"id": user.id, "username": user.username, "is_admin": user.is_admin})

            db.session.commit()

        print(f"\n📊 Created {len(created_users)} users total")

        # ============================================================
        # STEP 2: Create Devices for Each User
        # ============================================================
        print("\n🔧 STEP 2: Creating devices for each user...")
        print("-" * 50)

        device_templates = {
            "admin_user": [
                {"name": "System Monitor", "type": "system_monitor", "location": "Server Room"},
                {"name": "Network Gateway", "type": "gateway", "location": "Network Closet"},
            ],
            "demo_user": [
                {"name": "Demo Temperature Sensor", "type": "temperature_sensor", "location": "Conference Room A"},
                {"name": "Demo Humidity Sensor", "type": "humidity_sensor", "location": "Conference Room A"},
                {"name": "Demo Air Quality Monitor", "type": "air_quality", "location": "Main Office"},
            ],
            "test_user_1": [
                {"name": "Kitchen Temperature", "type": "temperature_sensor", "location": "Kitchen"},
                {"name": "Living Room Thermostat", "type": "thermostat", "location": "Living Room"},
                {"name": "Bedroom Climate", "type": "climate_sensor", "location": "Master Bedroom"},
            ],
            "test_user_2": [
                {"name": "Garden Soil Sensor", "type": "soil_sensor", "location": "Garden"},
                {"name": "Weather Station", "type": "weather_station", "location": "Rooftop"},
                {"name": "Pool Monitor", "type": "water_sensor", "location": "Pool Area"},
                {"name": "Greenhouse Controller", "type": "greenhouse_controller", "location": "Greenhouse"},
            ],
            "industrial_user": [
                {"name": "Pressure Monitor 1", "type": "pressure_sensor", "location": "Production Line A"},
                {"name": "Pressure Monitor 2", "type": "pressure_sensor", "location": "Production Line B"},
                {"name": "Vibration Sensor", "type": "vibration_sensor", "location": "Motor Assembly"},
                {"name": "Flow Meter", "type": "flow_meter", "location": "Main Pipeline"},
                {"name": "Tank Level Sensor", "type": "level_sensor", "location": "Storage Tank 1"},
            ],
        }

        with app.app_context():
            # Get fresh user objects from database using stored info
            refreshed_users = []
            for info in user_info:
                refreshed_user = User.query.get(info["id"])
                refreshed_users.append(refreshed_user)

            for user in refreshed_users:
                user_devices = device_templates.get(user.username, [])

                print(f"\n   👤 Creating devices for {user.username}:")

                for device_config in user_devices:
                    # Check if device already exists
                    existing_device = Device.query.filter_by(name=device_config["name"], user_id=user.id).first()

                    if existing_device:
                        print(f"      ♻️  Device '{device_config['name']}' already exists")
                        created_devices.append(existing_device)
                        continue

                    # Create metadata based on device type
                    metadata = {
                        "manufacturer": "IoTFlow Systems",
                        "firmware_version": f"v{random.randint(1,3)}.{random.randint(0,9)}.{random.randint(0,9)}",
                        "installation_date": (datetime.now() - timedelta(days=random.randint(1, 365))).isoformat(),
                        "calibration_date": (datetime.now() - timedelta(days=random.randint(1, 90))).isoformat(),
                        "test_data": True,
                    }

                    # Add type-specific metadata
                    if "temperature" in device_config["type"]:
                        metadata.update({"sensor_range": "-40°C to 85°C", "accuracy": "±0.5°C", "resolution": "0.1°C"})
                    elif "pressure" in device_config["type"]:
                        metadata.update({"pressure_range": "0-1000 PSI", "accuracy": "±0.1%", "output": "4-20mA"})
                    elif "humidity" in device_config["type"]:
                        metadata.update({"humidity_range": "0-100% RH", "accuracy": "±2% RH"})

                    device = Device(
                        name=device_config["name"],
                        device_type=device_config["type"],
                        description=f"Test {device_config['type'].replace('_', ' ').title()} for development",
                        location=device_config["location"],
                        metadata=metadata,
                        user_id=user.id,
                        status="active",
                    )

                    db.session.add(device)
                    db.session.flush()
                    created_devices.append(device)

                    print(f"      ✅ {device.name} (ID: {device.id}) - {device.device_type}")

            # Store device info before committing to avoid detached instance errors
            device_info = []
            for device in created_devices:
                device_info.append(
                    {"id": device.id, "name": device.name, "device_type": device.device_type, "api_key": device.api_key}
                )

            db.session.commit()

        print(f"\n📊 Created {len(created_devices)} devices total")

        # ============================================================
        # STEP 3: Generate Historical Telemetry Data
        # ============================================================
        print("\n📈 STEP 3: Generating historical telemetry data...")
        print("-" * 50)

        # Check if IoTDB is available
        from src.config.iotdb_config import iotdb_config

        iotdb_available = iotdb_config.enabled and iotdb_config.is_connected()

        if iotdb_available:
            print("   🔗 IoTDB is available - generating real telemetry data")
        else:
            print("   ⚠️  IoTDB not available - telemetry will be processed but not stored")

        telemetry_count = 0

        # Use stored device info to avoid detached instance errors
        for device_data in device_info:
            print(f"\n   📡 Generating data for {device_data['name']}...")

            # Generate data for the last 7 days
            end_time = datetime.now(timezone.utc)
            start_time = end_time - timedelta(days=7)

            # Generate data points every 15 minutes
            current_time = start_time
            device_data_count = 0

            while current_time <= end_time:
                # Generate realistic data based on device type
                telemetry_data = {
                    "device_id": device_data["id"],
                    "api_key": device_data["api_key"],
                    "timestamp": current_time.isoformat(),
                }

                # Add sensor-specific data
                if "temperature" in device_data["device_type"]:
                    base_temp = 22.0  # Base temperature
                    daily_variation = 5.0 * math.sin((current_time.hour / 24.0) * 2 * 3.14159)
                    noise = random.uniform(-1.0, 1.0)
                    telemetry_data["temperature"] = round(base_temp + daily_variation + noise, 1)
                    telemetry_data["battery_level"] = max(20, 100 - random.randint(0, 5))

                elif "humidity" in device_data["device_type"]:
                    base_humidity = 45.0
                    variation = 15.0 * math.sin((current_time.hour / 24.0) * 2 * 3.14159)
                    noise = random.uniform(-3.0, 3.0)
                    telemetry_data["humidity"] = max(0, min(100, round(base_humidity + variation + noise, 1)))
                    telemetry_data["temperature"] = round(20.0 + random.uniform(-2, 5), 1)

                elif "pressure" in device_data["device_type"]:
                    base_pressure = 1013.25  # Standard atmospheric pressure
                    variation = random.uniform(-5.0, 5.0)
                    telemetry_data["pressure"] = round(base_pressure + variation, 2)
                    telemetry_data["temperature"] = round(25.0 + random.uniform(-3, 3), 1)

                elif "air_quality" in device_data["device_type"]:
                    telemetry_data["pm25"] = random.randint(5, 35)
                    telemetry_data["pm10"] = random.randint(10, 50)
                    telemetry_data["co2"] = random.randint(400, 800)
                    telemetry_data["voc"] = random.randint(0, 500)

                elif "soil" in device_data["device_type"]:
                    telemetry_data["soil_moisture"] = random.randint(30, 80)
                    telemetry_data["soil_temperature"] = round(15.0 + random.uniform(0, 10), 1)
                    telemetry_data["ph"] = round(6.0 + random.uniform(0, 2), 1)
                    telemetry_data["nutrients"] = random.randint(20, 100)

                elif "flow" in device_data["device_type"]:
                    telemetry_data["flow_rate"] = round(random.uniform(10.0, 50.0), 2)
                    telemetry_data["total_volume"] = round(random.uniform(1000, 5000), 1)
                    telemetry_data["pressure"] = round(random.uniform(20.0, 80.0), 1)

                elif "level" in device_data["device_type"]:
                    telemetry_data["level"] = round(random.uniform(10.0, 90.0), 1)
                    telemetry_data["volume"] = round(random.uniform(100, 1000), 1)
                    telemetry_data["temperature"] = round(random.uniform(15.0, 30.0), 1)

                else:
                    # Generic sensor data
                    telemetry_data["value"] = round(random.uniform(0, 100), 2)
                    telemetry_data["status"] = random.choice(["normal", "normal", "normal", "warning"])

                # Add common fields
                telemetry_data["signal_strength"] = random.randint(-80, -30)
                telemetry_data["battery_level"] = max(20, 100 - random.randint(0, 3))

                # Send telemetry data with proper structure for IoTDB
                payload = {
                    "device_id": device_data["id"],
                    "api_key": device_data["api_key"],
                    "data": telemetry_data,
                    "metadata": {
                        "device_type": device_data["device_type"],
                        "location": "test_location",
                        "test_data": True,
                        "batch_type": "historical",
                    },
                    "timestamp": current_time.isoformat(),
                }

                response = client.post(
                    "/api/v1/telemetry",
                    data=json.dumps(payload),
                    content_type="application/json",
                    headers={"X-API-Key": device_data["api_key"]},
                )

                if response.status_code in [200, 201]:
                    device_data_count += 1
                    telemetry_count += 1

                # Move to next time point (15 minutes later)
                current_time += timedelta(minutes=15)

                # Add some randomness - occasionally skip a reading
                if random.random() < 0.05:  # 5% chance to skip
                    current_time += timedelta(minutes=15)

            print(f"      ✅ Generated {device_data_count} data points")

        print(f"\n📊 Generated {telemetry_count} total telemetry records")

        # ============================================================
        # STEP 4: Generate Recent Real-time Data
        # ============================================================
        print("\n⚡ STEP 4: Generating recent real-time data...")
        print("-" * 50)

        recent_count = 0

        # Generate data for the last hour with higher frequency
        for device_data in device_info[:5]:  # Limit to first 5 devices for recent data
            print(f"   📡 Recent data for {device_data['name']}...")

            end_time = datetime.now(timezone.utc)
            start_time = end_time - timedelta(hours=1)
            current_time = start_time

            while current_time <= end_time:
                telemetry_data = {
                    "device_id": device_data["id"],
                    "api_key": device_data["api_key"],
                    "timestamp": current_time.isoformat(),
                }

                # Generate more dynamic recent data
                if "temperature" in device_data["device_type"]:
                    telemetry_data["temperature"] = round(22.0 + random.uniform(-2, 3), 1)
                    telemetry_data["humidity"] = round(45.0 + random.uniform(-5, 10), 1)
                elif "pressure" in device_data["device_type"]:
                    telemetry_data["pressure"] = round(1013.25 + random.uniform(-2, 2), 2)
                else:
                    telemetry_data["value"] = round(random.uniform(20, 80), 2)

                telemetry_data["battery_level"] = random.randint(85, 100)
                telemetry_data["signal_strength"] = random.randint(-60, -30)

                # Send recent telemetry data with proper structure for IoTDB
                payload = {
                    "device_id": device_data["id"],
                    "api_key": device_data["api_key"],
                    "data": telemetry_data,
                    "metadata": {
                        "device_type": device_data["device_type"],
                        "location": "test_location",
                        "test_data": True,
                        "batch_type": "recent",
                    },
                    "timestamp": current_time.isoformat(),
                }

                response = client.post(
                    "/api/v1/telemetry",
                    data=json.dumps(payload),
                    content_type="application/json",
                    headers={"X-API-Key": device_data["api_key"]},
                )

                if response.status_code in [200, 201]:
                    recent_count += 1

                # Every 2 minutes for recent data
                current_time += timedelta(minutes=2)

        print(f"   ✅ Generated {recent_count} recent data points")

        # ============================================================
        # STEP 5: Verification and Summary
        # ============================================================
        print("\n🔍 STEP 5: Verifying created data...")
        print("-" * 50)

        with app.app_context():
            total_users = User.query.count()
            total_devices = Device.query.count()
            active_devices = Device.query.filter_by(status="active").count()

            print(f"   📊 Database Summary:")
            print(f"      - Total Users: {total_users}")
            print(f"      - Total Devices: {total_devices}")
            print(f"      - Active Devices: {active_devices}")
            print(f"      - Total Telemetry Records: {telemetry_count + recent_count}")

            print(f"\n   👥 Created Users:")
            for user in created_users:
                user_device_count = Device.query.filter_by(user_id=user.id).count()
                role = "Admin" if user.is_admin else "User"
                print(f"      - {user.username} ({role}) - {user_device_count} devices")

            print(f"\n   🔧 Device Types Created:")
            device_types = {}
            for device in created_devices:
                device_types[device.device_type] = device_types.get(device.device_type, 0) + 1

            for device_type, count in sorted(device_types.items()):
                print(f"      - {device_type.replace('_', ' ').title()}: {count}")

        # ============================================================
        # FINAL SUMMARY
        # ============================================================
        print("\n" + "=" * 80)
        print("🎉 PERSISTENT TEST DATA CREATION COMPLETED!")
        print("=" * 80)

        print(f"\n📋 What was created:")
        print(f"   ✅ {len(created_users)} test users (including admin)")
        print(f"   ✅ {len(created_devices)} IoT devices across different types")
        print(f"   ✅ {telemetry_count + recent_count} telemetry data points")
        print(f"   ✅ 7 days of historical data + 1 hour of recent data")

        print(f"\n🔑 Login Credentials (password: 'password123'):")
        for user in created_users:
            role = "Admin" if user.is_admin else "User"
            print(f"   - {user.username} ({role}): {user.email}")

        print(f"\n💾 Data Persistence:")
        print(f"   - All data is saved in the PostgreSQL database")
        print(f"   - Telemetry data is stored in IoTDB (if available)")
        print(f"   - Data will persist between application restarts")
        print(f"   - Use this data for development, testing, and demos")

        if iotdb_available:
            print(f"\n📈 Telemetry Data:")
            print(f"   - Historical patterns with realistic variations")
            print(f"   - Different sensor types with appropriate data ranges")
            print(f"   - Recent real-time data for live monitoring")
        else:
            print(f"\n⚠️  Note: IoTDB not available - telemetry processed but not stored")

        print(f"\n🚀 Next Steps:")
        print(f"   - Use the IoTFlow Dashboard to visualize this data")
        print(f"   - Test API endpoints with the created devices")
        print(f"   - Develop new features using this realistic dataset")

        print("=" * 80 + "\n")

        # Verify everything was created successfully
        assert len(created_users) >= 5, "Should have created at least 5 users"
        assert len(created_devices) >= 15, "Should have created at least 15 devices"
        assert telemetry_count > 0, "Should have generated telemetry data"

        print("✅ All assertions passed - persistent test data created successfully!")


class TestPersistentDataQuery:
    """
    Test querying the persistent data that was created
    """

    def test_query_persistent_data(self, client, app):
        """
        Query and verify the persistent test data exists and is accessible
        """

        from src.models import User, Device, db

        print("\n" + "=" * 80)
        print("🔍 QUERYING PERSISTENT TEST DATA")
        print("=" * 80)

        with app.app_context():
            # Query users
            users = User.query.all()
            print(f"\n👥 Found {len(users)} users in database:")

            for user in users:
                device_count = Device.query.filter_by(user_id=user.id).count()
                role = "Admin" if user.is_admin else "User"
                print(f"   - {user.username} ({role}): {device_count} devices")

            # Query devices
            devices = Device.query.all()
            print(f"\n🔧 Found {len(devices)} devices in database:")

            device_types = {}
            for device in devices:
                device_types[device.device_type] = device_types.get(device.device_type, 0) + 1

            for device_type, count in sorted(device_types.items()):
                print(f"   - {device_type.replace('_', ' ').title()}: {count}")

            # Test API access with a device
            if devices:
                test_device = devices[0]
                print(f"\n📡 Testing telemetry API with device: {test_device.name}")

                # Query recent telemetry
                response = client.get(
                    f"/api/v1/telemetry/{test_device.id}?limit=5", headers={"X-API-Key": test_device.api_key}
                )

                if response.status_code == 200:
                    data = response.get_json()
                    records = data.get("data", [])
                    print(f"   ✅ Retrieved {len(records)} recent telemetry records")

                    if records:
                        latest = records[0]
                        print(f"   📊 Latest reading: {latest.get('timestamp', 'N/A')}")
                        for key, value in latest.items():
                            if key not in ["timestamp", "device_id"]:
                                print(f"      - {key}: {value}")
                else:
                    print(f"   ⚠️  API query failed: {response.status_code}")

        print("\n" + "=" * 80)
        print("✅ PERSISTENT DATA QUERY COMPLETED")
        print("=" * 80 + "\n")
