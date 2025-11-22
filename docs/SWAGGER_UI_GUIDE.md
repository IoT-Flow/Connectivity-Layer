# Swagger UI Quick Start Guide

## 🚀 Getting Started

### Open Swagger UI
1. Start your server: `poetry run python app.py`
2. Open browser: http://localhost:5000/docs
3. You'll see the interactive API documentation

## 📋 Interface Overview

```
┌─────────────────────────────────────────────────────────┐
│  IoTFlow Connectivity Layer API                         │
│  [Authorize] button (top right)                         │
├─────────────────────────────────────────────────────────┤
│                                                          │
│  ▼ Health                                               │
│     GET  /health          Health check                  │
│     GET  /status          System status                 │
│                                                          │
│  ▼ Authentication                                       │
│     POST /api/v1/auth/register    Register user         │
│     POST /api/v1/auth/login       User login            │
│                                                          │
│  ▼ Devices                                              │
│     POST /api/v1/devices/register  Register device      │
│     GET  /api/v1/devices          List devices          │
│     ...                                                  │
└─────────────────────────────────────────────────────────┘
```

## 🎯 Step-by-Step Tutorial

### Example 1: Test Health Check (No Auth Required)

**Step 1:** Find the endpoint
- Scroll to "Health" section
- Click on `GET /health`

**Step 2:** Try it out
- Click the blue **"Try it out"** button
- You'll see the parameters section become editable

**Step 3:** Set parameters
- Check the box for `detailed` parameter
- Set it to `true`

**Step 4:** Execute
- Click the blue **"Execute"** button
- Wait for response (usually instant)

**Step 5:** View results
```json
{
  "status": "healthy",
  "checks": {
    "database": {
      "healthy": true,
      "response_time_ms": 3.34,
      "status": "connected"
    }
  },
  "metrics": { ... }
}
```

**Step 6:** Copy cURL command (optional)
- Scroll down to see the cURL command
- Click "Copy" to use it in terminal

---

### Example 2: Register a User (No Auth Required)

**Step 1:** Find endpoint
- Scroll to "Authentication" section
- Click on `POST /api/v1/auth/register`

**Step 2:** Try it out
- Click **"Try it out"**

**Step 3:** Fill in the request body
You'll see a JSON editor. Replace the example with:
```json
{
  "username": "john_doe",
  "email": "john@example.com",
  "password": "secure_password123"
}
```

**Step 4:** Execute
- Click **"Execute"**

**Step 5:** View response
```json
{
  "status": "success",
  "message": "User registered successfully",
  "user": {
    "user_id": "fd596e05-a937-4eea-bbaf-2779686b9f1b",
    "username": "john_doe",
    "email": "john@example.com"
  }
}
```

**Step 6:** Save the user_id
- Copy the `user_id` value
- You'll need it for registering devices

---

### Example 3: Login and Get Token (No Auth Required)

**Step 1:** Find endpoint
- Click on `POST /api/v1/auth/login`

**Step 2:** Try it out
- Click **"Try it out"**

**Step 3:** Enter credentials
```json
{
  "username": "john_doe",
  "password": "secure_password123"
}
```

**Step 4:** Execute
- Click **"Execute"**

**Step 5:** Copy the token
```json
{
  "status": "success",
  "token": "eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9...",
  "user": { ... }
}
```

**Step 6:** Copy the entire token value
- Select and copy the long token string
- You'll use this for authenticated requests

---

### Example 4: Authorize Swagger UI

**Step 1:** Click "Authorize" button
- Look at the top right of the page
- Click the **"Authorize"** button (lock icon)

**Step 2:** Enter authentication
You'll see two options:

**For API Key (Device authentication):**
```
ApiKeyAuth (apiKey)
Value: [paste your device API key here]
```

**For Bearer Token (User authentication):**
```
BearerAuth (apiKey)
Value: Bearer eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9...
```
⚠️ **Important:** Include the word "Bearer" followed by a space, then your token

**Step 3:** Click "Authorize"
- Click the **"Authorize"** button in the dialog
- You'll see a checkmark when successful

**Step 4:** Close the dialog
- Click **"Close"**
- Now all requests will include your authentication!

---

### Example 5: Register a Device (Requires Auth)

**Step 1:** Make sure you're authorized
- Check if the lock icons show as "locked" (authenticated)
- If not, follow Example 4 above

**Step 2:** Find endpoint
- Scroll to "Devices" section
- Click on `POST /api/v1/devices/register`

**Step 3:** Try it out
- Click **"Try it out"**

**Step 4:** Fill in device details
```json
{
  "name": "Temperature Sensor 1",
  "device_type": "sensor",
  "user_id": "fd596e05-a937-4eea-bbaf-2779686b9f1b"
}
```
⚠️ Use the `user_id` you saved from Example 2

**Step 5:** Execute
- Click **"Execute"**

**Step 6:** Save the API key
```json
{
  "status": "success",
  "device": {
    "id": 1,
    "api_key": "a1b2c3d4e5f6g7h8i9j0k1l2m3n4o5p6",
    "name": "Temperature Sensor 1",
    "device_type": "sensor"
  }
}
```
- Copy the `api_key` value
- You'll need it to submit telemetry data

---

### Example 6: Submit Telemetry Data (Requires Device API Key)

**Step 1:** Authorize with device API key
- Click **"Authorize"** button
- In ApiKeyAuth section, paste your device API key
- Click **"Authorize"** then **"Close"**

