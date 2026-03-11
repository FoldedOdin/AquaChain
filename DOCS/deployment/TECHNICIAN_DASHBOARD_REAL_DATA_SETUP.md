# Technician Dashboard Real Data Setup

## Overview

This document describes the setup completed to enable the Technician Dashboard to use actual data from DynamoDB instead of mock/fake values.

## Changes Made

### 1. API Gateway Routes Added

Added the following routes to `infrastructure/cdk/stacks/api_stack.py`:

```
GET  /api/v1/technician/tasks                    - Get assigned tasks for technician
POST /api/v1/technician/tasks/{taskId}/accept    - Accept a task assignment
PUT  /api/v1/technician/tasks/{taskId}/status    - Update task status
POST /api/v1/technician/tasks/{taskId}/notes     - Add notes to a task
POST /api/v1/technician/tasks/{taskId}/complete  - Complete a task
GET  /api/v1/technician/tasks/history            - Get task history
GET  /api/v1/technician/tasks/{taskId}/route     - Get route to task location
PUT  /api/v1/technician/location                 - Update technician location
```

All routes are protected with Cognito authentication and require the user to be in the `technicians` group.

### 2. Lambda Handler Functions Added

Added the following handler functions to `lambda/technician_service/handler.py`:

- `accept_technician_task()` - Accept a task assignment
- `update_technician_task_status()` - Update task status (en_route, in_progress, etc.)
- `add_technician_task_note()` - Add notes to a task
- `complete_technician_task()` - Complete a task with work details
- `get_technician_task_history()` - Get completed task history
- `get_task_route()` - Get route to task location
- `update_technician_location()` - Update technician's current location

### 3. Frontend Integration

The frontend is already configured to use real data:

- `frontend/src/pages/TechnicianDashboard.tsx` - Fetches tasks from API
- `frontend/src/services/technicianService.ts` - API client for technician operations
- `frontend/src/hooks/useDashboardData.ts` - Shared hook for dashboard data

## Data Flow

### Task Retrieval

1. Technician logs in and is assigned to `technicians` Cognito group
2. Frontend calls `GET /api/v1/technician/tasks`
3. Lambda handler extracts user info from JWT token
4. Queries DynamoDB `aquachain-service-requests` table for tasks assigned to technician
5. Transforms service requests to task format
6. Returns tasks with recent activity

### Task Status Updates

1. Technician updates task status (e.g., "Accept", "En Route", "In Progress")
2. Frontend calls `PUT /api/v1/technician/tasks/{taskId}/status`
3. Lambda validates status transition using `ServiceRequestManager`
4. Updates DynamoDB with new status and adds to status history
5. Sends real-time updates via WebSocket (if configured)
6. Sends notifications to consumer

### Task Completion

1. Technician completes task with work details
2. Frontend calls `POST /api/v1/technician/tasks/{taskId}/complete`
3. Lambda updates status to 'completed' with completion data
4. Stores work performed, parts used, and follow-up requirements
5. Sends completion notification to consumer
6. Schedules customer feedback request

## DynamoDB Schema

### Service Requests Table

**Table Name:** `aquachain-service-requests`

**Primary Key:** `requestId` (String)

**Attributes:**
- `requestId` - Unique service request ID (e.g., "SR-20240315103000-abc123")
- `consumerId` - Consumer who created the request
- `technicianId` - Assigned technician (if assigned)
- `deviceId` - Device requiring service
- `status` - Current status (pending, assigned, accepted, en_route, in_progress, completed, cancelled)
- `location` - Service location (latitude, longitude, address)
- `description` - Service request description
- `priority` - Priority level (low, normal, high, critical)
- `createdAt` - Creation timestamp (ISO 8601)
- `acceptedAt` - Acceptance timestamp
- `completedAt` - Completion timestamp
- `estimatedArrival` - Estimated arrival time
- `workPerformed` - Work performed details
- `partsUsed` - Parts used during service
- `notes` - Array of notes (technician notes, customer feedback)
- `statusHistory` - Array of status changes with timestamps

