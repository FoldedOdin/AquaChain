# Shipment Tracking API Gateway Architecture

## API Endpoint Flow Diagram

```
┌─────────────────────────────────────────────────────────────────────────┐
│                         API Gateway (aquachain-api)                      │
│                    https://api-id.execute-api.us-east-1.amazonaws.com    │
└─────────────────────────────────────────────────────────────────────────┘
                                    │
                    ┌───────────────┼───────────────┐
                    │               │               │
                    ▼               ▼               ▼
        ┌───────────────┐  ┌───────────────┐  ┌───────────────┐
        │  /api/shipments│  │ /api/webhooks │  │ /api/shipments│
        │               │  │   /{courier}  │  │  /{shipmentId}│
        └───────────────┘  └───────────────┘  └───────────────┘
                │                  │                  │
                │                  │                  │
                ▼                  ▼                  ▼

┌─────────────────────────────────────────────────────────────────────────┐
│                           ENDPOINT DETAILS                               │
└─────────────────────────────────────────────────────────────────────────┘

┌─────────────────────────────────────────────────────────────────────────┐
│ 1. POST /api/shipments                                    [Task 10.1]   │
├─────────────────────────────────────────────────────────────────────────┤
│ Purpose:     Create new shipment record                                 │
│ Auth:        Cognito User Pools (Admin role required)                   │
│ Rate Limit:  100 req/min (burst: 200)                                   │
│ Lambda:      create_shipment                                             │
│ CORS:        ✓ Enabled                                                   │
│                                                                          │
│ Request:                                                                 │
│   POST /api/shipments                                                    │
│   Authorization: Bearer <JWT_TOKEN>                                      │
│   Content-Type: application/json                                         │
│   {                                                                      │
│     "order_id": "ord_123",                                               │
│     "courier_name": "Delhivery",                                         │
│     "destination": {...}                                                 │
│   }                                                                      │
│                                                                          │
│ Response:                                                                │
│   {                                                                      │
│     "success": true,                                                     │
│     "shipment_id": "ship_456",                                           │
│     "tracking_number": "DELHUB789"                                       │
│   }                                                                      │
└─────────────────────────────────────────────────────────────────────────┘

┌─────────────────────────────────────────────────────────────────────────┐
│ 2. POST /api/webhooks/{courier}                           [Task 10.2]   │
├─────────────────────────────────────────────────────────────────────────┤
│ Purpose:     Receive courier webhook callbacks                          │
│ Auth:        None (HMAC-SHA256 signature verification in Lambda)        │
│ Rate Limit:  1000 req/min (burst: 2000)                                 │
│ Lambda:      webhook_handler                                             │
│ CORS:        ✓ Enabled                                                   │
│                                                                          │
│ Request:                                                                 │
│   POST /api/webhooks/delhivery                                           │
│   X-Webhook-Signature: <HMAC_SHA256>                                     │
│   Content-Type: application/json                                         │
│   {                                                                      │
│     "waybill": "DELHUB789",                                              │
│     "Status": "In Transit"                                               │
│   }                                                                      │
│                                                                          │
│ Response:                                                                │
│   {                                                                      │
│     "success": true,                                                     │
│     "processed": "ship_456"                                              │
│   }                                                                      │
│                                                                          │
│ Supported Couriers:                                                      │
│   • delhivery                                                            │
│   • bluedart                                                             │
│   • dtdc                                                                 │
└─────────────────────────────────────────────────────────────────────────┘

┌─────────────────────────────────────────────────────────────────────────┐
│ 3. GET /api/shipments/{shipmentId}                        [Task 10.3]   │
├─────────────────────────────────────────────────────────────────────────┤
│ Purpose:     Get shipment status by shipment ID                         │
│ Auth:        Cognito User Pools (All roles)                             │
│ Rate Limit:  200 req/min (burst: 400)                                   │
│ Lambda:      get_shipment_status                                         │
│ CORS:        ✓ Enabled                                                   │
│                                                                          │
│ Request:                                                                 │
│   GET /api/shipments/ship_456                                            │
│   Authorization: Bearer <JWT_TOKEN>                                      │
│                                                                          │
│ Response:                                                                │
│   {                                                                      │
│     "success": true,                                                     │
│     "shipment": {                                                        │
│       "shipment_id": "ship_456",                                         │
│       "tracking_number": "DELHUB789",                                    │
│       "internal_status": "in_transit",                                   │
│       "timeline": [...]                                                  │
│     },                                                                   │
│     "progress": {                                                        │
│       "percentage": 60,                                                  │
│       "status_message": "Package is on the way"                          │
│     }                                                                    │
│   }                                                                      │
└─────────────────────────────────────────────────────────────────────────┘

┌─────────────────────────────────────────────────────────────────────────┐
│ 4. GET /api/shipments?orderId={orderId}                   [Task 10.4]   │
├─────────────────────────────────────────────────────────────────────────┤
│ Purpose:     Get shipment status by order ID                            │
│ Auth:        Cognito User Pools (All roles)                             │
│ Rate Limit:  200 req/min (shared with endpoint 3)                       │
│ Lambda:      get_shipment_status                                         │
│ CORS:        ✓ Enabled                                                   │
│                                                                          │
│ Request:                                                                 │
│   GET /api/shipments?orderId=ord_123                                     │
│   Authorization: Bearer <JWT_TOKEN>                                      │
│                                                                          │
│ Response:                                                                │
│   Same as endpoint 3                                                     │
└─────────────────────────────────────────────────────────────────────────┘

┌─────────────────────────────────────────────────────────────────────────┐
│                        AUTHENTICATION FLOW                               │
└─────────────────────────────────────────────────────────────────────────┘

┌──────────────┐         ┌──────────────┐         ┌──────────────┐
│   Client     │         │   Cognito    │         │ API Gateway  │
│  (Frontend)  │         │  User Pool   │         │              │
└──────────────┘         └──────────────┘         └──────────────┘
       │                        │                        │
       │  1. Login Request      │                        │
       │───────────────────────>│                        │
       │                        │                        │
       │  2. JWT Token          │                        │
       │<───────────────────────│                        │
       │                        │                        │
       │  3. API Request + JWT  │                        │
       │────────────────────────────────────────────────>│
       │                        │                        │
       │                        │  4. Validate Token     │
       │                        │<───────────────────────│
       │                        │                        │
       │                        │  5. Token Valid        │
       │                        │───────────────────────>│
       │                        │                        │
       │                        │  6. Invoke Lambda      │
       │                        │        (if authorized) │
       │                        │                        │
       │  7. Response           │                        │
       │<────────────────────────────────────────────────│
       │                        │                        │

┌─────────────────────────────────────────────────────────────────────────┐
│                        WEBHOOK SECURITY FLOW                             │
└─────────────────────────────────────────────────────────────────────────┘

┌──────────────┐         ┌──────────────┐         ┌──────────────┐
│   Courier    │         │ API Gateway  │         │   Lambda     │
│   Service    │         │              │         │  (webhook)   │
└──────────────┘         └──────────────┘         └──────────────┘
       │                        │                        │
       │  1. Webhook Event      │                        │
       │  + HMAC Signature      │                        │
       │───────────────────────>│                        │
       │                        │                        │
       │                        │  2. Forward Request    │
       │                        │───────────────────────>│
       │                        │                        │
       │                        │  3. Verify Signature   │
       │                        │    (HMAC-SHA256)       │
       │                        │                        │
       │                        │  4. Process if Valid   │
       │                        │    (401 if Invalid)    │
       │                        │                        │
       │  5. Response           │                        │
       │<───────────────────────────────────────────────│
       │                        │                        │

┌─────────────────────────────────────────────────────────────────────────┐
│                         RATE LIMITING SUMMARY                            │
└─────────────────────────────────────────────────────────────────────────┘

┌────────────────────────────────┬──────────┬───────────┬──────────────┐
│ Endpoint                       │ Rate     │ Burst     │ Daily Quota  │
├────────────────────────────────┼──────────┼───────────┼──────────────┤
│ POST /api/shipments            │ 100/min  │ 200       │ 144,000      │
│ POST /api/webhooks/{courier}   │ 1000/min │ 2000      │ 1,440,000    │
│ GET /api/shipments/{id}        │ 200/min  │ 400       │ 288,000      │
│ GET /api/shipments?orderId=    │ 200/min  │ 400       │ 288,000      │
└────────────────────────────────┴──────────┴───────────┴──────────────┘

┌─────────────────────────────────────────────────────────────────────────┐
│                         CORS CONFIGURATION                               │
└─────────────────────────────────────────────────────────────────────────┘

Access-Control-Allow-Origin: *
Access-Control-Allow-Headers: Content-Type, X-Amz-Date, Authorization,
                              X-Api-Key, X-Amz-Security-Token,
                              X-Webhook-Signature
Access-Control-Allow-Methods: GET, POST, PUT, DELETE, OPTIONS

┌─────────────────────────────────────────────────────────────────────────┐
│                      LAMBDA FUNCTION MAPPING                             │
└─────────────────────────────────────────────────────────────────────────┘

┌────────────────────────────────┬──────────────────────────────────────┐
│ Lambda Function                │ Endpoints                            │
├────────────────────────────────┼──────────────────────────────────────┤
│ create_shipment                │ POST /api/shipments                  │
│ webhook_handler                │ POST /api/webhooks/{courier}         │
│ get_shipment_status            │ GET /api/shipments/{shipmentId}      │
│                                │ GET /api/shipments?orderId={orderId} │
└────────────────────────────────┴──────────────────────────────────────┘

┌─────────────────────────────────────────────────────────────────────────┐
│                         MONITORING & LOGGING                             │
└─────────────────────────────────────────────────────────────────────────┘

CloudWatch Logs:
  • /aws/apigateway/{api-id}
  • /aws/lambda/create_shipment
  • /aws/lambda/webhook_handler
  • /aws/lambda/get_shipment_status

CloudWatch Metrics:
  • Count - Number of API requests
  • 4XXError - Client errors
  • 5XXError - Server errors
  • Latency - Request latency
  • IntegrationLatency - Lambda execution time

Recommended Alarms:
  • High 4XX error rate (> 5%)
  • High 5XX error rate (> 1%)
  • High latency (P95 > 1000ms)
  • Rate limit exceeded (429 errors)

┌─────────────────────────────────────────────────────────────────────────┐
│                         DEPLOYMENT CHECKLIST                             │
└─────────────────────────────────────────────────────────────────────────┘

Prerequisites:
  ☐ AWS CLI configured
  ☐ Cognito User Pool created
  ☐ Lambda functions deployed
  ☐ DynamoDB tables created
  ☐ IAM roles configured

Setup:
  ☐ Set COGNITO_USER_POOL_ARN environment variable
  ☐ Run: python infrastructure/api_gateway/shipment_endpoints.py
  ☐ Run: python infrastructure/api_gateway/verify_shipment_endpoints.py
  ☐ Note API URL from output

Testing:
  ☐ Test POST /api/shipments with valid JWT
  ☐ Test GET /api/shipments/{shipmentId}
  ☐ Test GET /api/shipments?orderId={orderId}
  ☐ Test POST /api/webhooks/{courier} with signature
  ☐ Verify CORS headers in browser
  ☐ Test rate limiting

Post-Deployment:
  ☐ Configure CloudWatch alarms
  ☐ Set up monitoring dashboard
  ☐ Register webhook URLs with couriers
  ☐ Update frontend with API URL
  ☐ Restrict CORS origins in production
  ☐ Enable WAF (optional)

┌─────────────────────────────────────────────────────────────────────────┐
│                              STATUS                                      │
└─────────────────────────────────────────────────────────────────────────┘

Task 10: Implement API Gateway endpoints
  ✅ 10.1 POST /api/shipments endpoint
  ✅ 10.2 POST /api/webhooks/:courier endpoint
  ✅ 10.3 GET /api/shipments/:shipmentId endpoint
  ✅ 10.4 GET /api/shipments?orderId=:orderId endpoint

Status: ✅ COMPLETE (4/4 subtasks)