**Step 2:** Find endpoint
- Scroll to "Telemetry" section
- Click on `POST /api/v1/telemetry`

**Step 3:** Try it out
- Click **"Try it out"**

**Step 4:** Enter telemetry data
```json
{
  "measurements": [
    {
      "name": "temperature",
      "value": 25.5,
      "unit": "celsius"
    },
    {
      "name": "humidity",
      "value": 60,
      "unit": "percent"
    }
  ]
}
```

**Step 5:** Execute
- Click **"Execute"**

**Step 6:** Verify success
```json
{
  "status": "success",
  "message": "Telemetry data stored successfully",
  "count": 2
}
```

---

### Example 7: Retrieve Telemetry Data

**Step 1:** Find endpoint
- Click on `GET /api/v1/telemetry/device/{device_id}`

**Step 2:** Try it out
- Click **"Try it out"**

**Step 3:** Enter device ID
- In the `device_id` field, enter: `1`
- Optionally set `limit` to `10`

**Step 4:** Execute
- Click **"Execute"**

**Step 5:** View your data
```json
{
  "status": "success",
  "data": [
    {
      "device_id": 1,
      "measurement_name": "temperature",
      "timestamp": "2025-11-22T00:00:00Z",
      "numeric_value": 25.5,
      "unit": "celsius"
    },
    {
      "device_id": 1,
      "measurement_name": "humidity",
      "timestamp": "2025-11-22T00:00:00Z",
      "numeric_value": 60,
      "unit": "percent"
    }
  ],
  "count": 2
}
```

---

## 🎨 UI Features

### Color Coding
- **🟢 Green (GET)**: Read operations
- **🟡 Orange (POST)**: Create operations
- **🔵 Blue (PUT)**: Update operations
- **🔴 Red (DELETE)**: Delete operations

### Response Codes
- **200**: Success
- **201**: Created
- **400**: Bad request (check your input)
- **401**: Unauthorized (need to authenticate)
- **404**: Not found
- **500**: Server error

### Sections
Each endpoint shows:
- **Parameters**: What you need to provide
- **Request body**: JSON structure for POST/PUT
- **Responses**: What you'll get back
- **Example Value**: Sample request/response

---

## 💡 Pro Tips

### 1. Use the "Example Value" button
- Click "Example Value" to auto-fill the request body
- Then modify the values as needed

### 2. Copy cURL commands
- After executing, scroll down
- Copy the cURL command to use in scripts

### 3. Test error cases
- Try invalid data to see error responses
- Example: Register with a duplicate username

### 4. Use Models section
- Scroll to bottom to see all data models
- Shows the structure of User, Device, etc.

### 5. Download the spec
- Click "Download" at the top
- Get the OpenAPI spec file
- Import into Postman or other tools

---

## 🔧 Troubleshooting

### "401 Unauthorized" error
**Problem:** Endpoint requires authentication
**Solution:** 
1. Click "Authorize" button
2. Enter your API key or Bearer token
3. Try again

### "400 Bad Request" error
**Problem:** Invalid request data
**Solution:**
1. Check the "Example Value" for correct format
2. Verify all required fields are filled
3. Check data types (string vs number)

### "404 Not Found" error
**Problem:** Resource doesn't exist
**Solution:**
1. Verify the ID exists (e.g., device_id)
2. Check if you created the resource first

### Can't see response
**Problem:** Response section is collapsed
**Solution:**
1. Scroll down after clicking "Execute"
2. Look for "Responses" section
3. Expand if needed

### Server not responding
**Problem:** Flask app not running
**Solution:**
```bash
# Start the server
poetry run python app.py

# Check it's running
curl http://localhost:5000/health
```

---

## 📚 Quick Reference

### Common Workflow

```
1. Register User
   POST /api/v1/auth/register
   
2. Login
   POST /api/v1/auth/login
   → Save token
   
3. Authorize Swagger
   Click "Authorize" → Enter token
   
4. Register Device
   POST /api/v1/devices/register
   → Save device API key
   
5. Re-authorize with Device Key
   Click "Authorize" → Enter device API key
   
6. Submit Telemetry
   POST /api/v1/telemetry
   
7. View Data
   GET /api/v1/telemetry/device/{device_id}
```

### Keyboard Shortcuts
- **Tab**: Navigate between fields
- **Enter**: Submit form (when in text field)
- **Ctrl+C**: Copy selected text
- **Ctrl+F**: Search in page

---

## 🎓 Learning Path

### Beginner
1. ✅ Test health check
2. ✅ Register a user
3. ✅ Login and get token
4. ✅ Register a device

### Intermediate
5. ✅ Submit telemetry data
6. ✅ Retrieve telemetry data
7. ✅ Update device info
8. ✅ List all devices

### Advanced
9. ✅ Use query parameters (filtering, pagination)
10. ✅ Test time range queries
11. ✅ Create and configure charts
12. ✅ Use admin endpoints

---

## 📖 Additional Resources

- **Full API Docs**: `docs/API_DOCUMENTATION.md`
- **OpenAPI Spec**: `docs/openapi.yaml`
- **Code Examples**: See API_DOCUMENTATION.md
- **GitHub**: https://github.com/IoT-Flow/Connectivity-Layer

---

## ✨ Summary

Swagger UI makes testing your API easy:
1. **Click** on an endpoint
2. **Try it out**
3. **Fill in** the data
4. **Execute**
5. **See** the response

No need for cURL or Postman - everything is in your browser!

**Start here:** http://localhost:5000/docs
