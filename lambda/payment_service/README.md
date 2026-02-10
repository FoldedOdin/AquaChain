# Payment Service

Secure payment processing service for AquaChain with Razorpay integration and COD support.

## Features

- ✅ Razorpay online payment processing
- ✅ Cash on Delivery (COD) support
- ✅ Webhook handling for real-time updates
- ✅ Payment signature verification
- ✅ Secure credential management via AWS Secrets Manager
- ✅ Comprehensive audit logging
- ✅ Input validation and error handling

## Architecture

```
┌─────────────────┐
│  Frontend       │
│  (React)        │
└────────┬────────┘
         │
         ↓
┌─────────────────┐
│  API Gateway    │
└────────┬────────┘
         │
         ↓
┌─────────────────┐
│  Payment        │ ← Retrieves credentials from Secrets Manager
│  Service Lambda │ ← Processes payments
└────────┬────────┘ ← Stores records in DynamoDB
         │
         ↓
┌─────────────────┐
│  DynamoDB       │
│  (Payments)     │
└─────────────────┘
```

## API Endpoints

### 1. Create Razorpay Order

**POST** `/api/payments/create-razorpay-order`

Creates a Razorpay order for online payment.

**Request:**
```json
{
  "amount": 5000.00,
  "orderId": "order-123",
  "currency": "INR"
}
```

**Response:**
```json
{
  "success": true,
  "data": {
    "paymentId": "pay_order-123_1234567890",
    "razorpayOrder": {
      "id": "order_razorpay_123",
      "amount": 500000,
      "currency": "INR",
      "receipt": "order-123",
      "status": "created"
    }
  }
}
```

### 2. Verify Payment

**POST** `/api/payments/verify-payment`

Verifies Razorpay payment signature and updates status.

**Request:**
```json
{
  "paymentId": "pay_123",
  "orderId": "order-123",
  "signature": "abc123..."
}
```

**Response:**
```json
{
  "success": true,
  "data": {
    "paymentId": "pay_123",
    "status": "COMPLETED",
    "verified": true
  }
}
```

### 3. Create COD Payment

**POST** `/api/payments/create-cod-payment`

Creates a Cash on Delivery payment record.

**Request:**
```json
{
  "orderId": "order-123",
  "amount": 5000.00
}
```

**Response:**
```json
{
  "success": true,
  "data": {
    "paymentId": "cod_order-123_1234567890",
    "status": "COD_PENDING"
  }
}
```

### 4. Get Payment Status

**GET** `/api/payments/payment-status?orderId=order-123`

Retrieves payment status for an order.

**Response:**
```json
{
  "success": true,
  "data": {
    "paymentId": "pay_123",
    "status": "COMPLETED",
    "paymentMethod": "ONLINE",
    "amount": 5000.00,
    "createdAt": "2026-02-10T10:00:00Z",
    "updatedAt": "2026-02-10T10:05:00Z"
  }
}
```

### 5. Webhook Handler

**POST** `/api/webhooks/razorpay`

Handles Razorpay webhook events for payment status updates.

**Headers:**
```
X-Razorpay-Signature: <hmac_sha256_signature>
```

**Request:**
```json
{
  "event": "payment.captured",
  "payload": {
    "payment": {
      "id": "pay_123",
      "order_id": "order_razorpay_123",
      "amount": 500000,
      "status": "captured"
    }
  }
}
```

**Response:**
```json
{
  "success": true,
  "message": "Webhook processed successfully"
}
```

## Payment Status Flow

```
ONLINE Payment:
PENDING → PROCESSING → COMPLETED/FAILED

COD Payment:
COD_PENDING → COMPLETED (on delivery)

Cancelled:
ANY_STATUS → CANCELLED
```

## Environment Variables

| Variable | Description | Example |
|----------|-------------|---------|
| `PAYMENTS_TABLE_NAME` | DynamoDB payments table | `aquachain-table-payments-dev` |
| `ORDERS_TABLE_NAME` | DynamoDB orders table | `aquachain-table-orders-dev` |
| `RAZORPAY_SECRET_ARN` | AWS Secrets Manager ARN | `aquachain-secret-razorpay-credentials-dev` |

## AWS Secrets Manager Format

```json
{
  "key_id": "rzp_test_YOUR_KEY_ID",
  "key_secret": "YOUR_KEY_SECRET",
  "webhook_secret": "YOUR_WEBHOOK_SECRET"
}
```

## Security

### Credential Management
- ✅ Credentials stored in AWS Secrets Manager
- ✅ Never exposed in logs or responses
- ✅ Cached in memory for performance
- ✅ Automatic rotation support

### Signature Verification
- ✅ HMAC SHA256 signature verification
- ✅ Webhook signature validation
- ✅ Payment signature validation
- ✅ Constant-time comparison to prevent timing attacks

### Input Validation
- ✅ All inputs validated against schemas
- ✅ Amount range validation (1 - 1,000,000)
- ✅ String length validation
- ✅ Pattern matching for IDs

### Audit Logging
- ✅ All payment events logged
- ✅ User actions tracked
- ✅ Sensitive data redacted
- ✅ CloudWatch integration

## Testing

### Unit Tests

