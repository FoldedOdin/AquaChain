# DynamoDB GSI Quick Reference Guide

## Overview
This guide provides quick reference for using the optimized DynamoDB GSI queries implemented in Phase 4.

## Available GSIs

### Devices Table (`aquachain-devices`)
| GSI Name | Partition Key | Sort Key | Use Case |
|----------|--------------|----------|----------|
| `user_id-created_at-index` | user_id | created_at | List all devices for a user |
| `status-last_seen-index` | status | last_seen | Find devices by status (active/inactive) |

### Readings Table (`aquachain-readings`)
| GSI Name | Partition Key | Sort Key | Use Case |
|----------|--------------|----------|----------|
| `DeviceIndex` | deviceId | timestamp | List all readings for a device |
| `device_id-metric_type-index` | deviceId | metric_type | Query specific metric (pH, turbidity) |
| `alert_level-timestamp-index` | alert_level | timestamp | Find critical/warning alerts |

### Users Table (`aquachain-users`)
| GSI Name | Partition Key | Sort Key | Use Case |
|----------|--------------|----------|----------|
| `email-index` | email | - | Look up user by email |
| `organization_id-role-index` | organization_id | role | List users in organization by role |

## Python Usage

### Import the query functions
```python
from dynamodb_queries import (
    query_devices_by_user,
    query_devices_by_status,
    query_readings_by_device_and_metric,
    query_readings_by_alert_level,
    query_user_by_email,
    query_users_by_organization_and_role
)
```

### Query devices by user
```python
result = query_devices_by_user(
    user_id='user-123',
    limit=50,
    last_key=None  # For first page
)

devices = result['items']
next_page = result['last_key']  # Use for next page
has_more = result['has_more']
duration = result['duration_ms']
```

### Query devices by status
```python
result = query_devices_by_status(
    status='active',  # or 'inactive', 'maintenance', 'offline'
    limit=100
)
```

### Query readings by metric type
```python
result = query_readings_by_device_and_metric(
    device_id='device-456',
    metric_type='pH',  # or 'turbidity', 'temperature', etc.
    limit=100
)
```

### Query readings by alert level
```python
# Without time range
result = query_readings_by_alert_level(
    alert_level='critical',  # or 'warning', 'normal', 'info'
    limit=100
)

# With time range
result = query_readings_by_alert_level(
    alert_level='critical',
    start_time='2025-10-25T00:00:00Z',
    end_time='2025-10-25T23:59:59Z',
    limit=100
)
```

### Query user by email
```python
user = query_user_by_email('user@example.com')
if user:
    print(f"User ID: {user['userId']}")
```

### Query users by organization
```python
# All users in organization
result = query_users_by_organization_and_role(
    organization_id='org-789',
    limit=100
)

# Filter by role
result = query_users_by_organization_and_role(
    organization_id='org-789',
    role='technician',  # or 'admin', 'consumer'
    limit=100
)
```

## Pagination Pattern

All list queries support pagination:

```python
def get_all_devices(user_id):
    """Example: Get all devices across multiple pages"""
    all_devices = []
    last_key = None
    
    while True:
        result = query_devices_by_user(
            user_id=user_id,
            limit=100,
            last_key=last_key
        )
        
        all_devices.extend(result['items'])
        
        if not result['has_more']:
            break
            
        last_key = result['last_key']
    
    return all_devices
```

## API Endpoints

### Device Management
```bash
# List user's devices
GET /devices/by-user?userId=user-123&limit=50&lastKey=<encoded>

# List devices by status
GET /devices/by-status?status=active&limit=100

# Get device details
GET /devices/{deviceId}

# Update device status
PUT /devices/{deviceId}/status
Body: {"status": "active"}
```

### Readings Query
```bash
# Query by metric type
GET /readings/by-metric?deviceId=device-456&metricType=pH&limit=100

# Query by alert level
GET /readings/by-alert-level?alertLevel=critical&startTime=2025-10-25T00:00:00Z

# Get recent critical alerts
GET /readings/critical-alerts?hours=24
```

### User Management
```bash
# Look up user by email
GET /users/by-email?email=user@example.com

# List organization users
GET /users/by-organization?organizationId=org-789&role=technician&limit=100
```

## Performance Monitoring

### Automatic Logging
All queries automatically log:
- Query duration in milliseconds
- Number of items returned
- Warning if duration exceeds 500ms

### CloudWatch Metrics
View metrics in CloudWatch:
- Namespace: `AquaChain/DynamoDB`
- Metrics: `QueryDuration`, `ItemCount`, `SlowQueryCount`

### CloudWatch Dashboard
Access the dashboard:
- Dashboard name: `AquaChain-Query-Performance`
- Shows real-time query performance

### CloudWatch Alarms
Alarms trigger when:
- Average query duration > 500ms (2 periods)
- Slow query count > 10 (in 5 minutes)
- GSI throttling detected

