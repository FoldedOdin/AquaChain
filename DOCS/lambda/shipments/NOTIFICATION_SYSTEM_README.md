# Shipment Notification System

## Overview

The shipment notification system provides real-time, multi-channel notifications to stakeholders (Consumers, Technicians, and Admins) when shipment status changes occur.

## Architecture

```
┌─────────────────────────────────────────────────────────────┐
│              Shipments DynamoDB Table                        │
│  - DynamoDB Streams enabled (NEW_AND_OLD_IMAGES)            │
└─────────────────────────────────────────────────────────────┘
                              ↓
┌─────────────────────────────────────────────────────────────┐
│         Event Source Mapping (DynamoDB Stream)              │
│  - Batch size: 10 records                                   │
│  - Starting position: LATEST                                │
│  - Max retry attempts: 3                                    │
└─────────────────────────────────────────────────────────────┘
                              ↓
┌─────────────────────────────────────────────────────────────┐
│         notification_handler Lambda Function                │
│  1. Detects status changes (old vs new image)              │
│  2. Routes to appropriate notification function             │
│  3. Sends multi-channel notifications                       │
└─────────────────────────────────────────────────────────────┘
                              ↓
        ┌─────────────────────┼─────────────────────┐
        ↓                     ↓                     ↓
┌──────────────┐    ┌──────────────┐    ┌──────────────┐
│  Email (SES) │    │  SMS (SNS)   │    │  WebSocket   │
└──────────────┘    └──────────────┘    └──────────────┘
```

## Notification Channels

### 1. Email Notifications (SES)

**Shipment Created**
- Recipient: Consumer
- Content: Tracking number, courier name, estimated delivery
- Template: `format_shipment_created_email()`

**Out for Delivery**
- Recipient: Consumer
- Content: Tracking number, expected delivery time
- Template: `format_out_for_delivery_email()`

**Delivery Confirmation**
- Recipient: Consumer
- Content: Delivery timestamp, next steps for installation
- Template: `format_delivery_confirmation_email()`

**Delivery Failed**
- Recipient: Consumer
- Content: Retry count, action required, next steps
- Template: `format_delivery_failed_email()`

### 2. SMS Notifications (SNS)

**Out for Delivery**
- Recipient: Consumer
- Message: "Your AquaChain device is out for delivery! Track: {tracking_number}"

**Delivery Confirmation**
- Recipient: Consumer
- Message: "Your AquaChain device has been delivered! Installation will be scheduled soon."

### 3. WebSocket Notifications

**All Status Changes**
- Recipients: Consumer, Technician (if assigned), Admin
- Message Type: `shipment_status_update`
- Content: Full shipment details, timeline, progress
- Triggers: Real-time UI refresh

## Status-Specific Handlers

### shipment_created
- Email to Consumer with tracking info
- WebSocket update

### out_for_delivery
- Email to Consumer with ETA
- SMS to Consumer
- WebSocket update

### delivered
- Email to Consumer with delivery confirmation
- SMS to Consumer
- WebSocket update
- Notification to Technician (ready for installation)

### delivery_failed
- Email to Consumer with next steps
- WebSocket update
- Retry logic handled by webhook_handler

## Configuration

### Environment Variables

```bash
# DynamoDB Tables
ORDERS_TABLE=DeviceOrders
CONNECTIONS_TABLE=aquachain-websocket-connections

# SNS/SES Configuration
SNS_TOPIC_ARN=arn:aws:sns:region:account:topic
SES_FROM_EMAIL=noreply@aquachain.com

# WebSocket Configuration
WEBSOCKET_ENDPOINT=https://xxx.execute-api.region.amazonaws.com/prod
```

### IAM Permissions

The notification_handler Lambda requires:

```json
{
  "Version": "2012-10-17",
  "Statement": [
    {
      "Effect": "Allow",
      "Action": [
        "dynamodb:GetRecords",
        "dynamodb:GetShardIterator",
        "dynamodb:DescribeStream",
        "dynamodb:ListStreams",
        "dynamodb:GetItem",
        "dynamodb:Query",
        "dynamodb:Scan"
      ],
      "Resource": [
        "arn:aws:dynamodb:*:*:table/aquachain-shipments/stream/*",
        "arn:aws:dynamodb:*:*:table/DeviceOrders",
        "arn:aws:dynamodb:*:*:table/aquachain-websocket-connections"
      ]
    },
    {
      "Effect": "Allow",
      "Action": [
        "ses:SendEmail",
        "ses:SendRawEmail"
      ],
      "Resource": "*"
    },
    {
      "Effect": "Allow",
      "Action": [
        "sns:Publish"
      ],
      "Resource": "*"
    },
    {
      "Effect": "Allow",
      "Action": [
        "execute-api:ManageConnections"
      ],
      "Resource": "arn:aws:execute-api:*:*:*/*/POST/@connections/*"
    }
  ]
}
```

## Setup Instructions

### 1. Enable DynamoDB Streams

```bash
cd infrastructure/monitoring
python shipment_notification_stream.py
```

Or manually:

