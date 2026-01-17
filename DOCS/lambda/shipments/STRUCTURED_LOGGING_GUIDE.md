# Structured Logging Guide for Shipment Tracking

This guide explains how structured logging is implemented in the shipment tracking subsystem.

## Overview

All Lambda functions use JSON-formatted structured logging for consistent log aggregation and analysis. The `structured_logger` module provides a standardized logging interface.

## Standard Fields

Every log entry includes these standard fields:

- **timestamp**: ISO 8601 formatted UTC timestamp
- **level**: Log level (INFO, WARNING, ERROR, DEBUG, CRITICAL)
- **message**: Human-readable log message
- **service**: Name of the Lambda function
- **request_id**: AWS request ID for tracing (optional)
- **user_id**: User identifier (optional)

## Shipment-Specific Fields

For shipment operations, include these additional fields:

- **shipment_id**: Unique shipment identifier
- **order_id**: Associated order identifier
- **tracking_number**: Courier tracking number
- **courier**: Courier service name
- **status**: Current shipment status
- **error_code**: Error code for failures
- **error_type**: Exception type name
- **stack_trace**: Full stack trace for errors

## Usage Examples

### Basic Logging

```python
from structured_logger import get_logger

logger = get_logger(__name__, service='create-shipment')

logger.info(
    "Shipment created successfully",
    shipment_id=shipment_id,
    order_id=order_id,
    tracking_number=tracking_number
)
```

### Error Logging with Stack Trace

```python
try:
    # Operation that might fail
    create_shipment(order_id)
except Exception as e:
    logger.error(
        f"Failed to create shipment: {str(e)}",
        order_id=order_id,
        error_type=type(e).__name__,
        stack_trace=traceback.format_exc()
    )
```

### Webhook Processing

```python
logger.info(
    "Processing webhook",
    tracking_number=tracking_number,
    courier=courier_name,
    status=internal_status
)
```

### Performance Logging

```python
start_time = time.time()
# ... operation ...
duration_ms = (time.time() - start_time) * 1000

logger.info(
    "Operation completed",
    operation="create_shipment",
    duration_ms=duration_ms,
    shipment_id=shipment_id
)
```

## Log Levels

### INFO
Use for normal operations and successful completions:
- Shipment created
- Webhook processed
- Status updated
- Notification sent

### WARNING
Use for recoverable issues:
- Validation errors
- Retry attempts
- Invalid state transitions (out-of-order webhooks)
- Missing optional fields

### ERROR
Use for failures requiring attention:
- Database errors
- API failures after retries
- Transaction rollbacks
- Notification failures

### DEBUG
Use for detailed troubleshooting:
- Request/response payloads
- State machine transitions
- Query results
- Intermediate calculations

### CRITICAL
Use for system-wide failures:
- Service unavailability
- Data corruption
- Security breaches

## CloudWatch Logs Insights Queries

### Find all errors for a shipment

```
fields @timestamp, message, error_type, error_code
| filter shipment_id = "ship_xxx"
| filter level = "ERROR"
| sort @timestamp desc
```

### Track webhook processing latency

```
fields @timestamp, tracking_number, duration_ms
| filter message like /webhook processed/
| stats avg(duration_ms), max(duration_ms), count() by courier
```

### Find failed deliveries

```
fields @timestamp, shipment_id, order_id, retry_count
| filter status = "delivery_failed"
| sort @timestamp desc
```

### Monitor error rates by function

```
fields @timestamp, service, error_type
| filter level = "ERROR"
| stats count() by service, error_type
| sort count desc
```

## Best Practices

1. **Always include shipment_id and order_id** when available for traceability
2. **Use consistent field names** across all functions
3. **Include error_type and error_code** for all errors
4. **Log at appropriate levels** - don't overuse ERROR
5. **Avoid logging sensitive data** (PII, credentials, tokens)
6. **Use structured fields** instead of string interpolation
7. **Include context** - what operation, why it failed, what to do next

## Implementation Status

All shipment Lambda functions use structured logging:

✅ **create_shipment.py**
- Logs shipment creation with shipment_id, order_id, courier
- Logs errors with error_type and error_code
- Logs API calls with retry attempts

✅ **webhook_handler.py**
- Logs webhook processing with tracking_number, courier, status
- Logs state transitions
- Logs delivery confirmations and failures

✅ **get_shipment_status.py**
- Logs status queries with shipment_id or order_id
- Logs errors with error details

✅ **polling_fallback.py**
- Logs polling operations with shipment_id, courier
- Logs API queries and status updates

✅ **stale_shipment_detector.py**
- Logs stale shipment detection with counts
- Logs admin task creation
- Logs consumer notifications

## CloudWatch Metrics Integration

Structured logs are complemented by CloudWatch custom metrics:

- **ShipmentsCreated**: Count of shipments created
- **WebhooksProcessed**: Count of webhooks processed
- **DeliveryTime**: Time from creation to delivery (hours)
- **FailedDeliveries**: Count of failed deliveries
- **StaleShipments**: Count of stale shipments
- **LambdaErrors**: Count of Lambda errors by function

See `cloudwatch_metrics.py` for metric emission functions.

## Requirements Validation

This implementation satisfies:

✅ **Requirement 14.5**: Log all shipment actions with shipment_id, order_id
✅ **Requirement 14.5**: Log webhook events with tracking_number, courier
✅ **Requirement 14.5**: Log errors with stack traces
✅ **Requirement 14.5**: Use JSON format for easy parsing

## Next Steps

1. Set up CloudWatch Logs Insights dashboards
2. Configure log retention policies
3. Set up log-based alarms for critical errors
4. Export logs to S3 for long-term analysis
