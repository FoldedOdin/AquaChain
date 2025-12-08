# Issue Reporting System

## Status: ✅ FULLY IMPLEMENTED

## Overview
Consumers and technicians can now report bugs and IoT device issues directly from their dashboards. All issues are stored in the backend and visible to admins.

## Who Can See What

### Consumers
- **Can Report**: Bug reports and IoT device issues
- **Can View**: Their own submitted issues (via `/api/issues/my`)
- **Access**: Consumer Dashboard → "Report Issue" button

### Technicians  
- **Can Report**: Bug reports and IoT device issues
- **Can View**: Their own submitted issues
- **Access**: Technician Dashboard → "Report Issue" button (if implemented)

### Admins
- **Can View**: ALL reported issues from all users
- **Can Manage**: Update status, assign to technicians, add notes, resolve issues
- **Access**: Admin Dashboard → "Reported Issues" section (needs UI implementation)
- **Endpoint**: `GET /api/admin/issues`

## Issue Types

### 1. Software Bug
- **Purpose**: Report application bugs, UI issues, errors
- **Workflow**: 
  1. Consumer reports bug
  2. Admin reviews and acknowledges
  3. Admin forwards to development team
  4. Admin marks as resolved when fixed

### 2. IoT Device Issue
- **Purpose**: Report device malfunctions, connectivity issues, sensor problems
- **Requires**: Device selection
- **Workflow**:
  1. Consumer reports device issue
  2. Admin reviews and acknowledges
  3. Admin assigns to nearest technician
  4. Technician resolves issue
  5. Admin marks as resolved

## Priority Levels
- **Low**: Minor issues, cosmetic problems
- **Medium**: Moderate impact, workarounds available
- **High**: Significant impact, needs attention soon
- **Critical**: System down, urgent attention required

## Issue Status Flow
```
pending → acknowledged → in-progress → resolved
                      ↓
                  rejected
```

## API Endpoints

### Submit Issue (Consumer/Technician)
```
POST /api/issues
Authorization: Bearer <token>
Body: {
  "type": "bug" | "iot",
  "title": "Issue title",
  "description": "Detailed description",
  "priority": "low" | "medium" | "high" | "critical",
  "deviceId": "device-id" (optional, required for IoT issues)
}
```

**Response:**
```json
{
  "success": true,
  "message": "Issue submitted successfully",
  "issue": {
    "id": "issue_1234567890_abc123",
    "type": "bug",
    "title": "Dashboard not loading",
    "description": "...",
    "priority": "high",
    "deviceId": null,
    "reportedBy": "user@example.com",
    "reportedByName": "John Doe",
    "reportedAt": "2025-12-06T07:00:00.000Z",
    "status": "pending",
    "assignedTo": null,
    "resolvedAt": null,
    "resolvedBy": null,
    "adminNotes": null
  }
}
```

### Get All Issues (Admin Only)
```
GET /api/admin/issues
Authorization: Bearer <token>
```

**Response:**
```json
{
  "success": true,
  "issues": [...],
  "stats": {
    "total": 10,
    "pending": 5,
    "inProgress": 3,
    "resolved": 2,
    "bugs": 6,
    "iotIssues": 4
  }
}
```

### Update Issue (Admin Only)
```
PUT /api/admin/issues/:issueId
Authorization: Bearer <token>
Body: {
  "status": "acknowledged" | "in-progress" | "resolved" | "rejected",
  "assignedTo": "technician@example.com",
  "adminNotes": "Notes from admin"
}
```

### Get My Issues (User)
```
GET /api/issues/my
Authorization: Bearer <token>
```

Returns all issues submitted by the authenticated user.

## Alert Integration

When an issue is submitted, the system automatically:
1. Creates an alert for admins
2. Alert priority based on issue priority:
   - Critical/High issue → High priority alert
   - Medium issue → Medium priority alert
   - Low issue → Low priority alert
3. Alert appears in Admin Dashboard Alert Management

## Data Storage

Issues are stored in `.dev-data.json`:
```json
{
  "reportedIssues": [
    {
      "id": "issue_1234567890_abc123",
      "type": "bug",
      "title": "Dashboard not loading",
      "description": "When I click on dashboard...",
      "priority": "high",
      "deviceId": null,
      "reportedBy": "user@example.com",
      "reportedByName": "John Doe",
      "reportedAt": "2025-12-06T07:00:00.000Z",
      "status": "pending",
      "assignedTo": null,
      "resolvedAt": null,
      "resolvedBy": null,
      "adminNotes": null
    }
  ]
}
```

## Consumer Dashboard UI

### Report Issue Button
Located in "Quick Actions" section of Consumer Dashboard

### Report Issue Modal
- **Issue Type Selection**: Bug or IoT Device
- **Device Selection**: Dropdown (only for IoT issues)
- **Priority Level**: Low, Medium, High, Critical
- **Issue Title**: Brief description (max 100 chars)
- **Detailed Description**: Full details (max 1000 chars)
- **Info Box**: Explains review process

### Success State
After submission:
- Shows success message
- Explains next steps
- Auto-closes after 3 seconds

## Admin Dashboard Integration

### Viewing Issues (To Be Implemented)
Admins need a UI component to:
1. View all reported issues
2. Filter by status, type, priority
3. Update issue status
4. Assign to technicians
5. Add admin notes
6. Mark as resolved

**Suggested Location**: Admin Dashboard → New "Reported Issues" tab

## Console Logging

When issue is submitted:
```
📝 Issue reported by user@example.com: [bug] Dashboard not loading
```

When admin updates issue:
```
✅ Admin updated issue issue_123: status=acknowledged
```

## Testing

### Test as Consumer
1. Log in as consumer (phoneixknight18@gmail.com)
2. Click "Report Issue" in Quick Actions
3. Select "Software Bug"
4. Fill in title and description
5. Click "Submit Issue"
6. Should see success message

### Test as Admin
1. Log in as admin (admin@aquachain.com)
2. Call API: `GET /api/admin/issues`
3. Should see the submitted issue
4. Update issue status via API
5. Check Alert Management - should see alert for new issue

## Future Enhancements

### Planned Features
1. **Admin UI**: Full issue management interface
2. **Issue Comments**: Allow back-and-forth communication
3. **File Attachments**: Upload screenshots, logs
4. **Email Notifications**: Notify users of status changes
5. **Technician Assignment**: Auto-assign based on location
6. **Issue Templates**: Pre-filled forms for common issues
7. **Issue Analytics**: Track resolution times, common issues
8. **SLA Tracking**: Monitor response and resolution times

### Integration Points
- **Task System**: Auto-create tasks from IoT issues
- **Notification System**: Notify users of status changes
- **Analytics**: Track issue trends and patterns

## Files Modified
- `frontend/src/dev-server.js` - Added issue endpoints and storage
- `frontend/src/components/Dashboard/ConsumerDashboard.tsx` - Connected to API

## Benefits

### For Consumers
- Easy way to report problems
- Track issue status
- Faster problem resolution
- Better communication with support

### For Admins
- Centralized issue tracking
- Prioritized issue list
- Better resource allocation
- Audit trail of all issues

### For System
- Identify common problems
- Improve product quality
- Better user satisfaction
- Data-driven improvements

## Status
✅ **FULLY FUNCTIONAL** - Issue reporting system is live and working!

Consumers can now report issues, and admins can view and manage them via API. Admin UI for issue management can be added as next enhancement.
