# Get User Devices API

## Overview
New API endpoint to retrieve all devices belonging to a specific user.

## Endpoint

```
GET /api/v1/devices/user/{user_id}
```

## Description
Get a list of all devices registered by a specific user, with optional filtering and pagination.

## Parameters

### Path Parameters
- **user_id** (required): User UUID
  - Type: string
  - Example: `fd596e05a9374eeabbaf2779686b9f1b`

### Query Parameters
- **status** (optional): Filter by device status
  - Type: string
  - Values: `active`, `inactive`, `maintenance`
  - Example: `?status=active`

- **limit** (optional): Maximum number of devices to return
  - Type: integer
  - Default: 100
  - Example: `?limit=10`

- **offset** (optional): Number of devices to skip (pagination)
  - Type: integer
  - Default: 0
  - Example: `?offset=20`

## Response

### Success Response (200 OK)

```json
{
  "status": "success",
  "user_id": "fd596e05a9374eeabbaf2779686b9f1b",
  "username": "testuser",
  "total_devices": 5,
  "devices": [
    {
      "id": 1,
      "name": "Temperature Sensor 1",
      "device_type": "sensor",
      "status": "active",
      "location": "Living Room",
      "firmware_version": "1.0.0",
      "hardware_version": "v2",
      "last_seen": "2025-11-22T00:00:00Z",
      "created_at": "2025-11-21T00:00:00Z",
      "updated_at": "2025-11-22T00:00:00Z"
    }
  ],
  "meta": {
    "limit": 100,
    "offset": 0,
    "returned": 5
  }
}
```

### Error Response (404 Not Found)

```json
{
  "error": "User not found",
  "message": "No user found with ID: invalid-user-id"
}
```

## Examples

### Get All Devices for a User

```bash
curl http://localhost:5000/api/v1/devices/user/fd596e05a9374eeabbaf2779686b9f1b
```

### Get Only Active Devices

```bash
curl "http://localhost:5000/api/v1/devices/user/fd596e05a9374eeabbaf2779686b9f1b?status=active"
```

### Get Devices with Pagination

```bash
# Get first 10 devices
curl "http://localhost:5000/api/v1/devices/user/fd596e05a9374eeabbaf2779686b9f1b?limit=10&offset=0"

# Get next 10 devices
curl "http://localhost:5000/api/v1/devices/user/fd596e05a9374eeabbaf2779686b9f1b?limit=10&offset=10"
```

### Python Example

```python
import requests

user_id = "fd596e05a9374eeabbaf2779686b9f1b"
url = f"http://localhost:5000/api/v1/devices/user/{user_id}"

# Get all devices
response = requests.get(url)
data = response.json()

print(f"User: {data['username']}")
print(f"Total devices: {data['total_devices']}")

for device in data['devices']:
    print(f"- {device['name']} ({device['status']})")

# Get only active devices
response = requests.get(url, params={'status': 'active'})
active_devices = response.json()
print(f"Active devices: {active_devices['total_devices']}")
```

### JavaScript Example

```javascript
const userId = 'fd596e05a9374eeabbaf2779686b9f1b';
const url = `http://localhost:5000/api/v1/devices/user/${userId}`;

// Get all devices
fetch(url)
  .then(response => response.json())
  .then(data => {
    console.log(`User: ${data.username}`);
    console.log(`Total devices: ${data.total_devices}`);
    
    data.devices.forEach(device => {
      console.log(`- ${device.name} (${device.status})`);
    });
  });

// Get only active devices
fetch(`${url}?status=active`)
  .then(response => response.json())
  .then(data => {
    console.log(`Active devices: ${data.total_devices}`);
  });
```

## Features

### Security
- ✅ API keys are **not included** in the response for security
- ✅ Only returns devices belonging to the specified user
- ✅ User must exist in the system

### Filtering
- ✅ Filter by device status (active, inactive, maintenance)
- ✅ Combine filters with pagination

### Pagination
- ✅ Control number of results with `limit`
- ✅ Skip results with `offset`
- ✅ Get total count in response

### Response Metadata
- ✅ Total device count
- ✅ User information (username)
- ✅ Pagination info (limit, offset, returned count)

## Use Cases

### 1. User Dashboard
Display all devices for the logged-in user:
```javascript
// Get current user's devices
const response = await fetch(`/api/v1/devices/user/${currentUserId}`);
const data = await response.json();

// Display in dashboard
renderDeviceList(data.devices);
```

### 2. Device Management Page
Show devices with status filtering:
```javascript
// Show only active devices
const activeDevices = await fetch(
  `/api/v1/devices/user/${userId}?status=active`
).then(r => r.json());

// Show only offline devices
const offlineDevices = await fetch(
  `/api/v1/devices/user/${userId}?status=inactive`
).then(r => r.json());
```

### 3. Paginated Device List
Implement pagination for users with many devices:
```javascript
const pageSize = 10;
const page = 1;
const offset = (page - 1) * pageSize;

const response = await fetch(
  `/api/v1/devices/user/${userId}?limit=${pageSize}&offset=${offset}`
).then(r => r.json());

console.log(`Showing ${response.meta.returned} of ${response.total_devices} devices`);
```

### 4. Device Statistics
Get device statistics for a user:
```javascript
const allDevices = await fetch(`/api/v1/devices/user/${userId}`).then(r => r.json());
const activeDevices = await fetch(`/api/v1/devices/user/${userId}?status=active`).then(r => r.json());

const stats = {
  total: allDevices.total_devices,
  active: activeDevices.total_devices,
  inactive: allDevices.total_devices - activeDevices.total_devices
};

console.log(`User has ${stats.active} active devices out of ${stats.total} total`);
```

## Testing

### Run Tests
```bash
poetry run pytest tests/test_user_devices.py -v
```

### Test Coverage
- ✅ Endpoint exists
- ✅ Empty device list
- ✅ Multiple devices
- ✅ Invalid user ID
- ✅ Status filtering
- ✅ Pagination
- ✅ API key not in response
- ✅ Response structure

## Swagger UI

This endpoint is documented in Swagger UI:

**URL:** http://localhost:5000/docs

**Location:** Devices > GET /api/v1/devices/user/{user_id}

Try it out:
1. Open Swagger UI
2. Find "Devices" section
3. Click on `GET /api/v1/devices/user/{user_id}`
4. Click "Try it out"
5. Enter a user_id
6. Click "Execute"

## Related Endpoints

- `POST /api/v1/devices/register` - Register a new device
- `GET /api/v1/devices/{device_id}` - Get specific device details
- `GET /api/v1/admin/devices` - Get all devices (admin only)
- `GET /api/v1/users/{user_id}` - Get user details

## Notes

- Device API keys are excluded from the response for security
- Returns empty list if user has no devices
- Returns 404 if user doesn't exist
- Supports filtering and pagination
- Includes metadata about pagination and total count

## Changelog

### Version 1.0.0 (2025-11-22)
- ✅ Initial implementation
- ✅ Status filtering
- ✅ Pagination support
- ✅ Swagger documentation
- ✅ Comprehensive tests (8 tests)
