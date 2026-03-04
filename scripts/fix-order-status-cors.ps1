# Fix Order Status API Gateway Integration and CORS
# This script updates the existing /api/orders/{orderId}/status route to:
# 1. Point to the new order management Lambda
# 2. Enable CORS properly

$ErrorActionPreference = "Stop"

Write-Host "🔧 Fixing Order Status API Gateway Integration..." -ForegroundColor Cyan

# Get API Gateway ID
$apiId = "vtqjfznspc"
Write-Host "✓ API Gateway ID: $apiId" -ForegroundColor Green

# Get the new Lambda function ARN
$lambdaArn = aws lambda get-function --function-name aquachain-function-order-management-dev --query "Configuration.FunctionArn" --output text
Write-Host "✓ Lambda ARN: $lambdaArn" -ForegroundColor Green

# Get all resources
Write-Host "`n📋 Finding /api/orders/{orderId}/status resource..." -ForegroundColor Cyan
$resources = aws apigateway get-resources --rest-api-id $apiId --output json | ConvertFrom-Json

# Find the {orderId} resource
$orderIdResource = $resources.items | Where-Object { $_.path -eq "/api/orders/{orderId}" }

if (-not $orderIdResource) {
    Write-Host "❌ /api/orders/{orderId} resource not found!" -ForegroundColor Red
    exit 1
}

$orderIdResourceId = $orderIdResource.id
Write-Host "✓ Order ID Resource ID: $orderIdResourceId" -ForegroundColor Green

# Create /status sub-resource if it doesn't exist
Write-Host "`n📋 Creating /status sub-resource..." -ForegroundColor Cyan

try {
    $statusResourceJson = aws apigateway create-resource `
        --rest-api-id $apiId `
        --parent-id $orderIdResourceId `
        --path-part "status" `
        --output json
    
    $statusResource = $statusResourceJson | ConvertFrom-Json
    $resourceId = $statusResource.id
    Write-Host "✓ Status resource created: $resourceId" -ForegroundColor Green
} catch {
    Write-Host "⚠️  Status resource may already exist, trying to find it..." -ForegroundColor Yellow
    # Refresh resources and find it
    $resources = aws apigateway get-resources --rest-api-id $apiId --output json | ConvertFrom-Json
    $statusResource = $resources.items | Where-Object { $_.path -eq "/api/orders/{orderId}/status" }
    
    if (-not $statusResource) {
        Write-Host "❌ Could not create or find status resource!" -ForegroundColor Red
        exit 1
    }
    
    $resourceId = $statusResource.id
    Write-Host "✓ Found existing status resource: $resourceId" -ForegroundColor Green
}

# Update PUT method integration to point to new Lambda
Write-Host "`n🔄 Updating PUT method integration..." -ForegroundColor Cyan

# First, update the integration URI
$integrationUri = "arn:aws:apigateway:ap-south-1:lambda:path/2015-03-31/functions/$lambdaArn/invocations"

try {
    aws apigateway update-integration `
        --rest-api-id $apiId `
        --resource-id $resourceId `
        --http-method PUT `
        --patch-operations "op=replace,path=/uri,value=$integrationUri"
    
    Write-Host "✓ Integration URI updated" -ForegroundColor Green
} catch {
    Write-Host "⚠️  Integration update failed (may not exist yet)" -ForegroundColor Yellow
}

# Add OPTIONS method for CORS preflight
Write-Host "`n🌐 Adding OPTIONS method for CORS..." -ForegroundColor Cyan

try {
    # Create OPTIONS method
    aws apigateway put-method `
        --rest-api-id $apiId `
        --resource-id $resourceId `
        --http-method OPTIONS `
        --authorization-type NONE `
        --no-api-key-required
    
    Write-Host "✓ OPTIONS method created" -ForegroundColor Green
} catch {
    Write-Host "⚠️  OPTIONS method may already exist" -ForegroundColor Yellow
}

# Add MOCK integration for OPTIONS
try {
    aws apigateway put-integration `
        --rest-api-id $apiId `
        --resource-id $resourceId `
        --http-method OPTIONS `
        --type MOCK `
        --request-templates '{\"application/json\":\"{\\\"statusCode\\\": 200}\"}'
    
    Write-Host "✓ OPTIONS integration created" -ForegroundColor Green
} catch {
    Write-Host "⚠️  OPTIONS integration may already exist" -ForegroundColor Yellow
}

