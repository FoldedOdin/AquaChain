# Shipment Tracking API Gateway Endpoints

This document describes the API Gateway endpoints for the Shipment Tracking Automation subsystem.

## Overview

The shipment tracking system exposes 4 REST API endpoints through AWS API Gateway:

1. **POST /api/shipments** - Create new shipment
2. **POST /api/webhooks/{courier}** - Receive courier webhook callbacks
3. **GET /api/shipments/{shipmentId}** - Get shipment status by ID
4. **GET /api/shipments?orderId={orderId}** - Get shipment status by order ID

## Endpoints

### 1. POST /api/shipments

**Purpose:** Create a new shipment record when marking an order as shipped.

**Authentication:** Cognito User Pools (Admin role required)

**Rate Limit:** 100 requests/minute

**Request:**
```json
{
  "order_id": "ord_1735392000000",
  "courier_name": "Delhivery",
  "service_type": "Surface",
  "destination": {
    "address": "123 Main St, Bangalore",
    "pincode": "560001",
    "contact_name": "John Doe",
    "contact_phone": "+919876543210"
  },
  "package_details": {
    "weight": "0.5kg",
    "declared_value": 5000,
    "insurance": true
  }
}
```

**Response:**
```json
{
  "success": true,
  "shipment_id": "ship_1735478400000",
  "tracking_number": "DELHUB123456789",
  "estimated_delivery": "2025-12-31T18:00:00Z"
}
```

**Lambda Function:** `create_shipment`

**Requirements:** 1.1

---

### 2. POST /api/webhooks/{courier}

**Purpose:** Receive real-time status updates from courier services.

**Authentication:** None (HMAC-SHA256 signature verification in Lambda)

**Rate Limit:** 1000 requests/minute

**Path Parameters:**
- `courier` - Courier name (delhivery, bluedart, dtdc)

**Headers:**
- `X-Webhook-Signature` - HMAC-SHA256 signature for verification

**Request (Delhivery format):**
```json
{
  "waybill": "DELHUB123456789",
  "Status": "In Transit",
  "Scans": [{
    "ScanDetail": {
      "ScanDateTime": "2025-12-29T18:00:00Z",
      "ScannedLocation": "Pune Hub",
      "Instructions": "Package in transit"
    }
  }]
}
```

**Response:**
```json
{
  "success": true,
  "processed": "ship_1735478400000"
}
```

**Lambda Function:** `webhook_handler`

**Requirements:** 2.1, 10.5

**Security:**
- No Cognito authentication (public endpoint)
- HMAC-SHA256 signature verification in Lambda
- Rejects requests with invalid/missing signatures (401 Unauthorized)

---

### 3. GET /api/shipments/{shipmentId}

**Purpose:** Retrieve shipment status and timeline by shipment ID.

**Authentication:** Cognito User Pools (All roles: Admin, Consumer, Technician)

**Rate Limit:** 200 requests/minute

**Path Parameters:**
- `shipmentId` - Unique shipment identifier

**Response:**
```json
{
  "success": true,
  "shipment": {
    "shipment_id": "ship_1735478400000",
    "tracking_number": "DELHUB123456789",
    "internal_status": "in_transit",
    "timeline": [
      {
        "status": "shipment_created",
        "timestamp": "2025-12-29T12:00:00Z",
        "location": "Mumbai Warehouse",
        "description": "Shipment created"
      },
      {
        "status": "picked_up",
        "timestamp": "2025-12-29T14:30:00Z",
        "location": "Mumbai Hub",
        "description": "Package picked up"
      }
    ],
    "estimated_delivery": "2025-12-31T18:00:00Z"
  },
  "progress": {
    "percentage": 60,
    "current_status": "in_transit",
    "status_message": "Package is on the way"
  }
}
```

**Lambda Function:** `get_shipment_status`

**Requirements:** 3.1

---

### 4. GET /api/shipments?orderId={orderId}

**Purpose:** Retrieve shipment status by order ID (for consumers viewing their orders).

**Authentication:** Cognito User Pools (All roles: Admin, Consumer, Technician)

**Rate Limit:** 200 requests/minute (shared with endpoint 3)

**Query Parameters:**
- `orderId` - Order identifier

**Response:** Same as endpoint 3

**Lambda Function:** `get_shipment_status`

**Requirements:** 3.1

---

## CORS Configuration

All endpoints support CORS with the following headers:

```
Access-Control-Allow-Origin: *
Access-Control-Allow-Headers: Content-Type, X-Amz-Date, Authorization, X-Api-Key, X-Amz-Security-Token, X-Webhook-Signature
Access-Control-Allow-Methods: GET, POST, PUT, DELETE, OPTIONS
```

## Rate Limiting

Rate limits are enforced using AWS API Gateway Usage Plans:

| Endpoint | Rate Limit | Burst Limit | Daily Quota |
|----------|------------|-------------|-------------|
| POST /api/shipments | 100 req/min | 200 | 144,000 |
| POST /api/webhooks/{courier} | 1000 req/min | 2000 | 1,440,000 |
| GET /api/shipments/{shipmentId} | 200 req/min | 400 | 288,000 |
| GET /api/shipments?orderId={orderId} | 200 req/min | 400 | 288,000 |

## Authentication

### Cognito User Pools

Endpoints 1, 3, and 4 require Cognito authentication:

**Request Header:**
```
Authorization: Bearer <JWT_TOKEN>
```

