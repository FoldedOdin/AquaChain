# GDPRRequests Table Schema Documentation

## Overview

The GDPRRequests table tracks all GDPR data subject requests (data export and deletion) in the AquaChain system. This table provides comprehensive tracking of request lifecycle, status, and outcomes to ensure compliance with GDPR requirements.

## Table Configuration

- **Table Name**: `aquachain-gdpr-requests-{environment}`
- **Billing Mode**: PAY_PER_REQUEST (on-demand)
- **Encryption**: Customer-managed KMS key
- **Point-in-Time Recovery**: Enabled
- **Stream**: NEW_AND_OLD_IMAGES (for audit trail)

## Primary Key Schema

### Partition Key
- **Attribute**: `request_id`
- **Type**: String (UUID)
- **Description**: Unique identifier for each GDPR request

### Sort Key
- **Attribute**: `created_at`
- **Type**: String (ISO 8601 timestamp)
- **Description**: Timestamp when the request was created

## Attributes

### Required Attributes

| Attribute | Type | Description |
|-----------|------|-------------|
| `request_id` | String | Unique identifier (UUID) for the request |
| `user_id` | String | ID of the user making the request |
| `request_type` | String | Type of request: `export` or `deletion` |
| `status` | String | Current status: `pending`, `processing`, `completed`, `failed` |
| `created_at` | String | ISO 8601 timestamp when request was created |
| `updated_at` | String | ISO 8601 timestamp of last update |
| `user_email` | String | Email address of the requesting user |

### Optional Attributes (Export Requests)

| Attribute | Type | Description |
|-----------|------|-------------|
| `export_url` | String | Presigned S3 URL for downloading the export (7-day expiration) |
| `completed_at` | String | ISO 8601 timestamp when export was completed |
| `export_size_bytes` | Number | Size of the export file in bytes |
| `export_s3_key` | String | S3 key where the export is stored |

### Optional Attributes (Deletion Requests)

| Attribute | Type | Description |
|-----------|------|-------------|
| `scheduled_deletion_date` | String | ISO 8601 timestamp when deletion will occur (30 days from request) |
| `immediate` | Boolean | Whether immediate deletion was requested |
| `deletion_summary` | Map | Summary of deleted items by category |
| `completed_at` | String | ISO 8601 timestamp when deletion was completed |

### Optional Attributes (Error Handling)

| Attribute | Type | Description |
|-----------|------|-------------|
| `error_message` | String | Error message if request failed |
| `error_code` | String | Error code for failed requests |
| `retry_count` | Number | Number of retry attempts |

## Global Secondary Indexes (GSIs)

### GSI 1: user_id-created_at-index

**Purpose**: Query all requests for a specific user, ordered by creation date

- **Partition Key**: `user_id` (String)
- **Sort Key**: `created_at` (String)
- **Projection**: ALL

**Use Cases**:
- List all GDPR requests for a user
- Display request history in user privacy settings
- Audit user's data access requests

**Example Query**:
```python
response = table.query(
    IndexName='user_id-created_at-index',
    KeyConditionExpression=Key('user_id').eq('user-123'),
    ScanIndexForward=False  # Most recent first
)
```

### GSI 2: status-created_at-index

**Purpose**: Query requests by status, ordered by creation date

- **Partition Key**: `status` (String)
- **Sort Key**: `created_at` (String)
- **Projection**: ALL

**Use Cases**:
- Find all pending requests for processing
- Monitor failed requests for retry
- Generate compliance reports by status
- Track processing queue

**Example Query**:
```python
# Get all pending requests
response = table.query(
    IndexName='status-created_at-index',
    KeyConditionExpression=Key('status').eq('pending')
)

# Get failed requests from last 7 days
from datetime import datetime, timedelta
seven_days_ago = (datetime.utcnow() - timedelta(days=7)).isoformat()

response = table.query(
    IndexName='status-created_at-index',
    KeyConditionExpression=Key('status').eq('failed') & 
                          Key('created_at').gt(seven_days_ago)
)
```

## Status Lifecycle

### Export Request Lifecycle

```
pending → processing → completed
                    ↓
                  failed
```

