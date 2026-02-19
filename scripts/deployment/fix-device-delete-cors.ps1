# Fix CORS for DELETE /api/devices/{deviceId} endpoint
# This adds the OPTIONS method for CORS preflight

$ErrorActionPreference = "Stop"

$API_ID = "vtqjfznspc"
$REGION = "ap-south-1"

Write-Host "========================================" -ForegroundColor Cyan
Write-Host "Fix Device DELETE CORS" -ForegroundColor Cyan
Write-Host "========================================" -ForegroundColor Cyan
Write-Host ""

# Step 1: Find the /api/devices/{deviceId} resource
Write-Host "Step 1: Finding /api/devices/{deviceId} resource..." -ForegroundColor Yellow

$resources = aws apigateway get-resources --rest-api-id $API_ID --region $REGION | ConvertFrom-Json

# Find /api resource
$apiResource = $resources.items | Where-Object { $_.path -eq "/api" }
if (-not $apiResource) {
    Write-Host "ERROR: /api resource not found" -ForegroundColor Red
    exit 1
}

# Find /api/devices resource
$devicesResource = $resources.items | Where-Object { $_.path -eq "/api/devices" }
if (-not $devicesResource) {
    Write-Host "ERROR: /api/devices resource not found" -ForegroundColor Red
    exit 1
}

# Find /api/devices/{deviceId} resource
$deviceIdResource = $resources.items | Where-Object { 
    $_.pathPart -eq "{deviceId}" -and $_.parentId -eq $devicesResource.id 
}

if (-not $deviceIdResource) {
    Write-Host "ERROR: /api/devices/{deviceId} resource not found" -ForegroundColor Red
    exit 1
}

$RESOURCE_ID = $deviceIdResource.id
Write-Host "✓ Found resource: /api/devices/{deviceId} (ID: $RESOURCE_ID)" -ForegroundColor Green

# Step 2: Check if OPTIONS method exists
Write-Host ""
Write-Host "Step 2: Checking for existing OPTIONS method..." -ForegroundColor Yellow

try {
    $existingOptions = aws apigateway get-method `
        --rest-api-id $API_ID `
        --resource-id $RESOURCE_ID `
        --http-method OPTIONS `
        --region $REGION 2>$null | ConvertFrom-Json
    
    if ($existingOptions) {
        Write-Host "⚠ OPTIONS method already exists, deleting it first..." -ForegroundColor Yellow
        aws apigateway delete-method `
            --rest-api-id $API_ID `
            --resource-id $RESOURCE_ID `
            --http-method OPTIONS `
            --region $REGION | Out-Null
        Write-Host "✓ Deleted existing OPTIONS method" -ForegroundColor Green
    }
} catch {
    Write-Host "✓ No existing OPTIONS method found" -ForegroundColor Green
}

# Step 3: Create OPTIONS method with MOCK integration
Write-Host ""
Write-Host "Step 3: Creating OPTIONS method..." -ForegroundColor Yellow

aws apigateway put-method `
    --rest-api-id $API_ID `
    --resource-id $RESOURCE_ID `
    --http-method OPTIONS `
    --authorization-type NONE `
    --region $REGION | Out-Null

Write-Host "✓ Created OPTIONS method" -ForegroundColor Green

# Step 4: Create MOCK integration
Write-Host ""
Write-Host "Step 4: Creating MOCK integration..." -ForegroundColor Yellow

aws apigateway put-integration `
    --rest-api-id $API_ID `
    --resource-id $RESOURCE_ID `
    --http-method OPTIONS `
    --type MOCK `
    --request-templates '{\"application/json\": \"{\\\"statusCode\\\": 200}\"}' `
    --region $REGION | Out-Null

Write-Host "✓ Created MOCK integration" -ForegroundColor Green

# Step 5: Create method response
Write-Host ""
Write-Host "Step 5: Creating method response..." -ForegroundColor Yellow

aws apigateway put-method-response `
    --rest-api-id $API_ID `
    --resource-id $RESOURCE_ID `
    --http-method OPTIONS `
    --status-code 200 `
    --response-parameters '{\"method.response.header.Access-Control-Allow-Headers\":false,\"method.response.header.Access-Control-Allow-Methods\":false,\"method.response.header.Access-Control-Allow-Origin\":false}' `
    --region $REGION | Out-Null

Write-Host "✓ Created method response" -ForegroundColor Green

# Step 6: Create integration response with CORS headers
Write-Host ""
Write-Host "Step 6: Creating integration response with CORS headers..." -ForegroundColor Yellow

aws apigateway put-integration-response `
    --rest-api-id $API_ID `
    --resource-id $RESOURCE_ID `
    --http-method OPTIONS `
    --status-code 200 `
    --response-parameters '{\"method.response.header.Access-Control-Allow-Headers\":\"'"'"'Content-Type,X-Amz-Date,Authorization,X-Api-Key,X-Amz-Security-Token'"'"'\",\"method.response.header.Access-Control-Allow-Methods\":\"'"'"'GET,POST,PUT,DELETE,OPTIONS'"'"'\",\"method.response.header.Access-Control-Allow-Origin\":\"'"'"'*'"'"'\"}' `
    --region $REGION | Out-Null

Write-Host "✓ Created integration response with CORS headers" -ForegroundColor Green

# Step 7: Deploy to dev stage
Write-Host ""
Write-Host "Step 7: Deploying to dev stage..." -ForegroundColor Yellow

$deployment = aws apigateway create-deployment `
    --rest-api-id $API_ID `
    --stage-name dev `
    --description "Fix CORS for DELETE /api/devices/{deviceId}" `
    --region $REGION | ConvertFrom-Json

Write-Host "✓ Deployed to dev stage (Deployment ID: $($deployment.id))" -ForegroundColor Green

Write-Host ""
Write-Host "========================================" -ForegroundColor Green
Write-Host "✓ CORS Fix Complete!" -ForegroundColor Green
Write-Host "========================================" -ForegroundColor Green
Write-Host ""
Write-Host "The DELETE /api/devices/{deviceId} endpoint now has proper CORS support." -ForegroundColor Cyan
Write-Host "Test by removing a device from the Consumer Dashboard." -ForegroundColor Cyan
