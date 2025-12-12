#!/usr/bin/env python3
"""
Complete Flow Test: User → Device → API Key → Telemetry

This test creates everything through the Flask API:
1. Create user with password test123
2. Create device for that user  
3. Get API key from device
4. Send telemetry using that API key
"""

import requests
import json
import time
from datetime import datetime, timezone


def test_create_user():
    """Step 1: Create a new user directly in PostgreSQL"""
    print("🔍 Step 1: Creating New User in PostgreSQL")
    print("-" * 40)

    import psycopg2
    import sys
    import os

    # Add src to path to import password utilities
    sys.path.insert(0, os.path.join(os.path.dirname(__file__), "src"))
    from utils.password import hash_password
    import uuid

    timestamp = int(time.time())
    username = f"flask_test_user_{timestamp}"
    email = f"flask_test_user_{timestamp}@iotflow.test"
    password = "test123"
    user_id_uuid = uuid.uuid4().hex

    print(f"📊 Creating user: {username}")
    print(f"📊 Email: {email}")
    print(f"📊 Password: {password}")

    try:
        # Connect to PostgreSQL directly
        conn = psycopg2.connect(host="localhost", port=5432, database="iotflow", user="iotflow", password="iotflowpass")

        cursor = conn.cursor()

        # Create user with hashed password using PBKDF2-SHA256
        password_hash = hash_password(password)

        cursor.execute(
            """
            INSERT INTO users (user_id, username, email, password_hash, is_active, is_admin, created_at, updated_at)
            VALUES (%s, %s, %s, %s, %s, %s, %s, %s)
            RETURNING id
        """,
            (
                user_id_uuid,
                username,
                email,
                password_hash,
                True,
                False,
                datetime.now(timezone.utc),
                datetime.now(timezone.utc),
            ),
        )

        user_db_id = cursor.fetchone()[0]
        conn.commit()

        cursor.close()
        conn.close()

        print(f"✅ User created successfully!")
        print(f"   Database ID: {user_db_id}")
        print(f"   User ID: {user_id_uuid}")
        print(f"   Username: {username}")

        return user_id_uuid, user_db_id, username

    except Exception as e:
        print(f"❌ User creation failed: {e}")
        return None, None, None


def test_create_device(user_id_uuid):
    """Step 2: Create a new device for the user"""
    print(f"\n🔍 Step 2: Creating New Device for User {user_id_uuid}")
    print("-" * 40)

    timestamp = int(time.time())
    device_data = {
        "name": f"Flask Test Device {timestamp}",
        "description": "Device created for complete flow test",
        "device_type": "test_sensor",
        "location": "Flask Test Lab",
        "user_id": user_id_uuid,
    }

    print(f"📊 Creating device: {device_data['name']}")
    print(f"📊 Device type: {device_data['device_type']}")
    print(f"📊 User ID: {user_id_uuid}")

    try:
        response = requests.post(
            "http://localhost:5000/api/v1/devices/register",
            json=device_data,
            headers={"Content-Type": "application/json"},
            timeout=10,
        )

        print(f"📊 Device Registration Response: {response.status_code}")
        print(f"📊 Response: {response.text}")

        if response.status_code in [200, 201]:
            device_info = response.json()
            device_data = device_info.get("device", {})
            device_id = device_data.get("id")
            api_key = device_data.get("api_key")

            print("✅ Device created successfully!")
            print(f"   Device ID: {device_id}")
            print(f"   API Key: {api_key}")

            return device_id, api_key
        else:
            print("❌ Device creation failed")
            return None, None

    except Exception as e:
        print(f"❌ Device creation failed: {e}")
        return None, None


def test_verify_device(device_id, api_key):
    """Step 3: Verify device exists and API key works"""
    print(f"\n🔍 Step 3: Verifying Device {device_id}")
    print("-" * 40)

    try:
        # Check via admin endpoint
        response = requests.get(
            f"http://localhost:5000/api/v1/admin/devices/{device_id}",
            headers={"Authorization": "admin test"},
            timeout=10,
        )

        print(f"📊 Device Verification Response: {response.status_code}")

        if response.status_code == 200:
            device_info = response.json()
            device_data = device_info.get("device", {})

            print("✅ Device verified successfully!")
            print(f"   Name: {device_data.get('name')}")
            print(f"   Type: {device_data.get('device_type')}")
            print(f"   Status: {device_data.get('status')}")
            print(f"   User ID: {device_data.get('user_id')}")

            return True
        else:
            print(f"❌ Device verification failed: {response.text}")
            return False

    except Exception as e:
        print(f"❌ Device verification failed: {e}")
        return False


