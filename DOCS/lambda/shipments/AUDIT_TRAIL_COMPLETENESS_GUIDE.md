# Audit Trail Completeness - Quick Reference

## Property 12: Audit Trail Completeness

**Statement:** *For any* shipment, the webhook_events array must contain all received webhook payloads, and the timeline array must contain all status transitions in chronological order.

**Validates:** Requirements 15.2, 15.4

---

## What This Property Guarantees

### 1. Webhook Events Completeness
- ✅ All received webhook payloads are stored
- ✅ No webhook events are lost
- ✅ Each event has: event_id, received_at, courier_status, raw_payload
- ✅ Raw payloads are preserved (truncated if > 1000 chars)

### 2. Timeline Completeness
- ✅ All status transitions are recorded
- ✅ No status changes are lost
- ✅ Each entry has: status, timestamp, location, description
- ✅ Timeline is chronologically ordered

### 3. Consistency
- ✅ N webhook events = N+1 timeline entries (including creation)
- ✅ Each webhook event corresponds to a timeline entry
- ✅ Complete history is reconstructable

---

## Why This Matters

### Compliance
- Regulatory requirements for audit trails
- Data retention policies (2 years)
- Forensic analysis capabilities

### Dispute Resolution
- Complete event history
- Timestamp verification
- Status change tracking

### Debugging
- Webhook troubleshooting
- Timeline reconstruction
- Event correlation

---

## How It Works

### Webhook Event Storage

```python
# When webhook is received
webhook_event = {
    'event_id': 'evt_abc123',           # Deterministic ID
    'received_at': '2025-01-01T12:00:00Z',
    'courier_status': 'IN_TRANSIT',
    'raw_payload': '{"waybill":"..."}',  # Original payload
    'truncated': False                   # Truncation flag
}

# Append to webhook_events array
shipment['webhook_events'].append(webhook_event)
```

### Timeline Entry Storage

```python
# When status changes
timeline_entry = {
    'status': 'in_transit',              # Internal status
    'timestamp': '2025-01-01T12:00:00Z',
    'location': 'Mumbai Hub',
    'description': 'Package in transit'
}

# Append to timeline array
shipment['timeline'].append(timeline_entry)
```

### Atomic Updates

Both arrays are updated atomically in DynamoDB:

```python
shipments_table.update_item(
    Key={'shipment_id': shipment_id},
    UpdateExpression=(
        'SET timeline = list_append(timeline, :timeline), '
        'webhook_events = list_append(webhook_events, :webhook)'
    ),
    ExpressionAttributeValues={
        ':timeline': [timeline_entry],
        ':webhook': [webhook_event]
    }
)
```

---

## Testing Strategy

### Property-Based Tests

7 comprehensive tests verify:

1. **All webhook events preserved** (1-10 events)
2. **All status transitions recorded** (1-10 transitions)
3. **Webhook-timeline consistency** (2-8 events)
4. **Scalability with many events** (3-10 events)
5. **New shipment baseline** (minimal audit trail)
6. **Raw payload preservation** (varying sizes)
7. **Compliance query support** (timestamp/status queries)

### Test Execution

```bash
# Run all audit trail completeness tests
python -m pytest lambda/shipments/test_audit_trail_completeness.py -v

# Run specific test
python -m pytest lambda/shipments/test_audit_trail_completeness.py::TestAuditTrailCompleteness::test_all_webhook_events_are_preserved -v

# Run with Hypothesis verbosity
python -m pytest lambda/shipments/test_audit_trail_completeness.py -v --hypothesis-show-statistics
```

---

## Common Scenarios

### Scenario 1: Normal Shipment Lifecycle

```
Timeline:
1. shipment_created (2025-01-01 10:00)
2. picked_up (2025-01-01 11:00)
3. in_transit (2025-01-01 14:00)
4. out_for_delivery (2025-01-02 09:00)
5. delivered (2025-01-02 15:00)

Webhook Events:
1. evt_001 - PICKED_UP
2. evt_002 - IN_TRANSIT
3. evt_003 - OUT_FOR_DELIVERY
4. evt_004 - DELIVERED

Result: ✅ Complete audit trail (5 timeline, 4 webhooks)
```

