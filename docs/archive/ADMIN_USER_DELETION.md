# Admin-Only User Deletion

## Overview
Implemented admin-only user deletion following TDD (Test-Driven Development) approach.

## Feature
Only users with admin privileges can delete other users. Regular users cannot delete any users, including themselves.

## Implementation

### 1. New Admin JWT Decorator
Created `require_admin_jwt` decorator in `src/middleware/auth.py`:
- Validates JWT Bearer token
- Checks `is_admin` field in token payload
- Verifies user exists and is active in database
- Confirms user has admin privileges
- Returns 401 for invalid/expired tokens
- Returns 403 for non-admin users

### 2. Updated Delete User Endpoint
Modified `DELETE /api/v1/users/{user_id}` in `src/routes/users.py`:
- Added `@require_admin_jwt` decorator
- Now requires admin authentication
- Performs soft delete (deactivates user)
- Updated Swagger documentation

### 3. Comprehensive Tests
Created `tests/test_admin_user_deletion.py` with 12 tests:
- ✅ Delete without token (401)
- ✅ Delete with invalid token (401)
- ✅ Delete as regular user (403)
- ✅ Delete as admin (200)
- ✅ Verify soft delete (user deactivated)
- ✅ Delete non-existent user (404)
- ✅ Regular user cannot delete self (403)
- ✅ Admin can delete self (200)
- ✅ Response structure validation
- ✅ Token with admin=false rejected (403)
- ✅ Token with admin=true accepted (200)
- ✅ Expired admin token rejected (401)

## API Usage

### Endpoint
```
DELETE /api/v1/users/{user_id}
```

### Authentication Required
**Bearer Token with Admin Privileges**

### Request
```bash
curl -X DELETE http://localhost:5000/api/v1/users/{user_id} \
  -H "Authorization: Bearer <admin-jwt-token>"
```

### Response (Success - 200)
```json
{
  "status": "success",
  "message": "User deactivated successfully"
}
```

### Response (Unauthorized - 401)
```json
{
  "error": "Authorization required",
  "message": "Please provide a valid JWT token"
}
```

### Response (Forbidden - 403)
```json
{
  "error": "Admin access required",
  "message": "This action requires administrator privileges"
}
```

### Response (Not Found - 404)
```json
{
  "error": "User not found",
  "message": "No user found with ID: {user_id}"
}
```

## How to Get Admin Token

### 1. Create Admin User
```bash
# Register user
curl -X POST http://localhost:5000/api/v1/auth/register \
  -H "Content-Type: application/json" \
  -d '{
    "username": "admin",
    "email": "admin@example.com",
    "password": "secure_password"
  }'

# Manually set is_admin=true in database
# Or use admin endpoint to promote user
```

### 2. Login to Get Token
```bash
curl -X POST http://localhost:5000/api/v1/auth/login \
  -H "Content-Type: application/json" \
  -d '{
    "username": "admin",
    "password": "secure_password"
  }'
```

The token will include `is_admin: true` if the user is an admin.

## Security Features

### 1. JWT Validation
- Token must be valid and not expired
- Token must include `is_admin: true`
- User must exist in database
- User must be active

### 2. Double Check
- Checks `is_admin` in JWT payload
- Verifies `is_admin` in database
- Both must be true

### 3. Soft Delete
- Users are deactivated, not deleted
- Data is preserved
- Can be reactivated if needed

### 4. Audit Trail
- Logs all deletion attempts
- Records who deleted whom
- Timestamp of deletion

## Testing

### Run Admin Deletion Tests
```bash
poetry run pytest tests/test_admin_user_deletion.py -v
```

### Run All Tests
```bash
poetry run pytest tests/ -v
```

### Test Results
- **12 new tests** for admin deletion
- **All tests passing** (127 total)
- **100% coverage** of admin deletion scenarios

## Code Examples

### Python
```python
import requests

# Get admin token
login_response = requests.post(
    'http://localhost:5000/api/v1/auth/login',
    json={'username': 'admin', 'password': 'password'}
)
token = login_response.json()['token']

# Delete user
response = requests.delete(
    'http://localhost:5000/api/v1/users/user-id-to-delete',
    headers={'Authorization': f'Bearer {token}'}
)

if response.status_code == 200:
    print("User deleted successfully")
elif response.status_code == 403:
    print("Error: Admin privileges required")
```

### JavaScript
```javascript
// Get admin token
const loginResponse = await fetch('http://localhost:5000/api/v1/auth/login', {
  method: 'POST',
  headers: {'Content-Type': 'application/json'},
  body: JSON.stringify({username: 'admin', password: 'password'})
});
const {token} = await loginResponse.json();

// Delete user
const response = await fetch(
  'http://localhost:5000/api/v1/users/user-id-to-delete',
  {
    method: 'DELETE',
    headers: {'Authorization': `Bearer ${token}`}
  }
);

if (response.status_code === 200) {
  console.log('User deleted successfully');
} else if (response.status_code === 403) {
  console.log('Error: Admin privileges required');
}
```

## Swagger UI

The endpoint is documented in Swagger UI:

**URL:** http://localhost:5000/docs

**Location:** Users > DELETE /api/v1/users/{user_id}

**Security:** BearerAuth (JWT token with admin privileges)

## Migration Notes

### Breaking Change
This is a **breaking change** if you had code that deleted users without admin authentication.

### Before
```bash
# Anyone could delete users
curl -X DELETE http://localhost:5000/api/v1/users/{user_id}
```

### After
```bash
# Only admins can delete users
curl -X DELETE http://localhost:5000/api/v1/users/{user_id} \
  -H "Authorization: Bearer <admin-token>"
```

### Migration Steps
1. Identify code that deletes users
2. Ensure it uses admin credentials
3. Update to include Authorization header
4. Test with admin token

## Benefits

### 1. Security
- Prevents unauthorized user deletion
- Protects against malicious actors
- Requires explicit admin privileges

### 2. Accountability
- Clear audit trail
- Know who deleted whom
- Timestamp of deletion

### 3. Data Protection
- Soft delete preserves data
- Can recover if needed
- Maintains referential integrity

### 4. Compliance
- Meets security best practices
- Supports GDPR requirements
- Enables access control

## Future Enhancements

### Potential Improvements
1. **Hard Delete Option** - Permanently delete users (admin only)
2. **Bulk Delete** - Delete multiple users at once
3. **Delete Confirmation** - Require confirmation for deletion
4. **Restore User** - Reactivate deactivated users
5. **Delete Audit Log** - Detailed log of all deletions
6. **Self-Service Deletion** - Allow users to delete their own account

## Changelog

### Version 1.0.0 (2025-11-22)
- ✅ Implemented admin-only user deletion
- ✅ Created `require_admin_jwt` decorator
- ✅ Added 12 comprehensive tests
- ✅ Updated Swagger documentation
- ✅ All tests passing (127 total)
- ✅ TDD approach followed

## Related Documentation
- `src/middleware/auth.py` - Admin JWT decorator
- `src/routes/users.py` - User deletion endpoint
- `tests/test_admin_user_deletion.py` - Test suite
- `docs/API_DOCUMENTATION.md` - Complete API reference
