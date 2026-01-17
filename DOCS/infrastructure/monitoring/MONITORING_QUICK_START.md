# Shipment Monitoring - Quick Start Guide

Get the shipment tracking monitoring system up and running in 5 minutes.

## Prerequisites

- AWS CLI configured with appropriate credentials
- Python 3.8+ installed
- boto3 installed (`pip install boto3`)

## Step 1: Setup (2 minutes)

Run the setup script with your admin email:

```bash
cd infrastructure/monitoring
python setup_monitoring.py admin@aquachain.com
```

This creates:
- ✅ SNS topic for alarm notifications
- ✅ Email subscription (pending confirmation)
- ✅ 9 CloudWatch alarms
- ✅ CloudWatch dashboard

## Step 2: Confirm Email (1 minute)

1. Check your email inbox
2. Look for "AWS Notification - Subscription Confirmation"
3. Click "Confirm subscription"

## Step 3: View Dashboard (1 minute)

Open the CloudWatch dashboard:

```
https://console.aws.amazon.com/cloudwatch/home?region=us-east-1#dashboards:name=AquaChain-Shipments-Dashboard
```

You should see:
- Shipment metrics (may show "No data" initially)
- Webhook processing stats
- Delivery time charts
- Error tracking
- Alarm status

## Step 4: Verify Setup (1 minute)

```bash
python setup_monitoring.py verify
```

Expected output:
```
✓ SNS Topic exists
  Subscriptions: 1
    - admin@aquachain.com (confirmed)

✓ CloudWatch Alarms: 9 alarms
  ✓ AquaChain-Shipments-HighFailedDeliveryRate: OK
  ✓ AquaChain-Shipments-HighWebhookErrors: OK
  ...

✓ CloudWatch Dashboard exists
  - AquaChain-Shipments-Dashboard
```

## Step 5: Test Metrics (Optional)

Deploy Lambda functions and trigger operations to see metrics:

```bash
# Create a test shipment
aws lambda invoke \
  --function-name create_shipment \
  --payload '{"order_id":"test_001","courier_name":"Delhivery",...}' \
  response.json

# Check dashboard - you should see ShipmentsCreated metric increase
```

## What's Monitoring?

### Metrics Being Tracked

1. **ShipmentsCreated** - How many shipments are created
2. **WebhooksProcessed** - How many courier updates received
3. **DeliveryTime** - How long deliveries take
4. **FailedDeliveries** - How many deliveries fail
5. **StaleShipments** - How many shipments have no updates
6. **LambdaErrors** - How many function errors occur

### Alarms That Will Alert You

1. **Failed Delivery Rate > 5%** - Too many deliveries failing
2. **Webhook Errors > 10 per 5 min** - Webhook processing issues
3. **Stale Shipments > 10** - Too many shipments stuck
4. **Lambda Errors > 5 per 5 min** - Function errors

### When You'll Get Notified

You'll receive an email when:
- Delivery failure rate exceeds 5%
- Webhook processing has issues
- More than 10 shipments are stale
- Lambda functions are erroring repeatedly

## Troubleshooting

### "No data available" in dashboard

**Cause**: No metrics emitted yet  
**Solution**: Wait for Lambda functions to be invoked, or trigger test operations

### Email not received

**Cause**: Email in spam or wrong address  
**Solution**: Check spam folder, or resubscribe with correct email:
```bash
aws sns subscribe \
  --topic-arn <topic-arn> \
  --protocol email \
  --notification-endpoint correct@email.com
```

### Alarms showing "INSUFFICIENT_DATA"

**Cause**: Not enough data points yet  
**Solution**: Normal for new setup, will resolve after metrics are emitted

## Next Steps

1. ✅ Monitoring setup complete
2. 📊 View dashboard regularly
3. 📧 Respond to alarm notifications
4. 📝 Review CloudWatch Logs for details
5. 🔧 Adjust alarm thresholds if needed

## Quick Reference

### View Dashboard
```
https://console.aws.amazon.com/cloudwatch/home?region=us-east-1#dashboards:name=AquaChain-Shipments-Dashboard
```

### View Alarms
```
https://console.aws.amazon.com/cloudwatch/home?region=us-east-1#alarmsV2:
```

### View Metrics
```
https://console.aws.amazon.com/cloudwatch/home?region=us-east-1#metricsV2:graph=~();namespace=AquaChain/Shipments
```

### View Logs
```
https://console.aws.amazon.com/cloudwatch/home?region=us-east-1#logsV2:logs-insights
```

## Support

For detailed information, see:
- `SHIPMENT_MONITORING_README.md` - Complete guide
- `STRUCTURED_LOGGING_GUIDE.md` - Logging best practices
- `TASK_16_COMPLETION_SUMMARY.md` - Implementation details

## Success!

Your shipment tracking monitoring is now active. You'll receive alerts when issues occur and can view real-time metrics in the dashboard.

Happy monitoring! 📊✨
