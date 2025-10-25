# GDPR Data Deletion - Quick Reference Guide

## Overview
Complete GDPR-compliant data deletion system with 30-day waiting period, audit trail preservation, and comprehensive user controls.

## Key Components

### Backend Services
- **DataDeletionService**: Core deletion logic
- **deletion_handler**: Lambda handlers for API endpoints

### Frontend Components
- **DataDeletionPanel**: User interface for account deletion
- **gdprService**: API client for deletion operations

## API Endpoints

### Create Deletion Request
```bash
POST /gdpr/delete
{
  "user_id": "user-123",
  "email": "user@example.com",
  "immediate": false  # Optional, default false
}

Response (202):
{
  "request_id": "req-123",
  "status": "pending",
  "scheduled_deletion_date": "2025-11-24T12:00:00Z",
  "days_until_deletion": 30,
  "cancellation_info": "You can cancel this request within 30 days..."
}
```

### Get Deletion Status
```bash
GET /gdpr/delete/{request_id}

Response (200):
{
  "request_id": "req-123",
  "status": "pending",
  "created_at": "2025-10-25T12:00:00Z",
  "scheduled_deletion_date": "2025-11-24T12:00:00Z",
  "days_remaining": 30
}
```

### List User Deletions
```bash
GET /gdpr/deletions

Response (200):
{
  "deletions": [
    {
      "request_id": "req-123",
      "status": "pending",
      "created_at": "2025-10-25T12:00:00Z",
      "scheduled_deletion_date": "2025-11-24T12:00:00Z",
      "days_remaining": 30
    }
  ],
  "count": 1
}
```

### Cancel Deletion Request
```bash
POST /gdpr/delete/{request_id}/cancel

Response (200):
{
  "request_id": "req-123",
  "status": "cancelled",
  "message": "Your deletion request has been cancelled"
}
```

## Deletion Process

### What Gets Deleted
1. **User Profile**: Complete user record
2. **Devices**: All registered devices
3. **Sensor Readings**: All historical data
4. **Alerts**: All alert records
5. **Service Requests**: All support tickets
6. **Consent Records**: All consent preferences
7. **Cognito Account**: AWS Cognito user

### What Gets Anonymized (Not Deleted)
- **Audit Logs**: User ID replaced with `DELETED_{hash}`
  - Required for compliance (7-year retention)
  - Cannot be linked back to user
  - Maintains system audit trail

## Deletion Timeline

### Standard Deletion (30-Day Wait)
```
Day 0:  User requests deletion → Status: pending
Day 1-29: Waiting period → User can cancel
Day 30: Automatic processing → Status: processing
Day 30: Deletion complete → Status: completed
```

### Immediate Deletion (Admin/Testing)
```
Request with immediate=true → Status: processing
Immediate execution → Status: completed
```

## Frontend Usage

### Request Deletion
```typescript
import { gdprService } from './services/gdprService';

// Request deletion
const response = await gdprService.requestDataDeletion(
  userId,
  userEmail,
  false  // immediate
);

console.log(response.request_id);
console.log(response.days_until_deletion);
```

### Check Status
```typescript
// Get status
const status = await gdprService.getDeletionStatus(requestId);

console.log(status.status);
console.log(status.days_remaining);
```

### Cancel Request
```typescript
// Cancel deletion
const result = await gdprService.cancelDeletionRequest(requestId);

console.log(result.status);  // 'cancelled'
```

### List Requests
```typescript
// List all deletions
const { deletions, count } = await gdprService.listUserDeletions();

deletions.forEach(deletion => {
  console.log(deletion.request_id, deletion.status);
});
```

## Backend Usage

### DataDeletionService
```python
from data_deletion_service import DataDeletionService

service = DataDeletionService()

# Delete user data
summary = service.delete_user_data(
    user_id='user-123',
    request_id='req-123',
    user_email='user@example.com'
)

print(f"Deleted {summary['deleted_items']['devices']} devices")
print(f"Anonymized {summary['anonymized_items']['audit_logs']} logs")
```

### Lambda Handler
```python
from deletion_handler import handler

# API Gateway event
event = {
    'body': json.dumps({
        'user_id': 'user-123',
        'email': 'user@example.com'
    })
}

response = handler(event, context)
```

## Scheduled Processing

### EventBridge Configuration
```yaml
Schedule: cron(0 2 * * ? *)  # Daily at 2 AM UTC
Target: process_scheduled_deletions Lambda
```

### Manual Trigger
```python
from deletion_handler import process_scheduled_deletions

# Process pending deletions
result = process_scheduled_deletions({}, context)

print(f"Processed: {result['processed_count']}")
print(f"Failed: {result['failed_count']}")
```

