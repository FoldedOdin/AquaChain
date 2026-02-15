# Add System Metrics Endpoint to API Gateway
# This script adds the /api/admin/system/metrics endpoint with proper CORS

Write-Host "========================================" -ForegroundColor Cyan
Write-Host "Add System Metrics Endpoint" -ForegroundColor Cyan
Write-Host "========================================" -ForegroundColor Cyan
Write-Host ""

$ErrorActionPreference = "Stop"

# Configuration
$API_ID = "vtqjfznspc"
$REGION = "ap-south-1"
$LAMBDA_ARN = "arn:aws:lambda:ap-south-1:758346259059:function:aquachain-function-admin-service-dev"

# Step 1: Get root resource
Write-Host "Step 1: Finding API Gateway resources..." -ForegroundColor Yellow

$ROOT_RESOURCE = aws apigateway get-resources --rest-api-id $API_ID --region $REGION --query "items[?path=='/'].id" --output text

if ([string]::IsNullOrEmpty($ROOT_RESOURCE)) {
    Write-Host "  ✗ Could not find root resource" -ForegroundColor Red
    exit 1
}

Write-Host "  ✓ Root resource: $ROOT_RESOURCE" -ForegroundColor Green

# Find /api resource
$API_RESOURCE = aws apigateway get-resources --rest-api-id $API_ID --region $REGION --query "items[?path=='/api'].id" --output text

if ([string]::IsNullOrEmpty($API_RESOURCE)) {
    Write-Host "  Creating /api resource..." -ForegroundColor Gray
    $API_RESOURCE_JSON = aws apigateway create-resource --rest-api-id $API_ID --parent-id $ROOT_RESOURCE --path-part "api" --region $REGION --output json | ConvertFrom-Json
    $API_RESOURCE = $API_RESOURCE_JSON.id
}

Write-Host "  ✓ /api resource: $API_RESOURCE" -ForegroundColor Green

# Find /api/admin resource
$ADMIN_RESOURCE = aws apigateway get-resources --rest-api-id $API_ID --region $REGION --query "items[?path=='/api/admin'].id" --output text

if ([string]::IsNullOrEmpty($ADMIN_RESOURCE)) {
    Write-Host "  Creating /api/admin resource..." -ForegroundColor Gray
    $ADMIN_RESOURCE_JSON = aws apigateway create-resource --rest-api-id $API_ID --parent-id $API_RESOURCE --path-part "admin" --region $REGION --output json | ConvertFrom-Json
    $ADMIN_RESOURCE = $ADMIN_RESOURCE_JSON.id
}

Write-Host "  ✓ /api/admin resource: $ADMIN_RESOURCE" -ForegroundColor Green

# Find /api/admin/system resource
$SYSTEM_RESOURCE = aws apigateway get-resources --rest-api-id $API_ID --region $REGION --query "items[?path=='/api/admin/system'].id" --output text

if ([string]::IsNullOrEmpty($SYSTEM_RESOURCE)) {
    Write-Host "  Creating /api/admin/system resource..." -ForegroundColor Gray
    $SYSTEM_RESOURCE_JSON = aws apigateway create-resource --rest-api-id $API_ID --parent-id $ADMIN_RESOURCE --path-part "system" --region $REGION --output json | ConvertFrom-Json
    $SYSTEM_RESOURCE = $SYSTEM_RESOURCE_JSON.id
}

Write-Host "  ✓ /api/admin/system resource: $SYSTEM_RESOURCE" -ForegroundColor Green

# Find or create /api/admin/system/metrics resource
$METRICS_RESOURCE = aws apigateway get-resources --rest-api-id $API_ID --region $REGION --query "items[?path=='/api/admin/system/metrics'].id" --output text

if ([string]::IsNullOrEmpty($METRICS_RESOURCE)) {
    Write-Host "  Creating /api/admin/system/metrics resource..." -ForegroundColor Gray
    $METRICS_RESOURCE_JSON = aws apigateway create-resource --rest-api-id $API_ID --parent-id $SYSTEM_RESOURCE --path-part "metrics" --region $REGION --output json | ConvertFrom-Json
    $METRICS_RESOURCE = $METRICS_RESOURCE_JSON.id
}

Write-Host "  ✓ /api/admin/system/metrics resource: $METRICS_RESOURCE" -ForegroundColor Green
Write-Host ""

# Step 2: Add OPTIONS method for CORS
Write-Host "Step 2: Adding OPTIONS method for CORS..." -ForegroundColor Yellow

try {
    aws apigateway put-method `
        --rest-api-id $API_ID `
        --resource-id $METRICS_RESOURCE `
        --http-method OPTIONS `
        --authorization-type NONE `
        --region $REGION `
        --output json 2>$null | Out-Null
    
    Write-Host "  ✓ OPTIONS method created" -ForegroundColor Green
} catch {
    Write-Host "  ℹ OPTIONS method may already exist" -ForegroundColor Gray
}

