# IoTFlow API Documentation

This directory contains comprehensive API documentation for the IoTFlow Connectivity Layer.

## Documentation Files

### 📘 [API_DOCUMENTATION.md](./API_DOCUMENTATION.md)
Complete API reference with:
- Quick start guide
- All endpoints documented
- Request/response examples
- Code samples (Python, JavaScript, cURL)
- Best practices
- Error handling

### 📋 [openapi.yaml](./openapi.yaml)
OpenAPI 3.0 specification file:
- Machine-readable API specification
- Can be imported into API tools (Postman, Insomnia)
- Used for code generation
- Powers the interactive Swagger UI

## Interactive Documentation

### Swagger UI
Visit the interactive API documentation at:

**URL:** http://localhost:5000/docs

Features:
- ✅ Try out API endpoints directly in browser
- ✅ See request/response examples
- ✅ Test authentication
- ✅ View all available endpoints
- ✅ Download OpenAPI spec

### OpenAPI Spec JSON
**URL:** http://localhost:5000/apispec.json

## Quick Links

### Getting Started
1. [Register a user](./API_DOCUMENTATION.md#1-register-a-user)
2. [Login](./API_DOCUMENTATION.md#2-login)
3. [Register a device](./API_DOCUMENTATION.md#3-register-a-device)
4. [Submit telemetry](./API_DOCUMENTATION.md#4-submit-telemetry-data)

### Common Operations
- [Authentication](./API_DOCUMENTATION.md#authentication)
- [Device Management](./API_DOCUMENTATION.md#devices)
- [Telemetry Data](./API_DOCUMENTATION.md#telemetry)
- [Charts](./API_DOCUMENTATION.md#charts)

### Code Examples
- [Python Examples](./API_DOCUMENTATION.md#python)
- [JavaScript Examples](./API_DOCUMENTATION.md#javascript-nodejs)
- [cURL Examples](./API_DOCUMENTATION.md#curl)

## Using the Documentation

### For Developers
1. Read [API_DOCUMENTATION.md](./API_DOCUMENTATION.md) for complete reference
2. Use [Swagger UI](http://localhost:5000/docs) to test endpoints
3. Copy code examples for your language
4. Check error responses and status codes

### For API Consumers
1. Import [openapi.yaml](./openapi.yaml) into your API client
2. Generate client SDKs using OpenAPI generators
3. Use interactive docs for testing

### For Integration
```bash
# Import OpenAPI spec into Postman
# File > Import > openapi.yaml

# Generate Python client
openapi-generator-cli generate -i openapi.yaml -g python -o ./client

# Generate JavaScript client
openapi-generator-cli generate -i openapi.yaml -g javascript -o ./client
```

## API Overview

### Base URL
- **Development:** `http://localhost:5000`
- **Production:** `https://api.iotflow.example.com`

### Authentication Methods
1. **API Key** (Devices): `X-API-Key` header
2. **JWT Bearer** (Users): `Authorization: Bearer <token>` header

### Main Endpoints
- `/health` - System health check
- `/api/v1/auth/*` - Authentication
- `/api/v1/users/*` - User management
- `/api/v1/devices/*` - Device management
- `/api/v1/telemetry/*` - Telemetry data
- `/api/v1/charts/*` - Chart configuration
- `/api/v1/admin/*` - Admin operations

## Testing the API

### Using cURL
```bash
# Health check
curl http://localhost:5000/health

# Register user
curl -X POST http://localhost:5000/api/v1/auth/register \
  -H "Content-Type: application/json" \
  -d '{"username":"test","email":"test@example.com","password":"password123"}'
```

### Using Python
```python
import requests

# Health check
response = requests.get('http://localhost:5000/health')
print(response.json())
```

### Using Swagger UI
1. Open http://localhost:5000/docs
2. Click on any endpoint
3. Click "Try it out"
4. Fill in parameters
5. Click "Execute"

## Support

- **Issues:** https://github.com/IoT-Flow/Connectivity-Layer/issues
- **Discussions:** https://github.com/IoT-Flow/Connectivity-Layer/discussions

## Contributing

To update documentation:
1. Edit [API_DOCUMENTATION.md](./API_DOCUMENTATION.md) for text docs
2. Edit [openapi.yaml](./openapi.yaml) for OpenAPI spec
3. Restart Flask app to see changes in Swagger UI

## License

MIT License - See LICENSE file for details
