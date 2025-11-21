# 🔧 Database Setup Troubleshooting Guide

Complete guide to fix PostgreSQL table creation issues.

---

## 🎯 Problem: Tables Not Created

If the database `iotflow` exists but tables are not created, follow these solutions:

---

## ✅ Solution 1: Using Python Script (Recommended)

### Step 1: Run the Table Creation Script

```bash
# Make the script executable
chmod +x scripts/create_postgres_tables.py

# Run the script
poetry run python scripts/create_postgres_tables.py
```

**What it does:**
- ✅ Checks PostgreSQL connection
- ✅ Lists existing tables
- ✅ Creates all required tables
- ✅ Creates admin and test users
- ✅ Verifies the setup

**Expected Output:**
```
============================================================
PostgreSQL Table Creation Script
IoT Connectivity Layer
============================================================

[Step 1/5] Checking database connection...
✓ PostgreSQL connection successful
✓ PostgreSQL version: PostgreSQL 15.x
✓ Connected to database: iotflow

[Step 2/5] Checking existing tables...
⚠ No tables found in database

[Step 3/5] Creating database tables...
📋 Creating database tables...

✓ Successfully created 8 tables:
  - users
  - devices
  - device_auth
  - device_configurations
  - device_control
  - charts
  - chart_devices
  - chart_measurements

[Step 4/5] Creating initial data...
👤 Creating initial users...
  ✓ Created admin user
  ✓ Created test user

[Step 5/5] Verifying setup...
🔍 Verifying database setup...
✓ All 8 required tables exist
✓ Found 2 users in database
✓ Found 0 devices in database

✅ Database setup verification passed!

============================================================
✅ DATABASE SETUP COMPLETED SUCCESSFULLY!
============================================================
```

---

## ✅ Solution 2: Using SQL Script

### Step 1: Connect to PostgreSQL

```bash
# Using Docker
docker exec -it iotflow_postgres psql -U iotflow -d iotflow

# Or from host (if psql is installed)
psql -h localhost -U iotflow -d iotflow
```

### Step 2: Run the SQL Script

```bash
# From outside the container
docker exec -i iotflow_postgres psql -U iotflow -d iotflow < scripts/create_tables.sql

# Or copy and paste the SQL commands manually
```

### Step 3: Verify Tables

```sql
-- List all tables
\dt

-- Or using SQL
SELECT table_name 
FROM information_schema.tables 
WHERE table_schema = 'public' 
ORDER BY table_name;
```

**Expected Output:**
```
           List of relations
 Schema |        Name         | Type  |  Owner  
--------+---------------------+-------+---------
 public | chart_devices       | table | iotflow
 public | chart_measurements  | table | iotflow
 public | charts              | table | iotflow
 public | device_auth         | table | iotflow
 public | device_configurations | table | iotflow
 public | device_control      | table | iotflow
 public | devices             | table | iotflow
 public | users               | table | iotflow
(8 rows)
```

---

## ✅ Solution 3: Using init_db.py (Original Method)

### Step 1: Ensure Correct DATABASE_URL

```bash
# Check your .env file
cat .env | grep DATABASE_URL

# Should be:
DATABASE_URL=postgresql://iotflow:iotflowpass@postgres:5432/iotflow

# Or for local connection:
DATABASE_URL=postgresql://iotflow:iotflowpass@localhost:5432/iotflow
```

### Step 2: Run init_db.py

```bash
poetry run python init_db.py
```

**If it asks for confirmation:**
```
This will drop and recreate all database tables. Continue? (y/N): y
```

---

## 🔍 Diagnostic Commands

### Check PostgreSQL is Running

```bash
# Check Docker container
docker ps | grep postgres

# Check PostgreSQL logs
docker logs iotflow_postgres

# Check if port is open
nc -zv localhost 5432
```

### Check Database Exists

```bash
# List all databases
docker exec -it iotflow_postgres psql -U iotflow -c "\l"

# Connect to database
docker exec -it iotflow_postgres psql -U iotflow -d iotflow -c "SELECT current_database();"
```

### Check User Permissions

```bash
# Check user privileges
docker exec -it iotflow_postgres psql -U iotflow -d iotflow -c "\du"

# Grant all permissions (if needed)
docker exec -it iotflow_postgres psql -U postgres -d iotflow -c "GRANT ALL PRIVILEGES ON DATABASE iotflow TO iotflow;"
docker exec -it iotflow_postgres psql -U postgres -d iotflow -c "GRANT ALL PRIVILEGES ON ALL TABLES IN SCHEMA public TO iotflow;"
docker exec -it iotflow_postgres psql -U postgres -d iotflow -c "GRANT ALL PRIVILEGES ON ALL SEQUENCES IN SCHEMA public TO iotflow;"
```

### Check Tables

```bash
# List tables
docker exec -it iotflow_postgres psql -U iotflow -d iotflow -c "\dt"

# Count records in users table
docker exec -it iotflow_postgres psql -U iotflow -d iotflow -c "SELECT COUNT(*) FROM users;"
```

---

## 🐛 Common Issues and Fixes

### Issue 1: "Database does not exist"

**Error:**
```
FATAL: database "iotflow" does not exist
```

**Fix:**
```bash
# Create the database
docker exec -it iotflow_postgres psql -U postgres -c "CREATE DATABASE iotflow;"

# Grant permissions
docker exec -it iotflow_postgres psql -U postgres -c "GRANT ALL PRIVILEGES ON DATABASE iotflow TO iotflow;"

# Then run the table creation script
poetry run python scripts/create_postgres_tables.py
```

