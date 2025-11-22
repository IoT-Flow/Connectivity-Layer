#!/bin/bash

# Send 10 temperature records for jmal sensor with 10-second intervals
API_KEY="kP4ZS7osJIYtQ5FVerIpqh9XqHjY4wBZ"
BASE_URL="http://localhost:5000/api/v1"
DEVICE_NAME="jmal"

echo "============================================================"
echo "📡 Sending Temperature Data for $DEVICE_NAME Sensor"
echo "============================================================"
echo "API Key: $API_KEY"
echo "Records: 10"
echo "Interval: 10 seconds"
echo "============================================================"
echo ""

SUCCESS=0
FAILED=0

# Send 10 temperature readings with 10-second intervals
for i in {1..10}; do
    # Generate realistic temperature data (18-28°C)
    TEMP=$(echo "scale=2; $RANDOM + ($RANDOM % 1000) / 100" | bc)
    
    TIMESTAMP=$(date -u +"%Y-%m-%dT%H:%M:%S.%3NZ")
    
    echo "📊 Record $i/10 - $(date '+%H:%M:%S')"
    echo "   Temperature: ${TEMP}°C"
    echo "   Timestamp: $TIMESTAMP"
    
    # Send telemetry
    RESPONSE=$(curl -s -w "\n%{http_code}" -X POST "$BASE_URL/devices/telemetry" \
        -H "X-API-Key: $API_KEY" \
        -H "Content-Type: application/json" \
        -d "{
            \"data\": {
                \"temperature\": $TEMP
            }
        }")
    
    HTTP_CODE=$(echo "$RESPONSE" | tail -n1)
    BODY=$(echo "$RESPONSE" | head -n-1)
    
    if [ "$HTTP_CODE" -eq 201 ]; then
        echo "   ✅ Success"
        ((SUCCESS++))
    else
        echo "   ❌ Failed - Status: $HTTP_CODE"
        echo "   Response: $BODY"
        ((FAILED++))
    fi
    
    echo ""
    
    # Wait 10 seconds before next record (except for the last one)
    if [ $i -lt 10 ]; then
        echo "⏳ Waiting 10 seconds..."
        echo ""
        sleep 10
    fi
done

# Summary
echo "============================================================"
echo "📈 Summary"
echo "============================================================"
echo "✅ Successful: $SUCCESS/10"
echo "❌ Failed: $FAILED/10"
echo "⏱️  Total time: ~90 seconds (9 intervals × 10 seconds)"
echo "============================================================"

if [ $SUCCESS -eq 10 ]; then
    echo "🎉 All telemetry data sent successfully!"
elif [ $SUCCESS -gt 0 ]; then
    echo "⚠️  Some records failed to send"
else
    echo "❌ All records failed. Check if:"
    echo "   - The server is running"
    echo "   - The API key is valid"
    echo "   - The device is active"
fi
