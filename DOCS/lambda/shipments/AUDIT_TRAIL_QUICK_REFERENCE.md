# Audit Trail Quick Reference Guide

## Quick Start

```python
from audit_trail import (
    create_timeline_entry,
    create_webhook_event,
    create_admin_action_log,
    validate_audit_trail_completeness,
    calculate_ttl_timestamp
)
```

## Common Tasks

### 1. Create Timeline Entry

```python
# Create a timeline entry for status change
timeline_entry = create_timeline_entry(
    status='in_transit',
    timestamp='2025-01-01T12:00:00Z',
    location='Mumbai Hub',
    description='Package in transit to destination'
)

# Result:
# {
#   'status': 'in_transit',
#   'timestamp': '2025-01-01T12:00:00Z',
#   'location': 'Mumbai Hub',
#   'description': 'Package in transit to destination'
# }
```

### 2. Store Webhook Event

```python
# Store webhook event with automatic truncation
webhook_event = create_webhook_event(
    event_id='evt_abc123',
    courier_status='IN_TRANSIT',
    raw_payload={'waybill': 'TEST123', 'Status': 'In Transit'},
    max_payload_size=1000  # Optional, defaults to 1000
)

# Result:
# {
#   'event_id': 'evt_abc123',
#   'received_at': '2025-01-01T12:00:00Z',
#   'courier_status': 'IN_TRANSIT',
#   'raw_payload': '{"waybill": "TEST123", ...}',
#   'truncated': False
# }
```

### 3. Log Admin Action

```python
# Log admin intervention
admin_action = create_admin_action_log(
    action_type='ADDRESS_CHANGED',
    user_id='admin-user-123',
    details={
        'old_address': '123 Old St',
        'new_address': '456 New St',
        'reason': 'Customer requested address correction'
    }
)

# Result:
# {
#   'action_type': 'ADDRESS_CHANGED',
#   'user_id': 'admin-user-123',
#   'timestamp': '2025-01-01T12:00:00Z',
#   'details': {...}
# }
```

### 4. Calculate TTL

```python
# Calculate TTL for 2-year retention
ttl_timestamp = calculate_ttl_timestamp(years=2)

# Add to shipment
shipment_item = {
    'shipment_id': 'ship_xxx',
    'audit_ttl': ttl_timestamp  # Unix timestamp
}
```

### 5. Validate Audit Trail

```python
# Validate complete audit trail
validation = validate_audit_trail_completeness(shipment)

if validation['valid']:
    print("✓ Audit trail is complete")
else:
    print("Errors:", validation['errors'])
    print("Warnings:", validation['warnings'])
```

## Integration Examples

### In create_shipment.py

```python
from audit_trail import create_timeline_entry, create_admin_action_log, calculate_ttl_timestamp

# Create initial timeline entry
timeline_entry = create_timeline_entry(
    status='shipment_created',
    timestamp=current_timestamp,
    location='Warehouse',
    description='Shipment created and handed to courier'
)

# Log admin action
admin_action = create_admin_action_log(
    action_type='SHIPMENT_CREATED',
    user_id=user_id,
    details={'courier': courier_name, 'tracking': tracking_number}
)

# Calculate TTL
ttl_timestamp = calculate_ttl_timestamp(years=2)

# Build shipment item
shipment_item = {
    'shipment_id': shipment_id,
    'timeline': [timeline_entry],
    'admin_actions': [admin_action],
    'audit_ttl': ttl_timestamp
}
```

### In webhook_handler.py

```python
from audit_trail import create_timeline_entry, create_webhook_event

# Create timeline entry
timeline_entry = create_timeline_entry(
    status=internal_status,
    timestamp=webhook_timestamp,
    location=webhook_location,
    description=webhook_description
)

# Create webhook event
webhook_event = create_webhook_event(
    event_id=event_id,
    courier_status=courier_status,
    raw_payload=raw_webhook_payload
)

# Update shipment
update_expression = 'SET timeline = list_append(timeline, :timeline), ' \
                   'webhook_events = list_append(webhook_events, :event)'
```

### In admin_intervention.py

```python
from audit_trail import create_admin_action_log, create_timeline_entry

# Log admin action
admin_action = create_admin_action_log(
    action_type='ADDRESS_CHANGED',
    user_id=user_id,
    details={'new_address': new_address, 'reason': reason}
)

# Create timeline entry
timeline_entry = create_timeline_entry(
    status='address_changed',
    timestamp=current_timestamp,
    location='Admin Portal',
    description=f'Address updated: {reason}'
)

# Update shipment
update_expression = 'SET admin_actions = list_append(admin_actions, :action), ' \
                   'timeline = list_append(timeline, :timeline)'
```

## Validation Functions

### Validate Timeline Entry

```python
from audit_trail import validate_timeline_entry

entry = {
    'status': 'in_transit',
    'timestamp': '2025-01-01T12:00:00Z',
    'location': 'Mumbai Hub',
    'description': 'Package in transit'
}

is_valid = validate_timeline_entry(entry)
# Returns: True if all required fields present and non-empty
```

