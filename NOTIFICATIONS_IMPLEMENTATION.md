# Notifications System - Implementation Summary

## Current Status

### Before
❌ **Hardcoded** - Notifications were static data defined in the component
❌ **Not Persistent** - Disappeared on page refresh
❌ **No API** - Couldn't be updated dynamically
❌ **Role-based only** - Same notifications for all users of same role

### After
✅ **API-Driven** - Notifications fetched from backend
✅ **Persistent** - Stored in database (dev: file, prod: DynamoDB)
✅ **Dynamic** - Can be created, updated, deleted
✅ **User-Specific** - Each user has their own notifications
✅ **Real-time Ready** - Can be pushed via WebSocket

## What Was Implemented

### 1. Frontend Service
**File**: `frontend/src/services/notificationService.ts`

**Methods**:
- `getNotifications()` - Fetch all notifications
- `markAsRead(id)` - Mark single notification as read
- `markAllAsRead()` - Mark all as read
- `deleteNotification(id)` - Remove notification
- `createNotification(data)` - Create new notification (admin)
- `getUnreadCount()` - Get count of unread notifications

### 2. Backend API Endpoints
**File**: `frontend/src/dev-server.js`

**Endpoints**:
```javascript
GET    /api/notifications              - Get user's notifications
PUT    /api/notifications/:id/read     - Mark as read
PUT    /api/notifications/read-all     - Mark all as read
DELETE /api/notifications/:id          - Delete notification
GET    /api/notifications/unread-count - Get unread count
```

### 3. Data Storage
**Development**: Stored in `.dev-data.json` file
**Production**: Will use DynamoDB table

**Structure**:
```javascript
{
  notifications: {
    "user_123": [
      {
        id: "notif_123",
        type: "success",
        title: "Water Quality Normal",
        message: "All parameters within safe ranges",
        timestamp: "2025-11-06T12:00:00Z",
        read: false,
        priority: "low",
        userId: "user_123"
      }
    ]
  }
}
```

## Notification Types

### Type: `success`
- Color: Green
- Icon: CheckCircle
- Use: Positive updates, completed actions

### Type: `info`
- Color: Blue
- Icon: InformationCircle
- Use: General information, updates

### Type: `warning`
- Color: Amber/Orange
- Icon: ExclamationTriangle
- Use: Warnings, attention needed

### Type: `error`
- Color: Red
- Icon: ExclamationTriangle
- Use: Errors, critical issues

## Priority Levels

### Low Priority
- General information
- Non-urgent updates
- Background notifications

### Medium Priority
- Important updates
- Scheduled maintenance
- Task assignments

### High Priority
- Urgent issues
- System alerts
- Critical warnings

## Default Notifications by Role

### Consumer
1. **Water Quality Normal** (success, low)
   - "All parameters are within safe ranges for your area."
2. **Maintenance Scheduled** (info, medium)
   - "Routine sensor calibration planned for tomorrow morning."

### Technician
1. **Sensor Calibration Required** (warning, high)
   - "pH sensor at Station #47 showing drift, requires immediate attention."
2. **Task Assignment** (info, medium)
   - "New maintenance task assigned for North Reservoir."

### Admin
1. **System Alert** (error, high)
   - "Backup system showing warnings, requires investigation."
2. **System Update Deployed** (success, medium)
   - "Dashboard v2.1.3 successfully deployed with enhanced security."

## Usage Examples

### Fetch Notifications
```typescript
import { notificationService } from '../services/notificationService';

const notifications = await notificationService.getNotifications();
```

### Mark as Read
```typescript
await notificationService.markAsRead('notif_123');
```

### Mark All as Read
```typescript
await notificationService.markAllAsRead();
```

### Delete Notification
```typescript
await notificationService.deleteNotification('notif_123');
```

### Get Unread Count
```typescript
const count = await notificationService.getUnreadCount();
```

## Updating NotificationCenter Component

To use the new API-driven notifications, update `NotificationCenter.tsx`:

```typescript
import { useEffect, useState } from 'react';
import { notificationService } from '../../services/notificationService';

const NotificationCenter: React.FC<NotificationCenterProps> = ({ userRole }) => {
  const [notifications, setNotifications] = useState<Notification[]>([]);
  const [isLoading, setIsLoading] = useState(true);

  // Fetch notifications on mount
  useEffect(() => {
    loadNotifications();
  }, []);

  const loadNotifications = async () => {
    try {
      setIsLoading(true);
      const data = await notificationService.getNotifications();
      setNotifications(data);
    } catch (error) {
      console.error('Failed to load notifications:', error);
    } finally {
      setIsLoading(false);
    }
  };

  const markAsRead = async (id: string) => {
    try {
      await notificationService.markAsRead(id);
      setNotifications(prev => 
        prev.map(n => n.id === id ? { ...n, read: true } : n)
      );
    } catch (error) {
      console.error('Failed to mark as read:', error);
    }
  };

  const markAllAsRead = async () => {
    try {
      await notificationService.markAllAsRead();
      setNotifications(prev => prev.map(n => ({ ...n, read: true })));
    } catch (error) {
      console.error('Failed to mark all as read:', error);
    }
  };

  const removeNotification = async (id: string) => {
    try {
      await notificationService.deleteNotification(id);
      setNotifications(prev => prev.filter(n => n.id !== id));
    } catch (error) {
      console.error('Failed to delete notification:', error);
    }
  };

  // ... rest of component
};
```

