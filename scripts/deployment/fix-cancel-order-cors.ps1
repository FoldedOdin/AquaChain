# Fix CORS for DELETE /api/orders/{orderId} endpoint
# This script configures the OPTIONS method for order cancellation

$API_ID = "vtqjfznspc"
$RESOURCE_ID = "x0imdx"  # /api/orders/{orderId}
$REGION = "ap-south-1"
$STAGE = "dev"

Write-Host "Configuring CORS for DELETE /api/orders/{orderId}..." -ForegroundColor Cyan

# Step 1: Create OPTIONS method if it doesn't exist
Write-Host "`nStep 1: Creating OPTIONS method..." -ForegroundColor Yellow
try {
    aws apigateway put-method `
        --rest-api-id $API_ID `
        --resource-id $RESOURCE_ID `
        --http-method OPTIONS `
        --authorization-type NONE `
        --region $REGION `
        --no-api-key-required 2>$null
    Write-Host "OPTIONS method created successfully" -ForegroundColor Green
} catch {
    Write-Host "OPTIONS method may already exist, continuing..." -ForegroundColor Yellow
}

# Step 2: Set up MOCK integration
Write-Host "`nStep 2: Setting up MOCK integration..." -ForegroundColor Yellow
aws apigateway put-integration `
    --rest-api-id $API_ID `
    --resource-id $RESOURCE_ID `
    --http-method OPTIONS `
    --type MOCK `
    --request-templates '{\"application/json\":\"{\\\"statusCode\\\": 200}\"}' `
    --region $REGION

if ($LASTEXITCODE -eq 0) {
    Write-Host "MOCK integration configured successfully" -ForegroundColor Green
} else {
    Write-Host "Failed to configure MOCK integration" -ForegroundColor Red
    exit 1
}

# Step 3: Set up method response
Write-Host "`nStep 3: Setting up method response..." -ForegroundColor Yellow
aws apigateway put-method-response `
    --rest-api-id $API_ID `
    --resource-id $RESOURCE_ID `
    --http-method OPTIONS `
    --status-code 200 `
    --response-parameters '{\"method.response.header.Access-Control-Allow-Headers\":false,\"method.response.header.Access-Control-Allow-Methods\":false,\"method.response.header.Access-Control-Allow-Origin\":false}' `
    --region $REGION

if ($LASTEXITCODE -eq 0) {
    Write-Host "Method response configured successfully" -ForegroundColor Green
} else {
    Write-Host "Failed to configure method response" -ForegroundColor Red
    exit 1
}

# Step 4: Set up integration response with CORS headers
Write-Host "`nStep 4: Setting up integration response with CORS headers..." -ForegroundColor Yellow
aws apigateway put-integration-response `
    --rest-api-id $API_ID `
    --resource-id $RESOURCE_ID `
    --http-method OPTIONS `
    --status-code 200 `
    --response-parameters '{\"method.response.header.Access-Control-Allow-Headers\":\"'"'"'Content-Type,Authorization'"'"'\",\"method.response.header.Access-Control-Allow-Methods\":\"'"'"'DELETE,OPTIONS'"'"'\",\"method.response.header.Access-Control-Allow-Origin\":\"'"'"'*'"'"'\"}' `
    --region $REGION

if ($LASTEXITCODE -eq 0) {
    Write-Host "Integration response configured successfully" -ForegroundColor Green
} else {
    Write-Host "Failed to configure integration response" -ForegroundColor Red
    exit 1
}

# Step 5: Deploy API to dev stage
Write-Host "`nStep 5: Deploying API to dev stage..." -ForegroundColor Yellow
aws apigateway create-deployment `
    --rest-api-id $API_ID `
    --stage-name $STAGE `
    --description "Fix CORS for order cancellation endpoint" `
    --region $REGION

if ($LASTEXITCODE -eq 0) {
    Write-Host "`nCORS configuration complete!" -ForegroundColor Green
    Write-Host "API deployed to: https://$API_ID.execute-api.$REGION.amazonaws.com/$STAGE" -ForegroundColor Cyan
    Write-Host "`nYou can now test order cancellation from the frontend." -ForegroundColor Green
} else {
    Write-Host "Failed to deploy API" -ForegroundColor Red
    exit 1
}