# Add OPTIONS method response
try {
    aws apigateway put-method-response `
        --rest-api-id $apiId `
        --resource-id $resourceId `
        --http-method OPTIONS `
        --status-code 200 `
        --response-parameters '{\"method.response.header.Access-Control-Allow-Headers\":false,\"method.response.header.Access-Control-Allow-Methods\":false,\"method.response.header.Access-Control-Allow-Origin\":false}'
    
    Write-Host "✓ OPTIONS method response created" -ForegroundColor Green
} catch {
    Write-Host "⚠️  OPTIONS method response may already exist" -ForegroundColor Yellow
}

# Add OPTIONS integration response with CORS headers
try {
    aws apigateway put-integration-response `
        --rest-api-id $apiId `
        --resource-id $resourceId `
        --http-method OPTIONS `
        --status-code 200 `
        --response-parameters '{\"method.response.header.Access-Control-Allow-Headers\":\"'"'"'Content-Type,Authorization'"'"'\",\"method.response.header.Access-Control-Allow-Methods\":\"'"'"'OPTIONS,PUT'"'"'\",\"method.response.header.Access-Control-Allow-Origin\":\"'"'"'*'"'"'\"}'
    
    Write-Host "✓ OPTIONS integration response created" -ForegroundColor Green
} catch {
    Write-Host "⚠️  OPTIONS integration response may already exist" -ForegroundColor Yellow
}

# Update PUT method response to include CORS headers
Write-Host "`n🔧 Updating PUT method response for CORS..." -ForegroundColor Cyan

try {
    aws apigateway put-method-response `
        --rest-api-id $apiId `
        --resource-id $resourceId `
        --http-method PUT `
        --status-code 200 `
        --response-parameters '{\"method.response.header.Access-Control-Allow-Origin\":false}'
    
    Write-Host "✓ PUT method response updated" -ForegroundColor Green
} catch {
    Write-Host "⚠️  PUT method response update failed" -ForegroundColor Yellow
}

# Update PUT integration response to include CORS headers
try {
    aws apigateway put-integration-response `
        --rest-api-id $apiId `
        --resource-id $resourceId `
        --http-method PUT `
        --status-code 200 `
        --response-parameters '{\"method.response.header.Access-Control-Allow-Origin\":\"'"'"'*'"'"'\"}'
    
    Write-Host "✓ PUT integration response updated" -ForegroundColor Green
} catch {
    Write-Host "⚠️  PUT integration response update failed" -ForegroundColor Yellow
}

# Grant Lambda permission to API Gateway
Write-Host "`n🔐 Granting API Gateway permission to invoke Lambda..." -ForegroundColor Cyan

try {
    aws lambda add-permission `
        --function-name aquachain-function-order-management-dev `
        --statement-id apigateway-order-status-put `
        --action lambda:InvokeFunction `
        --principal apigateway.amazonaws.com `
        --source-arn "arn:aws:execute-api:ap-south-1:758346259059:$apiId/*/PUT/api/orders/*/status"
    
    Write-Host "✓ Lambda permission granted" -ForegroundColor Green
} catch {
    Write-Host "⚠️  Permission may already exist" -ForegroundColor Yellow
}

# Deploy the API
Write-Host "`n🚀 Deploying API changes..." -ForegroundColor Cyan

aws apigateway create-deployment `
    --rest-api-id $apiId `
    --stage-name dev `
    --description "Fix order status CORS and Lambda integration"

Write-Host "✓ API deployed successfully!" -ForegroundColor Green

Write-Host "`n✅ Order Status API Fixed!" -ForegroundColor Green
Write-Host "`nTest it now:" -ForegroundColor Cyan
Write-Host "1. Open http://localhost:3000" -ForegroundColor White
Write-Host "2. Go to My Orders" -ForegroundColor White
Write-Host "3. Click 'Mark as Shipped'" -ForegroundColor White
Write-Host "4. Refresh the page - status should persist!" -ForegroundColor White