```bash
aws dynamodb update-table \
  --table-name aquachain-shipments \
  --stream-specification StreamEnabled=true,StreamViewType=NEW_AND_OLD_IMAGES
```

### 2. Deploy Lambda Function

```bash
cd lambda/shipments
zip -r notification_handler.zip notification_handler.py
aws lambda create-function \
  --function-name shipment-notification-handler \
  --runtime python3.11 \
  --handler notification_handler.handler \
  --role arn:aws:iam::ACCOUNT:role/lambda-execution-role \
  --zip-file fileb://notification_handler.zip \
  --environment Variables="{ORDERS_TABLE=DeviceOrders,SNS_TOPIC_ARN=arn:aws:sns:...}"
```

### 3. Create Event Source Mapping

```bash
STREAM_ARN=$(aws dynamodb describe-table \
  --table-name aquachain-shipments \
  --query 'Table.LatestStreamArn' \
  --output text)

aws lambda create-event-source-mapping \
  --function-name shipment-notification-handler \
  --event-source-arn $STREAM_ARN \
  --batch-size 10 \
  --starting-position LATEST
```

### 4. Configure SES

```bash
# Verify sender email
aws ses verify-email-identity --email-address noreply@aquachain.com

# Move out of SES sandbox (for production)
# Request via AWS Console: SES > Account Dashboard > Request Production Access
```

## Testing

### Test Email Notifications

```python
import boto3
import json

dynamodb = boto3.resource('dynamodb')
table = dynamodb.Table('aquachain-shipments')

# Update shipment status to trigger notification
table.update_item(
    Key={'shipment_id': 'ship_test_123'},
    UpdateExpression='SET internal_status = :status',
    ExpressionAttributeValues={':status': 'out_for_delivery'}
)
```

### Test SMS Notifications

Ensure phone numbers are in E.164 format: `+1234567890`

### Test WebSocket Notifications

1. Connect to WebSocket API
2. Subscribe to shipment updates
3. Update shipment status
4. Verify real-time message received

## Monitoring

### CloudWatch Logs

```bash
# View notification handler logs
aws logs tail /aws/lambda/shipment-notification-handler --follow

# Filter for errors
aws logs filter-log-events \
  --log-group-name /aws/lambda/shipment-notification-handler \
  --filter-pattern "ERROR"
```

### Metrics

- **Invocations**: Number of stream records processed
- **Errors**: Failed notification attempts
- **Duration**: Processing time per batch
- **Iterator Age**: Stream processing lag

### Alarms

```bash
# Create alarm for high error rate
aws cloudwatch put-metric-alarm \
  --alarm-name shipment-notification-errors \
  --metric-name Errors \
  --namespace AWS/Lambda \
  --statistic Sum \
  --period 300 \
  --threshold 10 \
  --comparison-operator GreaterThanThreshold \
  --dimensions Name=FunctionName,Value=shipment-notification-handler
```

## Troubleshooting

### Notifications Not Sent

1. **Check DynamoDB Stream**: Verify stream is enabled
   ```bash
   aws dynamodb describe-table --table-name aquachain-shipments \
     --query 'Table.StreamSpecification'
   ```

2. **Check Event Source Mapping**: Verify mapping is active
   ```bash
   aws lambda list-event-source-mappings \
     --function-name shipment-notification-handler
   ```

3. **Check Lambda Logs**: Look for errors
   ```bash
   aws logs tail /aws/lambda/shipment-notification-handler --follow
   ```

4. **Check IAM Permissions**: Verify Lambda has required permissions

### Email Delivery Issues

1. **SES Sandbox**: Verify recipient emails if in sandbox mode
2. **Email Verification**: Ensure sender email is verified
3. **Bounce/Complaint**: Check SES reputation dashboard

### SMS Delivery Issues

1. **Phone Format**: Ensure E.164 format (+1234567890)
2. **SNS Permissions**: Verify Lambda can publish to SNS
3. **SMS Spending Limit**: Check SNS spending limits

### WebSocket Issues

1. **Endpoint Configuration**: Verify WEBSOCKET_ENDPOINT is set
2. **Connection Table**: Ensure connections table exists
3. **API Gateway Permissions**: Verify Lambda can post to connections

## Requirements Validation

- ✅ **1.5**: Notifications sent on shipment creation
- ✅ **4.1**: Technician notified on delivery
- ✅ **13.1**: Email sent on shipment creation
- ✅ **13.2**: SMS sent on out for delivery
- ✅ **13.3**: Email and SMS sent on delivery confirmation
- ✅ **13.4**: Email sent on delivery failure
- ✅ **13.5**: WebSocket updates for real-time UI refresh

## Related Files

- `lambda/shipments/notification_handler.py` - Main notification Lambda
- `infrastructure/monitoring/shipment_notification_stream.py` - Setup script
- `lambda/websocket_api/broadcast_handler.py` - WebSocket broadcast handler
- `.kiro/specs/shipment-tracking-automation/design.md` - Design document
- `.kiro/specs/shipment-tracking-automation/requirements.md` - Requirements
