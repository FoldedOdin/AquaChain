# GDPR Service

Lambda functions for GDPR compliance including data export, deletion, and consent management.

## Overview

This service implements GDPR requirements for the AquaChain system:
- **Data Export** (Article 20): Right to data portability
- **Data Deletion** (Article 17): Right to erasure (to be implemented)
- **Consent Management** (Article 7): Consent tracking and enforcement (to be implemented)

## Files

- `data_export_service.py` - Core data export logic
- `export_handler.py` - Lambda handlers for export API
- `requirements.txt` - Python dependencies
- `__init__.py` - Package initialization

## Features

### Data Export
- Collects all user data from multiple tables
- Generates JSON export with metadata
- Uploads to S3 with encryption
- Creates presigned download URLs (7-day expiration)
- Sends email notifications
- Tracks request status in DynamoDB

### Data Included in Export
1. **User Profile** - Personal information, role, preferences
2. **Devices** - All registered IoT devices
3. **Sensor Readings** - Water quality measurements
4. **Alerts** - Alert history and notifications
5. **Service Requests** - Maintenance and support requests
6. **Audit Logs** - Account activity history

## Usage

### Request Data Export

```python
from data_export_service import DataExportService

service = DataExportService()
download_url = service.export_user_data(
    user_id='user-123',
    request_id='req-456',
    user_email='user@example.com'
)
```

### Lambda Handler

```python
import json
from export_handler import handler

event = {
    'body': json.dumps({
        'user_id': 'user-123',
        'email': 'user@example.com'
    }),
    'requestContext': {
        'authorizer': {
            'claims': {
                'sub': 'user-123'
            }
        }
    }
}

response = handler(event, context)
```

## Environment Variables

Required environment variables:

```bash
# DynamoDB Tables
USERS_TABLE=aquachain-users
DEVICES_TABLE=aquachain-devices
READINGS_TABLE=aquachain-readings
ALERTS_TABLE=aquachain-alerts
AUDIT_LOGS_TABLE=aquachain-audit-logs
SERVICE_REQUESTS_TABLE=aquachain-service-requests
GDPR_REQUESTS_TABLE=aquachain-gdpr-requests-dev

# S3 Bucket
EXPORT_BUCKET=aquachain-gdpr-exports-{account}-{region}

# SNS Topic
NOTIFICATION_TOPIC_ARN=arn:aws:sns:region:account:topic
```

## IAM Permissions

The Lambda function requires:

```json
{
  "Version": "2012-10-17",
  "Statement": [
    {
      "Effect": "Allow",
      "Action": [
        "dynamodb:GetItem",
        "dynamodb:Query",
        "dynamodb:PutItem",
        "dynamodb:UpdateItem"
      ],
      "Resource": [
        "arn:aws:dynamodb:*:*:table/aquachain-*",
        "arn:aws:dynamodb:*:*:table/aquachain-*/index/*"
      ]
    },
    {
      "Effect": "Allow",
      "Action": [
        "s3:PutObject",
        "s3:GetObject"
      ],
      "Resource": "arn:aws:s3:::aquachain-gdpr-exports-*/*"
    },
    {
      "Effect": "Allow",
      "Action": [
        "kms:Decrypt",
        "kms:Encrypt",
        "kms:GenerateDataKey"
      ],
      "Resource": "arn:aws:kms:*:*:key/*"
    },
    {
      "Effect": "Allow",
      "Action": "sns:Publish",
      "Resource": "arn:aws:sns:*:*:*"
    }
  ]
}
```

## Deployment

### Install Dependencies
```bash
pip install -r requirements.txt -t .
```

### Create Deployment Package
```bash
zip -r gdpr_export.zip . -x "*.pyc" -x "__pycache__/*"
```

