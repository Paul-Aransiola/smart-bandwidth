# Bandwidth Threshold Monitoring & Auto-Deactivation

## Overview

The bandwidth threshold monitoring system allows you to set usage limits for devices and automatically deactivate them when they exceed these thresholds. Admin users receive alerts whenever a device breaches its configured threshold.

You can configure thresholds at two levels:

- **Global threshold**: A system-wide default that applies to all devices without individual thresholds
- **Per-device thresholds**: Custom limits for specific devices that override the global threshold

## Features

- **Global and per-device bandwidth thresholds**: Set a system-wide default or custom limits in Mbps for each device
- **Priority-based threshold application**: Device-specific thresholds override global settings
- **Configurable time windows**: Monitor bandwidth usage over 1-1440 minute periods
- **Auto-deactivation**: Automatically block devices that exceed thresholds
- **Admin notifications**: Real-time alerts sent to all admin users via WebSocket and email
- **Breach tracking**: Track how many times each device has breached its threshold
- **Manual reactivation**: Admins can re-enable deactivated devices

## Threshold Priority

The system applies thresholds in the following priority order:

1. **Individual device threshold** (if configured)
2. **Global threshold** (if configured and device has no individual threshold)
3. **No threshold** (device is not monitored)

This allows you to set a global default for most devices while still having the flexibility to customize thresholds for specific devices.

## API Endpoints

### Set Bandwidth Threshold

**`POST /api/v1/threshold/devices/{device_id}/set`**

Configure bandwidth threshold for a device.

**Parameters:**

- `device_id` (path): Device ID
- `threshold_mbps` (query): Bandwidth threshold in Mbps
- `auto_deactivate` (query, optional): Enable auto-deactivation (default: false)
- `time_window_minutes` (query, optional): Time window for evaluation (default: 5, range: 1-1440)

**Example:**

```bash
curl -X POST "http://localhost:8000/api/v1/threshold/devices/1/set?threshold_mbps=100&auto_deactivate=true&time_window_minutes=10"
```

**Response:**

```json
{
  "success": true,
  "message": "Bandwidth threshold configured: 100 Mbps",
  "data": {
    "device_id": 1,
    "device_ip": "192.168.8.1",
    "device_hostname": "router",
    "threshold_mbps": 100,
    "auto_deactivate": true,
    "time_window_minutes": 10
  }
}
```

### Get Threshold Status

**`GET /api/v1/threshold/devices/{device_id}/status`**

Get current bandwidth usage and threshold status for a device.

**Example:**

```bash
curl "http://localhost:8000/api/v1/threshold/devices/1/status"
```

**Response:**

```json
{
  "success": true,
  "message": "Threshold status retrieved",
  "data": {
    "device_id": 1,
    "device_hostname": "router",
    "device_ip": "192.168.8.1",
    "threshold_configured": true,
    "current_usage_mbps": 45.32,
    "threshold_mbps": 100,
    "time_window_minutes": 10,
    "threshold_breached": false,
    "auto_deactivate_enabled": true,
    "breach_count": 0,
    "last_breach": null
  }
}
```

### Check Threshold Manually

**`POST /api/v1/threshold/devices/{device_id}/check`**

Trigger an immediate threshold check for a device.

**Example:**

```bash
curl -X POST "http://localhost:8000/api/v1/threshold/devices/1/check"
```

### List Devices with Thresholds

**`GET /api/v1/threshold/devices`**

Get all devices that have bandwidth thresholds configured.

**Example:**

```bash
curl "http://localhost:8000/api/v1/threshold/devices"
```

**Response:**

```json
{
  "success": true,
  "message": "Found 3 devices with thresholds configured",
  "data": {
    "devices": [
      {
        "device_id": 1,
        "ip_address": "192.168.8.1",
        "hostname": "router",
        "status": "active",
        "threshold_mbps": 100,
        "auto_deactivate": true,
        "time_window_minutes": 10,
        "breach_count": 0,
        "last_breach": null
      }
    ],
    "count": 3
  }
}
```

## Global Threshold Endpoints