**Token Claims:**
- `sub` - User ID
- `email` - User email
- `cognito:groups` - User roles (Admin, Consumer, Technician)

### Webhook Signature Verification

Endpoint 2 uses HMAC-SHA256 signature verification:

**Request Header:**
```
X-Webhook-Signature: <HMAC_SHA256_SIGNATURE>
```

**Verification Process:**
1. Extract signature from header
2. Compute HMAC-SHA256 of request body using webhook secret
3. Compare signatures using constant-time comparison
4. Reject if signatures don't match (401 Unauthorized)

## Deployment

### Prerequisites

1. AWS CLI configured with appropriate credentials
2. Cognito User Pool created
3. Lambda functions deployed:
   - `create_shipment`
   - `webhook_handler`
   - `get_shipment_status`

### Setup Script

```bash
# Set Cognito User Pool ARN
export COGNITO_USER_POOL_ARN="arn:aws:cognito-idp:us-east-1:123456789012:userpool/us-east-1_XXXXXXXXX"

# Run setup script
python infrastructure/api_gateway/shipment_endpoints.py
```

### Verification

```bash
# Verify endpoint configuration
python infrastructure/api_gateway/verify_shipment_endpoints.py
```

### Manual Testing

```bash
# Get API URL from deployment output
API_URL="https://<api-id>.execute-api.us-east-1.amazonaws.com/prod"

# Test POST /api/shipments (requires auth token)
curl -X POST "${API_URL}/api/shipments" \
  -H "Authorization: Bearer <JWT_TOKEN>" \
  -H "Content-Type: application/json" \
  -d '{
    "order_id": "ord_test_001",
    "courier_name": "Delhivery",
    "destination": {...}
  }'

# Test GET /api/shipments/{shipmentId} (requires auth token)
curl -X GET "${API_URL}/api/shipments/ship_1735478400000" \
  -H "Authorization: Bearer <JWT_TOKEN>"

# Test GET /api/shipments?orderId={orderId} (requires auth token)
curl -X GET "${API_URL}/api/shipments?orderId=ord_test_001" \
  -H "Authorization: Bearer <JWT_TOKEN>"

# Test POST /api/webhooks/{courier} (no auth, signature required)
curl -X POST "${API_URL}/api/webhooks/delhivery" \
  -H "X-Webhook-Signature: <HMAC_SIGNATURE>" \
  -H "Content-Type: application/json" \
  -d '{
    "waybill": "DELHUB123456789",
    "Status": "In Transit"
  }'
```

## Monitoring

### CloudWatch Metrics

API Gateway automatically emits metrics:
- `Count` - Number of API requests
- `4XXError` - Client errors
- `5XXError` - Server errors
- `Latency` - Request latency
- `IntegrationLatency` - Lambda execution time

### CloudWatch Logs

Access logs are enabled with the following format:
```json
{
  "requestId": "$context.requestId",
  "ip": "$context.identity.sourceIp",
  "httpMethod": "$context.httpMethod",
  "resourcePath": "$context.resourcePath",
  "status": "$context.status",
  "responseLength": "$context.responseLength"
}
```

### Alarms

Recommended CloudWatch alarms:
1. High 4XX error rate (> 5%)
2. High 5XX error rate (> 1%)
3. High latency (P95 > 1000ms)
4. Rate limit exceeded (429 errors)

## Security

### Best Practices

1. **Cognito Authentication:**
   - Use short-lived JWT tokens (1 hour)
   - Implement token refresh mechanism
   - Validate user roles in Lambda

2. **Webhook Security:**
   - Store webhook secrets in AWS Secrets Manager
   - Rotate secrets periodically
   - Use constant-time comparison for signatures
   - Log all webhook attempts

3. **Rate Limiting:**
   - Monitor rate limit metrics
   - Adjust limits based on usage patterns
   - Implement exponential backoff in clients

4. **CORS:**
   - In production, restrict origins to specific domains
   - Remove wildcard (*) from Access-Control-Allow-Origin

5. **WAF (Optional):**
   - Add AWS WAF for additional protection
   - Block malicious IPs
   - Prevent SQL injection and XSS attacks

## Troubleshooting

### Common Issues

**1. 401 Unauthorized on authenticated endpoints**
- Verify JWT token is valid and not expired
- Check Cognito User Pool ARN is correct
- Ensure Authorization header is present

**2. 403 Forbidden**
- Verify user has required role (Admin for POST /api/shipments)
- Check Cognito groups claim

**3. 429 Too Many Requests**
- Rate limit exceeded
- Implement exponential backoff
- Request rate limit increase if needed

**4. 500 Internal Server Error**
- Check Lambda function logs in CloudWatch
- Verify Lambda has correct permissions
- Check DynamoDB table exists and is accessible

**5. Webhook signature verification fails**
- Verify webhook secret is correct
- Check signature header name (X-Webhook-Signature)
- Ensure request body is not modified

## References

- [Design Document](.kiro/specs/shipment-tracking-automation/design.md)
- [Requirements Document](.kiro/specs/shipment-tracking-automation/requirements.md)
- [Tasks Document](.kiro/specs/shipment-tracking-automation/tasks.md)
- [AWS API Gateway Documentation](https://docs.aws.amazon.com/apigateway/)
- [AWS Lambda Integration](https://docs.aws.amazon.com/apigateway/latest/developerguide/set-up-lambda-integrations.html)
