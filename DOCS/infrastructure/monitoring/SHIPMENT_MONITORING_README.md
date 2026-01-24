# Shipment Tracking Monitoring System

Complete monitoring and alerting infrastructure for the AquaChain shipment tracking subsystem.

## Overview

This monitoring system provides real-time visibility into shipment operations with:

- **CloudWatch Custom Metrics**: Track shipment creation, delivery, failures, and performance
- **CloudWatch Alarms**: Automated alerts for threshold breaches
- **CloudWatch Dashboard**: Visual monitoring of all metrics and alarm status
- **Structured Logging**: JSON-formatted logs for easy analysis

## Architecture

```
┌─────────────────────────────────────────────────────────────┐
│                  Lambda Functions                            │
│  - create_shipment                                          │
│  - webhook_handler                                          │
│  - get_shipment_status                                      │
│  - polling_fallback                                         │
│  - stale_shipment_detector                                  │
└─────────────────────────────────────────────────────────────┘
                              ↓
┌─────────────────────────────────────────────────────────────┐
│              CloudWatch Custom Metrics                       │
│  - ShipmentsCreated                                         │
│  - WebhooksProcessed                                        │
│  - DeliveryTime                                             │
│  - FailedDeliveries                                         │
│  - StaleShipments                                           │
│  - LambdaErrors                                             │
└─────────────────────────────────────────────────────────────┘
                              ↓
┌─────────────────────────────────────────────────────────────┐
│              CloudWatch Alarms                               │
│  - HighFailedDeliveryRate (> 5%)                           │
│  - HighWebhookErrors (> 10 per 5 min)                      │
│  - HighStaleShipments (> 10)                               │
│  - Lambda Function Errors (> 5 per 5 min)                  │
└─────────────────────────────────────────────────────────────┘
                              ↓
┌─────────────────────────────────────────────────────────────┐
│                   SNS Notifications                          │
│  Email/SMS alerts to DevOps team                            │
└─────────────────────────────────────────────────────────────┘
```

## Quick Start

### 1. Setup Monitoring Infrastructure

```bash
cd infrastructure/monitoring
python setup_monitoring.py admin@aquachain.com
```

This will:
- Create SNS topic for alarm notifications
- Subscribe your email to alarms
- Create all CloudWatch alarms
- Create CloudWatch dashboard

### 2. Confirm Email Subscription

Check your email and confirm the SNS subscription to receive alarm notifications.

### 3. View Dashboard

Open the CloudWatch dashboard:
```
https://console.aws.amazon.com/cloudwatch/home?region=us-east-1#dashboards:name=AquaChain-Shipments-Dashboard
```

### 4. Deploy Lambda Functions

Ensure all Lambda functions are deployed with the `cloudwatch_metrics` module:

```bash
cd lambda/shipments
# Deploy functions with metrics enabled
```

## CloudWatch Metrics

### ShipmentsCreated

**Description**: Count of shipments created  
**Unit**: Count  
**Dimensions**: Courier  
**Emitted by**: `create_shipment` Lambda  

**Usage**:
```python
from cloudwatch_metrics import emit_shipment_created

emit_shipment_created(shipment_id, order_id, courier_name)
```

### WebhooksProcessed

**Description**: Count of webhooks processed  
**Unit**: Count  
**Dimensions**: Courier, Status, Success  
**Emitted by**: `webhook_handler` Lambda  

**Usage**:
```python
from cloudwatch_metrics import emit_webhook_processed

emit_webhook_processed(tracking_number, courier_name, status, success=True)
```

### DeliveryTime

**Description**: Time from shipment creation to delivery  
**Unit**: Hours  
**Dimensions**: Courier  
**Emitted by**: `webhook_handler` Lambda (on delivery confirmation)  

**Usage**:
```python
from cloudwatch_metrics import emit_delivery_time

emit_delivery_time(shipment_id, courier_name, hours)
```

### FailedDeliveries

