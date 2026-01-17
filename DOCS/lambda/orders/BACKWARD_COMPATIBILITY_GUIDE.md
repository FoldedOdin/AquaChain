# Backward Compatibility Guide

## Overview
This guide explains how the shipment tracking system maintains backward compatibility with existing order workflows.

## Key Principles

### 1. External Status Unchanged
- **DeviceOrders.status** remains "shipped" for external APIs
- Internal shipment states managed separately in Shipments table
- Existing UI components work without changes

### 2. Internal Fields Hidden
- `shipment_id` and `tracking_number` stored in DeviceOrders
- These fields NOT exposed in API responses
- Maintains existing API contract

### 3. Graceful Degradation
- System continues when Shipments table unavailable
- Orders proceed with manual tracking
- DevOps alerted automatically

## API Endpoints

### GET /api/orders
**Handler:** `lambda/orders/get_orders.py`

**Query Parameters:**
- `userId` - Filter by user ID (optional, admin only)
- `status` - Filter by status (optional)

**Response Format:**
```json
{
  "success": true,
  "orders": [
    {
      "orderId": "ord_123",
      "userId": "user_456",
      "status": "shipped",
      "deviceSKU": "AQ-001",
      "address": "123 Main St",
      "createdAt": "2025-01-01T00:00:00Z"
      // Note: shipment_id and tracking_number NOT included
    }
  ]
}
```

**Key Features:**
- ✅ Removes `shipment_id` and `tracking_number` from responses
- ✅ Preserves `status` field unchanged
- ✅ Role-based access control
- ✅ Supports filtering by status and userId

## Graceful Degradation

### When Shipments Table Unavailable

**Behavior:**
1. `create_shipment` catches `ResourceNotFoundException`
2. Falls back to manual tracking mode
3. Updates order status to "shipped" without shipment tracking
4. Sends DevOps alert via SNS
5. Logs error for monitoring

**Code Example:**
```python
try:
    # Attempt atomic transaction
    dynamodb_client.transact_write_items(...)
except ClientError as e:
    if e.response['Error']['Code'] == 'ResourceNotFoundException':
        # Graceful degradation
        alert_devops_shipments_table_unavailable(...)
        fallback_update_order_status(...)
```

**DevOps Alert:**
```json
{
  "alert_type": "SHIPMENTS_TABLE_UNAVAILABLE",
  "severity": "HIGH",
  "order_id": "ord_123",
  "shipment_id": "ship_456",
  "tracking_number": "TRACK789",
  "message": "Shipments table is unavailable. Order proceeding with manual tracking.",
  "action_required": "Check DynamoDB table status and restore if needed"
}
```

## Existing Workflow Preservation

### Technician Workflow
**Status:** ✅ Unchanged

**Flow:**
1. Technician queries orders by status
2. Accepts task (order status: "shipped")
3. Starts installation (status: "in_progress")
4. Completes installation (status: "completed")

**Key Points:**
- Shipment fields don't block task acceptance
- All status transitions work normally
- TechnicianId field remains functional

### Order Status Transitions
**Status:** ✅ Unchanged

**Valid Transitions:**
```
pending → approved → shipped → in_progress → completed
```

**Implementation:**
- Status updates work with or without shipment fields
- Old orders (without shipment fields) still work
- New orders (with shipment fields) work seamlessly

## Testing

### Run All Backward Compatibility Tests
```bash
# Backward compatibility tests
python -m pytest lambda/orders/test_backward_compatibility.py -v

# Graceful degradation tests
python -m pytest lambda/shipments/test_graceful_degradation.py -v

# Existing workflow tests
python -m pytest lambda/orders/test_existing_workflow.py -v
```

### Test Coverage
- ✅ API response format unchanged
- ✅ Shipment fields removed from responses
- ✅ Status field preserved
- ✅ Graceful degradation when table unavailable
- ✅ DevOps alerts sent correctly
- ✅ Fallback order updates work
- ✅ Technician workflow unchanged
- ✅ Installation flow works
- ✅ Order completion updates correctly
- ✅ Old orders (without shipment fields) work

