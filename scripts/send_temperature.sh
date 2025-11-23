#!/bin/bash

# Configuration
API_KEY="9TEKN7VGOcmYsFgjjxeL2quGR99g0JBM"
BASE_URL="http://localhost:5000"
ENDPOINT="${BASE_URL}/api/v1/telemetry"
INTERVAL=10
TOTAL_RECORDS=10

echo "======================================================================"
echo "IoTFlow Temperature Telemetry Sender"
echo "======================================================================"
echo "API Key: ${API_KEY}"
echo "Endpoint: ${ENDPOINT}"
echo "Interval: ${INTERVAL} seconds"
echo "Total Records: ${TOTAL_RECORDS}"
echo "======================================================================"

# Test server connection
echo "Testing server connection..."
if curl -s -f "${BASE_URL}/health" > /dev/null 2>&1; then
    echo "✓ Server is reachable"
else
    echo "✗ Cannot connect to server at ${BASE_URL}"
    echo "  Make sure Flask app is running: poetry run python app.py"
    exit 1
fi

# Send telemetry data
success_count=0

for i in $(seq 1 $TOTAL_RECORDS); do
    # Generate random temperature between 20.0 and 30.0
    temperature=$(awk -v min=20 -v max=30 'BEGIN{srand(); printf "%.2f", min+rand()*(max-min)}')
    
    # Get current timestamp in ISO format
    timestamp=$(date -u +"%Y-%m-%dT%H:%M:%S.%3NZ")
    
    echo ""
    echo "[${i}/${TOTAL_RECORDS}] Sending telemetry at $(date +%H:%M:%S)"
    echo "  Temperature: ${temperature}°C"
    
    # Send POST request
    response=$(curl -s -w "\n%{http_code}" -X POST "${ENDPOINT}" \
        -H "X-API-Key: ${API_KEY}" \
        -H "Content-Type: application/json" \
        -d "{
            \"data\": {
                \"temperature\": ${temperature}
            },
            \"timestamp\": \"${timestamp}\"
        }")
    
    # Extract HTTP status code (last line)
    http_code=$(echo "$response" | tail -n1)
    response_body=$(echo "$response" | sed '$d')
    
    if [ "$http_code" -eq 201 ]; then
        echo "  ✓ Success: Data stored"
        ((success_count++))
    else
        echo "  ✗ Error ${http_code}: ${response_body}"
    fi
    
    # Wait before next record (except for last one)
    if [ $i -lt $TOTAL_RECORDS ]; then
        echo "  ⏳ Waiting ${INTERVAL} seconds..."
        sleep $INTERVAL
    fi
done

# Summary
echo ""
echo "======================================================================"
echo "Summary"
echo "======================================================================"
echo "Total sent: ${TOTAL_RECORDS}"
echo "Successful: ${success_count}"
echo "Failed: $((TOTAL_RECORDS - success_count))"
echo "======================================================================"

if [ $success_count -eq $TOTAL_RECORDS ]; then
    echo "✓ All telemetry data sent successfully!"
    exit 0
else
    echo "⚠ $((TOTAL_RECORDS - success_count)) records failed"
    exit 1
fi
