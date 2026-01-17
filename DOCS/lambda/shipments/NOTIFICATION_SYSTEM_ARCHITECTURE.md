# Shipment Notification System - Architecture Overview

## System Architecture

```
┌─────────────────────────────────────────────────────────────────────┐
│                    Shipment Lifecycle Events                         │
│  (create_shipment, webhook_handler, polling_fallback, etc.)        │
└─────────────────────────────────────────────────────────────────────┘
                              ↓
                    Updates Shipments Table
                              ↓
┌─────────────────────────────────────────────────────────────────────┐
│                  Shipments DynamoDB Table                            │
│  - Primary Key: shipment_id                                         │
│  - GSIs: order_id, tracking_number, status-created_at              │
│  - DynamoDB Streams: ENABLED (NEW_AND_OLD_IMAGES)                  │
└─────────────────────────────────────────────────────────────────────┘
                              ↓
                    Stream Event Generated
                              ↓
┌─────────────────────────────────────────────────────────────────────┐
│              DynamoDB Stream Event Source Mapping                    │
│  - Batch size: 10 records                                           │
│  - Starting position: LATEST                                        │
│  - Max retry attempts: 3                                            │
│  - Bisect batch on error: True                                      │
└─────────────────────────────────────────────────────────────────────┘
                              ↓
                    Triggers Lambda Function
                              ↓
┌─────────────────────────────────────────────────────────────────────┐
│            notification_handler Lambda Function                      │
│                                                                      │
│  1. Parse DynamoDB Stream Event                                     │
│  2. Convert DynamoDB format to Python dict                          │
│  3. Detect status change (compare old vs new)                       │
│  4. Fetch order details from DeviceOrders table                     │
│  5. Route to status-specific handler                                │
└─────────────────────────────────────────────────────────────────────┘
                              ↓
                    Status-Specific Routing
                              ↓
        ┌─────────────────────┼─────────────────────┐
        ↓                     ↓                     ↓
┌──────────────┐    ┌──────────────┐    ┌──────────────┐
│  shipment_   │    │ out_for_     │    │  delivered   │
│  created     │    │ delivery     │    │              │
└──────────────┘    └──────────────┘    └──────────────┘
        ↓                     ↓                     ↓
┌──────────────┐    ┌──────────────┐    ┌──────────────┐
│ Email        │    │ Email        │    │ Email        │
│ WebSocket    │    │ SMS          │    │ SMS          │
│              │    │ WebSocket    │    │ WebSocket    │
│              │    │              │    │ Technician   │
└──────────────┘    └──────────────┘    └──────────────┘
        ↓                     ↓                     ↓
┌─────────────────────────────────────────────────────────────────────┐
│                    Notification Delivery                             │
│                                                                      │
│  Email (SES)          SMS (SNS)          WebSocket (API Gateway)    │
│  - HTML templates     - E.164 format     - Real-time updates        │
│  - Transactional      - Transactional    - Subscription filtering   │
│  - Retry on failure   - High priority    - Stale cleanup            │
└─────────────────────────────────────────────────────────────────────┘
                              ↓
                    Stakeholders Notified
                              ↓
        ┌─────────────────────┼─────────────────────┐
        ↓                     ↓                     ↓
┌──────────────┐    ┌──────────────┐    ┌──────────────┐
│  Consumer    │    │  Technician  │    │    Admin     │
│  - Email     │    │  - WebSocket │    │  - WebSocket │
│  - SMS       │    │  - SNS       │    │  - Email     │
│  - WebSocket │    │              │    │              │
└──────────────┘    └──────────────┘    └──────────────┘
```

## Component Details

### 1. DynamoDB Streams

**Purpose**: Capture all changes to Shipments table in real-time

**Configuration**:
- Stream view type: `NEW_AND_OLD_IMAGES`
  - Provides both old and new item images
  - Enables status change detection
  - Supports idempotent processing

**Stream Record Format**:
```json
{
  "eventID": "1",
  "eventName": "MODIFY",
  "eventVersion": "1.1",
  "eventSource": "aws:dynamodb",
  "awsRegion": "us-east-1",
  "dynamodb": {
    "Keys": {
      "shipment_id": {"S": "ship_xxx"}
    },
    "NewImage": {
      "shipment_id": {"S": "ship_xxx"},
      "internal_status": {"S": "delivered"},
      ...
    },
    "OldImage": {
      "shipment_id": {"S": "ship_xxx"},
      "internal_status": {"S": "out_for_delivery"},
      ...
    },
    "SequenceNumber": "111",
    "SizeBytes": 26,
    "StreamViewType": "NEW_AND_OLD_IMAGES"
  }
}
```

### 2. Event Source Mapping