## Deployment Checklist

### Pre-Deployment
- [ ] Review all test results (22 tests should pass)
- [ ] Verify SNS topic configured for DevOps alerts
- [ ] Confirm IAM roles have necessary permissions
- [ ] Test in staging environment

### Deployment
- [ ] Deploy `get_orders.py` Lambda function
- [ ] Configure API Gateway endpoint
- [ ] Update environment variables
- [ ] Enable CloudWatch logging

### Post-Deployment
- [ ] Monitor CloudWatch logs for errors
- [ ] Verify API responses match expected format
- [ ] Test with existing UI components
- [ ] Monitor for graceful degradation events
- [ ] Verify DevOps alerts working

## Monitoring

### CloudWatch Metrics
- **API Response Time**: Monitor GET /api/orders latency
- **Error Rate**: Track 4xx and 5xx errors
- **Graceful Degradation Events**: Count ResourceNotFoundException occurrences

### CloudWatch Logs
- Search for: `"Shipments table not found"`
- Search for: `"falling back to manual tracking"`
- Search for: `"DevOps alert sent"`

### SNS Alerts
- Monitor DevOps SNS topic for high-severity alerts
- Alert type: `SHIPMENTS_TABLE_UNAVAILABLE`

## Troubleshooting

### Issue: API Returns Shipment Fields
**Symptom:** API response includes `shipment_id` or `tracking_number`

**Solution:**
1. Verify `ensure_backward_compatibility()` is called
2. Check Lambda function version deployed
3. Review CloudWatch logs for errors

### Issue: Graceful Degradation Not Working
**Symptom:** Order creation fails when Shipments table unavailable

**Solution:**
1. Verify `ClientError` exception handling in `execute_atomic_transaction()`
2. Check error code is `ResourceNotFoundException`
3. Verify `fallback_update_order_status()` is called
4. Review CloudWatch logs for error details

### Issue: DevOps Alerts Not Sent
**Symptom:** No SNS notification when Shipments table unavailable

**Solution:**
1. Verify `SNS_TOPIC_ARN` environment variable set
2. Check IAM role has `sns:Publish` permission
3. Verify SNS topic exists and is active
4. Review CloudWatch logs for SNS errors

## Best Practices

### 1. Always Test Backward Compatibility
- Run all tests before deployment
- Verify existing UI components work
- Test with old orders (without shipment fields)

### 2. Monitor Graceful Degradation
- Set up CloudWatch alarms for ResourceNotFoundException
- Monitor DevOps SNS topic
- Track fallback order updates

### 3. Maintain API Contract
- Never expose internal shipment fields in API responses
- Keep status field unchanged
- Preserve existing response format

### 4. Handle Failures Gracefully
- Always catch DynamoDB errors
- Provide fallback mechanisms
- Alert DevOps for infrastructure issues

## References

### Code Files
- `lambda/orders/get_orders.py` - DeviceOrders API handler
- `lambda/shipments/create_shipment.py` - Shipment creation with graceful degradation
- `lambda/orders/test_backward_compatibility.py` - Backward compatibility tests
- `lambda/shipments/test_graceful_degradation.py` - Graceful degradation tests
- `lambda/orders/test_existing_workflow.py` - Existing workflow tests

### Requirements
- Requirement 8.1: DeviceOrders status unchanged
- Requirement 8.2: Existing APIs return expected status
- Requirement 8.3: Existing workflow functions
- Requirement 8.4: Graceful degradation

### Related Documentation
- `.kiro/specs/shipment-tracking-automation/requirements.md`
- `.kiro/specs/shipment-tracking-automation/design.md`
- `lambda/orders/TASK_17_COMPLETION_SUMMARY.md`
