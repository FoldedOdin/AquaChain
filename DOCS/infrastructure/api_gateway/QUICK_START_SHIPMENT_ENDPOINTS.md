# Quick Start: Shipment API Gateway Endpoints

This guide will help you quickly set up the API Gateway endpoints for shipment tracking.

## Prerequisites

1. **AWS CLI** configured with credentials
2. **Python 3.8+** installed
3. **Boto3** installed (`pip install boto3`)
4. **Cognito User Pool** created
5. **Lambda functions** deployed:
   - `create_shipment`
   - `webhook_handler`
   - `get_shipment_status`

## Step 1: Set Environment Variables

```bash
# Set your Cognito User Pool ARN
export COGNITO_USER_POOL_ARN="arn:aws:cognito-idp:us-east-1:YOUR_ACCOUNT_ID:userpool/us-east-1_XXXXXXXXX"

# Set AWS region (optional, defaults to us-east-1)
export AWS_DEFAULT_REGION="us-east-1"
```

## Step 2: Deploy Lambda Functions (if not already deployed)

```bash
# Navigate to lambda/shipments directory
cd lambda/shipments

# Package and deploy create_shipment
zip -r create_shipment.zip create_shipment.py
aws lambda create-function \
  --function-name create_shipment \
  --runtime python3.11 \
  --role arn:aws:iam::YOUR_ACCOUNT_ID:role/lambda-execution-role \
  --handler create_shipment.handler \
  --zip-file fileb://create_shipment.zip

# Package and deploy webhook_handler
zip -r webhook_handler.zip webhook_handler.py
aws lambda create-function \
  --function-name webhook_handler \
  --runtime python3.11 \
  --role arn:aws:iam::YOUR_ACCOUNT_ID:role/lambda-execution-role \
  --handler webhook_handler.handler \
  --zip-file fileb://webhook_handler.zip

# Package and deploy get_shipment_status
zip -r get_shipment_status.zip get_shipment_status.py
aws lambda create-function \
  --function-name get_shipment_status \
  --runtime python3.11 \
  --role arn:aws:iam::YOUR_ACCOUNT_ID:role/lambda-execution-role \
  --handler get_shipment_status.handler \
  --zip-file fileb://get_shipment_status.zip
```

## Step 3: Run Setup Script

```bash
# Navigate to infrastructure/api_gateway directory
cd infrastructure/api_gateway

# Run the setup script
python shipment_endpoints.py
```

**Expected Output:**
```
=== Setting up POST /api/shipments endpoint ===
Created POST method with Lambda integration: create_shipment
Created CORS OPTIONS method
Created usage plan: aquachain-shipments-100rpm

=== Task 10.1 Complete ===
{
  "endpoint": "POST /api/shipments",
  "resource_id": "abc123",
  "lambda": "create_shipment",
  "auth": "Cognito (Admin)",
  "rate_limit": "100 req/min"
}

=== Setting up POST /api/webhooks/:courier endpoint ===
...

API deployed to: https://abc123xyz.execute-api.us-east-1.amazonaws.com/prod
```

## Step 4: Verify Setup

```bash
# Run verification script
python verify_shipment_endpoints.py
```

**Expected Output:**
```
================================================================================
SHIPMENT API GATEWAY ENDPOINTS VERIFICATION REPORT
================================================================================

10.1 Create POST /api/shipments endpoint
Status: ✓ PASSED
...

Overall Status: ✓ ALL CHECKS PASSED
================================================================================
```

## Step 5: Test Endpoints

### Get API URL

```bash
# From setup script output, note the API URL
API_URL="https://abc123xyz.execute-api.us-east-1.amazonaws.com/prod"
```

### Test POST /api/shipments

```bash
# Get JWT token from Cognito
JWT_TOKEN="your-jwt-token-here"

# Create shipment
curl -X POST "${API_URL}/api/shipments" \
  -H "Authorization: Bearer ${JWT_TOKEN}" \
  -H "Content-Type: application/json" \
  -d '{
    "order_id": "ord_test_001",
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
  }'
```

