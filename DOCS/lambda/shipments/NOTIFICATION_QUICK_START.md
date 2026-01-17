# Shipment Notification System - Quick Start Guide

## 🚀 Quick Setup (5 minutes)

### Prerequisites
- Shipments DynamoDB table created
- AWS CLI configured
- Lambda execution role with required permissions

### Step 1: Enable DynamoDB Streams (1 min)

```bash
aws dynamodb update-table \
  --table-name aquachain-shipments \
  --stream-specification StreamEnabled=true,StreamViewType=NEW_AND_OLD_IMAGES
```

### Step 2: Deploy Notification Lambda (2 min)

```bash
cd lambda/shipments

# Package Lambda
zip -r notification_handler.zip notification_handler.py

# Deploy
aws lambda create-function \
  --function-name shipment-notification-handler \
  --runtime python3.11 \
  --handler notification_handler.handler \
  --role arn:aws:iam::YOUR_ACCOUNT:role/lambda-execution-role \
  --zip-file fileb://notification_handler.zip \
  --timeout 30 \
  --memory-size 256 \
  --environment Variables="{
    ORDERS_TABLE=DeviceOrders,
    CONNECTIONS_TABLE=aquachain-websocket-connections,
    SNS_TOPIC_ARN=arn:aws:sns:REGION:ACCOUNT:topic,
    SES_FROM_EMAIL=noreply@aquachain.com,
    WEBSOCKET_ENDPOINT=https://xxx.execute-api.REGION.amazonaws.com/prod
  }"
```

### Step 3: Connect Stream to Lambda (1 min)

```bash
# Get stream ARN
STREAM_ARN=$(aws dynamodb describe-table \
  --table-name aquachain-shipments \
  --query 'Table.LatestStreamArn' \
  --output text)

# Create event source mapping
aws lambda create-event-source-mapping \
  --function-name shipment-notification-handler \
  --event-source-arn $STREAM_ARN \
  --batch-size 10 \
  --starting-position LATEST \
  --maximum-retry-attempts 3 \
  --bisect-batch-on-function-error
```

### Step 4: Verify SES Email (1 min)

```bash
# Verify sender email
aws ses verify-email-identity --email-address noreply@aquachain.com

# Check verification status
aws ses get-identity-verification-attributes \
  --identities noreply@aquachain.com
```

## ✅ Test the System

### Test 1: Create a Shipment

```bash
# This will trigger shipment_created notification
aws dynamodb put-item \
  --table-name aquachain-shipments \
  --item '{
    "shipment_id": {"S": "ship_test_001"},
    "order_id": {"S": "ord_test_001"},
    "tracking_number": {"S": "TEST123456"},
    "internal_status": {"S": "shipment_created"},
    "courier_name": {"S": "Delhivery"},
    "estimated_delivery": {"S": "2025-12-31T18:00:00Z"},
    "created_at": {"S": "2025-12-29T12:00:00Z"}
  }'
```

Expected: Email sent to consumer with tracking info

### Test 2: Update to Out for Delivery

```bash
# This will trigger out_for_delivery notification
aws dynamodb update-item \
  --table-name aquachain-shipments \
  --key '{"shipment_id": {"S": "ship_test_001"}}' \
  --update-expression "SET internal_status = :status" \
  --expression-attribute-values '{":status": {"S": "out_for_delivery"}}'
```

Expected: Email + SMS sent to consumer

### Test 3: Mark as Delivered

```bash
# This will trigger delivered notification
aws dynamodb update-item \
  --table-name aquachain-shipments \
  --key '{"shipment_id": {"S": "ship_test_001"}}' \
  --update-expression "SET internal_status = :status, delivered_at = :time" \
  --expression-attribute-values '{
    ":status": {"S": "delivered"},
    ":time": {"S": "2025-12-30T14:30:00Z"}
  }'
```

Expected: Email + SMS to consumer, notification to technician

## 📊 Monitor Notifications

### View Lambda Logs

```bash
# Real-time logs
aws logs tail /aws/lambda/shipment-notification-handler --follow

# Last 10 minutes
aws logs tail /aws/lambda/shipment-notification-handler --since 10m
```

### Check Notification Metrics

```bash
# Lambda invocations
aws cloudwatch get-metric-statistics \
  --namespace AWS/Lambda \
  --metric-name Invocations \
  --dimensions Name=FunctionName,Value=shipment-notification-handler \
  --start-time $(date -u -d '1 hour ago' +%Y-%m-%dT%H:%M:%S) \
  --end-time $(date -u +%Y-%m-%dT%H:%M:%S) \
  --period 300 \
  --statistics Sum

# Lambda errors
aws cloudwatch get-metric-statistics \
  --namespace AWS/Lambda \
  --metric-name Errors \
  --dimensions Name=FunctionName,Value=shipment-notification-handler \
  --start-time $(date -u -d '1 hour ago' +%Y-%m-%dT%H:%M:%S) \
  --end-time $(date -u +%Y-%m-%dT%H:%M:%S) \
  --period 300 \
  --statistics Sum
```

## 🔧 Common Issues

### Issue: Emails not sending

**Solution 1**: Check SES sandbox mode
```bash
# If in sandbox, verify recipient email
aws ses verify-email-identity --email-address recipient@example.com
```

**Solution 2**: Check sender email verification
```bash
aws ses get-identity-verification-attributes \
  --identities noreply@aquachain.com
```

### Issue: SMS not sending

**Solution**: Verify phone number format (E.164)
- ✅ Correct: `+1234567890`
- ❌ Wrong: `1234567890`, `(123) 456-7890`

### Issue: WebSocket not working

**Solution**: Check endpoint configuration
```bash
# Verify WEBSOCKET_ENDPOINT environment variable
aws lambda get-function-configuration \
  --function-name shipment-notification-handler \
  --query 'Environment.Variables.WEBSOCKET_ENDPOINT'
```

### Issue: No notifications at all

**Solution**: Check event source mapping
```bash
# List mappings
aws lambda list-event-source-mappings \
  --function-name shipment-notification-handler

# Check mapping state (should be "Enabled")
```

## 📝 Notification Flow Summary

```
Shipment Status Change
        ↓
DynamoDB Stream Event
        ↓
notification_handler Lambda
        ↓
    ┌───┴───┬───────┐
    ↓       ↓       ↓
  Email    SMS   WebSocket
    ↓       ↓       ↓
Consumer Consumer  All Users
```

## 🎯 Next Steps

1. **Production Setup**: Move SES out of sandbox mode
2. **Monitoring**: Set up CloudWatch alarms for errors
3. **Testing**: Test all notification scenarios
4. **Documentation**: Update team on notification system

## 📚 Additional Resources

- [Full Documentation](./NOTIFICATION_SYSTEM_README.md)
- [Design Document](../../.kiro/specs/shipment-tracking-automation/design.md)
- [Requirements](../../.kiro/specs/shipment-tracking-automation/requirements.md)
- [AWS SES Documentation](https://docs.aws.amazon.com/ses/)
- [AWS SNS Documentation](https://docs.aws.amazon.com/sns/)
- [DynamoDB Streams](https://docs.aws.amazon.com/amazondynamodb/latest/developerguide/Streams.html)
