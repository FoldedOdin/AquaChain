#!/bin/bash

# Test Order API Endpoint
# This script tests the orders API to see what response format it returns

API_ENDPOINT="https://vtqjfznspc.execute-api.ap-south-1.amazonaws.com/dev"
TOKEN="YOUR_AUTH_TOKEN_HERE"

echo "Testing POST /api/orders endpoint..."
echo "=================================="

curl -X POST "${API_ENDPOINT}/api/orders" \
  -H "Content-Type: application/json" \
  -H "Authorization: Bearer ${TOKEN}" \
  -d '{
    "consumerId": "test-user-123",
    "deviceType": "ESP32-BASIC",
    "serviceType": "INSTALLATION",
    "paymentMethod": "ONLINE",
    "deliveryAddress": {
      "street": "123 Test St",
      "city": "Mumbai",
      "state": "Maharashtra",
      "pincode": "400001",
      "country": "India"
    },
    "contactInfo": {
      "phone": "+919876543210",
      "email": "test@example.com"
    },
    "amount": 5000
  }' \
  -v

echo ""
echo "=================================="
echo "Check the response above to see:"
echo "1. HTTP status code"
echo "2. Response headers"
echo "3. Response body format"
