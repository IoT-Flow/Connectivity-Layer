# Demo Quick Start

## 🚀 Run the Complete Demo in 2 Steps

### Step 1: Start the Server
```bash
python app.py
```

### Step 2: Run the Demo
```bash
# Python version (recommended)
python demo_complete_workflow.py

# OR Bash version (faster)
./demo_workflow.sh
```

## 📊 What Gets Created

- ✅ **1 User** - Registered and logged in
- ✅ **2 Devices** - Living Room & Bedroom sensors
- ✅ **20 Telemetry Readings** - 10 per device (temperature, humidity, pressure, battery)
- ✅ **2 Charts** - Temperature comparison & Multi-sensor dashboard
- ✅ **Different Colors** - Red, Blue, Yellow for different measurements

## 🎨 Charts Created

### Chart 1: Temperature Comparison
- Both devices
- Temperature only
- **Red color** (#FF6384)

### Chart 2: Living Room Dashboard
- Living Room device only
- Temperature, Humidity, Pressure
- **Red, Blue, Yellow** colors

## ✅ Expected Output

```
============================================================
  STEP 1: User Registration
============================================================
✅ User registered successfully!
ℹ️  User ID: fd596e05a9374eeabbaf2779686b9f1b

============================================================
  STEP 2: User Login
============================================================
✅ Login successful!

============================================================
  STEP 3: Device Registration
============================================================
✅ Device registered: Living Room Sensor
✅ Device registered: Bedroom Sensor

============================================================
  STEP 4: Submit Telemetry Data
============================================================
✅ All 10 readings submitted successfully!
✅ All 10 readings submitted successfully!

============================================================
  STEP 5: Create Custom Charts
============================================================
✅ Chart created: Temperature Comparison
✅ Chart created: Living Room Dashboard

============================================================
  STEP 6: Retrieve Chart Data
============================================================
✅ Chart data retrieved successfully!

============================================================
  DEMO SUMMARY
============================================================
📊 Demo Completed Successfully!
```

## 🔍 Verify Results

### Check Swagger UI
http://localhost:5000/docs

### Query Chart Data
```bash
# Get all charts
curl "http://localhost:5000/api/v1/charts" | python -m json.tool

# Get chart data (use chart ID from demo output)
curl "http://localhost:5000/api/v1/charts/{chart_id}/data" | python -m json.tool
```

## 📝 Next Steps

1. ✅ Demo completed - All APIs working
2. 🚀 Build frontend dashboard
3. 🎨 Integrate chart visualization
4. 📊 Display real-time data

---

**For detailed information, see:** `DEMO_GUIDE.md`