```bash
cd lambda/payment_service
pytest tests/unit/ -v
```

### Integration Tests

```bash
cd tests/integration
pytest test_payment_service.py -v
```

### Test with Mock Data

```python
from payment_service import PaymentService

service = PaymentService()

# Create Razorpay order
result = service.create_razorpay_order(
    amount=5000.00,
    order_id="test-order-123",
    currency="INR"
)

print(result)
```

## Monitoring

### CloudWatch Metrics

- `PaymentCreated` - Payment records created
- `PaymentCompleted` - Successful payments
- `PaymentFailed` - Failed payments
- `WebhookProcessed` - Webhooks handled

### CloudWatch Logs

```bash
# View payment service logs
aws logs tail /aws/lambda/aquachain-function-payment-service-dev --follow

# View webhook logs
aws logs tail /aws/lambda/aquachain-function-razorpay-webhook-dev --follow

# Filter for errors
aws logs tail /aws/lambda/aquachain-function-payment-service-dev \
  --follow \
  --filter-pattern "ERROR"
```

### Alarms

Set up CloudWatch alarms for:
- Payment failure rate > 5%
- Webhook processing errors
- Lambda execution errors
- DynamoDB throttling

## Error Handling

### Error Codes

| Code | Description | HTTP Status |
|------|-------------|-------------|
| `CREATE_RAZORPAY_ORDER_FAILED` | Order creation failed | 400 |
| `PAYMENT_VERIFICATION_FAILED` | Signature verification failed | 400 |
| `COD_PAYMENT_CREATION_FAILED` | COD payment creation failed | 400 |
| `GET_PAYMENT_STATUS_FAILED` | Status retrieval failed | 400 |
| `WEBHOOK_PROCESSING_FAILED` | Webhook processing failed | 500 |
| `PAYMENT_SERVICE_ERROR` | Unhandled error | 500 |

### Error Response Format

```json
{
  "success": false,
  "error": "Error message",
  "error_code": "ERROR_CODE"
}
```

## Deployment

### Deploy with CDK

```bash
cd infrastructure/cdk
cdk deploy AquaChain-Compute-dev
```

### Manual Deployment

```bash
# Package Lambda
cd lambda/payment_service
zip -r payment_service.zip .

# Upload to Lambda
aws lambda update-function-code \
  --function-name aquachain-function-payment-service-dev \
  --zip-file fileb://payment_service.zip
```

## Dependencies

```
boto3>=1.26.0
botocore>=1.29.0
```

## Configuration

### IAM Permissions Required

```json
{
  "Version": "2012-10-17",
  "Statement": [
    {
      "Effect": "Allow",
      "Action": [
        "secretsmanager:GetSecretValue"
      ],
      "Resource": "arn:aws:secretsmanager:*:*:secret:aquachain-secret-razorpay-credentials-*"
    },
    {
      "Effect": "Allow",
      "Action": [
        "dynamodb:PutItem",
        "dynamodb:GetItem",
        "dynamodb:UpdateItem",
        "dynamodb:Query"
      ],
      "Resource": [
        "arn:aws:dynamodb:*:*:table/aquachain-table-payments-*",
        "arn:aws:dynamodb:*:*:table/aquachain-table-payments-*/index/*"
      ]
    },
    {
      "Effect": "Allow",
      "Action": [
        "logs:CreateLogGroup",
        "logs:CreateLogStream",
        "logs:PutLogEvents"
      ],
      "Resource": "arn:aws:logs:*:*:*"
    }
  ]
}
```

## Troubleshooting

### Issue: "Payment service configuration error"

**Cause**: Cannot retrieve credentials from Secrets Manager

**Fix**:
1. Verify secret exists: `aws secretsmanager describe-secret --secret-id aquachain-secret-razorpay-credentials-dev`
2. Check IAM permissions
3. Verify secret format is correct JSON

### Issue: "Invalid payment signature"

**Cause**: Signature verification failed

**Fix**:
1. Verify Key Secret is correct in Secrets Manager
2. Check signature generation on frontend
3. Ensure order ID matches

### Issue: "Webhook signature verification failed"

**Cause**: Webhook secret mismatch

**Fix**:
1. Copy exact webhook secret from Razorpay dashboard
2. Update in Secrets Manager with webhook_secret field
3. Redeploy Lambda function

## Best Practices

1. **Always verify signatures** - Never skip signature verification
2. **Use test mode in development** - Use test keys for development
3. **Monitor payment logs** - Set up CloudWatch alarms
4. **Rotate credentials** - Rotate Razorpay keys periodically
5. **Handle idempotency** - Webhooks may be delivered multiple times
6. **Validate amounts** - Always validate payment amounts
7. **Audit everything** - Log all payment events for compliance

## Support

- **Documentation**: [RAZORPAY_SETUP.md](../../DOCS/guides/RAZORPAY_SETUP.md)
- **Quick Start**: [RAZORPAY_QUICK_START.md](../../DOCS/guides/RAZORPAY_QUICK_START.md)
- **Razorpay Docs**: https://razorpay.com/docs/
- **AWS Support**: https://aws.amazon.com/support/

---

**Version**: 1.0  
**Last Updated**: February 2026  
**Maintained By**: AquaChain Backend Team