**Description**: Count of failed delivery attempts  
**Unit**: Count  
**Dimensions**: Courier, RetryCount  
**Emitted by**: `webhook_handler` Lambda  

**Usage**:
```python
from cloudwatch_metrics import emit_failed_delivery

emit_failed_delivery(shipment_id, courier_name, retry_count)
```

### StaleShipments

**Description**: Count of shipments with no updates for 7+ days  
**Unit**: Count  
**Emitted by**: `stale_shipment_detector` Lambda  

**Usage**:
```python
from cloudwatch_metrics import emit_stale_shipments

emit_stale_shipments(count)
```

### LambdaErrors

**Description**: Count of Lambda function errors  
**Unit**: Count  
**Dimensions**: FunctionName, ErrorType  
**Emitted by**: All Lambda functions  

**Usage**:
```python
from cloudwatch_metrics import emit_lambda_error

emit_lambda_error('create_shipment', 'ValidationError')
```

## CloudWatch Alarms

### HighFailedDeliveryRate

**Threshold**: > 5% over 1 hour  
**Metric**: (FailedDeliveries / ShipmentsCreated) * 100  
**Action**: SNS notification to DevOps  

**What it means**: More than 5% of shipments are failing delivery, indicating potential courier issues or address problems.

**Response**:
1. Check courier service status
2. Review failed delivery reasons
3. Contact courier support if widespread
4. Verify customer addresses

### HighWebhookErrors

**Threshold**: > 10 errors per 5 minutes  
**Metric**: WebhookErrors  
**Action**: SNS notification + Enable polling fallback  

**What it means**: Webhook processing is failing, possibly due to invalid payloads or signature verification issues.

**Response**:
1. Check CloudWatch Logs for error details
2. Verify webhook signature configuration
3. Check courier API documentation for payload changes
4. Polling fallback will activate automatically

### HighStaleShipments

**Threshold**: > 10 stale shipments  
**Metric**: StaleShipments  
**Action**: SNS notification to Admin  

**What it means**: Multiple shipments have no updates for 7+ days, indicating tracking issues or lost packages.

**Response**:
1. Review admin tasks created by stale detector
2. Contact couriers for package location
3. Initiate insurance claims if necessary
4. Arrange replacement shipments

### Lambda Function Errors

**Threshold**: > 5 errors per 5 minutes  
**Metric**: LambdaErrors by FunctionName  
**Action**: SNS notification to DevOps  

**What it means**: A Lambda function is experiencing repeated errors.

**Response**:
1. Check CloudWatch Logs for stack traces
2. Review recent code deployments
3. Check DynamoDB table availability
4. Verify IAM permissions

## CloudWatch Dashboard

The dashboard provides real-time visualization of:

### Row 1: Overview Metrics
- **Shipments Created**: Total shipments created over time
- **Shipments Delivered**: Count of successful deliveries
- **Failed Deliveries**: Count of failed delivery attempts
- **Stale Shipments**: Current count of stale shipments

### Row 2: Webhook Metrics
- **Webhooks Processed**: Webhook processing rate
- **Webhook Errors**: Error count with threshold line
- **Webhook Success Rate**: Percentage of successful webhook processing

### Row 3: Delivery Performance
- **Delivery Time by Courier**: Average, p50, p90, p99 delivery times

### Row 4: Error Tracking
- **Lambda Errors by Function**: Stacked view of errors per function

### Row 5: Alarm Status
- **Alarm Status**: Current state of all alarms (OK, ALARM, INSUFFICIENT_DATA)

## Structured Logging

All Lambda functions use JSON-formatted structured logging for consistent log analysis.

### Standard Fields

Every log entry includes:
- `timestamp`: ISO 8601 UTC timestamp
- `level`: Log level (INFO, WARNING, ERROR)
- `message`: Human-readable message
- `service`: Lambda function name
- `request_id`: AWS request ID
- `shipment_id`: Shipment identifier (when available)
- `order_id`: Order identifier (when available)

