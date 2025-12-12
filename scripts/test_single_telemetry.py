#!/usr/bin/env python3
"""
Single Telemetry Test

Simple test to send telemetry data with one measurement using an existing API key.
Default API key: mZAziGMCmjDmfrOATJxGWqJX1vL4VgkR (from previous test)
"""

import requests
import json
import sys
from datetime import datetime, timezone


def test_send_single_telemetry(api_key="mZAziGMCmjDmfrOATJxGWqJX1vL4VgkR"):
    """Send telemetry data with a single measurement"""
    print("🚀 Single Telemetry Test")
    print("=" * 40)
    print(f"📊 Using API Key: {api_key[:20]}...")
    
    # Single measurement data
    telemetry_data = {
        "data": {
            "temperature": 22.5
        },
        "metadata": {
            "test_type": "single_measurement",
            "source": "test_single_telemetry.py"
        },
        "timestamp": datetime.now(timezone.utc).isoformat()
    }
    
    print(f"📊 Sending single measurement: temperature = {telemetry_data['data']['temperature']}°C")
    
    try:
        # Send telemetry to Flask API
        response = requests.post(
            "http://localhost:5000/api/v1/telemetry",
            json=telemetry_data,
            headers={
                "Content-Type": "application/json",
                "X-API-Key": api_key
            },
            timeout=10
        )
        
        print(f"📊 Response Status: {response.status_code}")
        
        if response.status_code == 201:
            response_data = response.json()
            print("✅ Telemetry sent successfully!")
            print(f"   Device ID: {response_data.get('device_id')}")
            print(f"   Device Name: {response_data.get('device_name')}")
            print(f"   Timestamp: {response_data.get('timestamp')}")
            return True, response_data
        else:
            print(f"❌ Telemetry failed: {response.status_code}")
            print(f"   Response: {response.text}")
            return False, None
            
    except Exception as e:
        print(f"❌ Request failed: {e}")
        return False, None


def test_verify_single_telemetry(api_key="mZAziGMCmjDmfrOATJxGWqJX1vL4VgkR", device_id=None):
    """Verify the single telemetry data was stored"""
    print(f"\n🔍 Verifying Single Telemetry Data")
    print("-" * 40)
    
    try:
        # Query telemetry via Flask API
        url = f"http://localhost:5000/api/v1/telemetry/{device_id}" if device_id else "http://localhost:5000/api/v1/telemetry"
        
        response = requests.get(
            url,
            headers={"X-API-Key": api_key},
            params={"limit": 1},
            timeout=10
        )
        
        print(f"📊 Query Response Status: {response.status_code}")
        
        if response.status_code == 200:
            telemetry_data = response.json()
            records = telemetry_data.get('data', [])
            
            print("✅ Telemetry query successful!")
            print(f"   Records found: {len(records)}")
            print(f"   IoTDB Available: {telemetry_data.get('iotdb_available')}")
            
            if records:
                latest = records[0]
                print(f"   Latest record timestamp: {latest.get('timestamp')}")
                print(f"   Temperature: {latest.get('temperature')}°C")
                
                # Check if our single measurement is there
                if latest.get('temperature') == 22.5:
                    print("✅ Single temperature measurement confirmed!")
                    return True
                else:
                    print(f"⚠️  Expected temperature 22.5°C, got {latest.get('temperature')}°C")
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
    """Run single telemetry test"""
    # Check if API key is provided as command line argument
    api_key = "mZAziGMCmjDmfrOATJxGWqJX1vL4VgkR"  # Default from previous test
    
    if len(sys.argv) > 1:
        api_key = sys.argv[1]
        print(f"📊 Using provided API key: {api_key[:20]}...")
    else:
        print(f"📊 Using default API key: {api_key[:20]}...")
    
    # Test 1: Send single telemetry
    success, response_data = test_send_single_telemetry(api_key)
    
    if not success:
        print("\n❌ Single telemetry test FAILED!")
        return 1
    
    # Test 2: Verify telemetry
    device_id = response_data.get('device_id') if response_data else None
    verification_success = test_verify_single_telemetry(api_key, device_id)
    
    # Summary
    print(f"\n📊 Single Telemetry Test Summary")
    print("=" * 40)
    print(f"   Send Telemetry: {'✅ PASS' if success else '❌ FAIL'}")
    print(f"   Verify Data: {'✅ PASS' if verification_success else '❌ FAIL'}")
    
    if success and verification_success:
        print("🎉 Single telemetry test PASSED!")
        print("✅ Single temperature measurement successfully stored and verified!")
        return 0
    else:
        print("⚠️  Single telemetry test had failures")
        return 1


if __name__ == "__main__":
    exit(main())