**Status Flow:**
```
pending → assigned → accepted → en_route → in_progress → completed
                                                        ↘ cancelled
```

## Testing

### 1. Create Test Service Request

```bash
# Create a test service request as a consumer
curl -X POST https://api.aquachain.example.com/api/v1/service-requests \
  -H "Authorization: Bearer <CONSUMER_TOKEN>" \
  -H "Content-Type: application/json" \
  -d '{
    "deviceId": "ESP32-TEST001",
    "location": {
      "latitude": 12.9716,
      "longitude": 77.5946,
      "address": "Bangalore, India"
    },
    "description": "Device calibration required",
    "priority": "normal"
  }'
```

### 2. Assign Technician (Admin)

```bash
# Assign technician to service request
curl -X PUT https://api.aquachain.example.com/api/v1/service-requests/SR-xxx/status \
  -H "Authorization: Bearer <ADMIN_TOKEN>" \
  -H "Content-Type: application/json" \
  -d '{
    "status": "assigned",
    "technicianId": "<TECHNICIAN_USER_ID>",
    "note": "Assigned to technician"
  }'
```

### 3. View Tasks (Technician)

```bash
# Get assigned tasks
curl -X GET https://api.aquachain.example.com/api/v1/technician/tasks \
  -H "Authorization: Bearer <TECHNICIAN_TOKEN>"
```

### 4. Accept Task (Technician)

```bash
# Accept task
curl -X POST https://api.aquachain.example.com/api/v1/technician/tasks/SR-xxx/accept \
  -H "Authorization: Bearer <TECHNICIAN_TOKEN>"
```

### 5. Update Task Status (Technician)

```bash
# Update to en_route
curl -X PUT https://api.aquachain.example.com/api/v1/technician/tasks/SR-xxx/status \
  -H "Authorization: Bearer <TECHNICIAN_TOKEN>" \
  -H "Content-Type: application/json" \
  -d '{
    "status": "en_route",
    "note": "On my way to customer location"
  }'
```

### 6. Complete Task (Technician)

```bash
# Complete task
curl -X POST https://api.aquachain.example.com/api/v1/technician/tasks/SR-xxx/complete \
  -H "Authorization: Bearer <TECHNICIAN_TOKEN>" \
  -H "Content-Type: application/json" \
  -d '{
    "workPerformed": "Calibrated pH sensor and replaced TDS sensor",
    "partsUsed": ["pH Sensor Calibration Kit", "TDS Sensor"],
    "followUpRequired": false
  }'
```

## Deployment

### Deploy All Changes

```bash
# Run deployment script
scripts\deployment\deploy-technician-dashboard-updates.bat dev
```

### Manual Deployment Steps

1. **Package Lambda Function:**
   ```bash
   cd lambda/technician_service
   powershell -Command "Compress-Archive -Path handler.py,*.py,requirements.txt -DestinationPath deployment.zip -Force"
   ```

2. **Update Lambda Function:**
   ```bash
   aws lambda update-function-code \
     --function-name AquaChain-Function-ServiceRequest-dev \
     --zip-file fileb://deployment.zip \
     --region ap-south-1
   ```

3. **Deploy CDK Stack:**
   ```bash
   cd infrastructure/cdk
   cdk deploy AquaChain-API-dev --require-approval never
   ```

## Verification

### 1. Check API Gateway Routes

```bash
# List API Gateway resources
aws apigateway get-resources \
  --rest-api-id <API_ID> \
  --region ap-south-1
```

### 2. Check Lambda Function

```bash
# Get Lambda function configuration
aws lambda get-function \
  --function-name AquaChain-Function-ServiceRequest-dev \
  --region ap-south-1
```

### 3. Test Frontend

