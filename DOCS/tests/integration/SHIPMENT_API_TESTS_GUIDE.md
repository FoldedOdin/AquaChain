# Shipment API Integration Tests - Quick Guide

## Running the Tests

### Run All Tests
```bash
python -m pytest tests/integration/test_shipment_api_endpoints.py -v
```

### Run Specific Test Suite
```bash
# POST /api/shipments tests
python -m pytest tests/integration/test_shipment_api_endpoints.py::TestPostShipmentsEndpoint -v

# POST /api/webhooks/:courier tests
python -m pytest tests/integration/test_shipment_api_endpoints.py::TestPostWebhooksEndpoint -v

# GET /api/shipments/:shipmentId tests
python -m pytest tests/integration/test_shipment_api_endpoints.py::TestGetShipmentByIdEndpoint -v

# GET /api/shipments?orderId tests
python -m pytest tests/integration/test_shipment_api_endpoints.py::TestGetShipmentByOrderIdEndpoint -v

# Rate limiting tests
python -m pytest tests/integration/test_shipment_api_endpoints.py::TestRateLimiting -v

# End-to-end workflow tests
python -m pytest tests/integration/test_shipment_api_endpoints.py::TestEndToEndWorkflow -v
```

### Run Single Test
```bash
python -m pytest tests/integration/test_shipment_api_endpoints.py::TestPostShipmentsEndpoint::test_create_shipment_with_valid_auth -v
```

### Run with Coverage
```bash
python -m pytest tests/integration/test_shipment_api_endpoints.py --cov=lambda/shipments --cov-report=html
```

## Test Structure

### Test Classes
1. **TestPostShipmentsEndpoint** - Tests for shipment creation endpoint
2. **TestPostWebhooksEndpoint** - Tests for webhook callback endpoint
3. **TestGetShipmentByIdEndpoint** - Tests for shipment status by ID
4. **TestGetShipmentByOrderIdEndpoint** - Tests for shipment status by order ID
5. **TestRateLimiting** - Tests for rate limiting behavior
6. **TestEndToEndWorkflow** - Tests for complete workflows

### Fixtures
- `mock_aws_environment` - AWS environment variables
- `mock_dynamodb` - DynamoDB table operations
- `mock_dynamodb_client` - DynamoDB client for transactions
- `sample_order` - Sample order data
- `sample_shipment` - Sample shipment data
- `mock_context` - Lambda context

## Test Scenarios Covered

### Authentication & Authorization ✅
- Valid Cognito JWT authentication
- Missing authentication
- Invalid authentication
- Role-based access control

### Request Validation ✅
- Required fields validation
- Invalid JSON handling
- Missing parameters
- Malformed payloads

### Webhook Security ✅
- HMAC-SHA256 signature verification
- Invalid signature rejection
- Missing signature rejection
- Signature tampering detection

### Error Handling ✅
- 400 Bad Request
- 401 Unauthorized
- 404 Not Found
- 500 Internal Server Error

### Business Logic ✅
- Shipment creation flow
- Webhook processing
- Status retrieval
- Timeline updates
- Idempotency

## Current Test Results

**Total Tests**: 18
**Passing**: 10 (55.6%)
**Failing**: 8 (44.4%)

### Passing Tests ✅
- All POST /api/shipments tests (4/4)
- Webhook signature validation tests (2/5)
- All GET by shipment ID tests (3/3)
- Rate limiting simulation (1/2)

### Failing Tests ⚠️
- Webhook payload tests (3) - signature format issues
- Query parameter tests (3) - mock configuration
- High volume webhook test (1) - signature format
- End-to-end test (1) - signature format

## Troubleshooting

### Issue: Webhook Signature Mismatch
**Symptom**: Tests fail with 401 Unauthorized
**Cause**: JSON serialization format differs
**Fix**: Ensure consistent JSON formatting with `separators=(',', ':')`

### Issue: Query Parameter Tests Failing
**Symptom**: Tests fail with 500 errors
**Cause**: DynamoDB query mock not properly configured
**Fix**: Verify mock_dynamodb.query return value structure

### Issue: Import Errors
**Symptom**: Module not found errors
**Cause**: Python path not set correctly
**Fix**: Run from project root directory

## Next Steps

1. Fix webhook signature format consistency
2. Fix query parameter mock configuration
3. Add tests for multi-courier support
4. Add tests for delivery failure scenarios
5. Add performance/load tests
6. Add WebSocket notification tests

## Related Files

- **Test File**: `tests/integration/test_shipment_api_endpoints.py`
- **Lambda Handlers**:
  - `lambda/shipments/create_shipment.py`
  - `lambda/shipments/webhook_handler.py`
  - `lambda/shipments/get_shipment_status.py`
- **API Gateway Config**: `infrastructure/api_gateway/shipment_endpoints.py`
- **Summary**: `tests/integration/TASK_10_5_COMPLETION_SUMMARY.md`
