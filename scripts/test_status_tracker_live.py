#!/usr/bin/env python3
"""
Quick test to verify status_tracker is working in the live Flask app
"""
import requests
import json

# Test the device status endpoint
response = requests.get('http://localhost:5000/api/v1/devices/11/status')
data = response.json()

print("=" * 60)
print("Device Status Check")
print("=" * 60)
print(json.dumps(data, indent=2))
print()
print(f"Is Online: {data['device']['is_online']}")
print(f"Status Source: {data['device']['status_source']}")
print(f"Last Seen Source: {data['device']['last_seen_source']}")
print()

# Check if status_source is 'status_tracker' (what we want)
if data['device']['status_source'] == 'status_tracker':
    print("✅ SUCCESS! Using DeviceStatusTracker")
elif data['device']['status_source'] == 'database':
    print("⚠️  WARNING! Fallback to database (status_tracker not available)")
else:
    print(f"⚠️  UNEXPECTED: Using {data['device']['status_source']}")
print("=" * 60)
