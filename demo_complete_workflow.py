#!/usr/bin/env python3
"""
Complete IoT Dashboard Demo Script
===================================

This script demonstrates the complete workflow:
1. User registration
2. User login
3. Device registration (2 devices)
4. Submit telemetry data (10 readings per device)
5. Create 2 custom charts with different colors
6. Retrieve and display chart data

Usage:
    python demo_complete_workflow.py
"""

import requests
import json
import time
from datetime import datetime, timedelta
import random

# Configuration
BASE_URL = "http://localhost:5000"
API_BASE = f"{BASE_URL}/api/v1"

# Colors for charts
COLORS = {
    'temperature': '#FF6384',  # Red
    'humidity': '#36A2EB',     # Blue
    'pressure': '#FFCE56',     # Yellow
    'battery': '#4BC0C0',      # Teal
}

class IoTDashboardDemo:
    def __init__(self):
        self.user_data = None
        self.auth_token = None
        self.devices = []
        self.charts = []
        
    def print_section(self, title):
        """Print a section header"""
        print("\n" + "="*60)
        print(f"  {title}")
        print("="*60)
    
    def print_success(self, message):
        """Print success message"""
        print(f"✅ {message}")
    
    def print_info(self, message):
        """Print info message"""
        print(f"ℹ️  {message}")
    
    def print_error(self, message):
        """Print error message"""
        print(f"❌ {message}")
    
    def step_1_register_user(self):
        """Step 1: Register a new user"""
        self.print_section("STEP 1: User Registration")
        
        user_data = {
            "username": f"demo_user_{int(time.time())}",
            "email": f"demo_{int(time.time())}@example.com",
            "password": "SecurePassword123!"
        }
        
        self.print_info(f"Registering user: {user_data['username']}")
        
        response = requests.post(
            f"{API_BASE}/auth/register",
            json=user_data
        )
        
        if response.status_code == 201:
            result = response.json()
            self.user_data = {
                'username': user_data['username'],
                'email': user_data['email'],
                'password': user_data['password'],
                'user_id': result.get('user', {}).get('user_id')
            }
            self.print_success(f"User registered successfully!")
            self.print_info(f"User ID: {self.user_data['user_id']}")
            return True
        else:
            self.print_error(f"Registration failed: {response.text}")
            return False
    
    def step_2_login_user(self):
        """Step 2: Login user"""
        self.print_section("STEP 2: User Login")
        
        self.print_info(f"Logging in as: {self.user_data['username']}")
        
        response = requests.post(
            f"{API_BASE}/auth/login",
            json={
                "username": self.user_data['username'],
                "password": self.user_data['password']
            }
        )
        
        if response.status_code == 200:
            result = response.json()
            self.auth_token = result.get('token')
            self.print_success("Login successful!")
            self.print_info(f"Auth token: {self.auth_token[:20]}...")
            return True
        else:
            self.print_error(f"Login failed: {response.text}")
            return False
    
    def step_3_register_devices(self):
        """Step 3: Register IoT devices"""
        self.print_section("STEP 3: Device Registration")
        
        devices_to_register = [
            {
                "name": "Living Room Sensor",
                "description": "Temperature and humidity sensor in living room",
                "device_type": "sensor",
                "location": "Living Room",
                "firmware_version": "1.0.0",
                "hardware_version": "v2.1"
            },
            {
                "name": "Bedroom Sensor",
                "description": "Environmental sensor in bedroom",
                "device_type": "sensor",
                "location": "Bedroom",
                "firmware_version": "1.0.0",
                "hardware_version": "v2.1"
            }
        ]
        
        for device_data in devices_to_register:
            self.print_info(f"Registering device: {device_data['name']}")
            
            response = requests.post(
                f"{API_BASE}/devices/register",
                json=device_data
            )
            
            if response.status_code == 201:
                result = response.json()
                device = result.get('device', {})
                self.devices.append({
                    'id': device.get('id'),
                    'name': device.get('name'),
                    'api_key': device.get('api_key'),
                    'location': device_data['location']
                })
                self.print_success(f"Device registered: {device.get('name')}")
                self.print_info(f"  Device ID: {device.get('id')}")
                self.print_info(f"  API Key: {device.get('api_key')[:20]}...")
            else:
                self.print_error(f"Device registration failed: {response.text}")
        
        return len(self.devices) > 0
    
    def step_4_submit_telemetry(self):
        """Step 4: Submit telemetry data"""
        self.print_section("STEP 4: Submit Telemetry Data")
        
        # Generate 10 telemetry readings for each device
        for device in self.devices:
            self.print_info(f"\nSubmitting telemetry for: {device['name']}")
            
            base_temp = 20 if device['location'] == 'Living Room' else 18
            base_humidity = 45 if device['location'] == 'Living Room' else 50
            
            for i in range(10):
                # Generate realistic sensor data
                telemetry_data = {
                    "data": {
                        "temperature": round(base_temp + random.uniform(-2, 3), 2),
                        "humidity": round(base_humidity + random.uniform(-5, 5), 2),
                        "pressure": round(1013 + random.uniform(-10, 10), 2),
                        "battery": round(100 - (i * 2), 2)
                    },
                    "timestamp": (datetime.now() - timedelta(minutes=10-i)).isoformat()
                }
                
                response = requests.post(
                    f"{API_BASE}/telemetry",
                    headers={"X-API-Key": device['api_key']},
                    json=telemetry_data
                )
                
                if response.status_code == 201:
                    if i == 0:
                        self.print_success(f"Telemetry data submitted (reading {i+1}/10)")
                    elif i == 9:
                        self.print_success(f"All 10 readings submitted successfully!")
                else:
                    self.print_error(f"Failed to submit reading {i+1}: {response.text}")
                
                # Small delay to simulate real-time data
                time.sleep(0.1)
        
        return True
    
    def step_5_create_charts(self):
        """Step 5: Create custom charts"""
        self.print_section("STEP 5: Create Custom Charts")
        
        # Chart 1: Temperature comparison (both devices)
        self.print_info("\nCreating Chart 1: Temperature Comparison")
        
        chart1_data = {
            "name": "Temperature Comparison",
            "title": "Living Room vs Bedroom Temperature",
            "description": "Compare temperature readings from both sensors",
            "type": "line",
            "user_id": self.user_data['user_id'],
            "time_range": "1h",
            "refresh_interval": 30
        }
        
        response = requests.post(
            f"{API_BASE}/charts",
            json=chart1_data
        )
        
        if response.status_code == 201:
            chart1 = response.json()['chart']
            self.charts.append(chart1)
            self.print_success(f"Chart created: {chart1['name']}")
            self.print_info(f"  Chart ID: {chart1['id']}")
            
            # Add both devices to chart 1
            for device in self.devices:
                response = requests.post(
                    f"{API_BASE}/charts/{chart1['id']}/devices",
                    json={"device_id": device['id']}
                )
                if response.status_code == 201:
                    self.print_success(f"  Added device: {device['name']}")
            
            # Add temperature measurement with red color
            response = requests.post(
                f"{API_BASE}/charts/{chart1['id']}/measurements",
                json={
                    "measurement_name": "temperature",
                    "display_name": "Temperature (°C)",
                    "color": COLORS['temperature']
                }
            )
            if response.status_code == 201:
                self.print_success(f"  Added measurement: Temperature (Red)")
        
        # Chart 2: Multi-sensor dashboard (Living Room only)
        self.print_info("\nCreating Chart 2: Living Room Multi-Sensor Dashboard")
        
        chart2_data = {
            "name": "Living Room Dashboard",
            "title": "Living Room Environmental Monitoring",
            "description": "Temperature, Humidity, and Pressure in Living Room",
            "type": "line",
            "user_id": self.user_data['user_id'],
            "time_range": "1h",
            "refresh_interval": 30
        }
        
        response = requests.post(
            f"{API_BASE}/charts",
            json=chart2_data
        )
        
        if response.status_code == 201:
            chart2 = response.json()['chart']
            self.charts.append(chart2)
            self.print_success(f"Chart created: {chart2['name']}")
            self.print_info(f"  Chart ID: {chart2['id']}")
            
            # Add only Living Room device
            living_room_device = next(d for d in self.devices if d['location'] == 'Living Room')
            response = requests.post(
                f"{API_BASE}/charts/{chart2['id']}/devices",
                json={"device_id": living_room_device['id']}
            )
            if response.status_code == 201:
                self.print_success(f"  Added device: {living_room_device['name']}")
            
            # Add multiple measurements with different colors
            measurements = [
                {
                    "measurement_name": "temperature",
                    "display_name": "Temperature (°C)",
                    "color": COLORS['temperature']
                },
                {
                    "measurement_name": "humidity",
                    "display_name": "Humidity (%)",
                    "color": COLORS['humidity']
                },
                {
                    "measurement_name": "pressure",
                    "display_name": "Pressure (hPa)",
                    "color": COLORS['pressure']
                }
            ]
            
            for measurement in measurements:
                response = requests.post(
                    f"{API_BASE}/charts/{chart2['id']}/measurements",
                    json=measurement
                )
                if response.status_code == 201:
                    self.print_success(f"  Added measurement: {measurement['display_name']}")
        
        return len(self.charts) > 0
    
    def step_6_retrieve_chart_data(self):
        """Step 6: Retrieve and display chart data"""
        self.print_section("STEP 6: Retrieve Chart Data")
        
        for chart in self.charts:
            self.print_info(f"\nRetrieving data for: {chart['name']}")
            
            response = requests.get(
                f"{API_BASE}/charts/{chart['id']}/data"
            )
            
            if response.status_code == 200:
                data = response.json()
                self.print_success(f"Chart data retrieved successfully!")
                self.print_info(f"  Chart Type: {data['chart_type']}")
                self.print_info(f"  Data Points: {data['count']}")
                self.print_info(f"  Series Count: {len(data['series'])}")
                
                # Display series information
                for series in data['series']:
                    self.print_info(f"    - {series['name']} (Color: {series['color']}) - {len(series['data'])} points")
                
                # Show sample data points
                if data['data']:
                    self.print_info(f"\n  Sample Data Points:")
                    for i, point in enumerate(data['data'][:3]):
                        self.print_info(f"    {i+1}. {point['measurement_name']}: {point['value']} at {point['timestamp']}")
            else:
                self.print_error(f"Failed to retrieve chart data: {response.text}")
    
    def step_7_display_summary(self):
        """Step 7: Display summary"""
        self.print_section("DEMO SUMMARY")
        
        print("\n📊 Demo Completed Successfully!\n")
        
        print("User Information:")
        print(f"  Username: {self.user_data['username']}")
        print(f"  Email: {self.user_data['email']}")
        print(f"  User ID: {self.user_data['user_id']}")
        
        print(f"\nDevices Registered: {len(self.devices)}")
        for device in self.devices:
            print(f"  - {device['name']} (ID: {device['id']})")
        
        print(f"\nTelemetry Data:")
        print(f"  Total Readings: {len(self.devices) * 10} (10 per device)")
        
        print(f"\nCharts Created: {len(self.charts)}")
        for chart in self.charts:
            print(f"  - {chart['name']} (ID: {chart['id']})")
        
        print("\n🌐 Access Points:")
        print(f"  API Base: {API_BASE}")
        print(f"  Swagger UI: {BASE_URL}/docs")
        print(f"  Health Check: {BASE_URL}/health")
        
        print("\n📝 Next Steps:")
        print("  1. Open Swagger UI to explore all endpoints")
        print("  2. Use the chart IDs to retrieve data")
        print("  3. Build the frontend dashboard")
        print("  4. Integrate with these APIs")
        
        print("\n" + "="*60)
    
    def run(self):
        """Run the complete demo"""
        print("\n" + "="*60)
        print("  IoT Dashboard Complete Workflow Demo")
        print("="*60)
        print("\nThis demo will:")
        print("  1. Register a new user")
        print("  2. Login the user")
        print("  3. Register 2 IoT devices")
        print("  4. Submit 10 telemetry readings per device")
        print("  5. Create 2 custom charts with different colors")
        print("  6. Retrieve and display chart data")
        print("\n" + "="*60)
        
        input("\nPress Enter to start the demo...")
        
        try:
            # Execute all steps
            if not self.step_1_register_user():
                return
            
            time.sleep(1)
            
            if not self.step_2_login_user():
                return
            
            time.sleep(1)
            
            if not self.step_3_register_devices():
                return
            
            time.sleep(1)
            
            if not self.step_4_submit_telemetry():
                return
            
            time.sleep(1)
            
            if not self.step_5_create_charts():
                return
            
            time.sleep(1)
            
            self.step_6_retrieve_chart_data()
            
            time.sleep(1)
            
            self.step_7_display_summary()
            
        except requests.exceptions.ConnectionError:
            self.print_error("\nCannot connect to the API server!")
            self.print_info("Please make sure the Flask application is running:")
            self.print_info("  python app.py")
            self.print_info(f"\nExpected server: {BASE_URL}")
        except Exception as e:
            self.print_error(f"\nAn error occurred: {str(e)}")
            import traceback
            traceback.print_exc()


if __name__ == "__main__":
    demo = IoTDashboardDemo()
    demo.run()
