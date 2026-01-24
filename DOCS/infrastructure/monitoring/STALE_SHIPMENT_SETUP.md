# Stale Shipment Detection Setup Guide

This guide explains how to set up the EventBridge rule for daily stale shipment detection.

## Overview

The stale shipment detection system:
- Runs daily at 9 AM UTC
- Checks for shipments with no updates for 7+ days
- Queries courier APIs for latest status
- Marks shipments as "lost" if courier has no updates
- Creates high-priority admin tasks for investigation
- Notifies consumers with apology and resolution steps

## Requirements

- AWS CLI configured with appropriate credentials
- Python 3.8+ with boto3 installed
- Lambda function `aquachain-stale-shipment-detector` deployed
- Appropriate IAM permissions for EventBridge and Lambda

## Quick Setup

### Option 1: Using Python Script

```bash
# Navigate to infrastructure/monitoring directory
cd infrastructure/monitoring

# Run setup script (creates and enables rule)
python stale_shipment_eventbridge.py

# Or specify custom Lambda ARN
python stale_shipment_eventbridge.py --lambda-arn arn:aws:lambda:us-east-1:123456789012:function:aquachain-stale-shipment-detector

# Create rule but keep it disabled
python stale_shipment_eventbridge.py --disabled
```

### Option 2: Using AWS CLI

```bash
# Create EventBridge rule
aws events put-rule \
  --name aquachain-stale-shipment-detector \
  --schedule-expression "cron(0 9 * * ? *)" \
  --state ENABLED \
  --description "Trigger stale shipment detection daily at 9 AM"

# Add Lambda as target
aws events put-targets \
  --rule aquachain-stale-shipment-detector \
  --targets "Id"="1","Arn"="arn:aws:lambda:REGION:ACCOUNT_ID:function:aquachain-stale-shipment-detector"

# Add Lambda permission
aws lambda add-permission \
  --function-name aquachain-stale-shipment-detector \
  --statement-id aquachain-stale-shipment-detector-invoke-permission \
  --action lambda:InvokeFunction \
  --principal events.amazonaws.com \
  --source-arn arn:aws:events:REGION:ACCOUNT_ID:rule/aquachain-stale-shipment-detector
```

## Management Commands

### Check Rule Status

```bash
python stale_shipment_eventbridge.py --status
```

### Enable Rule

```bash
python stale_shipment_eventbridge.py --enable
```

### Disable Rule

```bash
python stale_shipment_eventbridge.py --disable
```

### Delete Rule

```bash
python stale_shipment_eventbridge.py --delete
```

## Schedule Configuration

The rule uses a cron expression: `cron(0 9 * * ? *)`

This means:
- **Minute**: 0 (at the top of the hour)
- **Hour**: 9 (9 AM)
- **Day of month**: * (every day)
- **Month**: * (every month)
- **Day of week**: ? (any day)
- **Year**: * (every year)

**Result**: Triggers daily at 9:00 AM UTC

### Changing the Schedule

To run at a different time, modify the cron expression in `stale_shipment_eventbridge.py`:

```python
# Run at 6 AM UTC
self.schedule_expression = 'cron(0 6 * * ? *)'

# Run twice daily (9 AM and 9 PM UTC)
# Note: You'll need two separate rules for this
self.schedule_expression = 'cron(0 9,21 * * ? *)'

# Run every 12 hours
self.schedule_expression = 'rate(12 hours)'
```

## Environment Variables

The Lambda function uses these environment variables:

```bash
SHIPMENTS_TABLE=aquachain-shipments
ADMIN_TASKS_TABLE=aquachain-admin-tasks
SNS_TOPIC_ARN=arn:aws:sns:REGION:ACCOUNT_ID:aquachain-notifications
STALE_THRESHOLD_DAYS=7
DELHIVERY_API_KEY=your-api-key
BLUEDART_API_KEY=your-api-key
DTDC_API_KEY=your-api-key
```

## Monitoring

### CloudWatch Logs

View Lambda execution logs:

```bash
aws logs tail /aws/lambda/aquachain-stale-shipment-detector --follow
```

### CloudWatch Metrics

Monitor these metrics:
- `StaleShipmentsFound` - Number of stale shipments detected
- `ShipmentsMarkedLost` - Number of shipments marked as lost
- `AdminTasksCreated` - Number of admin tasks created
- Lambda invocation errors

### CloudWatch Alarms

Set up alarms for:
- High number of stale shipments (> 10)
- Lambda execution failures
- Lambda timeout errors

## Testing

### Manual Trigger

Test the Lambda function manually:

```bash
aws lambda invoke \
  --function-name aquachain-stale-shipment-detector \
  --payload '{"source":"manual","trigger":"test"}' \
  response.json

cat response.json
```

### Expected Output

```json
{
  "statusCode": 200,
  "body": "{\"success\": true, \"stale_shipments_found\": 5, \"shipments_marked_lost\": 2, \"admin_tasks_created\": 2, \"errors\": []}"
}
```

## Troubleshooting

### Rule Not Triggering

1. Check rule is enabled:
   ```bash
   python stale_shipment_eventbridge.py --status
   ```

2. Verify Lambda has correct permissions:
   ```bash
   aws lambda get-policy --function-name aquachain-stale-shipment-detector
   ```

3. Check CloudWatch Logs for errors

### Lambda Timeout

If processing many stale shipments:
- Increase Lambda timeout (default: 3 seconds, recommended: 60 seconds)
- Increase Lambda memory (more memory = faster CPU)

### No Stale Shipments Found

This is normal if:
- All shipments are being updated regularly
- Webhooks are functioning properly
- No shipments are older than 7 days

## IAM Permissions Required

### EventBridge Permissions

```json
{
  "Version": "2012-10-17",
  "Statement": [
    {
      "Effect": "Allow",
      "Action": [
        "events:PutRule",
        "events:PutTargets",
        "events:EnableRule",
        "events:DisableRule",
        "events:DescribeRule",
        "events:DeleteRule",
        "events:RemoveTargets"
      ],
      "Resource": "arn:aws:events:*:*:rule/aquachain-stale-shipment-detector"
    }
  ]
}
```

### Lambda Permissions

```json
{
  "Version": "2012-10-17",
  "Statement": [
    {
      "Effect": "Allow",
      "Action": [
        "lambda:AddPermission",
        "lambda:GetPolicy"
      ],
      "Resource": "arn:aws:lambda:*:*:function:aquachain-stale-shipment-detector"
    }
  ]
}
```

## Production Deployment Checklist

- [ ] Lambda function deployed and tested
- [ ] Environment variables configured
- [ ] EventBridge rule created
- [ ] Lambda permissions added
- [ ] Rule enabled
- [ ] CloudWatch alarms configured
- [ ] SNS topic configured for notifications
- [ ] Admin tasks table exists
- [ ] Courier API keys configured
- [ ] Test manual invocation successful
- [ ] Monitor first scheduled execution

## Support

For issues or questions:
- Check CloudWatch Logs: `/aws/lambda/aquachain-stale-shipment-detector`
- Review Lambda metrics in CloudWatch
- Contact DevOps team

## Related Documentation

- [Stale Shipment Detector Lambda](../../lambda/shipments/stale_shipment_detector.py)
- [Shipment Tracking Design](../../.kiro/specs/shipment-tracking-automation/design.md)
- [Shipment Tracking Requirements](../../.kiro/specs/shipment-tracking-automation/requirements.md)