### Get Global Threshold

**`GET /api/v1/threshold/global`**

Retrieve the current global threshold settings.

**Example:**

```bash
curl "http://localhost:8000/api/v1/threshold/global"
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

**`POST /api/v1/threshold/global/set`**

Configure the global bandwidth threshold that applies to all devices without individual thresholds.

**Parameters:**

- `threshold_mbps` (query): Global bandwidth threshold in Mbps
- `auto_deactivate` (query, optional): Enable auto-deactivation (default: false)
- `time_window_minutes` (query, optional): Time window for evaluation (default: 5, range: 1-1440)

**Example:**

```bash
curl -X POST "http://localhost:8000/api/v1/threshold/global/set?threshold_mbps=50&auto_deactivate=true&time_window_minutes=5"
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

**`DELETE /api/v1/threshold/global`**

Remove the global threshold settings.

**Example:**

```bash
curl -X DELETE "http://localhost:8000/api/v1/threshold/global"
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

### Remove Threshold

**`DELETE /api/v1/threshold/devices/{device_id}`**

Remove bandwidth threshold configuration from a device.

**Example:**

```bash
curl -X DELETE "http://localhost:8000/api/v1/threshold/devices/1"
```

### Reactivate Device

**`POST /api/v1/threshold/devices/{device_id}/reactivate`**

Reactivate a device that was auto-deactivated due to threshold breach.

**Parameters:**

- `reset_breach_count` (query, optional): Reset breach counter to 0 (default: false)

**Example:**

```bash
curl -X POST "http://localhost:8000/api/v1/threshold/devices/1/reactivate?reset_breach_count=true"
```

## Device Schema Updates

The Device model has been extended with the following fields:

```python
bandwidth_threshold_mbps: float | None          # Bandwidth threshold in Mbps
auto_deactivate_on_threshold: bool              # Auto-deactivate when exceeded
threshold_time_window_minutes: int              # Time window for evaluation (default: 5)
threshold_breach_count: int                     # Number of breaches
last_threshold_breach: datetime | None          # Last breach timestamp
```

Device status enum has a new value:

```python
DEACTIVATED = "deactivated"  # Auto-deactivated due to threshold breach
```

## How It Works

1. **Monitoring Service**: A background service runs every 60 seconds checking all devices
2. **Threshold Resolution**: For each device:
   - If the device has an individual threshold configured, use that
   - Otherwise, if a global threshold is configured, use the global threshold
   - Skip devices with no threshold (neither individual nor global)
3. **Bandwidth Calculation**: Calculate average bandwidth usage over the configured time window
4. **Threshold Check**: If usage exceeds the threshold:
   - Breach count is incremented
   - Last breach timestamp is recorded
   - Admin users receive notifications
   - If auto-deactivation is enabled, the device is blocked at the network level
5. **Admin Alerts**: All admin users receive real-time notifications via:
   - WebSocket broadcast (instant browser notifications)
   - Email (if configured)

## Usage Scenarios

### Scenario 1: Global Threshold Only

Set a global threshold to monitor all devices without configuring each one individually:

```bash
# Set global threshold to 100 Mbps with auto-deactivation
curl -X POST "http://localhost:8000/api/v1/threshold/global/set?threshold_mbps=100&auto_deactivate=true&time_window_minutes=10"
```

All devices without individual thresholds will now be monitored against this 100 Mbps limit.

### Scenario 2: Mixed Thresholds

Set a global threshold for most devices, but override it for specific high-bandwidth devices:

```bash
# Set global threshold to 50 Mbps
curl -X POST "http://localhost:8000/api/v1/threshold/global/set?threshold_mbps=50&auto_deactivate=true"

# Set higher threshold for server (device ID 5)
curl -X POST "http://localhost:8000/api/v1/threshold/devices/5/set?threshold_mbps=200&auto_deactivate=false"

