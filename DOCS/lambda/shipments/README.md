# Shipment Tracking Subsystem

Automated courier integration for AquaChain device delivery tracking.

## Overview

This subsystem extends the existing order management system with automated shipment tracking via courier webhooks. It maintains backward compatibility while adding real-time delivery visibility.

## Architecture

```
Admin marks "shipped"
    ↓
create_shipment.py → Courier API → Tracking Number
    ↓
Shipments DynamoDB Table
    ↓
Courier Webhooks → webhook_handler.py → Status Updates
    ↓
Notifications → Consumer/Technician/Admin
```

## Lambda Functions

### 1. create_shipment.py
- **Trigger:** API Gateway POST /api/shipments
- **Purpose:** Create shipment record and register with courier
- **Input:** Order ID, courier name, destination, package details
- **Output:** Shipment ID, tracking number, ETA

### 2. webhook_handler.py
- **Trigger:** API Gateway POST /api/webhooks/:courier
- **Purpose:** Process courier status updates
- **Input:** Courier-specific webhook payload
- **Output:** Updated shipment status

### 3. get_shipment_status.py
- **Trigger:** API Gateway GET /api/shipments/:shipmentId
- **Purpose:** Retrieve shipment details for UI
- **Input:** Shipment ID or Order ID
- **Output:** Shipment details with timeline and progress

## Environment Variables

```bash
SHIPMENTS_TABLE=aquachain-shipments
ORDERS_TABLE=DeviceOrders
COURIER_API_KEY=your_courier_api_key
WEBHOOK_URL=https://api.aquachain.com/webhooks
WEBHOOK_SECRET=your_webhook_secret
SNS_TOPIC_ARN=arn:aws:sns:region:account:topic
```

## Supported Couriers

1. **Delhivery** - Fully integrated
2. **BlueDart** - Webhook normalization ready
3. **DTDC** - Webhook normalization ready

## Status Flow

```
shipment_created → picked_up → in_transit → out_for_delivery → delivered
                                    ↓
                              delivery_failed → retry or returned
```

## API Endpoints

### Create Shipment
```http
POST /api/shipments
Authorization: Bearer {admin_jwt}

{
  "order_id": "ord_xxx",
  "courier_name": "Delhivery",
  "service_type": "Surface",
  "destination": {
    "address": "123 Main St",
    "pincode": "560001",
    "contact_name": "John Doe",
    "contact_phone": "+919876543210"
  },
  "package_details": {
    "weight": "0.5kg",
    "declared_value": 5000
  }
}
```

### Get Shipment Status
```http
GET /api/shipments/{shipmentId}
GET /api/shipments?orderId={orderId}
```

### Webhook Endpoint
```http
POST /api/webhooks/delhivery
X-Webhook-Signature: {hmac_signature}

{
  "waybill": "DELHUB123456789",
  "Status": "In Transit",
  "Scans": [...]
}
```

## Testing

### Local Testing
```bash
# Test shipment creation
python -m pytest tests/test_create_shipment.py

# Test webhook handling
python -m pytest tests/test_webhook_handler.py

# Test status retrieval
python -m pytest tests/test_get_shipment_status.py
```

### Mock Webhook
```bash
curl -X POST https://api.aquachain.com/webhooks/delhivery \
  -H "Content-Type: application/json" \
  -H "X-Webhook-Signature: test-signature" \
  -d '{
    "waybill": "DELHUB123456789",
    "Status": "Delivered",
    "Scans": [{
      "ScanDetail": {
        "ScanDateTime": "2025-12-29T18:00:00Z",
        "ScannedLocation": "Bangalore",
        "Instructions": "Delivered successfully"
      }
    }]
  }'
```

## Deployment

### 1. Create DynamoDB Table
```bash
cd infrastructure/dynamodb
python shipments_table.py
```

### 2. Deploy Lambda Functions
```bash
cd lambda/shipments
zip -r shipments.zip *.py
aws lambda update-function-code \
  --function-name aquachain-create-shipment \
  --zip-file fileb://shipments.zip
```

### 3. Configure API Gateway
- Add POST /api/shipments endpoint
- Add POST /api/webhooks/:courier endpoint
- Add GET /api/shipments/:shipmentId endpoint
- Enable CORS

### 4. Register Webhook with Courier
```python
# Delhivery webhook registration
requests.post(
    'https://track.delhivery.com/api/webhook/register',
    headers={'Authorization': f'Token {API_KEY}'},
    json={'url': 'https://api.aquachain.com/webhooks/delhivery'}
)
```

## Monitoring

### CloudWatch Metrics
- `ShipmentsCreated` - Count of new shipments
- `WebhooksProcessed` - Count of webhook events
- `DeliveryTime` - Average delivery time in hours
- `FailedDeliveries` - Count of failed deliveries

### Alarms
- Failed delivery rate > 5%
- Webhook processing errors > 10/min
- Stale shipments (no update in 7 days)

## Error Handling

### Webhook Failures
- Automatic retry with exponential backoff
- Fallback to polling if webhooks fail
- Admin alerts after max retries

### Delivery Failures
- Max 3 retry attempts
- Admin escalation after max retries
- Automatic return-to-sender after 7 days

## Security

### Webhook Verification
```python
# HMAC signature verification
signature = hmac.new(
    WEBHOOK_SECRET.encode(),
    payload.encode(),
    hashlib.sha256
).hexdigest()
```

### Authorization
- Admin role required for shipment creation
- JWT validation on all endpoints
- Rate limiting: 100 req/min per user

## Troubleshooting

### Shipment not updating
1. Check webhook endpoint is accessible
2. Verify webhook signature is correct
3. Check CloudWatch logs for errors
4. Enable polling fallback

### Courier API errors
1. Verify API key is valid
2. Check rate limits
3. Review courier API documentation
4. Use mock mode for testing

## Future Enhancements

1. Multi-package shipments
2. International shipping support
3. Real-time GPS tracking
4. ML-based delivery time prediction
5. Blockchain proof of delivery