1. **pending**: Request created, waiting to be processed
2. **processing**: Export is being generated
3. **completed**: Export file ready, presigned URL available
4. **failed**: Export failed, error details recorded

### Deletion Request Lifecycle

```
pending → scheduled → processing → completed
                              ↓
                            failed
```

1. **pending**: Request created, 30-day waiting period starts
2. **scheduled**: Deletion scheduled for specific date
3. **processing**: Deletion in progress
4. **completed**: All data deleted, summary recorded
5. **failed**: Deletion failed, error details recorded

## Example Records

### Export Request Example

```json
{
  "request_id": "550e8400-e29b-41d4-a716-446655440000",
  "user_id": "user-123",
  "request_type": "export",
  "status": "completed",
  "created_at": "2025-10-25T10:30:00.000Z",
  "updated_at": "2025-10-25T10:32:15.000Z",
  "completed_at": "2025-10-25T10:32:15.000Z",
  "user_email": "user@example.com",
  "export_url": "https://s3.amazonaws.com/...",
  "export_size_bytes": 1048576,
  "export_s3_key": "gdpr-exports/user-123/2025-10-25T10:30:00.000Z.json"
}
```

### Deletion Request Example

```json
{
  "request_id": "660e8400-e29b-41d4-a716-446655440001",
  "user_id": "user-456",
  "request_type": "deletion",
  "status": "completed",
  "created_at": "2025-10-01T14:20:00.000Z",
  "updated_at": "2025-10-31T14:25:30.000Z",
  "completed_at": "2025-10-31T14:25:30.000Z",
  "scheduled_deletion_date": "2025-10-31T14:20:00.000Z",
  "immediate": false,
  "user_email": "user2@example.com",
  "deletion_summary": {
    "profile": 1,
    "devices": 3,
    "readings": 1250,
    "alerts": 45,
    "anonymized_audit_logs": 89
  }
}
```

### Failed Request Example

```json
{
  "request_id": "770e8400-e29b-41d4-a716-446655440002",
  "user_id": "user-789",
  "request_type": "export",
  "status": "failed",
  "created_at": "2025-10-25T15:00:00.000Z",
  "updated_at": "2025-10-25T15:02:30.000Z",
  "user_email": "user3@example.com",
  "error_code": "EXPORT_GENERATION_FAILED",
  "error_message": "Failed to retrieve sensor readings from DynamoDB",
  "retry_count": 3
}
```

## Access Patterns

### 1. Create New Request
```python
request_record = {
    'request_id': str(uuid.uuid4()),
    'user_id': user_id,
    'request_type': 'export',  # or 'deletion'
    'status': 'pending',
    'created_at': datetime.utcnow().isoformat(),
    'updated_at': datetime.utcnow().isoformat(),
    'user_email': user_email
}
table.put_item(Item=request_record)
```

### 2. Update Request Status
```python
table.update_item(
    Key={
        'request_id': request_id,
        'created_at': created_at
    },
    UpdateExpression='SET #status = :status, updated_at = :updated',
    ExpressionAttributeNames={'#status': 'status'},
    ExpressionAttributeValues={
        ':status': 'completed',
        ':updated': datetime.utcnow().isoformat()
    }
)
```

### 3. Get Request by ID
```python
response = table.get_item(
    Key={
        'request_id': request_id,
        'created_at': created_at
    }
)
request = response.get('Item')
```

### 4. List User's Requests
```python
response = table.query(
    IndexName='user_id-created_at-index',
    KeyConditionExpression=Key('user_id').eq(user_id),
    ScanIndexForward=False,  # Most recent first
    Limit=20
)
requests = response.get('Items', [])
```

### 5. Get Pending Requests for Processing
```python
response = table.query(
    IndexName='status-created_at-index',
    KeyConditionExpression=Key('status').eq('pending')
)
pending_requests = response.get('Items', [])
```

### 6. Monitor Failed Requests
```python
response = table.query(
    IndexName='status-created_at-index',
    KeyConditionExpression=Key('status').eq('failed')
)
failed_requests = response.get('Items', [])
```

## Compliance Requirements

This table design satisfies the following GDPR requirements:

### Requirement 10.1: Data Export
- Tracks export request status
- Stores presigned URL for secure download
- Records completion time for SLA monitoring