## Creating Notifications

### From Backend (Automated)
```javascript
// When water quality alert detected
const notification = {
  type: 'warning',
  title: 'Water Quality Alert',
  message: 'pH level outside safe range',
  read: false,
  priority: 'high',
  userId: 'user_123',
  deviceId: 'device_456'
};

// Add to user's notifications
const userNotifications = devNotifications.get(userId) || [];
userNotifications.push({
  id: `notif_${Date.now()}`,
  ...notification,
  timestamp: new Date().toISOString()
});
devNotifications.set(userId, userNotifications);
saveDevData();
```

### From Admin Dashboard
```typescript
// Admin creates notification for user
await notificationService.createNotification({
  type: 'info',
  title: 'System Maintenance',
  message: 'Scheduled maintenance on Sunday 2AM-4AM',
  read: false,
  priority: 'medium',
  userId: 'user_123'
});
```

## Real-Time Updates

### WebSocket Integration
To push notifications in real-time:

```javascript
// Backend: When notification created
wss.clients.forEach(client => {
  if (client.userId === notification.userId) {
    client.send(JSON.stringify({
      type: 'notification',
      data: notification
    }));
  }
});

// Frontend: Listen for notifications
const { latestUpdate } = useRealTimeUpdates('notifications');

useEffect(() => {
  if (latestUpdate?.type === 'notification') {
    setNotifications(prev => [latestUpdate.data, ...prev]);
  }
}, [latestUpdate]);
```

## Production Implementation

### DynamoDB Table Schema
```python
# Table: AquaChain-Notifications
{
  "id": "notif_123",              # Partition Key
  "userId": "user_123",           # GSI Partition Key
  "type": "success",
  "title": "Water Quality Normal",
  "message": "All parameters within safe ranges",
  "timestamp": "2025-11-06T12:00:00Z",  # GSI Sort Key
  "read": false,
  "priority": "low",
  "deviceId": "device_456",       # Optional
  "actionUrl": "/devices/456",    # Optional
  "expiresAt": 1699999999         # TTL for auto-deletion
}
```

### Lambda Function
```python
# lambda/notification_service/handler.py
import boto3
from datetime import datetime

dynamodb = boto3.resource('dynamodb')
notifications_table = dynamodb.Table('AquaChain-Notifications')

def get_notifications(event, context):
    user_id = event['requestContext']['authorizer']['claims']['sub']
    
    response = notifications_table.query(
        IndexName='UserIdIndex',
        KeyConditionExpression='userId = :userId',
        ExpressionAttributeValues={':userId': user_id},
        ScanIndexForward=False,  # Most recent first
        Limit=50
    )
    
    return {
        'statusCode': 200,
        'body': json.dumps({
            'success': True,
            'notifications': response['Items']
        })
    }
```

## Testing

### Test Notification Creation
```bash
# Login as user
# Check notifications - should see default ones

# Mark one as read
# Refresh - should still be marked as read

# Delete one
# Refresh - should be gone

# Mark all as read
# All should be marked as read
```

### Test API Endpoints
```bash
# Get notifications
curl -H "Authorization: Bearer $TOKEN" \
  http://localhost:3002/api/notifications

# Mark as read
curl -X PUT \
  -H "Authorization: Bearer $TOKEN" \
  http://localhost:3002/api/notifications/notif_123/read

# Delete notification
curl -X DELETE \
  -H "Authorization: Bearer $TOKEN" \
  http://localhost:3002/api/notifications/notif_123
```

## Benefits

### Before (Hardcoded)
- ❌ Same notifications for everyone
- ❌ Can't be updated
- ❌ Lost on refresh
- ❌ No persistence

### After (API-Driven)
- ✅ User-specific notifications
- ✅ Dynamic updates
- ✅ Persistent storage
- ✅ Can be managed
- ✅ Real-time capable
- ✅ Scalable

## Next Steps

1. **Update NotificationCenter Component**
   - Replace hardcoded data with API calls
   - Add loading states
   - Add error handling

2. **Add Notification Triggers**
   - Water quality alerts
   - Device offline alerts
   - Maintenance reminders
   - System updates

3. **Implement Real-Time Push**
   - WebSocket integration
   - Push notifications
   - Browser notifications

4. **Add Notification Preferences**
   - User settings for notification types
   - Email notifications
   - SMS notifications

5. **Production Deployment**
   - Create DynamoDB table
   - Deploy Lambda functions
   - Set up SNS/SES for email
   - Configure push notifications

## Status
✅ **Backend API Complete** - Endpoints ready for use
✅ **Service Layer Complete** - Frontend service ready
⏳ **Component Update Needed** - NotificationCenter needs to use API
⏳ **Real-Time Push** - WebSocket integration pending

---

**Date**: November 6, 2025
**Status**: API-Driven System Implemented
**Next**: Update NotificationCenter component to use API
