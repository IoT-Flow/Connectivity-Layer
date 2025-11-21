#!/bin/bash
# Quick fix script for PostgreSQL table creation issues

set -e

# Colors
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m' # No Color

echo -e "${BLUE}============================================================${NC}"
echo -e "${BLUE}IoTFlow Database Fix Script${NC}"
echo -e "${BLUE}============================================================${NC}"

# Check if PostgreSQL container is running
echo -e "\n${YELLOW}[1/5] Checking PostgreSQL container...${NC}"
if docker ps | grep -q iotflow_postgres; then
    echo -e "${GREEN}✓ PostgreSQL container is running${NC}"
else
    echo -e "${RED}✗ PostgreSQL container is not running${NC}"
    echo -e "${YELLOW}Starting PostgreSQL...${NC}"
    docker compose up -d postgres
    echo -e "${YELLOW}Waiting for PostgreSQL to be ready...${NC}"
    sleep 10
fi

# Check database exists
echo -e "\n${YELLOW}[2/5] Checking database exists...${NC}"
if docker exec iotflow_postgres psql -U iotflow -lqt | cut -d \| -f 1 | grep -qw iotflow; then
    echo -e "${GREEN}✓ Database 'iotflow' exists${NC}"
else
    echo -e "${RED}✗ Database 'iotflow' does not exist${NC}"
    echo -e "${YELLOW}Creating database...${NC}"
    docker exec iotflow_postgres psql -U postgres -c "CREATE DATABASE iotflow;"
    docker exec iotflow_postgres psql -U postgres -c "GRANT ALL PRIVILEGES ON DATABASE iotflow TO iotflow;"
    echo -e "${GREEN}✓ Database created${NC}"
fi

# Check tables exist
echo -e "\n${YELLOW}[3/5] Checking tables...${NC}"
TABLE_COUNT=$(docker exec iotflow_postgres psql -U iotflow -d iotflow -t -c "SELECT COUNT(*) FROM information_schema.tables WHERE table_schema = 'public';" | xargs)

if [ "$TABLE_COUNT" -eq "0" ]; then
    echo -e "${YELLOW}⚠ No tables found. Creating tables...${NC}"
    
    # Try Python script first
    if command -v poetry &> /dev/null; then
        echo -e "${BLUE}Using Python script to create tables...${NC}"
        poetry run python scripts/create_postgres_tables.py
    else
        echo -e "${YELLOW}Poetry not found. Using SQL script...${NC}"
        docker exec -i iotflow_postgres psql -U iotflow -d iotflow < scripts/create_tables.sql
    fi
    
    echo -e "${GREEN}✓ Tables created${NC}"
elif [ "$TABLE_COUNT" -lt "8" ]; then
    echo -e "${YELLOW}⚠ Found $TABLE_COUNT tables (expected 8)${NC}"
    echo -e "${YELLOW}Some tables may be missing. Recreating...${NC}"
    
    if command -v poetry &> /dev/null; then
        poetry run python scripts/create_postgres_tables.py
    else
        docker exec -i iotflow_postgres psql -U iotflow -d iotflow < scripts/create_tables.sql
    fi
else
    echo -e "${GREEN}✓ Found $TABLE_COUNT tables${NC}"
fi

# Verify tables
echo -e "\n${YELLOW}[4/5] Verifying tables...${NC}"
TABLES=$(docker exec iotflow_postgres psql -U iotflow -d iotflow -t -c "SELECT table_name FROM information_schema.tables WHERE table_schema = 'public' ORDER BY table_name;")

echo -e "${GREEN}Tables in database:${NC}"
echo "$TABLES" | while read -r table; do
    if [ ! -z "$table" ]; then
        echo -e "  ${GREEN}✓${NC} $table"
    fi
done

# Check users
echo -e "\n${YELLOW}[5/5] Checking users...${NC}"
USER_COUNT=$(docker exec iotflow_postgres psql -U iotflow -d iotflow -t -c "SELECT COUNT(*) FROM users;" 2>/dev/null | xargs || echo "0")

if [ "$USER_COUNT" -eq "0" ]; then
    echo -e "${YELLOW}⚠ No users found. Creating admin user...${NC}"
    
    if command -v poetry &> /dev/null; then
        poetry run python -c "
from app import create_app
from src.models import db, User
from werkzeug.security import generate_password_hash

app = create_app()
with app.app_context():
    admin = User(
        user_id='dcf1a',
        username='admin',
        email='admin@iotflow.local',
        password_hash=generate_password_hash('admin123'),
        is_admin=True
    )
    db.session.add(admin)
    db.session.commit()
    print('✓ Admin user created')
"
    fi
else
    echo -e "${GREEN}✓ Found $USER_COUNT users${NC}"
fi

# Final verification
echo -e "\n${BLUE}============================================================${NC}"
echo -e "${BLUE}Final Verification${NC}"
echo -e "${BLUE}============================================================${NC}"

# Test database connection
echo -e "\n${YELLOW}Testing database connection...${NC}"
if docker exec iotflow_postgres psql -U iotflow -d iotflow -c "SELECT 1;" > /dev/null 2>&1; then
    echo -e "${GREEN}✓ Database connection successful${NC}"
else
    echo -e "${RED}✗ Database connection failed${NC}"
    exit 1
fi

# Count tables
FINAL_TABLE_COUNT=$(docker exec iotflow_postgres psql -U iotflow -d iotflow -t -c "SELECT COUNT(*) FROM information_schema.tables WHERE table_schema = 'public';" | xargs)
echo -e "${GREEN}✓ Total tables: $FINAL_TABLE_COUNT${NC}"

# Count users
FINAL_USER_COUNT=$(docker exec iotflow_postgres psql -U iotflow -d iotflow -t -c "SELECT COUNT(*) FROM users;" 2>/dev/null | xargs || echo "0")
echo -e "${GREEN}✓ Total users: $FINAL_USER_COUNT${NC}"

# Display credentials
if [ "$FINAL_USER_COUNT" -gt "0" ]; then
    echo -e "\n${BLUE}============================================================${NC}"
    echo -e "${BLUE}Admin Credentials${NC}"
    echo -e "${BLUE}============================================================${NC}"
    echo -e "${GREEN}Username:${NC} admin"
    echo -e "${GREEN}Password:${NC} admin123"
    echo -e "${GREEN}Email:${NC} admin@iotflow.local"
    echo -e "${GREEN}User ID:${NC} dcf1a"
fi

echo -e "\n${BLUE}============================================================${NC}"
echo -e "${GREEN}✅ Database setup completed successfully!${NC}"
echo -e "${BLUE}============================================================${NC}"

echo -e "\n${YELLOW}Next steps:${NC}"
echo -e "  1. Start the Flask application:"
echo -e "     ${BLUE}poetry run python app.py${NC}"
echo -e "  2. Test the API:"
echo -e "     ${BLUE}curl http://localhost:5000/health${NC}"
echo -e "  3. Register a device:"
echo -e "     ${BLUE}curl -X POST http://localhost:5000/api/v1/devices/register \\${NC}"
echo -e "     ${BLUE}  -H 'Content-Type: application/json' \\${NC}"
echo -e "     ${BLUE}  -d '{\"name\":\"TestDevice\",\"device_type\":\"sensor\",\"user_id\":\"dcf1a\"}'${NC}"

echo ""