**Purpose**: Connect DynamoDB Stream to Lambda function

**Configuration**:
- **Batch size**: 10 records
  - Balances throughput and latency
  - Reduces Lambda invocations
  - Enables efficient processing

- **Starting position**: LATEST
  - Only process new records
  - Avoids reprocessing historical data
  - Suitable for real-time notifications

- **Max retry attempts**: 3
  - Automatic retry on Lambda errors
  - Prevents data loss
  - Exponential backoff between retries

- **Bisect batch on error**: True
  - Splits failed batches in half
  - Isolates problematic records
  - Improves error recovery

### 3. notification_handler Lambda

**Purpose**: Process stream events and send notifications

**Execution Flow**:
1. **Parse Event**: Extract records from DynamoDB Stream event
2. **Convert Format**: Transform DynamoDB format to Python dict
3. **Detect Changes**: Compare old and new images to find status changes
4. **Fetch Context**: Get order details from DeviceOrders table
5. **Route**: Call appropriate handler based on new status
6. **Notify**: Send notifications via multiple channels
7. **Log**: Record all actions for monitoring

**Error Handling**:
- Try-catch at every level
- Graceful degradation (notifications are non-critical)
- Detailed error logging
- No exceptions propagated to stream

**Performance**:
- Timeout: 30 seconds
- Memory: 256 MB
- Concurrent executions: Unlimited (default)
- Cold start: ~1-2 seconds

### 4. Notification Channels

#### Email (SES)

**Use Cases**:
- Detailed information
- Tracking links
- Next steps
- Professional communication

**Features**:
- HTML templates with branding
- Responsive design
- Plain text fallback
- Transactional priority

**Limitations**:
- SES sandbox mode (verify recipients)
- Sending limits (check quotas)
- Bounce/complaint handling required

#### SMS (SNS)

**Use Cases**:
- Urgent updates
- Time-sensitive notifications
- High-priority alerts

**Features**:
- E.164 phone format
- Transactional SMS type
- 160 character limit
- Global delivery

**Limitations**:
- Cost per message
- Character limits
- Opt-out requirements
- Regional restrictions

#### WebSocket (API Gateway)

**Use Cases**:
- Real-time UI updates
- Live tracking
- Instant notifications
- Dashboard updates

**Features**:
- Subscription-based filtering
- Automatic reconnection
- Stale connection cleanup
- Broadcast to multiple clients

**Limitations**:
- Connection management required
- Idle timeout (10 minutes default)
- Message size limits (128 KB)
- Connection limits per account

## Data Flow Examples

### Example 1: Shipment Created

```
1. Admin creates shipment via create_shipment Lambda
   ↓
2. Shipment record inserted into DynamoDB
   ↓
3. DynamoDB Stream generates INSERT event
   ↓
4. notification_handler Lambda triggered
   ↓
5. Status detected: shipment_created
   ↓
6. Order details fetched from DeviceOrders
   ↓
7. Notifications sent:
   - Email to consumer (tracking info)
   - WebSocket to all stakeholders
   ↓
8. Consumer receives email and sees update in dashboard
```

### Example 2: Out for Delivery

```
1. Courier webhook updates shipment status
   ↓
2. webhook_handler updates DynamoDB
   ↓
3. DynamoDB Stream generates MODIFY event
   ↓
4. notification_handler detects status change:
   old: in_transit → new: out_for_delivery
   ↓
5. Notifications sent:
   - Email to consumer (ETA)
   - SMS to consumer (urgent)
   - WebSocket to all stakeholders
   ↓
6. Consumer receives SMS and email
7. Dashboard updates in real-time
```

### Example 3: Delivered

```
1. Courier webhook confirms delivery
   ↓
2. webhook_handler updates DynamoDB
   ↓
3. DynamoDB Stream generates MODIFY event
   ↓
4. notification_handler detects status change:
   old: out_for_delivery → new: delivered
   ↓
5. Notifications sent:
   - Email to consumer (confirmation)
   - SMS to consumer (success)
   - WebSocket to all stakeholders
   - SNS to technician (ready to install)
   ↓
6. Consumer receives confirmation
7. Technician sees task is ready
8. Dashboard shows delivery complete
```

## Scalability Considerations

### Throughput

**DynamoDB Streams**:
- Handles millions of updates per second
- Automatic sharding
- No throughput limits

**Lambda**:
- Concurrent executions: 1000 (default)
- Can be increased via support ticket
- Auto-scaling based on load

**SES**:
- Sandbox: 200 emails/day
- Production: 50,000 emails/day (default)
- Can be increased via support ticket

**SNS**:
- 30,000 SMS/month (free tier)
- Pay-as-you-go beyond free tier
- No hard limits