### Scenario 2: Delivery Failure with Retries

```
Timeline:
1. shipment_created
2. picked_up
3. in_transit
4. out_for_delivery
5. delivery_failed (attempt 1)
6. in_transit
7. out_for_delivery
8. delivered

Webhook Events:
1-7. Corresponding webhook events

Result: ✅ Complete audit trail with retry history
```

### Scenario 3: Out-of-Order Webhooks

```
Webhooks Received:
1. IN_TRANSIT (12:00)
2. PICKED_UP (11:00)  ← Out of order
3. OUT_FOR_DELIVERY (14:00)

Timeline (sorted):
1. shipment_created (10:00)
2. picked_up (11:00)
3. in_transit (12:00)
4. out_for_delivery (14:00)

Result: ✅ Timeline chronologically ordered despite webhook order
```

---

## Validation Functions

### Check Audit Trail Completeness

```python
from audit_trail import validate_audit_trail_completeness

# Validate shipment audit trail
result = validate_audit_trail_completeness(shipment)

if result['valid']:
    print("✅ Audit trail is complete")
else:
    print("❌ Audit trail issues:")
    for error in result['errors']:
        print(f"  - {error}")
```

### Generate Audit Report

```python
from audit_trail import generate_audit_report

# Generate human-readable report
report = generate_audit_report(shipment)
print(report)
```

---

## Troubleshooting

### Issue: Missing Webhook Events

**Symptom:** Timeline has entries but webhook_events is empty

**Cause:** Webhooks not being received or stored

**Solution:**
1. Check webhook endpoint configuration
2. Verify signature validation
3. Check DynamoDB update expressions

### Issue: Timeline Out of Order

**Symptom:** Timeline entries not chronologically ordered

**Cause:** Out-of-order webhook processing

**Solution:**
1. Use `sort_timeline_chronologically()` utility
2. Validate timestamps before insertion
3. Check webhook timestamp parsing

### Issue: Inconsistent Counts

**Symptom:** webhook_events count ≠ timeline count - 1

**Cause:** Atomic update failure or missing entries

**Solution:**
1. Check DynamoDB transaction logs
2. Verify both arrays updated atomically
3. Check for error handling gaps

---

## Best Practices

### 1. Always Update Atomically

```python
# ✅ GOOD: Atomic update
update_expression = (
    'SET timeline = list_append(timeline, :timeline), '
    'webhook_events = list_append(webhook_events, :webhook)'
)

# ❌ BAD: Separate updates
update_timeline()
update_webhook_events()  # Could fail, leaving inconsistent state
```

### 2. Validate Before Storage

```python
# Validate timeline entry
if not validate_timeline_entry(entry):
    log_error("Invalid timeline entry")
    return

# Validate webhook event
if not all(k in event for k in ['event_id', 'received_at', 'courier_status']):
    log_error("Invalid webhook event")
    return
```

### 3. Handle Large Payloads

```python
# Truncate large payloads
max_size = 1000
payload_str = json.dumps(raw_payload)

if len(payload_str) > max_size:
    payload_str = payload_str[:max_size]
    truncated = True
```

### 4. Maintain Chronological Order

```python
# Sort timeline if needed
timeline = sort_timeline_chronologically(timeline)

# Validate order
assert validate_timeline_chronology(timeline)
```

---

## Related Documentation

- [Audit Trail Implementation](./audit_trail.py)
- [Webhook Handler](./webhook_handler.py)
- [Requirements 15.2, 15.4](../../.kiro/specs/shipment-tracking-automation/requirements.md)
- [Design Property 12](../../.kiro/specs/shipment-tracking-automation/design.md)

---

## Quick Commands

```bash
# Run audit trail tests
pytest lambda/shipments/test_audit_trail_completeness.py -v

# Validate specific shipment
python lambda/shipments/verify_audit_trail.py --shipment-id ship_123

# Generate audit report
python lambda/shipments/verify_audit_trail.py --shipment-id ship_123 --report

# Check all shipments
python lambda/shipments/verify_audit_trail.py --check-all
```

---

**Last Updated:** January 1, 2026  
**Property Status:** ✅ TESTED AND VALIDATED