# Add OPTIONS integration
try {
    aws apigateway put-integration `
        --rest-api-id $API_ID `
        --resource-id $METRICS_RESOURCE `
        --http-method OPTIONS `
        --type MOCK `
        --request-templates '{\"application/json\":\"{\\\"statusCode\\\": 200}\"}' `
        --region $REGION `
        --output json 2>$null | Out-Null
    
    Write-Host "  ✓ OPTIONS integration created" -ForegroundColor Green
} catch {
    Write-Host "  ℹ OPTIONS integration may already exist" -ForegroundColor Gray
}

# Add OPTIONS method response
try {
    aws apigateway put-method-response `
        --rest-api-id $API_ID `
        --resource-id $METRICS_RESOURCE `
        --http-method OPTIONS `
        --status-code 200 `
        --response-parameters '{\"method.response.header.Access-Control-Allow-Headers\":false,\"method.response.header.Access-Control-Allow-Methods\":false,\"method.response.header.Access-Control-Allow-Origin\":false}' `
        --region $REGION `
        --output json 2>$null | Out-Null
    
    Write-Host "  ✓ OPTIONS method response created" -ForegroundColor Green
} catch {
    Write-Host "  ℹ OPTIONS method response may already exist" -ForegroundColor Gray
}

# Add OPTIONS integration response with CORS headers
try {
    aws apigateway put-integration-response `
        --rest-api-id $API_ID `
        --resource-id $METRICS_RESOURCE `
        --http-method OPTIONS `
        --status-code 200 `
        --response-parameters '{\"method.response.header.Access-Control-Allow-Headers\":\"'"'"'Content-Type,X-Amz-Date,Authorization,X-Api-Key,X-Amz-Security-Token'"'"'\",\"method.response.header.Access-Control-Allow-Methods\":\"'"'"'GET,OPTIONS'"'"'\",\"method.response.header.Access-Control-Allow-Origin\":\"'"'"'*'"'"'\"}' `
        --region $REGION `
        --output json 2>$null | Out-Null
    
    Write-Host "  ✓ OPTIONS integration response created" -ForegroundColor Green
} catch {
    Write-Host "  ℹ OPTIONS integration response may already exist" -ForegroundColor Gray
}

Write-Host ""

# Step 3: Add GET method
Write-Host "Step 3: Adding GET method..." -ForegroundColor Yellow

try {
    aws apigateway put-method `
        --rest-api-id $API_ID `
        --resource-id $METRICS_RESOURCE `
        --http-method GET `
        --authorization-type COGNITO_USER_POOLS `
        --authorizer-id $(aws apigateway get-authorizers --rest-api-id $API_ID --region $REGION --query "items[0].id" --output text) `
        --region $REGION `
        --output json 2>$null | Out-Null
    
    Write-Host "  ✓ GET method created" -ForegroundColor Green
} catch {
    Write-Host "  ℹ GET method may already exist" -ForegroundColor Gray
}

# Add GET integration to Lambda
try {
    aws apigateway put-integration `
        --rest-api-id $API_ID `
        --resource-id $METRICS_RESOURCE `
        --http-method GET `
        --type AWS_PROXY `
        --integration-http-method POST `
        --uri "arn:aws:apigateway:$REGION:lambda:path/2015-03-31/functions/$LAMBDA_ARN/invocations" `
        --region $REGION `
        --output json 2>$null | Out-Null
    
    Write-Host "  ✓ GET integration created" -ForegroundColor Green
} catch {
    Write-Host "  ℹ GET integration may already exist" -ForegroundColor Gray
}

Write-Host ""

# Step 4: Deploy API
Write-Host "Step 4: Deploying API..." -ForegroundColor Yellow

aws apigateway create-deployment `
    --rest-api-id $API_ID `
    --stage-name dev `
    --region $REGION `
    --output json | Out-Null

Write-Host "  ✓ API deployed to dev stage" -ForegroundColor Green
Write-Host ""

Write-Host "========================================" -ForegroundColor Green
Write-Host "✓ Endpoint Added Successfully!" -ForegroundColor Green
Write-Host "========================================" -ForegroundColor Green
Write-Host ""
Write-Host "Endpoint URL:" -ForegroundColor Cyan
Write-Host "  GET https://vtqjfznspc.execute-api.ap-south-1.amazonaws.com/dev/api/admin/system/metrics" -ForegroundColor White
Write-Host ""
Write-Host "CORS is now enabled for this endpoint." -ForegroundColor Green
Write-Host ""