### Validate Timeline Chronology

```python
from audit_trail import validate_timeline_chronology

timeline = [
    {'status': 'created', 'timestamp': '2025-01-01T10:00:00Z', ...},
    {'status': 'picked_up', 'timestamp': '2025-01-01T12:00:00Z', ...},
    {'status': 'in_transit', 'timestamp': '2025-01-01T14:00:00Z', ...}
]

is_chronological = validate_timeline_chronology(timeline)
# Returns: True if timestamps are in ascending order
```

### Sort Timeline

```python
from audit_trail import sort_timeline_chronologically

# Sort timeline by timestamp
sorted_timeline = sort_timeline_chronologically(timeline)
```

## Reporting

### Generate Audit Report

```python
from audit_trail import generate_audit_report

# Generate human-readable report
report = generate_audit_report(shipment)
print(report)

# Output:
# ================================================================================
# SHIPMENT AUDIT REPORT
# ================================================================================
# Shipment ID: ship_xxx
# Order ID: ord_xxx
# ...
```

## Configuration

### Enable TTL on DynamoDB

```bash
# Run configuration script
python infrastructure/dynamodb/configure_shipments_ttl.py

# Verify TTL status
aws dynamodb describe-time-to-live --table-name aquachain-shipments
```

### Set Up S3 Archival

```bash
# Configure environment variables
export SHIPMENTS_TABLE=aquachain-shipments
export ARCHIVE_BUCKET=aquachain-shipment-archives

# Run archival Lambda
python lambda/shipments/archive_to_s3.py
```

## Testing

### Run All Tests

```bash
# Audit trail verification
python lambda/shipments/verify_audit_trail.py

# Webhook event storage
python lambda/shipments/test_webhook_event_storage.py

# Admin action logging
python lambda/shipments/test_admin_action_logging.py

# Data retention policy
python lambda/shipments/test_data_retention_policy.py
```

## Troubleshooting

### Timeline Entry Validation Fails

**Problem:** `validate_timeline_entry()` returns False

**Solution:**
```python
# Check for missing fields
required_fields = ['status', 'timestamp', 'location', 'description']
for field in required_fields:
    if field not in entry or not entry[field]:
        print(f"Missing or empty: {field}")
```

### Timeline Not Chronological

**Problem:** `validate_timeline_chronology()` returns False

**Solution:**
```python
# Sort timeline before validation
from audit_trail import sort_timeline_chronologically
sorted_timeline = sort_timeline_chronologically(timeline)
```

### Webhook Payload Too Large

**Problem:** DynamoDB item size limit exceeded

**Solution:**
```python
# Reduce max_payload_size
webhook_event = create_webhook_event(
    event_id=event_id,
    courier_status=status,
    raw_payload=payload,
    max_payload_size=500  # Reduce from default 1000
)
```

### TTL Not Deleting Items

**Problem:** Items past expiration still in table

**Solution:**
```bash
# Check TTL configuration
aws dynamodb describe-time-to-live --table-name aquachain-shipments

# Re-enable if needed
python infrastructure/dynamodb/configure_shipments_ttl.py
```

## Best Practices

1. **Always validate timeline entries** before adding to shipment
2. **Use create_* functions** instead of manual dictionary creation
3. **Check audit trail completeness** before marking shipment as complete
4. **Log all admin actions** with detailed information
5. **Set TTL on all shipments** for automatic cleanup
6. **Archive before deletion** for compliance
7. **Monitor CloudWatch metrics** for audit trail health

## API Reference

### create_timeline_entry()
- **Purpose:** Create properly formatted timeline entry
- **Required:** status, timestamp, location, description
- **Returns:** Dictionary with timeline entry

### create_webhook_event()
- **Purpose:** Create webhook event with truncation
- **Required:** event_id, courier_status, raw_payload
- **Optional:** max_payload_size (default 1000)
- **Returns:** Dictionary with webhook event

### create_admin_action_log()
- **Purpose:** Log admin action
- **Required:** action_type, user_id
- **Optional:** details
- **Returns:** Dictionary with admin action

### calculate_ttl_timestamp()
- **Purpose:** Calculate TTL for retention period
- **Optional:** years (default 2)
- **Returns:** Unix timestamp (integer)

### validate_audit_trail_completeness()
- **Purpose:** Validate complete audit trail
- **Required:** shipment dictionary
- **Returns:** {'valid': bool, 'errors': list, 'warnings': list}

### generate_audit_report()
- **Purpose:** Generate human-readable report
- **Required:** shipment dictionary
- **Returns:** Formatted string

## Support

For questions or issues:
1. Check `DATA_RETENTION_POLICY.md` for detailed documentation
2. Review `TASK_18_COMPLETION_SUMMARY.md` for implementation details
3. Run verification scripts to diagnose issues
4. Check CloudWatch logs for error messages
