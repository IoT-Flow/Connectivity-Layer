# Swagger UI Quick Fix

## ✅ SOLUTION

### Correct URL
Use port **5000**, not 3000:

```
✅ CORRECT: http://localhost:5000/docs
❌ WRONG:   http://localhost:3000/docs
```

### Why Port 5000?
- Flask server runs on port 5000 by default
- Port 3000 is typically used for React/frontend apps
- Check `app.py` - it runs on port 5000

## 🔍 Verify Server is Running

```bash
# Check if server is running
curl http://localhost:5000/health

# Should return:
{
  "status": "healthy",
  "message": "IoT Connectivity Layer is running",
  "version": "1.0.0"
}
```

## 📖 Access Swagger UI

1. **Open browser**
2. **Go to:** http://localhost:5000/docs
3. **You should see:** Interactive API documentation with endpoints

## 🎯 What You'll See

When you open http://localhost:5000/docs, you'll see:

```
IoTFlow Connectivity Layer API
REST API for IoT device connectivity and telemetry data management

▼ Authentication
  POST /api/v1/auth/register    Register new user
  POST /api/v1/auth/login       User login

▼ Devices
  POST /api/v1/devices/register  Register device
  GET  /api/v1/devices          List devices
  ...
```

## 🚀 Quick Test

Try this in your browser:

1. Open: http://localhost:5000/docs
2. Find: `POST /api/v1/auth/register`
3. Click: "Try it out"
4. Enter:
   ```json
   {
     "username": "testuser",
     "email": "test@example.com",
     "password": "password123"
   }
   ```
5. Click: "Execute"
6. See: Response with user details

## 🔧 Troubleshooting

### "This site can't be reached"
**Problem:** Server not running

**Solution:**
```bash
# Start the server
poetry run python app.py

# Check it's running
curl http://localhost:5000/health
```

### "No operations defined in spec!"
**Problem:** Endpoints not documented yet

**Solution:** We're adding Swagger docs to endpoints. Some endpoints may not show up yet, but the main ones (auth, devices, telemetry) are documented.

### Wrong port (3000 vs 5000)
**Problem:** Using port 3000 instead of 5000

**Solution:** Always use http://localhost:5000/docs

## 📚 More Help

- **Full Guide:** docs/SWAGGER_UI_GUIDE.md
- **API Docs:** docs/API_DOCUMENTATION.md
- **OpenAPI Spec:** docs/openapi.yaml

## ✨ Summary

**Correct URL:** http://localhost:5000/docs (port 5000, not 3000)

Open it now and start testing your API!
