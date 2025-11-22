# User Endpoints - Complete Reference

## Overview

We have **5 user management endpoints** available.

**Base URL:** `http://localhost:5000/api/v1/users`

---

## Quick Reference

| Method | Endpoint | Description | Auth Required |
|--------|----------|-------------|---------------|
| POST | `/api/v1/users` | Create new user | No |
| GET | `/api/v1/users` | List all users | **Admin JWT** |
| GET | `/api/v1/users/{user_id}` | Get user details | No |
| PUT | `/api/v1/users/{user_id}` | Update user | No |
| DELETE | `/api/v1/users/{user_id}` | Delete user | **Admin JWT** |

---

## 1. Create User

**Endpoint:** `POST /api/v1/users`

**Authentication:** None required

### curl Command:

```bash
curl -X POST http://localhost:5000/api/v1/users \
  -H "Content-Type: application/json" \
  -d '{
    "username": "newuser",
    "email": "newuser@example.com",
    "password": "SecurePassword123!",
    "is_admin": false
  }'
```

### Response (201 Created):

```json
{
  "status": "success",
  "message": "User created successfully",
  "user": {
    "id": 1,
    "user_id": "fd596e05a9374eeabbaf2779686b9f1b",
    "username": "newuser",
    "email": "newuser@example.com",
    "is_admin": false,
    "is_active": true,
    "created_at": "2025-11-22T00:00:00Z",
    "updated_at": "2025-11-22T00:00:00Z"
  }
}
```

---

## 2. List All Users (Admin Only)

**Endpoint:** `GET /api/v1/users`

**Authentication:** Admin JWT Token Required

### curl Command:

```bash
curl -X GET http://localhost:5000/api/v1/users \
  -H "Authorization: Bearer YOUR_ADMIN_JWT_TOKEN"
```

### With Pagination:

```bash
curl -X GET "http://localhost:5000/api/v1/users?limit=10&offset=0" \
  -H "Authorization: Bearer YOUR_ADMIN_JWT_TOKEN"
```

### Response (200 OK):

```json
{
  "status": "success",
  "users": [
    {
      "id": 1,
      "user_id": "fd596e05a9374eeabbaf2779686b9f1b",
      "username": "admin",
      "email": "admin@example.com",
      "is_admin": true,
      "is_active": true,
      "created_at": "2025-11-22T00:00:00Z"
    },
    {
      "id": 2,
      "user_id": "a1b2c3d4e5f6g7h8i9j0k1l2m3n4o5p6",
      "username": "user1",
      "email": "user1@example.com",
      "is_admin": false,
      "is_active": true,
      "created_at": "2025-11-22T01:00:00Z"
    }
  ],
  "meta": {
    "total": 2,
    "limit": 100,
    "offset": 0
  }
}
```

---

## 3. Get User Details

**Endpoint:** `GET /api/v1/users/{user_id}`

**Authentication:** None required

### curl Command:

```bash
curl -X GET http://localhost:5000/api/v1/users/fd596e05a9374eeabbaf2779686b9f1b
```

### Response (200 OK):

```json
{
  "status": "success",
  "user": {
    "id": 1,
    "user_id": "fd596e05a9374eeabbaf2779686b9f1b",
    "username": "admin",
    "email": "admin@example.com",
    "is_admin": true,
    "is_active": true,
    "created_at": "2025-11-22T00:00:00Z",
    "updated_at": "2025-11-22T00:00:00Z"
  }
}
```

---

## 4. Update User

**Endpoint:** `PUT /api/v1/users/{user_id}`

**Authentication:** None required (should be restricted to own user or admin)

### curl Command:

```bash
curl -X PUT http://localhost:5000/api/v1/users/fd596e05a9374eeabbaf2779686b9f1b \
  -H "Content-Type: application/json" \
  -d '{
    "username": "updateduser",
    "email": "updated@example.com",
    "is_active": true
  }'
```

### Update Password:

```bash
curl -X PUT http://localhost:5000/api/v1/users/fd596e05a9374eeabbaf2779686b9f1b \
  -H "Content-Type: application/json" \
  -d '{
    "password": "NewSecurePassword123!"
  }'
```

### Updatable Fields:

- `username`
- `email`
- `password`
- `is_active`
- `is_admin`

### Response (200 OK):

```json
{
  "status": "success",
  "message": "User updated successfully",
  "user": {
    "id": 1,
    "user_id": "fd596e05a9374eeabbaf2779686b9f1b",
    "username": "updateduser",
    "email": "updated@example.com",
    "is_admin": false,
    "is_active": true,
    "updated_at": "2025-11-22T02:00:00Z"
  }
}
```

---

## 5. Delete User (Admin Only)

**Endpoint:** `DELETE /api/v1/users/{user_id}`

**Authentication:** Admin JWT Token Required

**Note:** This is a soft delete - the user is deactivated, not permanently deleted.

### curl Command:

```bash
curl -X DELETE http://localhost:5000/api/v1/users/fd596e05a9374eeabbaf2779686b9f1b \
  -H "Authorization: Bearer YOUR_ADMIN_JWT_TOKEN"
```

