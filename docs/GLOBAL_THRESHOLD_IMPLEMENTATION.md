# Global Bandwidth Threshold Implementation

## Overview

The global bandwidth threshold feature has been successfully implemented, allowing administrators to set a system-wide default bandwidth threshold that applies to all devices without individual thresholds configured.

## Key Features

✅ **Global Settings Storage**: New `global_settings` table stores system-wide configuration
✅ **Priority-based Threshold Resolution**: Individual device thresholds override global settings
✅ **Automatic Application**: Global threshold applies to all active devices without individual thresholds
✅ **Complete REST API**: Full CRUD operations for managing global thresholds
✅ **Background Monitoring**: Integrated into existing 60-second monitoring cycle
✅ **Comprehensive Documentation**: Updated with usage examples and scenarios

## Implementation Details

### Database Changes

**New Table: `global_settings`**

```sql
CREATE TABLE global_settings (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    setting_key VARCHAR(255) NOT NULL UNIQUE,
    setting_value TEXT,
    setting_type VARCHAR(50) NOT NULL,
    description TEXT,
    created_at TIMESTAMP NOT NULL DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP NOT NULL DEFAULT CURRENT_TIMESTAMP
);

CREATE UNIQUE INDEX idx_global_settings_key ON global_settings(setting_key);
```

**Global Threshold Settings:**

- `global_bandwidth_threshold_mbps` (type: float)
- `global_auto_deactivate_on_threshold` (type: boolean)
- `global_threshold_time_window_minutes` (type: integer)

### Code Changes

#### New Files Created

1. **`/src/models/settings.py`**
   - `GlobalSettings` model for storing system-wide configuration
   - SQLAlchemy ORM model with key-value storage

2. **`/src/repositories/settings_repository.py`**
   - `GlobalSettingsRepository` with full CRUD operations
   - Methods: `get_by_key()`, `get_value()`, `set_value()`, `delete_by_key()`
   - Includes upsert logic for updating existing settings

3. **`/alembic/versions/c8d9f2a3b4e5_add_global_settings_table.py`**
   - Alembic migration for creating `global_settings` table
   - Includes upgrade and downgrade functions

#### Modified Files

1. **`/src/services/threshold_monitor.py`**
   - Added `GlobalSettingsRepository` import
   - Modified `_check_all_thresholds()` to:
     - Query global threshold settings from database
     - Get all active devices (not just those with individual thresholds)
     - Apply global threshold to devices without individual settings
   - Updated `_check_device_threshold()` to:
     - Accept global threshold parameters
     - Use device threshold if set, otherwise use global threshold
     - Skip devices with no threshold (neither individual nor global)
   - Modified `_deactivate_device()` to accept threshold as parameter

2. **`/src/api/routes/threshold.py`**
   - Added `GlobalSettingsRepository` import
   - Created three new endpoints:
     - `GET /api/v1/threshold/global` - Retrieve global settings
     - `POST /api/v1/threshold/global/set` - Configure global threshold
     - `DELETE /api/v1/threshold/global` - Remove global threshold
   - All endpoints include device count information

3. **`/src/main.py`**
   - Added `GlobalSettings` model import to ensure table creation

4. **`/docs/BANDWIDTH_THRESHOLD.md`**
   - Added "Global Threshold Endpoints" section
   - Updated "Overview" and "Features" sections
   - Added "Threshold Priority" explanation
   - Included three detailed usage scenarios:
     - Global threshold only
     - Mixed thresholds (global + per-device)
     - Per-device only

## API Endpoints

### Get Global Threshold Settings

```bash
GET /api/v1/threshold/global
```

**Response:**

```json
{
  "success": true,
  "message": "Global threshold settings retrieved successfully",
  "data": {
    "threshold_mbps": 50.0,
    "auto_deactivate": true,
    "time_window_minutes": 5,
    "devices_using_global_threshold": 12,
    "total_active_devices": 15
  }
}
```

### Set Global Threshold

```bash
POST /api/v1/threshold/global/set?threshold_mbps=50&auto_deactivate=true&time_window_minutes=5
```

**Response:**

```json
{
  "success": true,
  "message": "Global threshold settings updated successfully",
  "data": {
    "threshold_mbps": 50.0,
    "auto_deactivate": true,
    "time_window_minutes": 5,
    "devices_affected": 12,
    "total_active_devices": 15
  }
}
```

### Remove Global Threshold

```bash
DELETE /api/v1/threshold/global
```

**Response:**

```json
{
  "success": true,
  "message": "Global threshold settings removed successfully",
  "data": {
    "devices_previously_affected": 12
  }
}
```