### Requirement 10.2: Data Deletion
- Tracks deletion request status
- Implements 30-day processing window via `scheduled_deletion_date`
- Records deletion summary for compliance

### Requirement 10.4: Processing Timeline
- `created_at` and `completed_at` timestamps enable SLA monitoring
- 30-day deletion window tracked via `scheduled_deletion_date`
- Status transitions provide audit trail

### Requirement 10.5: User Notification
- `user_email` enables notification delivery
- `export_url` provided for download notifications
- Status updates trigger notification events

## Integration with Other Services

### Export Handler
- Creates request record with status `processing`
- Updates with `export_url` and `completed` status
- Records `export_size_bytes` for monitoring

### Deletion Handler
- Creates request with `scheduled_deletion_date`
- Updates status through lifecycle: `pending` → `scheduled` → `processing` → `completed`
- Stores `deletion_summary` for compliance reporting

### Compliance Service
- Queries by status for reporting
- Aggregates completion times for SLA metrics
- Monitors failed requests for alerting

### Frontend Privacy Settings
- Queries user's requests via `user_id-created_at-index`
- Displays request history and status
- Shows download links for completed exports

## Monitoring and Alerts

### Key Metrics to Track

1. **Request Volume**
   - Total requests per day/week/month
   - Requests by type (export vs deletion)

2. **Processing Time**
   - Average time from `created_at` to `completed_at`
   - Percentage meeting SLA (48 hours for export, 30 days for deletion)

3. **Failure Rate**
   - Percentage of requests with status `failed`
   - Common error codes

4. **Queue Depth**
   - Number of requests in `pending` status
   - Number of requests in `processing` status

### CloudWatch Alarms

```python
# Alert if too many failed requests
alarm = cloudwatch.Alarm(
    alarm_name='GDPRRequestFailureRate',
    metric=cloudwatch.Metric(
        namespace='AquaChain/GDPR',
        metric_name='FailedRequests',
        statistic='Sum'
    ),
    threshold=5,
    evaluation_periods=1,
    comparison_operator=cloudwatch.ComparisonOperator.GREATER_THAN_THRESHOLD
)

# Alert if export takes too long
alarm = cloudwatch.Alarm(
    alarm_name='GDPRExportSLABreach',
    metric=cloudwatch.Metric(
        namespace='AquaChain/GDPR',
        metric_name='ExportDuration',
        statistic='Average'
    ),
    threshold=172800,  # 48 hours in seconds
    evaluation_periods=1,
    comparison_operator=cloudwatch.ComparisonOperator.GREATER_THAN_THRESHOLD
)
```

## Best Practices

1. **Always use composite key**: Both `request_id` and `created_at` required for get/update operations
2. **Update timestamps**: Always update `updated_at` when modifying records
3. **Record errors**: Store `error_code` and `error_message` for failed requests
4. **Use GSIs for queries**: Never scan the table; use appropriate GSI
5. **Monitor SLAs**: Track completion times against GDPR requirements
6. **Audit trail**: DynamoDB Streams enabled for complete audit history
7. **Retention**: Keep records indefinitely for compliance (no TTL)

## CDK Stack Reference

The table is defined in `infrastructure/cdk/stacks/gdpr_compliance_stack.py`:

```python
self.gdpr_requests_table = dynamodb.Table(
    self, "GDPRRequestsTable",
    table_name=f"aquachain-gdpr-requests-{environment}",
    partition_key=dynamodb.Attribute(
        name="request_id",
        type=dynamodb.AttributeType.STRING
    ),
    sort_key=dynamodb.Attribute(
        name="created_at",
        type=dynamodb.AttributeType.STRING
    ),
    billing_mode=dynamodb.BillingMode.PAY_PER_REQUEST,
    encryption=dynamodb.TableEncryption.CUSTOMER_MANAGED,
    encryption_key=kms_key,
    point_in_time_recovery=True,
    stream=dynamodb.StreamViewType.NEW_AND_OLD_IMAGES
)
```

## Environment Variables

Lambda functions should use the following environment variable:

```bash
GDPR_REQUESTS_TABLE=aquachain-gdpr-requests-dev
```

This is automatically set by the CDK stack during deployment.
