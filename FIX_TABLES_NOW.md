# 🚨 QUICK FIX: Create PostgreSQL Tables

Your database `iotflow` exists but tables are missing. Here are **3 quick solutions**:

---

## ⚡ Solution 1: One-Line Fix (Fastest)

```bash
# Make scripts executable and run
chmod +x fix_database.sh scripts/create_postgres_tables.py && ./fix_database.sh
```

**This will:**
- ✅ Check PostgreSQL is running
- ✅ Create database if missing
- ✅ Create all 8 tables
- ✅ Create admin user
- ✅ Verify everything works

---

## ⚡ Solution 2: Python Script (Recommended)

```bash
# Run the table creation script
poetry run python scripts/create_postgres_tables.py
```

**Follow the prompts:**
- It will check your database connection
- Ask if you want to drop existing tables (if any)
- Create all required tables
- Create admin and test users
- Verify the setup

---

## ⚡ Solution 3: SQL Script (Direct)

```bash
# Run SQL script directly
docker exec -i iotflow_postgres psql -U iotflow -d iotflow < scripts/create_tables.sql
```

---

## 🔍 Verify It Worked

```bash
# Check tables exist
docker exec -it iotflow_postgres psql -U iotflow -d iotflow -c "\dt"

# Should show 8 tables:
# - users
# - devices
# - device_auth
# - device_configurations
# - device_control
# - charts
# - chart_devices
# - chart_measurements
```

---

## 🎯 Test the API

```bash
# 1. Health check
curl http://localhost:5000/health

# 2. Register a device
curl -X POST http://localhost:5000/api/v1/devices/register \
  -H "Content-Type: application/json" \
  -d '{
    "name": "TestDevice",
    "device_type": "sensor",
    "user_id": "dcf1a"
  }'
```

---

## 🔐 Default Credentials

After running any solution, you'll have:

**Admin User:**
- Username: `admin`
- Password: `admin123`
- User ID: `dcf1a`

**Test User:**
- Username: `test`
- Password: `test123`
- User ID: `testuser`

---

## 🐛 Still Not Working?

### Check PostgreSQL is Running

```bash
docker ps | grep postgres
# Should show "Up" status
```

### Check Database Exists

```bash
docker exec -it iotflow_postgres psql -U iotflow -c "\l" | grep iotflow
# Should show "iotflow" database
```

### Check Logs

```bash
# PostgreSQL logs
docker logs iotflow_postgres

# Flask logs
docker logs iotflow_connectivity
```

### Complete Reset (Nuclear Option)

```bash
# Stop everything
docker compose down -v

# Remove data
sudo rm -rf instance/postgres_data

# Start fresh
docker compose up -d postgres
sleep 10

# Create tables
poetry run python scripts/create_postgres_tables.py

# Start all services
docker compose up -d
```

---

## 📚 More Help

- **Detailed Guide**: See `docs/DATABASE_SETUP_TROUBLESHOOTING.md`
- **Quick Start**: See `QUICKSTART.md`
- **Setup Guide**: See `docs/SETUP_GUIDE.md`

---

## ✅ Success Checklist

After fixing, verify:

- [ ] PostgreSQL container is running
- [ ] Database `iotflow` exists
- [ ] 8 tables are created
- [ ] Admin user exists
- [ ] API health check passes
- [ ] Can register a device

**All checked? You're ready to go! 🚀**

---

**Quick Commands Reference:**

```bash
# Fix database
./fix_database.sh

# Or use Python
poetry run python scripts/create_postgres_tables.py

# Or use SQL
docker exec -i iotflow_postgres psql -U iotflow -d iotflow < scripts/create_tables.sql

# Verify
docker exec -it iotflow_postgres psql -U iotflow -d iotflow -c "\dt"

# Test API
curl http://localhost:5000/health
```