### Response (200 OK):

```json
{
  "status": "success",
  "message": "User deactivated successfully"
}
```

---

## Authentication Endpoints (Related)

These are in `/api/v1/auth`:

### Register

```bash
curl -X POST http://localhost:5000/api/v1/auth/register \
  -H "Content-Type: application/json" \
  -d '{
    "username": "newuser",
    "email": "newuser@example.com",
    "password": "Password123!"
  }'
```

### Login

```bash
curl -X POST http://localhost:5000/api/v1/auth/login \
  -H "Content-Type: application/json" \
  -d '{
    "username": "newuser",
    "password": "Password123!"
  }'
```

### Logout

```bash
curl -X POST http://localhost:5000/api/v1/auth/logout \
  -H "Authorization: Bearer YOUR_JWT_TOKEN"
```

---

## Error Responses

### 400 Bad Request

```json
{
  "error": "Missing required fields",
  "message": "username, email, and password are required"
}
```

### 401 Unauthorized

```json
{
  "error": "Unauthorized",
  "message": "Authentication token is required"
}
```

### 403 Forbidden

```json
{
  "error": "Forbidden",
  "message": "Admin privileges required"
}
```

### 404 Not Found

```json
{
  "error": "User not found",
  "message": "No user found with ID: fd596e05a9374eeabbaf2779686b9f1b"
}
```

### 409 Conflict

```json
{
  "error": "Username already exists",
  "message": "User with username 'testuser' already exists"
}
```

---

## Complete Workflow Example

```bash
# 1. Create a new user
curl -X POST http://localhost:5000/api/v1/users \
  -H "Content-Type: application/json" \
  -d '{
    "username": "johndoe",
    "email": "john@example.com",
    "password": "SecurePass123!"
  }'

# Save the user_id from response
USER_ID="fd596e05a9374eeabbaf2779686b9f1b"

# 2. Get user details
curl http://localhost:5000/api/v1/users/$USER_ID

# 3. Update user email
curl -X PUT http://localhost:5000/api/v1/users/$USER_ID \
  -H "Content-Type: application/json" \
  -d '{
    "email": "john.doe@example.com"
  }'

# 4. List all users (as admin)
curl http://localhost:5000/api/v1/users \
  -H "Authorization: Bearer $ADMIN_TOKEN"

# 5. Delete user (as admin)
curl -X DELETE http://localhost:5000/api/v1/users/$USER_ID \
  -H "Authorization: Bearer $ADMIN_TOKEN"
```

---

## Testing Tips

### 1. Pretty Print JSON

```bash
curl http://localhost:5000/api/v1/users/USER_ID | python -m json.tool
```

### 2. Save Response to Variable

```bash
RESPONSE=$(curl -s -X POST http://localhost:5000/api/v1/users \
  -H "Content-Type: application/json" \
  -d '{"username":"test","email":"test@example.com","password":"Test123!"}')

USER_ID=$(echo $RESPONSE | grep -o '"user_id":"[^"]*"' | cut -d'"' -f4)
echo "Created user: $USER_ID"
```

### 3. Check HTTP Status Only

```bash
curl -s -o /dev/null -w "%{http_code}" http://localhost:5000/api/v1/users/USER_ID
```

---

## Security Notes

⚠️ **Current Security Issues:**

1. **Update User** - No authentication required. Anyone can update any user.
   - **Recommendation:** Add authentication to restrict updates to own user or admin

2. **Get User** - No authentication required. Anyone can view user details.
   - **Recommendation:** Consider adding authentication or limiting exposed data

3. **JWT Not Implemented** - Login doesn't return JWT tokens yet.
   - **Recommendation:** Implement JWT token generation in login endpoint

---

## Recommended Security Improvements

### 1. Protect Update User Endpoint

```python
@user_bp.route("/<user_id>", methods=["PUT"])
@security_headers_middleware()
@require_jwt_or_admin  # Add authentication
def update_user(user_id):
    # Verify user can only update their own data or is admin
    pass
```

### 2. Implement JWT Token Generation

See `ADMIN_GET_USERS_GUIDE.md` for JWT implementation details.

### 3. Add Rate Limiting

```python
@user_bp.route("", methods=["POST"])
@security_headers_middleware()
@rate_limit(max_requests=5, window=3600)  # 5 registrations per hour
def create_user():
    pass
```

---

## Summary

### Available Endpoints:

✅ **5 User Endpoints**
- Create User
- List Users (Admin)
- Get User Details
- Update User
- Delete User (Admin)

✅ **3 Auth Endpoints**
- Register
- Login
- Logout

### Authentication Status:

- ✅ List Users - Admin JWT required
- ✅ Delete User - Admin JWT required
- ⚠️ Update User - No auth (should be protected)
- ⚠️ Get User - No auth (consider protecting)
- ⚠️ JWT tokens - Not yet returned by login

---

**Last Updated:** November 22, 2025  
**API Version:** 1.0.0  
**Status:** Functional with security improvements needed