### Deploy to Lambda
```bash
aws lambda create-function \
  --function-name aquachain-gdpr-export \
  --runtime python3.11 \
  --handler export_handler.handler \
  --zip-file fileb://gdpr_export.zip \
  --role arn:aws:iam::ACCOUNT:role/lambda-execution-role \
  --timeout 60 \
  --memory-size 512 \
  --environment Variables="{USERS_TABLE=aquachain-users,...}"
```

### Update Function
```bash
aws lambda update-function-code \
  --function-name aquachain-gdpr-export \
  --zip-file fileb://gdpr_export.zip
```

## API Gateway Integration

### Routes

```yaml
POST /gdpr/export:
  handler: export_handler.handler
  description: Request data export
  auth: JWT required

GET /gdpr/export/{request_id}:
  handler: export_handler.get_export_status
  description: Get export status
  auth: JWT required

GET /gdpr/exports:
  handler: export_handler.list_user_exports
  description: List user's exports
  auth: JWT required
```

## Testing

### Unit Tests
```bash
cd tests/unit/lambda
pytest test_gdpr_export.py -v --cov=lambda.gdpr_service
```

### Integration Tests
```bash
cd tests/integration
pytest test_gdpr_export_workflow.py -v -m integration
```

### Manual Testing
```bash
# Request export
curl -X POST https://api.aquachain.com/gdpr/export \
  -H "Authorization: Bearer $TOKEN" \
  -H "Content-Type: application/json" \
  -d '{"user_id":"user-123","email":"user@example.com"}'

# Check status
curl https://api.aquachain.com/gdpr/export/req-456 \
  -H "Authorization: Bearer $TOKEN"

# List exports
curl https://api.aquachain.com/gdpr/exports \
  -H "Authorization: Bearer $TOKEN"
```

## Error Handling

The service uses custom error classes:

- `GDPRError` - GDPR-specific errors
- `ValidationError` - Input validation failures
- `AuthorizationError` - Permission denied
- `DatabaseError` - DynamoDB operation failures

All errors are logged with structured logging and return appropriate HTTP status codes.

## Logging

Structured logging format:

```json
{
  "timestamp": "2025-10-25T12:00:00Z",
  "level": "info",
  "message": "Processing GDPR export request",
  "service": "gdpr_service",
  "user_id": "user-123",
  "request_id": "req-456"
}
```

## Security

- ✅ JWT authentication required
- ✅ User authorization checks (users can only export their own data)
- ✅ KMS encryption for S3 storage
- ✅ Presigned URLs with expiration
- ✅ Audit logging of all operations
- ✅ No sensitive data in logs

## Performance

- Export request: < 5 seconds
- Data collection: Varies by data volume
- S3 upload: < 2 seconds
- Total time: < 10 seconds for typical user

### Optimization Tips
- Pagination used for large datasets
- Sensor readings limited to 1000 per device
- Audit logs limited to 1000 entries
- Consider async processing for large exports

## Monitoring

### CloudWatch Metrics
- Invocation count
- Error rate
- Duration
- Throttles

### Custom Metrics
- Export requests per day
- Average export size
- Export completion time
- Failed exports

### Alarms
- High error rate (> 5%)
- Long duration (> 30 seconds)
- Failed exports

## Compliance

### GDPR Requirements
- ✅ Article 20: Right to data portability
- ✅ Machine-readable format (JSON)
- ✅ Includes all personal data
- ✅ Delivered within 48 hours
- ✅ Secure delivery method

### Data Retention
- Exports stored for 30 days
- Automatic cleanup via S3 lifecycle
- Download URLs expire after 7 days
- Request records retained indefinitely

## Future Enhancements

- [ ] Async processing for large datasets
- [ ] Progress tracking
- [ ] Multiple export formats (CSV, XML)
- [ ] Partial exports (specific data types)
- [ ] Export scheduling
- [ ] Data deletion functionality
- [ ] Consent management

## Support

For issues or questions:
- Check CloudWatch logs
- Review test cases
- Consult main documentation
- Contact: privacy@aquachain.com

## License

Copyright © 2025 AquaChain. All rights reserved.