### Example Log Entry

```json
{
  "timestamp": "2025-01-01T12:00:00.000Z",
  "level": "INFO",
  "message": "Shipment created successfully",
  "service": "create-shipment",
  "request_id": "abc-123",
  "shipment_id": "ship_1735478400000",
  "order_id": "ord_1735392000000",
  "tracking_number": "DELHUB123456789",
  "courier": "Delhivery"
}
```

### CloudWatch Logs Insights Queries

**Find all errors for a shipment**:
```
fields @timestamp, message, error_type, error_code
| filter shipment_id = "ship_xxx"
| filter level = "ERROR"
| sort @timestamp desc
```

**Track webhook processing latency**:
```
fields @timestamp, tracking_number, duration_ms
| filter message like /webhook processed/
| stats avg(duration_ms), max(duration_ms), count() by courier
```

**Monitor error rates by function**:
```
fields @timestamp, service, error_type
| filter level = "ERROR"
| stats count() by service, error_type
| sort count desc
```

See `lambda/shipments/STRUCTURED_LOGGING_GUIDE.md` for more examples.

## Maintenance

### Update Alarm Thresholds

Edit `infrastructure/monitoring/shipment_alarms.py` and update threshold values:

```python
# Example: Change failed delivery rate threshold to 10%
Threshold=10.0  # Changed from 5.0
```

Then redeploy:
```bash
python shipment_alarms.py
```

### Add New Metrics

1. Add metric emission function to `lambda/shipments/cloudwatch_metrics.py`
2. Call the function from appropriate Lambda
3. Add widget to dashboard in `infrastructure/monitoring/shipment_dashboard.py`
4. Create alarm if needed in `infrastructure/monitoring/shipment_alarms.py`

### Verify Setup

```bash
python setup_monitoring.py verify
```

This will check:
- SNS topic exists
- Email subscriptions are confirmed
- All alarms are created
- Dashboard exists

## Troubleshooting

### Metrics Not Appearing

**Problem**: Metrics not showing in CloudWatch  
**Solution**:
1. Verify Lambda functions are deployed with `cloudwatch_metrics` module
2. Check Lambda execution logs for metric emission errors
3. Verify IAM permissions include `cloudwatch:PutMetricData`

### Alarms Not Triggering

**Problem**: Alarms not sending notifications  
**Solution**:
1. Verify email subscription is confirmed (check inbox)
2. Check alarm state in CloudWatch console
3. Verify SNS topic has correct permissions
4. Check alarm threshold is being exceeded

### Dashboard Not Loading

**Problem**: Dashboard shows "No data available"  
**Solution**:
1. Wait for metrics to be emitted (may take a few minutes)
2. Verify Lambda functions are being invoked
3. Check dashboard time range (default is last 3 hours)
4. Verify metric namespace is correct

## Requirements Validation

This implementation satisfies:

✅ **Requirement 14.1**: Emit CloudWatch metrics for shipment operations  
✅ **Requirement 14.2**: Display metrics in CloudWatch dashboard  
✅ **Requirement 14.3**: Create alarms for failed delivery rate and stale shipments  
✅ **Requirement 14.4**: Create alarms for webhook errors and Lambda errors  
✅ **Requirement 14.5**: Implement structured logging with JSON format  

## Files

- `cloudwatch_metrics.py`: Metric emission utilities (in lambda/shipments/)
- `shipment_alarms.py`: CloudWatch alarm configuration
- `shipment_dashboard.py`: CloudWatch dashboard definition
- `setup_monitoring.py`: Complete setup script
- `SHIPMENT_MONITORING_README.md`: This file
- `STRUCTURED_LOGGING_GUIDE.md`: Logging best practices (in lambda/shipments/)

## Support

For issues or questions:
1. Check CloudWatch Logs for error details
2. Review alarm history in CloudWatch console
3. Verify setup with `python setup_monitoring.py verify`
4. Contact DevOps team for assistance
