# GDPR Data Export - Quick Reference Guide

## Overview

The GDPR data export feature allows users to download all their personal data in JSON format, complying with GDPR Article 20 (Right to Data Portability).

## User Flow

1. User navigates to Privacy Settings
2. Clicks "Request Data Export" button
3. System collects all user data
4. Export is uploaded to S3
5. User receives download link (valid for 7 days)
6. User downloads JSON file

## API Endpoints

### Request Data Export
```http
POST /api/gdpr/export
Authorization: Bearer {token}
Content-Type: application/json

{
  "user_id": "user-123",
  "email": "user@example.com"
}

Response:
{
  "request_id": "req-456",
  "status": "completed",
  "message": "Your data export is ready",
  "download_url": "https://s3.amazonaws.com/...",
  "expires_in_days": 7
}
```

### Get Export Status
```http
GET /api/gdpr/export/{request_id}
Authorization: Bearer {token}

Response:
{
  "request_id": "req-456",
  "status": "completed",
  "created_at": "2025-10-25T12:00:00Z",
  "completed_at": "2025-10-25T12:00:05Z",
  "download_url": "https://s3.amazonaws.com/..."
}
```

### List User Exports
```http
GET /api/gdpr/exports
Authorization: Bearer {token}

Response:
{
  "exports": [
    {
      "request_id": "req-456",
      "status": "completed",
      "created_at": "2025-10-25T12:00:00Z",
      "download_url": "https://s3.amazonaws.com/..."
    }
  ],
  "count": 1
}
```

## Export Data Structure

```json
{
  "export_metadata": {
    "export_date": "2025-10-25T12:00:00Z",
    "user_id": "user-123",
    "request_id": "req-456",
    "format_version": "1.0"
  },
  "profile": {
    "userId": "user-123",
    "email": "user@example.com",
    "name": "John Doe"
  },
  "devices": [...],
  "sensor_readings": [...],
  "alerts": [...],
  "service_requests": [...],
  "audit_logs": [...]
}
```

## Key Files

### Backend
- `lambda/gdpr_service/data_export_service.py` - Core export logic
- `lambda/gdpr_service/export_handler.py` - Lambda handlers
- `infrastructure/cdk/stacks/gdpr_compliance_stack.py` - Infrastructure

### Frontend
- `frontend/src/components/Privacy/DataExportPanel.tsx` - UI component
- `frontend/src/pages/PrivacySettings.tsx` - Settings page
- `frontend/src/services/gdprService.ts` - API service

### Tests
- `tests/unit/lambda/test_gdpr_export.py` - Unit tests
- `tests/integration/test_gdpr_export_workflow.py` - Integration tests

## Environment Variables

```bash
# Lambda
USERS_TABLE=aquachain-users
DEVICES_TABLE=aquachain-devices
READINGS_TABLE=aquachain-readings
ALERTS_TABLE=aquachain-alerts
AUDIT_LOGS_TABLE=aquachain-audit-logs
SERVICE_REQUESTS_TABLE=aquachain-service-requests
GDPR_REQUESTS_TABLE=aquachain-gdpr-requests-dev
EXPORT_BUCKET=aquachain-gdpr-exports-{account}-{region}
NOTIFICATION_TOPIC_ARN=arn:aws:sns:region:account:topic

# Frontend
REACT_APP_API_URL=https://api.aquachain.com
```

## Security Features

- ✅ JWT authentication required
- ✅ Users can only export their own data
- ✅ KMS encryption for S3 storage
- ✅ Presigned URLs with 7-day expiration
- ✅ Automatic cleanup after 30 days
- ✅ Audit logging of all export requests

## Common Operations

### Deploy Infrastructure
```bash
cd infrastructure/cdk
cdk deploy GDPRComplianceStack
```

### Run Tests
```bash
# Unit tests
pytest tests/unit/lambda/test_gdpr_export.py -v

# Integration tests
pytest tests/integration/test_gdpr_export_workflow.py -v -m integration
```

### Check Export Status
```bash
aws dynamodb get-item \
  --table-name aquachain-gdpr-requests-dev \
  --key '{"request_id": {"S": "req-456"}}'
```

### List Exports in S3
```bash
aws s3 ls s3://aquachain-gdpr-exports-{account}-{region}/gdpr-exports/
```

## Troubleshooting

### Export Fails
1. Check Lambda logs: `aws logs tail /aws/lambda/aquachain-gdpr-export`
2. Verify environment variables are set
3. Check IAM permissions for S3 and DynamoDB access
4. Verify KMS key permissions

### Download URL Expired
- URLs expire after 7 days
- Request a new export
- Exports are automatically deleted after 30 days

### Missing Data in Export
- Check table names in environment variables
- Verify GSI indexes exist on tables
- Check Lambda execution time (may timeout for large datasets)

### Frontend Not Loading Exports
- Check API endpoint configuration
- Verify CORS settings on API Gateway
- Check browser console for errors
- Verify authentication token is valid

## Performance Tips

- Exports complete in < 10 seconds for typical users
- Large datasets may require async processing (future enhancement)
- Pagination is used for sensor readings (1000 per device)
- Audit logs are limited to 1000 entries

## Compliance Notes

- ✅ GDPR Article 20 compliant
- ✅ Data provided in machine-readable format (JSON)
- ✅ Includes all personal data
- ✅ Delivered within 48 hours (currently synchronous)
- ✅ Secure delivery method
- ✅ User notification

## Next Steps

After implementing data export, consider:
1. Data deletion functionality (Task 16)
2. Consent management (Task 17)
3. Comprehensive audit logging (Task 18)
4. Compliance reporting (Task 20)

## Support

For issues or questions:
- Check logs in CloudWatch
- Review test cases for examples
- Consult TASK_15_GDPR_EXPORT_IMPLEMENTATION.md for details
- Contact: privacy@aquachain.com
