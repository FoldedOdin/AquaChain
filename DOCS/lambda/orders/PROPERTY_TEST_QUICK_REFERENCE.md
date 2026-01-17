# Property Test Quick Reference

## Running the Tests

### Run Property-Based Tests
```bash
python -m pytest lambda/orders/test_backward_compatibility_preservation.py -v
```

### Run All Backward Compatibility Tests
```bash
python -m pytest lambda/orders/test_backward_compatibility*.py -v
```

### Run with Coverage
```bash
python -m pytest lambda/orders/test_backward_compatibility_preservation.py --cov=lambda/orders --cov-report=html
```

## Test File Structure

```
lambda/orders/
├── get_orders.py                                    # Implementation
├── test_backward_compatibility.py                   # Unit tests (9 tests)
└── test_backward_compatibility_preservation.py      # Property tests (11 tests)
```

## Property 8: Backward Compatibility Preservation

### What It Tests
For any existing API endpoint that queries order status, the response format and status values must remain unchanged when the Shipments table is introduced.

### Requirements Validated
- **8.2:** Existing APIs return expected status without exposing internal shipment states
- **8.3:** Existing workflow continues to function

## Key Test Cases

### 1. Shipment Fields Never Exposed
```python
@given(order_id=..., shipment_id=..., tracking_number=...)
def test_shipment_fields_are_never_exposed(...)
```
**Validates:** shipment_id, tracking_number, internal_status are removed

### 2. External Status Remains Unchanged
```python
@given(order_id=..., status=...)
def test_external_status_remains_unchanged(...)
```
**Validates:** Status field preserved exactly

### 3. Internal Status Never Exposed
```python
@given(order_id=..., internal_status=...)
def test_internal_status_never_exposed(...)
```
**Validates:** Internal shipment states not leaked

### 4. Backward Compatibility is Idempotent
```python
@given(orders=...)
def test_backward_compatibility_is_idempotent(...)
```
**Validates:** Multiple applications produce same result

## Bug Found and Fixed

### Issue
The `ensure_backward_compatibility` function was not removing `internal_status` field.

### Fix
```python
# Added to lambda/orders/get_orders.py
if 'internal_status' in compatible_order:
    del compatible_order['internal_status']
```

### How It Was Found
Property test `test_internal_status_never_exposed` generated random orders with `internal_status` and verified removal.

## Test Results

```
Property Tests: 11/11 PASSED (700+ examples)
Unit Tests:     9/9 PASSED
Total:          20/20 PASSED
Bugs Found:     1
Bugs Fixed:     1
```

## Fields That Must Be Removed

The following fields exist in DynamoDB but must NOT be exposed in API responses:

1. ✅ `shipment_id` - Internal shipment reference
2. ✅ `tracking_number` - Courier tracking number
3. ✅ `internal_status` - Internal shipment state

## Fields That Must Be Preserved

The following fields must always be present and unchanged:

1. ✅ `orderId` - Order identifier
2. ✅ `userId` - User identifier
3. ✅ `status` - External order status (e.g., "shipped")
4. ✅ `deviceSKU` - Device model
5. ✅ `address` - Delivery address
6. ✅ `createdAt` - Creation timestamp

## Property Test Strategies

### Hypothesis Strategies Used
```python
order_id_strategy = st.text(alphabet='a-z0-9_-', min_size=10, max_size=30)
user_id_strategy = st.text(alphabet='a-z0-9_-', min_size=10, max_size=30)
shipment_id_strategy = st.text(alphabet='a-z0-9_-', min_size=10, max_size=30)
tracking_number_strategy = st.text(alphabet='A-Z0-9', min_size=8, max_size=20)
order_status_strategy = st.sampled_from(['pending', 'approved', 'shipped', ...])
internal_shipment_status_strategy = st.sampled_from(['shipment_created', ...])
```

### Test Settings
```python
@settings(max_examples=100, deadline=None)
```

## Common Test Patterns

### Pattern 1: Field Removal
```python
@given(order_with_field=...)
def test_field_removed(...):
    result = ensure_backward_compatibility([order])
    assert 'field_name' not in result[0]
```

### Pattern 2: Field Preservation
```python
@given(order=...)
def test_field_preserved(...):
    result = ensure_backward_compatibility([order])
    assert result[0]['field_name'] == order['field_name']
```

### Pattern 3: Idempotency
```python
@given(orders=...)
def test_idempotent(...):
    result1 = ensure_backward_compatibility(orders)
    result2 = ensure_backward_compatibility(result1)
    assert result1 == result2
```

## Debugging Failed Tests

### View Failing Example
When a property test fails, Hypothesis shows the failing example:
```
Falsifying example: test_internal_status_never_exposed(
    order_id='0000000000',
    user_id='0000000000',
    internal_status='shipment_created',
    shipment_id='0000000000',
)
```

### Reproduce Specific Example
```python
def test_specific_case():
    order_id = '0000000000'
    user_id = '0000000000'
    internal_status = 'shipment_created'
    # ... test with specific values
```

## Integration with CI/CD

### GitHub Actions
```yaml
- name: Run Property Tests
  run: |
    python -m pytest lambda/orders/test_backward_compatibility_preservation.py -v
```

### Pre-commit Hook
```bash
#!/bin/bash
python -m pytest lambda/orders/test_backward_compatibility_preservation.py --tb=short
```

## Performance

### Test Execution Time
- Property tests: ~3 seconds (700+ examples)
- Unit tests: ~1 second (9 examples)
- Total: ~4 seconds

### Optimization Tips
1. Use `@settings(max_examples=50)` for faster feedback during development
2. Use `@settings(max_examples=100)` for comprehensive validation
3. Use `deadline=None` to avoid timeout issues

## Troubleshooting

### Test Fails with "internal_status not removed"
**Solution:** Ensure `ensure_backward_compatibility` removes all three fields:
- shipment_id
- tracking_number
- internal_status

### Test Fails with "Status changed"
**Solution:** Verify external status is preserved, not replaced with internal status

### Test Fails with "Field missing"
**Solution:** Ensure essential fields (orderId, userId, status) are preserved

## Related Documentation

- **Implementation:** `lambda/orders/get_orders.py`
- **Unit Tests:** `lambda/orders/test_backward_compatibility.py`
- **Property Tests:** `lambda/orders/test_backward_compatibility_preservation.py`
- **Requirements:** `.kiro/specs/shipment-tracking-automation/requirements.md` (Requirement 8)
- **Design:** `.kiro/specs/shipment-tracking-automation/design.md` (Property 8)
- **Task Summary:** `lambda/orders/TASK_17_4_COMPLETION_SUMMARY.md`

## Quick Commands

```bash
# Run property tests
pytest lambda/orders/test_backward_compatibility_preservation.py -v

# Run with verbose output
pytest lambda/orders/test_backward_compatibility_preservation.py -vv

# Run specific test
pytest lambda/orders/test_backward_compatibility_preservation.py::TestBackwardCompatibilityPreservation::test_internal_status_never_exposed -v

# Run with coverage
pytest lambda/orders/test_backward_compatibility_preservation.py --cov=lambda/orders

# Run all backward compatibility tests
pytest lambda/orders/test_backward_compatibility*.py -v
```

## Success Criteria

✅ All 11 property tests pass
✅ All 9 unit tests pass
✅ No shipment fields exposed in API responses
✅ External status preserved
✅ Backward compatibility maintained
✅ Bug found and fixed

---

**Status:** ✅ COMPLETE
**Test Results:** 20/20 PASSED
**Coverage:** Requirements 8.2, 8.3