1. Log in as a technician user
2. Navigate to Technician Dashboard
3. Verify tasks are displayed (or "No tasks found" if no tasks assigned)
4. Check browser console for API calls
5. Verify no errors in CloudWatch Logs

### 4. Check CloudWatch Logs

```bash
# View Lambda logs
aws logs tail /aws/lambda/AquaChain-Function-ServiceRequest-dev \
  --follow \
  --region ap-south-1
```

## Troubleshooting

### Issue: "No tasks found"

**Possible Causes:**
1. No service requests assigned to technician
2. Technician not in `technicians` Cognito group
3. Service requests table is empty

**Solution:**
1. Create test service request as consumer
2. Assign technician to service request (as admin)
3. Verify technician is in correct Cognito group

### Issue: "Access denied" error

**Possible Causes:**
1. User not authenticated
2. User not in `technicians` group
3. JWT token expired

**Solution:**
1. Log out and log back in
2. Verify user is in `technicians` Cognito group
3. Check Cognito authorizer configuration

### Issue: "404 Not Found" for API routes

**Possible Causes:**
1. API Gateway routes not deployed
2. Lambda function not updated
3. Incorrect API endpoint URL

**Solution:**
1. Redeploy CDK stack
2. Verify API Gateway resources in AWS Console
3. Check API endpoint URL in frontend `.env` file

### Issue: Lambda timeout

**Possible Causes:**
1. DynamoDB query taking too long
2. Lambda cold start
3. Network issues

**Solution:**
1. Increase Lambda timeout (currently 30 seconds)
2. Add pagination to DynamoDB queries
3. Check CloudWatch Logs for errors

## Monitoring

### CloudWatch Metrics

Monitor the following metrics:

- **Lambda Invocations:** Number of API calls
- **Lambda Duration:** Response time
- **Lambda Errors:** Error rate
- **API Gateway 4xx Errors:** Client errors
- **API Gateway 5xx Errors:** Server errors
- **DynamoDB Consumed Capacity:** Read/write capacity usage

### CloudWatch Alarms

Set up alarms for:

- Lambda error rate > 1%
- API Gateway 5xx error rate > 1%
- Lambda duration > 5 seconds (p95)
- DynamoDB throttling events

## Security Considerations

### Authentication

- All routes require Cognito JWT token
- Token must be in `Authorization: Bearer <token>` header
- Token is validated by API Gateway Cognito authorizer

### Authorization

- Only users in `technicians` group can access technician routes
- Technicians can only view/update their own assigned tasks
- Admin users can view all service requests

### Data Privacy

- PII (customer phone, email) is not exposed in task list
- Sensitive data requires additional authorization
- All API calls are logged for audit

### Rate Limiting

- API Gateway throttling: 100 requests/second (burst: 200)
- WAF rate limiting: 200 requests/minute per IP
- Lambda concurrency: 100 concurrent executions

## Next Steps

### 1. Add Real-Time Updates

- Implement WebSocket integration for live task updates
- Send push notifications when task status changes
- Update dashboard automatically without refresh

### 2. Add Location Tracking

- Integrate AWS Location Service for route calculation
- Track technician location in real-time
- Show ETA to customer

### 3. Add Photo Uploads

- Implement S3 presigned URLs for photo uploads
- Allow technicians to upload before/after photos
- Store photo URLs in service request

### 4. Add Performance Metrics

- Track technician performance (completion rate, average time)
- Calculate customer satisfaction scores
- Generate performance reports

### 5. Add Inventory Management

- Track parts used per technician
- Implement inventory checkout/return workflow
- Send low stock alerts

## References

- [Product Requirements](../DOCS/product.md)
- [Technology Stack](../DOCS/tech.md)
- [API Documentation](../DOCS/api/)
- [Lambda Handler Code](../../lambda/technician_service/handler.py)
- [Frontend Service](../../frontend/src/services/technicianService.ts)
- [CDK API Stack](../../infrastructure/cdk/stacks/api_stack.py)
