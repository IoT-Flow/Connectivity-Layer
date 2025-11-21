# Telemetry Table Simplified - Complete

## Summary

Successfully simplified the `telemetry_data` table to only store numeric values with 5 columns.

## New Table Structure

```sql
CREATE TABLE telemetry_data (
    id BIGSERIAL PRIMARY KEY,
    device_id INTEGER NOT NULL,
    timestamp TIMESTAMP WITH TIME ZONE NOT NULL DEFAULT NOW(),
    measurement_name VARCHAR(100) NOT NULL,
    numeric_value DOUBLE PRECISION NOT NULL
)
```

### Columns:
1. **id** - Auto-incrementing primary key
2. **device_id** - Reference to the device
3. **timestamp** - When the measurement was taken
4. **measurement_name** - Name of the measurement (e.g., "temperature", "humidity")
5. **numeric_value** - The numeric value of the measurement

### Indexes:
- `idx_telemetry_device_time` - On (device_id, timestamp DESC)
- `idx_telemetry_measurement` - On (measurement_name)
- `idx_telemetry_device_measurement_time` - On (device_id, measurement_name, timestamp DESC)

## Changes Made

### 1. Table Structure
- **Removed columns**: user_id, text_value, boolean_value, json_value, metadata, location, sensor_type, quality_flag, created_at
- **Kept columns**: id, device_id, timestamp, measurement_name, numeric_value
- **Result**: Only numeric telemetry data is stored

### 2. Service Updates (`src/services/postgres_telemetry.py`)
- Updated `_create_telemetry_table()` to create simplified table
- Updated `write_telemetry_data()` to only store numeric values (non-numeric values are skipped with a warning)
- Updated `get_device_telemetry()` to query only numeric columns
- Updated `get_device_latest_telemetry()` to query only numeric columns
- Simplified indexes

### 3. Migration
- Created `migrate_simplify_telemetry.py` script
- Old table renamed to `telemetry_data_old` (can be dropped after verification)
- Migrated 9 numeric records out of 12 total records
- Non-numeric data was not migrated

## Test Results

✅ **All tests passed:**
- Device registration: ✓
- Numeric telemetry storage: ✓
- Mixed data handling (non-numeric skipped): ✓
- Latest telemetry retrieval: ✓
- Telemetry history retrieval: ✓

### Example Test Output:
```json
{
  "count": 42.0,
  "temperature": 24.0
}
```

## Usage

### Sending Telemetry (Only Numeric Values)
```bash
curl -X POST http://localhost:5000/api/v1/telemetry \
  -H "X-API-Key: YOUR_API_KEY" \
  -H "Content-Type: application/json" \
  -d '{
    "data": {
      "temperature": 23.5,
      "humidity": 65.0,
      "pressure": 1013.25
    }
  }'
```

### What Happens to Non-Numeric Data?
Non-numeric values (strings, booleans, objects) are **automatically skipped** with a warning in the logs:
```
WARNING: Skipping non-numeric value for status: online
```

## Migration Steps

1. **Run migration script:**
   ```bash
   poetry run python migrate_simplify_telemetry.py
   ```

2. **Restart application:**
   ```bash
   poetry run python app.py
   ```

3. **Test the API:**
   ```bash
   poetry run python test_simplified_api.py
   ```

4. **Drop old table (after verification):**
   ```sql
   DROP TABLE telemetry_data_old;
   ```

## Benefits

1. **Simpler schema** - Only 5 columns instead of 12
2. **Better performance** - Smaller table size, faster queries
3. **Type safety** - Only numeric data, no type confusion
4. **Cleaner data model** - One measurement per row
5. **Easier to query** - No need to check multiple value columns

## Notes

- The old table `telemetry_data_old` is kept for backup
- Non-numeric data sent to the API is silently skipped
- All existing numeric data was migrated successfully
- Indexes are optimized for time-series queries