## Best Practices

### 1. Always use pagination for list operations
```python
# ✅ Good - with pagination
result = query_devices_by_user(user_id='user-123', limit=100)

# ❌ Bad - trying to get all at once
result = query_devices_by_user(user_id='user-123', limit=10000)
```

### 2. Use appropriate page sizes
- Small screens/mobile: limit=20-50
- Desktop dashboards: limit=50-100
- Background processing: limit=100-500

### 3. Handle pagination tokens properly
```python
# ✅ Good - encode/decode pagination tokens
import base64
import json

# Encode for API response
if result.get('last_key'):
    encoded_key = base64.b64encode(
        json.dumps(result['last_key']).encode()
    ).decode()

# Decode from API request
if last_key_param:
    last_key = json.loads(base64.b64decode(last_key_param))
```

### 4. Use time ranges for alert queries
```python
# ✅ Good - limit time range
result = query_readings_by_alert_level(
    alert_level='critical',
    start_time='2025-10-25T00:00:00Z',
    end_time='2025-10-25T23:59:59Z'
)

# ⚠️ Caution - unbounded query
result = query_readings_by_alert_level(alert_level='critical')
```

### 5. Monitor query performance
```python
from query_performance_monitor import track_query_performance

@track_query_performance('my_custom_query')
def my_query_function():
    # Your query logic
    pass
```

## Common Patterns

### Pattern 1: User Dashboard
```python
def get_user_dashboard_data(user_id):
    """Get all data for user dashboard"""
    # Get user's devices
    devices = query_devices_by_user(user_id, limit=10)
    
    # Get recent critical alerts for user's devices
    alerts = []
    for device in devices['items']:
        device_alerts = query_readings_by_alert_level(
            alert_level='critical',
            limit=5
        )
        alerts.extend(device_alerts['items'])
    
    return {
        'devices': devices['items'],
        'critical_alerts': alerts[:10]
    }
```

### Pattern 2: Admin Monitoring
```python
def get_system_health():
    """Get system-wide health metrics"""
    # Get all active devices
    active = query_devices_by_status('active', limit=1000)
    
    # Get all inactive devices
    inactive = query_devices_by_status('inactive', limit=1000)
    
    # Get recent critical alerts
    alerts = query_readings_by_alert_level(
        alert_level='critical',
        start_time=(datetime.utcnow() - timedelta(hours=24)).isoformat()
    )
    
    return {
        'active_devices': len(active['items']),
        'inactive_devices': len(inactive['items']),
        'critical_alerts_24h': len(alerts['items'])
    }
```

### Pattern 3: Metric Analysis
```python
def analyze_device_metric(device_id, metric_type, days=7):
    """Analyze specific metric over time"""
    start_time = (datetime.utcnow() - timedelta(days=days)).isoformat()
    
    result = query_readings_by_device_and_metric(
        device_id=device_id,
        metric_type=metric_type,
        limit=1000
    )
    
    readings = result['items']
    
    # Calculate statistics
    values = [r['value'] for r in readings]
    return {
        'count': len(values),
        'average': sum(values) / len(values) if values else 0,
        'min': min(values) if values else 0,
        'max': max(values) if values else 0
    }
```

## Troubleshooting

### Query is slow (>500ms)
1. Check CloudWatch metrics for the specific operation
2. Verify you're using the correct GSI
3. Reduce page size (limit parameter)
4. Add time range filters where applicable
5. Check for GSI throttling in CloudWatch

### Getting throttled
1. Check CloudWatch alarms for throttling events
2. Consider switching to provisioned capacity
3. Reduce query frequency
4. Implement exponential backoff retry logic

### Pagination not working
1. Verify last_key is properly encoded/decoded
2. Check that last_key structure matches table schema
3. Ensure last_key includes all key attributes

### No results returned
1. Verify partition key value exists in table
2. Check sort key range if using range queries
3. Verify GSI has been fully built (check table status)
4. Check CloudWatch logs for errors

## Migration from Scan Operations

### Before (Scan)
```python
# ❌ Inefficient scan operation
response = table.scan(
    FilterExpression=Attr('user_id').eq(user_id)
)
devices = response['Items']
```

### After (GSI Query)
```python
# ✅ Efficient GSI query
result = query_devices_by_user(user_id=user_id)
devices = result['items']
```

### Performance Comparison
| Operation | Scan | GSI Query | Improvement |
|-----------|------|-----------|-------------|
| Latency | 2-5s | 50-100ms | 20-50x faster |
| RCU Cost | High | Low | 10-20x cheaper |
| Scalability | Poor | Excellent | Unlimited |

## Support

For issues or questions:
1. Check CloudWatch logs for error details
2. Review CloudWatch metrics for performance data
3. Check CloudWatch alarms for system issues
4. Consult the full implementation summary: `TASK_9_GSI_OPTIMIZATION_SUMMARY.md`