## Deletion Summary Structure

```json
{
  "deletion_metadata": {
    "deletion_date": "2025-10-25T12:00:00Z",
    "user_id": "user-123",
    "request_id": "req-123",
    "format_version": "1.0"
  },
  "deleted_items": {
    "profile": 1,
    "devices": 2,
    "readings": 150,
    "alerts": 5,
    "service_requests": 3,
    "consents": 1,
    "cognito_account": 1
  },
  "anonymized_items": {
    "audit_logs": 25
  },
  "errors": []
}
```

## Status Values

- **pending**: Waiting for 30-day period
- **processing**: Currently being deleted
- **completed**: Successfully deleted
- **failed**: Deletion failed (see error_message)
- **cancelled**: User cancelled request

## Error Handling

### Common Errors
```json
{
  "error": "UNAUTHORIZED_DELETION",
  "message": "You can only delete your own data"
}

{
  "error": "INVALID_STATUS",
  "message": "Cannot cancel request with status 'processing'"
}

{
  "error": "REQUEST_NOT_FOUND",
  "message": "Deletion request not found"
}
```

## Testing

### Run Unit Tests
```bash
# Python tests
pytest tests/unit/lambda/test_gdpr_deletion.py -v

# Expected: 80%+ coverage
```

### Run Integration Tests
```bash
# Integration tests
pytest tests/integration/test_gdpr_deletion_workflow.py -v
```

### Test Scenarios
1. Create deletion request
2. Verify 30-day wait
3. Cancel request
4. Process scheduled deletions
5. Verify audit log anonymization
6. Check compliance record

## Monitoring

### CloudWatch Metrics
- Deletion requests created
- Deletions completed
- Deletions failed
- Average processing time

### CloudWatch Logs
```
[INFO] Starting GDPR data deletion
[INFO] Deleted user profile
[INFO] Deleted 2 devices
[INFO] Deleted 150 sensor readings
[INFO] Anonymized 25 audit logs
[INFO] GDPR data deletion completed successfully
```

## Security

### Authorization
- Users can only delete their own data
- JWT token validation required
- Request ownership verification

### Audit Trail
- All deletions logged
- Audit logs anonymized (not deleted)
- Compliance records stored in S3

## Compliance

### GDPR Requirements
- ✅ Right to Erasure (Article 17)
- ✅ 30-day processing window
- ✅ User notification
- ✅ Audit trail preservation
- ✅ Compliance record keeping

### Data Retention
- **User Data**: Deleted after 30 days
- **Audit Logs**: Anonymized, 7-year retention
- **Deletion Records**: Permanent in compliance bucket

## Troubleshooting

### Deletion Not Processing
1. Check EventBridge schedule is enabled
2. Verify Lambda has correct permissions
3. Check CloudWatch logs for errors
4. Verify scheduled_deletion_date is in past

### Audit Logs Not Anonymizing
1. Check audit_logs table exists
2. Verify GSI 'user_id-timestamp-index' exists
3. Check Lambda has update permissions
4. Review CloudWatch logs

### Cognito Deletion Failing
1. Verify USER_POOL_ID is configured
2. Check Lambda has admin_delete_user permission
3. Confirm user exists in Cognito
4. Check user pool region matches

## Environment Variables

```bash
# Required
USERS_TABLE=aquachain-users
DEVICES_TABLE=aquachain-devices
READINGS_TABLE=aquachain-readings
ALERTS_TABLE=aquachain-alerts
AUDIT_LOGS_TABLE=aquachain-audit-logs
SERVICE_REQUESTS_TABLE=aquachain-service-requests
USER_CONSENTS_TABLE=aquachain-user-consents
GDPR_REQUESTS_TABLE=aquachain-gdpr-requests
USER_POOL_ID=us-east-1_xxxxx
COMPLIANCE_BUCKET=aquachain-compliance
NOTIFICATION_TOPIC_ARN=arn:aws:sns:region:account:topic
```

## Quick Commands

### Create Test Deletion
```bash
curl -X POST https://api.aquachain.com/gdpr/delete \
  -H "Authorization: Bearer $TOKEN" \
  -H "Content-Type: application/json" \
  -d '{"user_id":"user-123","email":"test@example.com"}'
```

### Check Status
```bash
curl https://api.aquachain.com/gdpr/delete/req-123 \
  -H "Authorization: Bearer $TOKEN"
```

### Cancel Request
```bash
curl -X POST https://api.aquachain.com/gdpr/delete/req-123/cancel \
  -H "Authorization: Bearer $TOKEN"
```

## Support

For issues or questions:
- Check CloudWatch logs
- Review deletion summary in S3
- Contact: privacy@aquachain.com