## How It Works

### Threshold Resolution Logic

The monitoring service applies thresholds in the following priority order:

1. **Individual Device Threshold** (highest priority)
   - If a device has `bandwidth_threshold_mbps` set and > 0
   - Uses device's `auto_deactivate_on_threshold` setting
   - Uses device's `threshold_time_window_minutes` setting

2. **Global Threshold** (fallback)
   - If device has no individual threshold OR threshold is NULL/0
   - If global threshold is configured and > 0
   - Uses global `auto_deactivate` setting
   - Uses global `time_window_minutes` setting

3. **No Threshold** (lowest priority)
   - If neither individual nor global threshold is set
   - Device is not monitored for bandwidth usage

### Monitoring Process

Every 60 seconds, the threshold monitor:

1. Queries the `global_settings` table for global threshold configuration
2. Gets all devices with individual thresholds configured
3. If global threshold exists, gets all active devices without individual thresholds
4. For each device:
   - Resolves which threshold to use (individual or global)
   - Calculates average bandwidth over time window
   - Checks if threshold is exceeded
   - Sends alerts if breached
   - Auto-deactivates if enabled

## Usage Examples

### Example 1: Set Global Default for All Devices

```bash
# Set 100 Mbps global threshold with auto-deactivation
curl -X POST "http://localhost:8000/api/v1/threshold/global/set?threshold_mbps=100&auto_deactivate=true&time_window_minutes=10"

# All devices without individual thresholds are now monitored at 100 Mbps
```

### Example 2: Override Global for Specific Device

```bash
# Set global threshold
curl -X POST "http://localhost:8000/api/v1/threshold/global/set?threshold_mbps=50&auto_deactivate=true"

# Override for high-bandwidth server
curl -X POST "http://localhost:8000/api/v1/threshold/devices/5/set?threshold_mbps=200&auto_deactivate=false"

# Server (device 5) uses 200 Mbps, all others use 50 Mbps
```

### Example 3: Check Current Configuration

```bash
# Check global settings
curl "http://localhost:8000/api/v1/threshold/global"

# Check specific device status
curl "http://localhost:8000/api/v1/threshold/devices/5/status"

# List all devices with individual thresholds
curl "http://localhost:8000/api/v1/threshold/devices"
```

## Testing

The implementation has been successfully tested:

✅ Backend starts without errors
✅ `global_settings` table created and recognized by SQLAlchemy
✅ All imports resolve correctly
✅ Threshold monitor service starts successfully
✅ API routes registered at `/api/v1/threshold/global/*`

## Migration Path

If you're already using per-device thresholds:

1. **Existing configurations are preserved**: Individual thresholds continue to work
2. **Add global threshold gradually**: Set a global default, then remove individual thresholds for standard devices
3. **Keep overrides for special cases**: Maintain individual thresholds for servers, critical devices, or high-bandwidth users

## Benefits

1. **Reduced Configuration Overhead**: Set one global threshold instead of configuring every device
2. **Consistent Policy Enforcement**: All devices follow the same baseline threshold
3. **Flexible Exceptions**: Override global threshold for devices that need different limits
4. **Scalability**: Automatically applies to new devices without additional configuration
5. **Clear Priority System**: Easy to understand which threshold applies to each device

## Database Schema

### Global Settings Table

| Column | Type | Description |
|--------|------|-------------|
| `id` | INTEGER | Primary key |
| `setting_key` | VARCHAR(255) | Unique setting identifier (indexed) |
| `setting_value` | TEXT | Value stored as text |
| `setting_type` | VARCHAR(50) | Type: string, integer, float, boolean, json |
| `description` | TEXT | Human-readable description |
| `created_at` | TIMESTAMP | Creation timestamp |
| `updated_at` | TIMESTAMP | Last update timestamp |

### Reserved Setting Keys

- `global_bandwidth_threshold_mbps`: Global bandwidth limit in Mbps
- `global_auto_deactivate_on_threshold`: Auto-deactivation flag (true/false)
- `global_threshold_time_window_minutes`: Time window for threshold evaluation

## Future Enhancements

Possible future improvements:

- [ ] Schedule-based global thresholds (peak hours vs off-peak)
- [ ] Device group thresholds (IoT devices, servers, workstations)
- [ ] Global threshold inheritance with percentage adjustments
- [ ] Web UI for managing global thresholds
- [ ] Historical tracking of global threshold changes

## Support

For issues or questions:

- See main documentation: `/docs/BANDWIDTH_THRESHOLD.md`
- Check API docs: `http://localhost:8000/docs`
- Review logs: Threshold monitor logs all threshold checks and breaches