### Issue 2: "Permission denied"

**Error:**
```
ERROR: permission denied for schema public
```

**Fix:**
```bash
# Grant schema permissions
docker exec -it iotflow_postgres psql -U postgres -d iotflow -c "GRANT ALL ON SCHEMA public TO iotflow;"
docker exec -it iotflow_postgres psql -U postgres -d iotflow -c "GRANT ALL PRIVILEGES ON ALL TABLES IN SCHEMA public TO iotflow;"
docker exec -it iotflow_postgres psql -U postgres -d iotflow -c "GRANT ALL PRIVILEGES ON ALL SEQUENCES IN SCHEMA public TO iotflow;"
```

### Issue 3: "Connection refused"

**Error:**
```
could not connect to server: Connection refused
```

**Fix:**
```bash
# Check PostgreSQL is running
docker ps | grep postgres

# If not running, start it
docker compose up -d postgres

# Wait for it to be ready
docker logs -f iotflow_postgres

# Check port binding
docker port iotflow_postgres
```

### Issue 4: "Role does not exist"

**Error:**
```
FATAL: role "iotflow" does not exist
```

**Fix:**
```bash
# Create the user
docker exec -it iotflow_postgres psql -U postgres -c "CREATE USER iotflow WITH PASSWORD 'iotflowpass';"

# Grant permissions
docker exec -it iotflow_postgres psql -U postgres -c "ALTER USER iotflow CREATEDB;"
docker exec -it iotflow_postgres psql -U postgres -c "GRANT ALL PRIVILEGES ON DATABASE iotflow TO iotflow;"
```

### Issue 5: Wrong DATABASE_URL

**Error:**
```
sqlalchemy.exc.OperationalError: (psycopg2.OperationalError) could not translate host name
```

**Fix:**
```bash
# Check your .env file
cat .env | grep DATABASE_URL

# If running Flask locally (outside Docker), use:
DATABASE_URL=postgresql://iotflow:iotflowpass@localhost:5432/iotflow

# If running Flask in Docker, use:
DATABASE_URL=postgresql://iotflow:iotflowpass@postgres:5432/iotflow

# Update .env and restart
```

---

## 🔄 Complete Reset (Nuclear Option)

If nothing works, do a complete reset:

```bash
# 1. Stop all services
docker compose down

# 2. Remove volumes (DELETES ALL DATA!)
docker compose down -v

# 3. Remove PostgreSQL data directory
sudo rm -rf instance/postgres_data

# 4. Start PostgreSQL
docker compose up -d postgres

# 5. Wait for PostgreSQL to initialize
sleep 10

# 6. Create tables
poetry run python scripts/create_postgres_tables.py

# 7. Start all services
docker compose up -d
```

---

## ✅ Verification Checklist

After running any solution, verify everything works:

```bash
# 1. Check PostgreSQL is running
docker ps | grep postgres
# ✓ Should show "Up" status

# 2. Check database exists
docker exec -it iotflow_postgres psql -U iotflow -c "\l" | grep iotflow
# ✓ Should show "iotflow" database

# 3. Check tables exist
docker exec -it iotflow_postgres psql -U iotflow -d iotflow -c "\dt"
# ✓ Should show 8 tables

# 4. Check users exist
docker exec -it iotflow_postgres psql -U iotflow -d iotflow -c "SELECT username FROM users;"
# ✓ Should show "admin" and "test"

# 5. Test Flask connection
poetry run python -c "from app import create_app; app = create_app(); app.app_context().push(); from src.models import db; print('✓ Flask can connect to database')"

# 6. Test API health check
curl http://localhost:5000/health
# ✓ Should return {"status": "healthy"}
```

---

## 📊 Quick Reference Commands

```bash
# Connect to PostgreSQL
docker exec -it iotflow_postgres psql -U iotflow -d iotflow

# List databases
\l

# List tables
\dt

# Describe table structure
\d users

# Count records
SELECT COUNT(*) FROM users;

# Exit psql
\q

# View PostgreSQL logs
docker logs iotflow_postgres

# Restart PostgreSQL
docker restart iotflow_postgres
```

---

## 🆘 Still Having Issues?

### Check Application Logs

```bash
# Flask application logs
tail -f logs/iotflow.log

# Docker container logs
docker logs -f iotflow_connectivity
```

### Check Environment Variables

```bash
# Print all environment variables
poetry run python -c "import os; from dotenv import load_dotenv; load_dotenv(); print('DATABASE_URL:', os.getenv('DATABASE_URL'))"
```

### Test Database Connection

```bash
# Test connection with Python
poetry run python -c "
from sqlalchemy import create_engine, text
import os
from dotenv import load_dotenv

load_dotenv()
db_url = os.getenv('DATABASE_URL')
print(f'Testing connection to: {db_url}')

engine = create_engine(db_url)
with engine.connect() as conn:
    result = conn.execute(text('SELECT version()'))
    print('✓ Connection successful!')
    print(result.fetchone()[0])
"
```

---

## 📝 Summary

**Recommended approach:**

1. ✅ Use `poetry run python scripts/create_postgres_tables.py` (easiest)
2. ✅ Or use SQL script: `docker exec -i iotflow_postgres psql -U iotflow -d iotflow < scripts/create_tables.sql`
3. ✅ Verify with diagnostic commands
4. ✅ Test API: `curl http://localhost:5000/health`

**If all else fails:**
- Complete reset with `docker compose down -v`
- Start fresh with table creation script

---

**Last Updated**: 2025-01-21
