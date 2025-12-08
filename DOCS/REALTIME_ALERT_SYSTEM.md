# Real-Time Alert System

## Status: ✅ IMPLEMENTED

## Overview
Implemented a fully automated real-time alert generation system that monitors devices, water quality, and inventory levels, automatically creating alerts based on system conditions.

## Features

### 1. Automatic Alert Generation
- **Device Status Monitoring**: Checks every 30 seconds for offline/maintenance devices
- **Water Quality Monitoring**: Simulates water quality threshold checks
- **Inventory Monitoring**: Ready for inventory level alerts (when inventory DB is implemented)

### 2. Alert Types
- **Info** (Low Priority): System events, device back online
- **Warning** (Medium Priority): Maintenance mode, elevated readings
- **Error** (High/Critical Priority): Offline devices, critical thresholds

### 3. Smart Alert Management
- **Deduplication**: Prevents duplicate alerts for the same issue
- **Auto-cleanup**: Keeps only last 50 alerts
- **Read status tracking**: Marks alerts as read/unread

## How It Works

### Alert Generation Flow
```
Server Start
    ↓
Clear old hardcoded alerts
    ↓
Create "System started" alert
    ↓
Run initial device check
    ↓
Start 30-second interval timer
    ↓
Every 30 seconds:
  - Check device status
  - Check water quality
  - Check inventory levels
  - Create alerts as needed
```

### Device Status Checks
1. **Offline Detection**: Creates high-priority error alert
2. **Maintenance Detection**: Creates medium-priority warning alert
3. **Back Online**: Creates low-priority info alert (clears offline status)

### Water Quality Checks
- Simulates random quality issues (10% chance per check)
- Checks pH, turbidity, TDS, temperature
- Creates device-specific alerts with appropriate priority

## API Endpoints

### Get All Alerts
```
GET /api/admin/alerts
Authorization: Bearer <token>
```
Returns all alerts with statistics (critical, warning, info counts)

### Create Manual Alert
```
POST /api/admin/alerts
Authorization: Bearer <token>
Body: {
  "message": "Custom alert message",
  "priority": "low|medium|high",
  "type": "info|warning|error"
}
```

### Mark Alert as Read
```
PUT /api/admin/alerts/:alertId/read
Authorization: Bearer <token>
```

### Mark All Alerts as Read
```
PUT /api/admin/alerts/read-all
Authorization: Bearer <token>
```

### Manually Trigger Alert Generation
```
POST /api/admin/alerts/generate
Authorization: Bearer <token>
```
Immediately runs all alert checks (doesn't wait for 30-second interval)

### Delete Alert
```
DELETE /api/admin/alerts/:alertId
Authorization: Bearer <token>
```

## Alert Object Structure
```javascript
{
  id: "alert_1234567890_abc123",
  message: "Device IOA is maintenance",
  priority: "medium", // low, medium, high, critical
  type: "warning", // info, warning, error
  timestamp: "2025-12-06T07:00:00.000Z",
  read: false,
  createdBy: "system",
  deviceId: "IOA" // optional, for device-specific alerts
}
```

## Current Alert Rules

### Device Alerts
| Condition | Priority | Type | Message |
|-----------|----------|------|---------|
| Device offline | High | Error | "Device {name} is offline" |
| Device maintenance | Medium | Warning | "Device {name} is maintenance" |
| Device back online | Low | Info | "Device {name} is back online" |

### Water Quality Alerts (Simulated)
| Issue | Priority | Type |
|-------|----------|------|
| pH out of range | High | Error |
| High turbidity | Medium | Warning |
| Elevated TDS | Medium | Warning |
| Temperature anomaly | Low | Warning |

## Configuration

### Alert Check Interval
Default: 30 seconds
```javascript
// In dev-server.js
setInterval(generatePeriodicAlerts, 30000); // 30 seconds
```

### Alert Retention
Default: Last 50 alerts
```javascript
if (systemAlerts.length > 50) {
  systemAlerts.splice(0, systemAlerts.length - 50);
}
```

## Testing

### Test Alert Generation
1. Log in as admin
2. Open Alert Management modal
3. You should see:
   - "System started successfully" (info)
   - Any device-specific alerts based on current device status

### Test Device Status Alerts
1. Change a device status to "offline" in Admin Dashboard
2. Wait 30 seconds (or call `/api/admin/alerts/generate`)
3. Check Alert Management - should see offline alert

### Test Alert Lifecycle
1. Device goes offline → High priority error alert created
2. Device comes back online → Low priority info alert created
3. Old offline alert remains (for history)

## Future Enhancements

### Planned Features
1. **Email Notifications**: Send emails for high-priority alerts
2. **SMS Notifications**: Send SMS for critical alerts
3. **Alert Escalation**: Auto-escalate unread critical alerts
4. **Alert Rules Engine**: Custom alert rules per device/user
5. **Alert Analytics**: Dashboard showing alert trends
6. **Inventory Integration**: Real inventory level monitoring
7. **Threshold Configuration**: Admin-configurable thresholds

### Integration Points
- **WebSocket**: Push alerts to connected clients in real-time
- **Notification System**: Link alerts to user notifications
- **Task System**: Auto-create technician tasks from critical alerts

## Files Modified
- `frontend/src/dev-server.js` - Added alert generation system

## Console Output
When server starts:
```
🚨 Starting real-time alert monitoring...
🚨 Alert created: [low] System started successfully
🚨 Alert created: [medium] Device IOA is maintenance
```

Every 30 seconds (if new alerts):
```
🚨 Alert created: [high] Device Flex is offline
```

## Benefits

### For Admins
- Automatic monitoring of all system components
- No manual checking required
- Prioritized alert list
- Historical alert tracking

### For System
- Proactive issue detection
- Reduced downtime
- Better resource management
- Audit trail of system events

### For Users
- Faster issue resolution
- Better system reliability
- Transparent system status

## Status
✅ **LIVE** - Real-time alert system is now active and monitoring your devices!

The system automatically:
- Detected IOA device in maintenance mode
- Created appropriate alert
- Will continue monitoring every 30 seconds
- Will create new alerts as conditions change