### Test GET /api/shipments/{shipmentId}

```bash
# Get shipment status by ID
curl -X GET "${API_URL}/api/shipments/ship_1735478400000" \
  -H "Authorization: Bearer ${JWT_TOKEN}"
```

### Test GET /api/shipments?orderId={orderId}

```bash
# Get shipment status by order ID
curl -X GET "${API_URL}/api/shipments?orderId=ord_test_001" \
  -H "Authorization: Bearer ${JWT_TOKEN}"
```

### Test POST /api/webhooks/{courier}

```bash
# Generate HMAC signature
WEBHOOK_SECRET="your-webhook-secret"
PAYLOAD='{"waybill":"DELHUB123","Status":"In Transit"}'
SIGNATURE=$(echo -n "$PAYLOAD" | openssl dgst -sha256 -hmac "$WEBHOOK_SECRET" | cut -d' ' -f2)

# Send webhook
curl -X POST "${API_URL}/api/webhooks/delhivery" \
  -H "X-Webhook-Signature: ${SIGNATURE}" \
  -H "Content-Type: application/json" \
  -d "$PAYLOAD"
```

## Step 6: Monitor

### View CloudWatch Logs

```bash
# View API Gateway logs
aws logs tail /aws/apigateway/YOUR_API_ID --follow

# View Lambda logs
aws logs tail /aws/lambda/create_shipment --follow
aws logs tail /aws/lambda/webhook_handler --follow
aws logs tail /aws/lambda/get_shipment_status --follow
```

### View CloudWatch Metrics

```bash
# Get API Gateway metrics
aws cloudwatch get-metric-statistics \
  --namespace AWS/ApiGateway \
  --metric-name Count \
  --dimensions Name=ApiName,Value=aquachain-api \
  --start-time 2025-01-01T00:00:00Z \
  --end-time 2025-01-01T23:59:59Z \
  --period 3600 \
  --statistics Sum
```

## Troubleshooting

### Issue: "API not found"

**Solution:** Run the setup script again. It will create the API if it doesn't exist.

### Issue: "Lambda function not found"

**Solution:** Deploy Lambda functions first (see Step 2).

### Issue: "Cognito authorizer error"

**Solution:** Verify `COGNITO_USER_POOL_ARN` is correct:
```bash
aws cognito-idp list-user-pools --max-results 10
```

### Issue: "Permission denied"

**Solution:** Add Lambda invoke permissions:
```bash
aws lambda add-permission \
  --function-name create_shipment \
  --statement-id apigateway-invoke \
  --action lambda:InvokeFunction \
  --principal apigateway.amazonaws.com
```

### Issue: "CORS error in browser"

**Solution:** Verify CORS is configured correctly:
```bash
# Check OPTIONS method exists
aws apigateway get-method \
  --rest-api-id YOUR_API_ID \
  --resource-id YOUR_RESOURCE_ID \
  --http-method OPTIONS
```

## Next Steps

1. **Configure Webhook Secrets:** Store webhook secrets in AWS Secrets Manager
2. **Set Up Monitoring:** Create CloudWatch alarms for errors and latency
3. **Enable WAF:** Add AWS WAF for additional security
4. **Update Frontend:** Update frontend to use new API endpoints
5. **Register Webhooks:** Register webhook URLs with courier services

## Additional Resources

- [Full Documentation](SHIPMENT_ENDPOINTS_README.md)
- [Design Document](../../.kiro/specs/shipment-tracking-automation/design.md)
- [Requirements Document](../../.kiro/specs/shipment-tracking-automation/requirements.md)
- [AWS API Gateway Best Practices](https://docs.aws.amazon.com/apigateway/latest/developerguide/best-practices.html)

## Support

For issues or questions:
1. Check CloudWatch logs for errors
2. Review the troubleshooting section above
3. Consult the full documentation
4. Check AWS service health dashboard