def test_send_telemetry(api_key, device_id):
    """Step 4: Send telemetry using the API key"""
    print(f"\n🔍 Step 4: Sending Telemetry with API Key")
    print("-" * 40)

    test_data = {
        "data": {
            "temperature": 25.8,
            "humidity": 62.1,
            "pressure": 1012.5,
            "complete_flow_test": True,
            "device_id": device_id,
        },
        "metadata": {"test_type": "complete_flow_test", "source": "test_complete_flow.py", "created_via": "flask_api"},
        "timestamp": datetime.now(timezone.utc).isoformat(),
    }

    print(f"📊 Using API Key: {api_key[:20]}...")
    print(f"📊 Test Data: {test_data['data']}")

    try:
        response = requests.post(
            "http://localhost:5000/api/v1/telemetry",
            json=test_data,
            headers={"Content-Type": "application/json", "X-API-Key": api_key},
            timeout=15,
        )

        print(f"📊 Telemetry Response: {response.status_code}")
        print(f"📊 Response: {response.text}")

        if response.status_code == 201:
            telemetry_response = response.json()
            print("✅ Telemetry sent successfully!")
            print(f"   Device ID: {telemetry_response.get('device_id')}")
            print(f"   Device Name: {telemetry_response.get('device_name')}")
            print(f"   Timestamp: {telemetry_response.get('timestamp')}")
            return True
        else:
            print(f"❌ Telemetry failed: {response.status_code}")
            return False

    except Exception as e:
        print(f"❌ Telemetry sending failed: {e}")
        return False


def test_verify_telemetry_in_iotdb(device_id, user_id, api_key):
    """Step 5: Verify telemetry was stored in IoTDB"""
    print(f"\n🔍 Step 5: Verifying Telemetry in IoTDB")
    print("-" * 40)

    try:
        # Query telemetry via Flask API using the device's API key
        response = requests.get(
            f"http://localhost:5000/api/v1/telemetry/{device_id}",
            headers={"X-API-Key": api_key},  # Use the device's API key
            params={"limit": 3},
            timeout=10,
        )

        print(f"📊 Telemetry Query Response: {response.status_code}")

        if response.status_code == 200:
            telemetry_data = response.json()
            records = telemetry_data.get("data", [])

            print("✅ Telemetry query successful!")
            print(f"   Records found: {len(records)}")
            print(f"   IoTDB Available: {telemetry_data.get('iotdb_available')}")

            if records:
                latest = records[0]
                print(f"   Latest record timestamp: {latest.get('timestamp')}")
                print(f"   Latest record data: {latest}")

                # Verify our test data is there
                if latest.get("complete_flow_test"):
                    print("✅ Our test data confirmed in IoTDB!")
                    return True
                else:
                    print("⚠️  Test data not found in latest record")
                    return False
            else:
                print("⚠️  No telemetry records found")
                return False
        else:
            print(f"❌ Telemetry query failed: {response.text}")
            return False

    except Exception as e:
        print(f"❌ Telemetry verification failed: {e}")
        return False


def main():
    """Run complete flow test"""
    print("🚀 Complete Flow Test: User → Device → API Key → Telemetry")
    print("=" * 60)

    # Step 1: Create user
    user_result = test_create_user()
    if not user_result or len(user_result) != 3:
        print("❌ Cannot continue without user")
        return 1

    user_id_uuid, user_db_id, username = user_result

    # Step 2: Create device
    device_id, api_key = test_create_device(user_id_uuid)
    if not device_id or not api_key:
        print("❌ Cannot continue without device and API key")
        return 1

    # Step 3: Verify device
    device_verified = test_verify_device(device_id, api_key)
    if not device_verified:
        print("❌ Device verification failed")
        return 1

    # Step 4: Send telemetry
    telemetry_sent = test_send_telemetry(api_key, device_id)
    if not telemetry_sent:
        print("❌ Telemetry sending failed")
        return 1

    # Step 5: Verify in IoTDB
    telemetry_verified = test_verify_telemetry_in_iotdb(device_id, user_db_id, api_key)

    # Summary
    print("\n" + "=" * 60)
    print("📊 Complete Flow Test Summary")
    print("=" * 60)

    results = [
        ("User Creation", user_id_uuid is not None),
        ("Device Creation", device_id is not None and api_key is not None),
        ("Device Verification", device_verified),
        ("Telemetry Sending", telemetry_sent),
        ("IoTDB Verification", telemetry_verified),
    ]

    passed = 0
    for test_name, result in results:
        status = "✅ PASS" if result else "❌ FAIL"
        print(f"   {status}: {test_name}")
        if result:
            passed += 1

    print(f"\n📈 Results: {passed}/{len(results)} tests passed")

    if passed == len(results):
        print("🎉 Complete flow test PASSED!")
        print("✅ User → Device → API Key → Telemetry → IoTDB flow working!")

        print(f"\n💾 Created Resources:")
        print(f"   👤 User ID: {user_id_uuid}")
        print(f"   🔧 Device ID: {device_id}")
        print(f"   🔑 API Key: {api_key}")
        print(f"   📊 Telemetry: Stored in IoTDB")

    else:
        print("⚠️  Complete flow test had failures")

    return 0 if passed == len(results) else 1


if __name__ == "__main__":
    exit(main())