# Set lower threshold for IoT device (device ID 12)
curl -X POST "http://localhost:8000/api/v1/threshold/devices/12/set?threshold_mbps=10&auto_deactivate=true"
```

Result:

- Device 5 (server): Uses 200 Mbps threshold, alerts only (no auto-deactivation)
- Device 12 (IoT): Uses 10 Mbps threshold with auto-deactivation
- All other devices: Use 50 Mbps global threshold with auto-deactivation

### Scenario 3: Per-Device Only

Don't set a global threshold, configure only specific devices:

```bash
# No global threshold set
# Configure only critical devices
curl -X POST "http://localhost:8000/api/v1/threshold/devices/1/set?threshold_mbps=150&auto_deactivate=true"
curl -X POST "http://localhost:8000/api/v1/threshold/devices/3/set?threshold_mbps=75&auto_deactivate=true"
```

Only devices 1 and 3 will be monitored; all other devices are not subject to threshold monitoring.

## Alert Message Format

When a threshold is breached, admins receive:

```
⚠️ BANDWIDTH THRESHOLD BREACH ALERT ⚠️

Device: router (192.168.8.1)
Current Usage: 125.50 Mbps
Threshold: 100.00 Mbps
Time Window: 10 minutes
Breach Count: 1

🚫 Device has been AUTO-DEACTIVATED

Please review device activity and take appropriate action.
```

## Example Usage Scenario

### Setup

```bash
# Set 50 Mbps threshold with auto-deactivation for a high-usage device
curl -X POST "http://localhost:8000/api/v1/threshold/devices/3/set?threshold_mbps=50&auto_deactivate=true&time_window_minutes=5"
```

### Monitoring

```bash
# Check current status
curl "http://localhost:8000/api/v1/threshold/devices/3/status"
```

### Response to Breach

When the device exceeds 50 Mbps average over 5 minutes:

1. Device status changes to `DEACTIVATED`
2. Network traffic from device is blocked
3. Admin users receive alert notification
4. Breach count increments

### Recovery

```bash
# Investigate and reactivate device
curl -X POST "http://localhost:8000/api/v1/threshold/devices/3/reactivate?reset_breach_count=true"
```

## Configuration

The threshold monitor runs with the following defaults:

- Check interval: 60 seconds
- Default time window: 5 minutes
- Time window range: 1-1440 minutes (1 minute to 24 hours)

## Best Practices

1. **Start Conservative**: Set thresholds higher than normal usage to avoid false positives
2. **Use Time Windows**: Longer time windows (10-15 minutes) provide more stable measurements
3. **Monitor Breach Counts**: High breach counts may indicate a threshold is set too low
4. **Test Before Auto-Deactivate**: Start with `auto_deactivate=false` to monitor before enabling automatic blocking
5. **Admin Account Setup**: Ensure admin users have valid email addresses for notifications

## Database Migration

The feature requires database schema changes. Run the migration:

```bash
cd /Users/admin/Documents/smart_bandwith
sqlite3 bandwidth_monitor.db < alembic/versions/bf45cc9a1e3f_add_bandwidth_threshold_fields.py
```

Or use the provided SQL directly:

```sql
ALTER TABLE devices ADD COLUMN bandwidth_threshold_mbps REAL;
ALTER TABLE devices ADD COLUMN auto_deactivate_on_threshold INTEGER NOT NULL DEFAULT 0;
ALTER TABLE devices ADD COLUMN threshold_time_window_minutes INTEGER NOT NULL DEFAULT 5;
ALTER TABLE devices ADD COLUMN threshold_breach_count INTEGER NOT NULL DEFAULT 0;
ALTER TABLE devices ADD COLUMN last_threshold_breach TIMESTAMP;
```

## Troubleshooting

### Device Not Deactivating

- Check `auto_deactivate_on_threshold` is set to `true`
- Verify device status is not already `DEACTIVATED`
- Check bandwidth usage is actually exceeding threshold
- Review time window settings

### No Admin Notifications

- Verify admin users exist in database with `role='admin'` and `is_active=true`
- Check WebSocket connection is established
- Review backend logs for notification errors

### False Positives

- Increase time window for more stable averages
- Raise threshold value
- Check for bandwidth spikes vs sustained high usage
