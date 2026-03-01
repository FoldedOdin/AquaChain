# Add Orders Placeholder Endpoint
# This creates a simple endpoint that returns "coming soon" message

Write-Host "Adding orders placeholder endpoint..." -ForegroundColor Yellow

$API_ID = "vtqjfznspc"
$REGION = "ap-south-1"

# Get resources
$resources = aws apigateway get-resources --rest-api-id $API_ID --region $REGION | ConvertFrom-Json
$apiResource = $resources.items | Where-Object { $_.path -eq "/api" }

# Create /api/orders if not exists
$ordersResource = $resources.items | Where-Object { $_.path -eq "/api/orders" }
if (-not $ordersResource) {
    $ordersResource = aws apigateway create-resource `
        --rest-api-id $API_ID `
        --parent-id $apiResource.id `
        --path-part "orders" `
        --region $REGION | ConvertFrom-Json
}

# Add OPTIONS for CORS
aws apigateway put-method --rest-api-id $API_ID --resource-id $ordersResource.id --http-method OPTIONS --authorization-type NONE --region $REGION 2>$null | Out-Null
aws apigateway put-integration --rest-api-id $API_ID --resource-id $ordersResource.id --http-method OPTIONS --type MOCK --request-templates '{\"application/json\":\"{\\\"statusCode\\\": 200}\"}' --region $REGION 2>$null | Out-Null
aws apigateway put-method-response --rest-api-id $API_ID --resource-id $ordersResource.id --http-method OPTIONS --status-code 200 --response-parameters '{\"method.response.header.Access-Control-Allow-Headers\":false,\"method.response.header.Access-Control-Allow-Methods\":false,\"method.response.header.Access-Control-Allow-Origin\":false}' --region $REGION 2>$null | Out-Null
aws apigateway put-integration-response --rest-api-id $API_ID --resource-id $ordersResource.id --http-method OPTIONS --status-code 200 --response-parameters '{\"method.response.header.Access-Control-Allow-Headers\":\"\\\"Content-Type,Authorization\\\"\",\"method.response.header.Access-Control-Allow-Methods\":\"\\\"POST,OPTIONS\\\"\",\"method.response.header.Access-Control-Allow-Origin\":\"\\\"*\\\"\"}' --region $REGION 2>$null | Out-Null

# Add POST with mock response
aws apigateway put-method --rest-api-id $API_ID --resource-id $ordersResource.id --http-method POST --authorization-type NONE --region $REGION 2>$null | Out-Null
aws apigateway put-integration --rest-api-id $API_ID --resource-id $ordersResource.id --http-method POST --type MOCK --request-templates '{\"application/json\":\"{\\\"statusCode\\\": 200}\"}' --region $REGION 2>$null | Out-Null
aws apigateway put-method-response --rest-api-id $API_ID --resource-id $ordersResource.id --http-method POST --status-code 200 --response-models '{\"application/json\":\"Empty\"}' --region $REGION 2>$null | Out-Null
aws apigateway put-integration-response --rest-api-id $API_ID --resource-id $ordersResource.id --http-method POST --status-code 200 --response-templates '{\"application/json\":\"{\\\"success\\\":false,\\\"message\\\":\\\"Device ordering feature coming soon. Please contact support for assistance.\\\"}\"}' --region $REGION 2>$null | Out-Null

# Deploy
aws apigateway create-deployment --rest-api-id $API_ID --stage-name dev --region $REGION | Out-Null

Write-Host "✅ Placeholder endpoint added" -ForegroundColor Green
Write-Host "Endpoint: https://$API_ID.execute-api.$REGION.amazonaws.com/dev/api/orders" -ForegroundColor Cyan
Write-Host "Returns: Feature coming soon message" -ForegroundColor Yellow
