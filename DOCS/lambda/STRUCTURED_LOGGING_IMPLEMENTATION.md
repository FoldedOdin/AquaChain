# Structured Logging Implementation Summary

## Overview

Implemented structured logging across all AquaChain Lambda functions to provide consistent, JSON-formatted logs with standard fields for improved log aggregation, analysis, and monitoring.

## Implementation Details

### 1. StructuredLogger Class

Created `lambda/shared/structured_logger.py` with the following features:

- **JSON-formatted output**: All logs are output as JSON for easy parsing by log aggregation tools
- **Standard fields**: Every log entry includes:
  - `timestamp`: ISO 8601 formatted UTC timestamp
  - `level`: Log level (INFO, WARNING, ERROR, DEBUG, CRITICAL)
  - `message`: Human-readable log message
  - `service`: Service/Lambda function name
  - `request_id`: AWS request ID for tracing (optional)
  - `user_id`: User identifier (optional)
- **Custom fields**: Support for additional fields via kwargs (e.g., `device_id`, `duration_ms`, `error_code`)
- **Convenience methods**: `info()`, `warning()`, `error()`, `debug()`, `critical()`

### 2. Updated Lambda Functions

Replaced standard Python logging with StructuredLogger in the following Lambda functions:

#### Main Lambda Handlers
- `lambda/data_processing/handler.py` - Data processing service
- `lambda/auth_service/handler.py` - Authentication service
- `lambda/user_management/handler.py` - User management service
- `lambda/ml_inference/handler.py` - ML inference service
- `lambda/notification_service/handler.py` - Notification service
- `lambda/websocket_api/handler.py` - WebSocket API handler
- `lambda/websocket_api/broadcast_handler.py` - WebSocket broadcast handler
- `lambda/technician_service/handler.py` - Technician service
- `lambda/slo_calculator/handler.py` - SLO calculator
- `lambda/pagerduty_integration/handler.py` - PagerDuty integration

#### Utility Modules
- `lambda/user_management/user_utils.py`
- `lambda/technician_service/service_request_manager.py`
- `lambda/technician_service/location_service.py`
- `lambda/technician_service/availability_manager.py`
- `lambda/technician_service/assignment_algorithm.py`

#### Shared Modules
- `lambda/shared/error_handler.py`
- `lambda/shared/security_middleware.py`
- `lambda/shared/security_integration_example.py`
- `lambda/shared/encryption_manager.py`
- `lambda/shared/audit_logger.py`

### 3. Enhanced Logging in data_processing Lambda

Added comprehensive structured logging with performance metrics:

```python
# Request tracking
logger.info(
    "Processing IoT data event",
    request_id=request_id,
    event_source=event.get('Records', [{}])[0].get('eventSource')
)

# Performance metrics
duration_ms = (datetime.utcnow() - start_time).total_seconds() * 1000
logger.info(
    "Data processing completed successfully",
    request_id=request_id,
    device_id=validated_data['deviceId'],
    wqi=ml_results['wqi'],
    anomaly_type=ml_results['anomalyType'],
    duration_ms=duration_ms
)

# Error logging with context
logger.error(
    "Data validation error",
    request_id=request_id,
    error_code='VALIDATION_ERROR',
    error_message=str(e)
)
```

### 4. Removed Print Statements

Replaced or removed print statements in:
- `lambda/shared/xray_utils.py` - Replaced with silent error handling
- `lambda/pagerduty_integration/handler.py` - Replaced with structured logging
- `lambda/ml_training/training_data_validator.py` - Removed for performance

## Usage Examples

### Basic Logging

```python
from structured_logger import get_logger

logger = get_logger(__name__, service='my-service')

# Simple info log
logger.info("Processing started")

# Log with custom fields
logger.info(
    "User action completed",
    user_id="user-123",
    action="login",
    duration_ms=150
)
```

### Request Tracking

```python
def lambda_handler(event, context):
    request_id = context.request_id
    start_time = datetime.utcnow()
    
    logger.info(
        "Request received",
        request_id=request_id,
        event_type=event.get('type')
    )
    
    # ... processing ...
    
    duration_ms = (datetime.utcnow() - start_time).total_seconds() * 1000
    logger.info(
        "Request completed",
        request_id=request_id,
        duration_ms=duration_ms
    )
```

### Error Logging

```python
try:
    # ... operation ...
except Exception as e:
    logger.error(
        "Operation failed",
        request_id=request_id,
        error_code='OPERATION_ERROR',
        error_message=str(e),
        device_id=device_id
    )
```

## Log Output Format

Example structured log entry:

```json
{
  "timestamp": "2025-10-25T12:34:56.789Z",
  "level": "INFO",
  "message": "Data processing completed successfully",
  "service": "data-processing",
  "request_id": "abc-123-def-456",
  "device_id": "DEV-1234",
  "wqi": 85.5,
  "anomaly_type": "normal",
  "duration_ms": 245.3
}
```

## Benefits

1. **Consistent Format**: All logs follow the same JSON structure
2. **Easy Parsing**: JSON format enables easy parsing by CloudWatch Insights, Elasticsearch, etc.
3. **Request Tracing**: request_id field enables end-to-end request tracing
4. **Performance Monitoring**: duration_ms field tracks operation performance
5. **Contextual Information**: Custom fields provide rich context for debugging
6. **Searchable**: Structured fields enable efficient log searching and filtering

## CloudWatch Insights Queries

Example queries for the new structured logs:

```
# Find slow operations
fields @timestamp, message, service, duration_ms
| filter duration_ms > 500
| sort duration_ms desc

# Track errors by service
fields @timestamp, service, error_code, error_message
| filter level = "ERROR"
| stats count() by service

# Monitor specific device
fields @timestamp, message, wqi, anomaly_type
| filter device_id = "DEV-1234"
| sort @timestamp desc

# Request tracing
fields @timestamp, service, message
| filter request_id = "abc-123-def-456"
| sort @timestamp asc
```

## Next Steps

1. Configure CloudWatch log retention policies
2. Set up CloudWatch Insights dashboards for monitoring
3. Create CloudWatch alarms for error rates and performance thresholds
4. Integrate with centralized logging system (e.g., Elasticsearch, Splunk)
5. Add log sampling for high-volume operations if needed

## Requirements Satisfied

- ✅ Requirement 2.5: Standardize logging patterns across all services using structured logging with consistent fields
- ✅ JSON-formatted logging with standard fields (timestamp, level, message, service, request_id, user_id)
- ✅ Support for custom fields via kwargs
- ✅ Replaced print statements and basic logging with StructuredLogger
- ✅ Added request_id tracking throughout request lifecycle
- ✅ Log performance metrics (duration_ms) for key operations
