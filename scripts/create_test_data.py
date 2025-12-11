#!/usr/bin/env python3
"""
Standalone script to create persistent test data in the PostgreSQL database.
This script bypasses the test framework and directly creates data for development use.

Requirements:
- PostgreSQL database running (via docker-compose up postgres)
- Python dependencies installed (pip install -r requirements.txt)
- If you get psycopg2 errors, install: pip install psycopg2-binary
"""

import os
import sys
import json
import time
import random
from datetime import datetime, timezone, timedelta

# Add the src directory to the path
sys.path.insert(0, os.path.join(os.path.dirname(__file__), 'src'))

# Set environment to use PostgreSQL
os.environ['DATABASE_URL'] = 'postgresql://iotflow:iotflowpass@localhost:5432/iotflow'
os.environ['FLASK_ENV'] = 'development'

from app import create_app
from src.models import User, Device, db
from src.utils.password import hash_password
import requests


def create_persistent_test_data():
    """
    Creates comprehensive test data that persists in the PostgreSQL database.
    """
    
    print("=" * 80)
    print("🏗️  CREATING PERSISTENT TEST DATA FOR DEVELOPMENT")
    print("=" * 80)
    
    # Show password hashing info
    print(f"\n🔐 Password Security Configuration:")
    print(f"   - Using PBKDF2-SHA256 with 210,000 iterations")
    print(f"   - OWASP 2023 compliant password hashing")
    print(f"   - Default password for all test users: 'password123'")
    
    # Create Flask app
    app = create_app('development')
    
    created_users = []
    created_devices = []
    
    with app.app_context():
        # Ensure tables exist
        db.create_all()
        
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
                "description": "System administrator"
            },
            {
                "username": "demo_user",
                "email": "demo@iotflow.dev", 
                "is_admin": False,
                "description": "Demo user for presentations"
            },
            {
                "username": "test_user_1",
                "email": "test1@iotflow.dev",
                "is_admin": False,
                "description": "Test user with temperature sensors"
            },
            {
                "username": "test_user_2", 
                "email": "test2@iotflow.dev",
                "is_admin": False,
                "description": "Test user with environmental sensors"
            },
            {
                "username": "industrial_user",
                "email": "industrial@iotflow.dev",
                "is_admin": False,
                "description": "Industrial monitoring user"
            }
        ]
        
        for user_config in test_users_config:
            # Check if user already exists
            existing_user = User.query.filter_by(username=user_config["username"]).first()
            if existing_user:
                print(f"   ♻️  User '{user_config['username']}' already exists (ID: {existing_user.id})")
                created_users.append(existing_user)
                continue
            
            # Hash the password using the backend's password utility
            password_hash = hash_password("password123")
            
            user = User(
                username=user_config["username"],
                email=user_config["email"],
                password_hash=password_hash,
                is_active=True,
                is_admin=user_config["is_admin"]
            )
            
            db.session.add(user)
            db.session.flush()  # Get ID without committing
            created_users.append(user)
            
            role = "Admin" if user.is_admin else "User"
            print(f"   ✅ Created {role}: {user.username} (ID: {user.id}) - {user_config['description']}")
            print(f"      🔐 Password hash format: {password_hash[:30]}...")
        
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
                {"name": "Network Gateway", "type": "gateway", "location": "Network Closet"}
            ],
            "demo_user": [
                {"name": "Demo Temperature Sensor", "type": "temperature_sensor", "location": "Conference Room A"},
                {"name": "Demo Humidity Sensor", "type": "humidity_sensor", "location": "Conference Room A"},
                {"name": "Demo Air Quality Monitor", "type": "air_quality", "location": "Main Office"}
            ],
            "test_user_1": [
                {"name": "Kitchen Temperature", "type": "temperature_sensor", "location": "Kitchen"},
                {"name": "Living Room Thermostat", "type": "thermostat", "location": "Living Room"},
                {"name": "Bedroom Climate", "type": "climate_sensor", "location": "Master Bedroom"}
            ],
            "test_user_2": [
                {"name": "Garden Soil Sensor", "type": "soil_sensor", "location": "Garden"},
                {"name": "Weather Station", "type": "weather_station", "location": "Rooftop"},
                {"name": "Pool Monitor", "type": "water_sensor", "location": "Pool Area"},
                {"name": "Greenhouse Controller", "type": "greenhouse_controller", "location": "Greenhouse"}
            ],
            "industrial_user": [
                {"name": "Pressure Monitor 1", "type": "pressure_sensor", "location": "Production Line A"},
                {"name": "Pressure Monitor 2", "type": "pressure_sensor", "location": "Production Line B"},
                {"name": "Vibration Sensor", "type": "vibration_sensor", "location": "Motor Assembly"},
                {"name": "Flow Meter", "type": "flow_meter", "location": "Main Pipeline"},
                {"name": "Tank Level Sensor", "type": "level_sensor", "location": "Storage Tank 1"}
            ]
        }
        
        for user in created_users:
            user_devices = device_templates.get(user.username, [])
            
            print(f"\n   👤 Creating devices for {user.username}:")
            
            for device_config in user_devices:
                # Check if device already exists
                existing_device = Device.query.filter_by(
                    name=device_config["name"], 
                    user_id=user.id
                ).first()
                
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
                    "test_data": True
                }
                
                # Add type-specific metadata
                if "temperature" in device_config["type"]:
                    metadata.update({
                        "sensor_range": "-40°C to 85°C",
                        "accuracy": "±0.5°C",
                        "resolution": "0.1°C"
                    })
                elif "pressure" in device_config["type"]:
                    metadata.update({
                        "pressure_range": "0-1000 PSI",
                        "accuracy": "±0.1%",
                        "output": "4-20mA"
                    })
                elif "humidity" in device_config["type"]:
                    metadata.update({
                        "humidity_range": "0-100% RH",
                        "accuracy": "±2% RH"
                    })
                
                device = Device(
                    name=device_config["name"],
                    device_type=device_config["type"],
                    description=f"Test {device_config['type'].replace('_', ' ').title()} for development",
                    location=device_config["location"],
                    metadata=metadata,
                    user_id=user.id,
                    status="active"
                )
                
                db.session.add(device)
                db.session.flush()
                created_devices.append(device)
                
                print(f"      ✅ {device.name} (ID: {device.id}) - {device.device_type}")
        
        db.session.commit()
        print(f"\n📊 Created {len(created_devices)} devices total")
        
        # ============================================================
        # STEP 3: Generate Historical Telemetry Data via MQTT
        # ============================================================
        print("\n📈 STEP 3: Generating historical telemetry data via MQTT...")
        print("-" * 50)
        
        # Import MQTT client for direct telemetry sending
        import paho.mqtt.client as mqtt
        
        # Check if IoTDB is available
        from src.config.iotdb_config import iotdb_config
        iotdb_available = iotdb_config.enabled and iotdb_config.is_connected()
        
        if iotdb_available:
            print("   🔗 IoTDB is available - generating real telemetry data")
        else:
            print("   ⚠️  IoTDB not available - telemetry will be processed but not stored")
        
        # Setup MQTT client for sending telemetry
        mqtt_client = mqtt.Client()
        
        def on_connect(client, userdata, flags, rc):
            if rc == 0:
                print("   📡 Connected to MQTT broker for telemetry sending")
            else:
                print(f"   ❌ Failed to connect to MQTT broker: {rc}")
        
        mqtt_client.on_connect = on_connect
        
        try:
            mqtt_client.connect("localhost", 1883, 60)
            mqtt_client.loop_start()
            time.sleep(1)  # Wait for connection
            
            telemetry_count = 0
            
            # Generate historical data for all devices
            for device in created_devices:
                print(f"   📡 Generating historical data for {device.name}...")
                
                # Generate data for the last 24 hours
                end_time = datetime.now(timezone.utc)
                start_time = end_time - timedelta(hours=24)
                
                # Generate data points every 30 minutes
                current_time = start_time
                device_data_count = 0
                
                while current_time <= end_time:
                    # Generate realistic data based on device type
                    telemetry_data = {
                        "device_id": device.id,
                        "timestamp": current_time.isoformat()
                    }
                    
                    # Add sensor-specific data with realistic patterns
                    if "temperature" in device.device_type:
                        # Daily temperature variation
                        base_temp = 22.0
                        daily_variation = 8.0 * random.sin((current_time.hour / 24.0) * 2 * 3.14159)
                        noise = random.uniform(-2.0, 2.0)
                        telemetry_data["temperature"] = round(base_temp + daily_variation + noise, 1)
                        telemetry_data["humidity"] = round(45.0 + random.uniform(-10, 15), 1)
                        telemetry_data["battery_level"] = max(20, 100 - random.randint(0, 3))
                    
                    elif "humidity" in device.device_type:
                        base_humidity = 50.0
                        variation = 20.0 * random.sin((current_time.hour / 24.0) * 2 * 3.14159)
                        noise = random.uniform(-5.0, 5.0)
                        telemetry_data["humidity"] = max(0, min(100, round(base_humidity + variation + noise, 1)))
                        telemetry_data["temperature"] = round(20.0 + random.uniform(-2, 5), 1)
                        telemetry_data["battery_level"] = max(20, 100 - random.randint(0, 2))
                    
                    elif "pressure" in device.device_type:
                        base_pressure = 1013.25
                        variation = random.uniform(-8.0, 8.0)
                        telemetry_data["pressure"] = round(base_pressure + variation, 2)
                        telemetry_data["temperature"] = round(25.0 + random.uniform(-3, 3), 1)
                        telemetry_data["status"] = random.choice(["normal", "normal", "normal", "warning"])
                    
                    elif "air_quality" in device.device_type:
                        # Air quality varies by time of day (worse during rush hours)
                        rush_hour_factor = 1.5 if current_time.hour in [7, 8, 17, 18, 19] else 1.0
                        telemetry_data["pm25"] = int(random.randint(5, 25) * rush_hour_factor)
                        telemetry_data["pm10"] = int(random.randint(10, 40) * rush_hour_factor)
                        telemetry_data["co2"] = random.randint(400, 800)
                        telemetry_data["voc"] = random.randint(0, 500)
                        telemetry_data["aqi"] = min(500, int((telemetry_data["pm25"] * 2) + random.randint(0, 50)))
                    
                    elif "soil" in device.device_type:
                        telemetry_data["soil_moisture"] = random.randint(30, 80)
                        telemetry_data["soil_temperature"] = round(15.0 + random.uniform(0, 10), 1)
                        telemetry_data["ph"] = round(6.0 + random.uniform(0, 2), 1)
                        telemetry_data["nutrients"] = random.randint(20, 100)
                        telemetry_data["conductivity"] = round(random.uniform(0.5, 2.0), 2)
                    
                    elif "flow" in device.device_type:
                        base_flow = 25.0
                        variation = random.uniform(-10.0, 15.0)
                        telemetry_data["flow_rate"] = max(0, round(base_flow + variation, 2))
                        telemetry_data["total_volume"] = round(random.uniform(1000, 5000), 1)
                        telemetry_data["pressure"] = round(random.uniform(20.0, 80.0), 1)
                    
                    elif "level" in device.device_type:
                        telemetry_data["level"] = round(random.uniform(10.0, 90.0), 1)
                        telemetry_data["volume"] = round(random.uniform(100, 1000), 1)
                        telemetry_data["temperature"] = round(random.uniform(15.0, 30.0), 1)
                    
                    elif "weather" in device.device_type:
                        # Weather station data
                        telemetry_data["temperature"] = round(20.0 + random.uniform(-5, 10), 1)
                        telemetry_data["humidity"] = round(50.0 + random.uniform(-20, 30), 1)
                        telemetry_data["pressure"] = round(1013.25 + random.uniform(-10, 10), 2)
                        telemetry_data["wind_speed"] = round(random.uniform(0, 25), 1)
                        telemetry_data["wind_direction"] = random.randint(0, 360)
                        telemetry_data["rainfall"] = round(random.uniform(0, 5), 1) if random.random() < 0.3 else 0
                    
                    elif "vibration" in device.device_type:
                        # Industrial vibration sensor
                        base_vibration = 2.0
                        variation = random.uniform(-1.0, 3.0)
                        telemetry_data["vibration_x"] = round(base_vibration + variation, 2)
                        telemetry_data["vibration_y"] = round(base_vibration + random.uniform(-1.0, 3.0), 2)
                        telemetry_data["vibration_z"] = round(base_vibration + random.uniform(-1.0, 3.0), 2)
                        telemetry_data["frequency"] = round(random.uniform(50, 200), 1)
                        telemetry_data["amplitude"] = round(random.uniform(0.1, 5.0), 2)
                    
                    elif "greenhouse" in device.device_type:
                        # Greenhouse controller
                        telemetry_data["temperature"] = round(25.0 + random.uniform(-3, 5), 1)
                        telemetry_data["humidity"] = round(70.0 + random.uniform(-15, 15), 1)
                        telemetry_data["co2"] = random.randint(800, 1200)
                        telemetry_data["light_intensity"] = random.randint(200, 800)
                        telemetry_data["soil_moisture"] = random.randint(60, 90)
                    
                    else:
                        # Generic sensor data
                        telemetry_data["value"] = round(random.uniform(0, 100), 2)
                        telemetry_data["status"] = random.choice(["normal", "normal", "normal", "warning"])
                        telemetry_data["battery_level"] = max(20, 100 - random.randint(0, 5))
                    
                    # Add common fields
                    telemetry_data["signal_strength"] = random.randint(-80, -30)
                    if "battery_level" not in telemetry_data:
                        telemetry_data["battery_level"] = max(20, 100 - random.randint(0, 3))
                    
                    # Send via MQTT to the telemetry topic
                    topic = f"iotflow/devices/{device.id}/telemetry"
                    payload = json.dumps(telemetry_data)
                    
                    result = mqtt_client.publish(topic, payload, qos=1)
                    if result.rc == 0:
                        device_data_count += 1
                        telemetry_count += 1
                    
                    # Move to next time point (30 minutes later)
                    current_time += timedelta(minutes=30)
                    
                    # Add some randomness - occasionally skip a reading
                    if random.random() < 0.05:  # 5% chance to skip
                        current_time += timedelta(minutes=30)
                
                print(f"      ✅ Generated {device_data_count} historical data points")
            
            # Generate recent real-time data (last 2 hours with higher frequency)
            print(f"\n   ⚡ Generating recent real-time data...")
            recent_count = 0
            
            for device in created_devices:
                end_time = datetime.now(timezone.utc)
                start_time = end_time - timedelta(hours=2)
                current_time = start_time
                
                while current_time <= end_time:
                    telemetry_data = {
                        "device_id": device.id,
                        "timestamp": current_time.isoformat()
                    }
                    
                    # Generate more dynamic recent data
                    if "temperature" in device.device_type:
                        telemetry_data["temperature"] = round(22.0 + random.uniform(-3, 4), 1)
                        telemetry_data["humidity"] = round(45.0 + random.uniform(-8, 12), 1)
                        telemetry_data["battery_level"] = random.randint(85, 100)
                    elif "pressure" in device.device_type:
                        telemetry_data["pressure"] = round(1013.25 + random.uniform(-3, 3), 2)
                        telemetry_data["temperature"] = round(25.0 + random.uniform(-2, 2), 1)
                    elif "air_quality" in device.device_type:
                        telemetry_data["pm25"] = random.randint(8, 30)
                        telemetry_data["pm10"] = random.randint(15, 45)
                        telemetry_data["co2"] = random.randint(450, 750)
                    else:
                        telemetry_data["value"] = round(random.uniform(30, 70), 2)
                        telemetry_data["status"] = "normal"
                    
                    telemetry_data["signal_strength"] = random.randint(-60, -30)
                    if "battery_level" not in telemetry_data:
                        telemetry_data["battery_level"] = random.randint(90, 100)
                    
                    # Send via MQTT
                    topic = f"iotflow/devices/{device.id}/telemetry"
                    payload = json.dumps(telemetry_data)
                    
                    result = mqtt_client.publish(topic, payload, qos=1)
                    if result.rc == 0:
                        recent_count += 1
                        telemetry_count += 1
                    
                    # Every 5 minutes for recent data
                    current_time += timedelta(minutes=5)
            
            print(f"   ✅ Generated {recent_count} recent real-time data points")
            print(f"\n📊 Generated {telemetry_count} total telemetry records via MQTT")
            
            # Wait a moment for messages to be sent
            time.sleep(2)
            
        except Exception as e:
            print(f"   ❌ Error sending telemetry via MQTT: {e}")
            telemetry_count = 0
        
        finally:
            mqtt_client.loop_stop()
            mqtt_client.disconnect()
        
        # ============================================================
        # STEP 4: Verification and Summary
        # ============================================================
        print("\n🔍 STEP 4: Verifying created data...")
        print("-" * 50)
        
        total_users = User.query.count()
        total_devices = Device.query.count()
        active_devices = Device.query.filter_by(status="active").count()
        
        print(f"   📊 Database Summary:")
        print(f"      - Total Users: {total_users}")
        print(f"      - Total Devices: {total_devices}")
        print(f"      - Active Devices: {active_devices}")
        print(f"      - Sample Telemetry Records: {telemetry_count}")
        
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
    print(f"   ✅ {telemetry_count} sample telemetry data points")
    
    print(f"\n🔑 Login Credentials (password: 'password123'):")
    for user in created_users:
        role = "Admin" if user.is_admin else "User"
        print(f"   - {user.username} ({role}): {user.email}")
    
    print(f"\n� Paassword Security:")
    print(f"   - Passwords hashed using PBKDF2-SHA256 with 210,000 iterations")
    print(f"   - Follows OWASP 2023 recommendations for password storage")
    print(f"   - Each password uses a unique 256-bit salt")
    
    print(f"\n💾 Data Persistence:")
    print(f"   - All data is saved in the PostgreSQL database")
    print(f"   - Telemetry data is stored via the API (IoTDB if available)")
    print(f"   - Data will persist between application restarts")
    print(f"   - Use this data for development, testing, and demos")
    
    print(f"\n🚀 Next Steps:")
    print(f"   - Use the IoTFlow Dashboard to visualize this data")
    print(f"   - Test API endpoints with the created devices")
    print(f"   - Develop new features using this realistic dataset")
    
    print("=" * 80 + "\n")
    
    return len(created_users), len(created_devices), telemetry_count


if __name__ == "__main__":
    try:
        users, devices, telemetry = create_persistent_test_data()
        print(f"✅ Successfully created {users} users, {devices} devices, and {telemetry} telemetry records!")
        sys.exit(0)
    except Exception as e:
        print(f"❌ Error creating test data: {e}")
        import traceback
        traceback.print_exc()
        sys.exit(1)