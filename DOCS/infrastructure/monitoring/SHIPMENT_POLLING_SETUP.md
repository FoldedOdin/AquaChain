# Shipment Polling Fallback EventBridge Setup

This document describes how to set up and manage the EventBridge rule for the shipment polling fallback mechanism.

## Overview

The polling fallback mechanism ensures shipment tracking continues even when courier webhooks fail. An EventBridge rule triggers the `polling_fallback` Lambda function every 4 hours to check for stale shipments and query courier APIs directly.

## Requirements

- AWS CLI configured with appropriate credentials
- Python 3.8+ with boto3 installed
- Lambda function `aquachain-polling-fallback` deployed
- Appropriate IAM permissions for EventBridge and Lambda

## Quick Start

### 1. Set Up Complete Infrastructure

Create the EventBridge rule, add Lambda target, and configure permissions:

```bash
cd infrastructure/monitoring
python shipment_polling_eventbridge.py --region us-east-1
```

This will:
- Create EventBridge rule `aquachain-shipment-polling-fallback`
- Schedule it to run every 4 hours
- Add `aquachain-polling-fallback` Lambda as target
- Configure Lambda invoke permissions
- Enable the rule immediately

### 2. Create Rule But Keep It Disabled

If you want to create the infrastructure but not enable it yet:

```bash
python shipment_polling_eventbridge.py --region us-east-1 --disabled
```

### 3. Specify Custom Lambda ARN

If your Lambda function has a different name or ARN:

```bash
python shipment_polling_eventbridge.py --region us-east-1 --lambda-arn arn:aws:lambda:us-east-1:123456789012:function:my-polling-function
```

## Management Commands

### Check Rule Status

```bash
python shipment_polling_eventbridge.py --status
```

Output:
```json
{
  "rule_name": "aquachain-shipment-polling-fallback",
  "arn": "arn:aws:events:us-east-1:123456789012:rule/aquachain-shipment-polling-fallback",
  "state": "ENABLED",
  "schedule": "rate(4 hours)",
  "description": "Trigger shipment polling fallback every 4 hours to check for stale shipments"
}
```

### Enable Rule

Enable the rule when webhook failures are detected:

```bash
python shipment_polling_eventbridge.py --enable
```

### Disable Rule

Disable the rule when webhooks are functioning properly:

```bash
python shipment_polling_eventbridge.py --disable
```

### Delete Rule

Remove the rule and all targets:

```bash
python shipment_polling_eventbridge.py --delete
```

## Programmatic Usage

You can also use the `ShipmentPollingEventBridge` class in your Python code:

```python
from shipment_polling_eventbridge import ShipmentPollingEventBridge

# Initialize
eventbridge = ShipmentPollingEventBridge(region='us-east-1')

# Set up complete infrastructure
result = eventbridge.setup_complete_polling_infrastructure(enabled=True)

# Enable/disable dynamically
eventbridge.enable_rule()
eventbridge.disable_rule()

# Check status
status = eventbridge.get_rule_status()
print(f"Rule is {status['state']}")
```

## Automatic Enable/Disable Based on Webhook Failures

The rule can be automatically enabled when webhook failures are detected. Add this logic to your webhook monitoring:

```python
import boto3
from shipment_polling_eventbridge import ShipmentPollingEventBridge

def monitor_webhook_health():
    """Monitor webhook health and enable/disable polling accordingly"""
    
    # Check webhook error rate
    webhook_error_rate = get_webhook_error_rate()  # Your monitoring logic
    
    eventbridge = ShipmentPollingEventBridge()
    
    if webhook_error_rate > 0.1:  # More than 10% errors
        print("High webhook error rate detected, enabling polling fallback")
        eventbridge.enable_rule()
    else:
        print("Webhooks functioning normally, disabling polling fallback")
        eventbridge.disable_rule()
```

## Schedule Configuration

The default schedule is `rate(4 hours)`, which triggers the Lambda every 4 hours.

To change the schedule, modify the `schedule_expression` in the class:

```python
eventbridge = ShipmentPollingEventBridge()
eventbridge.schedule_expression = 'rate(2 hours)'  # Run every 2 hours
eventbridge.create_eventbridge_rule()
```

Valid schedule expressions:
- `rate(4 hours)` - Every 4 hours
- `rate(30 minutes)` - Every 30 minutes
- `cron(0 */4 * * ? *)` - Every 4 hours using cron
- `cron(0 0 * * ? *)` - Daily at midnight

## IAM Permissions Required

The IAM user/role running this script needs:

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
        "events:ListTargetsByRule",
        "events:RemoveTargets",
        "events:DeleteRule"
      ],
      "Resource": "arn:aws:events:*:*:rule/aquachain-shipment-polling-fallback"
    },
    {
      "Effect": "Allow",
      "Action": [
        "lambda:AddPermission",
        "lambda:RemovePermission"
      ],
      "Resource": "arn:aws:lambda:*:*:function:aquachain-polling-fallback"
    },
    {
      "Effect": "Allow",
      "Action": "sts:GetCallerIdentity",
      "Resource": "*"
    }
  ]
}
```

## Monitoring

### CloudWatch Metrics

The polling fallback Lambda emits custom metrics:

- `ShipmentsChecked` - Number of stale shipments checked
- `ShipmentsUpdated` - Number of shipments updated from polling
- `PollingErrors` - Number of errors during polling

### CloudWatch Logs

View Lambda execution logs:

```bash
aws logs tail /aws/lambda/aquachain-polling-fallback --follow
```

### EventBridge Metrics

Monitor rule invocations:

```bash
aws cloudwatch get-metric-statistics \
  --namespace AWS/Events \
  --metric-name Invocations \
  --dimensions Name=RuleName,Value=aquachain-shipment-polling-fallback \
  --start-time 2025-01-01T00:00:00Z \
  --end-time 2025-01-02T00:00:00Z \
  --period 3600 \
  --statistics Sum
```

## Troubleshooting

### Rule Not Triggering

1. Check rule is enabled:
   ```bash
   python shipment_polling_eventbridge.py --status
   ```

2. Verify Lambda has correct permissions:
   ```bash
   aws lambda get-policy --function-name aquachain-polling-fallback
   ```

3. Check EventBridge invocation metrics in CloudWatch

### Lambda Errors

1. View recent errors:
   ```bash
   aws logs filter-log-events \
     --log-group-name /aws/lambda/aquachain-polling-fallback \
     --filter-pattern "ERROR"
   ```

2. Check Lambda configuration:
   ```bash
   aws lambda get-function --function-name aquachain-polling-fallback
   ```

### Permission Errors

If you see "AccessDeniedException", ensure:
- IAM role has required permissions
- Lambda execution role has DynamoDB and courier API access
- EventBridge has permission to invoke Lambda

## Best Practices

1. **Start Disabled**: Create the rule disabled initially, enable only when needed
2. **Monitor Costs**: Polling every 4 hours is cost-effective, but adjust based on needs
3. **Alert on Failures**: Set up CloudWatch alarms for polling errors
4. **Test Regularly**: Manually invoke the Lambda to ensure it works correctly
5. **Document Changes**: Log when you enable/disable the rule and why

## Related Documentation

- [Polling Fallback Lambda](../../lambda/shipments/polling_fallback.py)
- [Shipment Tracking Design](../../.kiro/specs/shipment-tracking-automation/design.md)
- [AWS EventBridge Documentation](https://docs.aws.amazon.com/eventbridge/)