### Cost Optimization

**DynamoDB Streams**:
- $0.02 per 100,000 read request units
- Included in DynamoDB pricing

**Lambda**:
- First 1M requests free
- $0.20 per 1M requests after
- $0.0000166667 per GB-second

**SES**:
- $0.10 per 1,000 emails

**SNS SMS**:
- $0.00645 per SMS (US)
- Varies by country

### Performance Optimization

1. **Batch Processing**: Process 10 records per Lambda invocation
2. **Parallel Execution**: Multiple Lambda instances run concurrently
3. **Efficient Queries**: Use GSIs for fast lookups
4. **Connection Pooling**: Reuse AWS SDK clients
5. **Async Operations**: Don't wait for notification delivery

## Monitoring and Alerting

### Key Metrics

1. **Lambda Invocations**: Number of times Lambda is triggered
2. **Lambda Errors**: Failed invocations
3. **Lambda Duration**: Processing time per batch
4. **Stream Iterator Age**: Lag in stream processing
5. **SES Bounces**: Failed email deliveries
6. **SNS Failures**: Failed SMS deliveries

### Recommended Alarms

```yaml
Alarms:
  - Name: HighErrorRate
    Metric: Lambda Errors
    Threshold: > 10 in 5 minutes
    Action: SNS notification to DevOps
  
  - Name: HighDuration
    Metric: Lambda Duration
    Threshold: > 10 seconds
    Action: SNS notification to DevOps
  
  - Name: StreamLag
    Metric: Iterator Age
    Threshold: > 1 hour
    Action: SNS notification to DevOps
  
  - Name: EmailBounces
    Metric: SES Bounces
    Threshold: > 5% bounce rate
    Action: SNS notification to DevOps
```

### Logging Strategy

**Structured Logging**:
```python
logger.info(
    "Sending notification",
    shipment_id=shipment_id,
    order_id=order_id,
    status=status,
    notification_type="email",
    recipient=consumer_email
)
```

**Log Levels**:
- INFO: Normal operations
- WARNING: Recoverable errors
- ERROR: Failed operations
- DEBUG: Detailed debugging (disabled in production)

## Security Considerations

### IAM Permissions

**Principle of Least Privilege**:
- Only grant required permissions
- Use resource-level restrictions
- Separate roles for different functions

**Required Permissions**:
- DynamoDB: Read from Streams and tables
- SES: Send emails
- SNS: Publish messages
- API Gateway: Manage WebSocket connections

### Data Protection

**In Transit**:
- TLS 1.3 for all API calls
- Encrypted WebSocket connections
- HTTPS for all HTTP traffic

**At Rest**:
- DynamoDB encryption enabled
- CloudWatch Logs encryption
- Secrets Manager for sensitive data

### PII Handling

**Email Addresses**:
- Stored in DeviceOrders table
- Not logged in CloudWatch
- Masked in error messages

**Phone Numbers**:
- E.164 format validation
- Not logged in CloudWatch
- Masked in error messages

## Disaster Recovery

### Backup Strategy

**DynamoDB**:
- Point-in-time recovery enabled
- Automated backups
- Cross-region replication (optional)

**Lambda**:
- Version control in Git
- Automated deployments
- Blue-green deployment strategy

### Failure Scenarios

**Scenario 1: Lambda Failure**
- Automatic retry (3 attempts)
- Exponential backoff
- Dead letter queue (optional)

**Scenario 2: SES Outage**
- Graceful degradation
- Log failed attempts
- Manual retry via CloudWatch Logs

**Scenario 3: SNS Outage**
- Graceful degradation
- Log failed attempts
- Manual retry via CloudWatch Logs

**Scenario 4: Stream Processing Lag**
- Monitor iterator age
- Scale Lambda concurrency
- Investigate slow operations

## Future Enhancements

1. **Push Notifications**: Mobile app notifications via FCM/APNS
2. **Slack Integration**: Notifications to Slack channels
3. **WhatsApp**: Notifications via WhatsApp Business API
4. **Notification Preferences**: User-configurable notification settings
5. **Delivery Reports**: Track notification delivery status
6. **A/B Testing**: Test different notification templates
7. **Localization**: Multi-language support
8. **Rich Media**: Include images and videos in notifications

## Related Documentation

- [Notification System README](./NOTIFICATION_SYSTEM_README.md)
- [Quick Start Guide](./NOTIFICATION_QUICK_START.md)
- [Task 15 Completion Summary](./TASK_15_COMPLETION_SUMMARY.md)
- [Design Document](../../.kiro/specs/shipment-tracking-automation/design.md)
- [Requirements Document](../../.kiro/specs/shipment-tracking-automation/requirements.md)
