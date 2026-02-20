# Fix CORS for GET /api/profile/{userId} endpoint
# This script adds OPTIONS method support to allow CORS preflight requests

$ErrorActionPreference = "Stop"

Write-Host "🔧 Fixing CORS for GET /api/profile/{userId} endpoint..." -ForegroundColor Cyan

# Configuration
$API_ID = "vtqjfznspc"
$REGION = "ap-south-1"
$RESOURCE_PATH = "/api/profile/{userId}"

Write-Host "📍 API Gateway ID: $API_ID" -ForegroundColor Yellow
Write-Host "📍 Region: $REGION" -ForegroundColor Yellow
Write-Host "📍 Resource Path: $RESOURCE_PATH" -ForegroundColor Yellow

# Step 1: Find the resource ID for /api/profile/{userId}
Write-Host "`n🔍 Finding resource ID for $RESOURCE_PATH..." -ForegroundColor Cyan

$resources = aws apigateway get-resources --rest-api-id $API_ID --region $REGION | ConvertFrom-Json

# Find /api resource
$apiResource = $resources.items | Where-Object { $_.path -eq "/api" }
if (-not $apiResource) {
    Write-Host "❌ /api resource not found" -ForegroundColor Red
    exit 1
}

# Find /api/profile resource
$profileResource = $resources.items | Where-Object { $_.path -eq "/api/profile" }
if (-not $profileResource) {
    Write-Host "❌ /api/profile resource not found" -ForegroundColor Red
    exit 1
}

# Find /api/profile/{userId} resource
$userIdResource = $resources.items | Where-Object { $_.path -eq "/api/profile/{userId}" }
if (-not $userIdResource) {
    Write-Host "❌ /api/profile/{userId} resource not found" -ForegroundColor Red
    exit 1
}

$RESOURCE_ID = $userIdResource.id
Write-Host "✅ Found resource ID: $RESOURCE_ID" -ForegroundColor Green

# Step 2: Check if OPTIONS method already exists
Write-Host "`n🔍 Checking for existing OPTIONS method..." -ForegroundColor Cyan

try {
    $existingMethod = aws apigateway get-method `
        --rest-api-id $API_ID `
        --resource-id $RESOURCE_ID `
        --http-method OPTIONS `
        --region $REGION 2>&1
    
    if ($LASTEXITCODE -eq 0) {
        Write-Host "⚠️  OPTIONS method already exists, deleting it first..." -ForegroundColor Yellow
        aws apigateway delete-method `
            --rest-api-id $API_ID `
            --resource-id $RESOURCE_ID `
            --http-method OPTIONS `
            --region $REGION | Out-Null
        Write-Host "✅ Deleted existing OPTIONS method" -ForegroundColor Green
    }
} catch {
    Write-Host "✅ No existing OPTIONS method found" -ForegroundColor Green
}

# Step 3: Create OPTIONS method with MOCK integration
Write-Host "`n🔧 Creating OPTIONS method with MOCK integration..." -ForegroundColor Cyan

aws apigateway put-method `
    --rest-api-id $API_ID `
    --resource-id $RESOURCE_ID `
    --http-method OPTIONS `
    --authorization-type NONE `
    --region $REGION | Out-Null

if ($LASTEXITCODE -ne 0) {
    Write-Host "❌ Failed to create OPTIONS method" -ForegroundColor Red
    exit 1
}

Write-Host "✅ Created OPTIONS method" -ForegroundColor Green

# Step 4: Set up MOCK integration
Write-Host "`n🔧 Setting up MOCK integration..." -ForegroundColor Cyan

aws apigateway put-integration `
    --rest-api-id $API_ID `
    --resource-id $RESOURCE_ID `
    --http-method OPTIONS `
    --type MOCK `
    --request-templates '{\"application/json\": \"{\\\"statusCode\\\": 200}\"}' `
    --region $REGION | Out-Null

if ($LASTEXITCODE -ne 0) {
    Write-Host "❌ Failed to set up MOCK integration" -ForegroundColor Red
    exit 1
}

Write-Host "✅ Set up MOCK integration" -ForegroundColor Green

# Step 5: Set up method response
Write-Host "`n🔧 Setting up method response..." -ForegroundColor Cyan

aws apigateway put-method-response `
    --rest-api-id $API_ID `
    --resource-id $RESOURCE_ID `
    --http-method OPTIONS `
    --status-code 200 `
    --response-parameters '{\"method.response.header.Access-Control-Allow-Headers\":false,\"method.response.header.Access-Control-Allow-Methods\":false,\"method.response.header.Access-Control-Allow-Origin\":false}' `
    --region $REGION | Out-Null

if ($LASTEXITCODE -ne 0) {
    Write-Host "❌ Failed to set up method response" -ForegroundColor Red
    exit 1
}

Write-Host "✅ Set up method response" -ForegroundColor Green

# Step 6: Set up integration response with CORS headers
Write-Host "`n🔧 Setting up integration response with CORS headers..." -ForegroundColor Cyan

aws apigateway put-integration-response `
    --rest-api-id $API_ID `
    --resource-id $RESOURCE_ID `
    --http-method OPTIONS `
    --status-code 200 `
    --response-parameters '{\"method.response.header.Access-Control-Allow-Headers\":\"'"'"'Content-Type,X-Amz-Date,Authorization,X-Api-Key,X-Amz-Security-Token'"'"'\",\"method.response.header.Access-Control-Allow-Methods\":\"'"'"'GET,OPTIONS'"'"'\",\"method.response.header.Access-Control-Allow-Origin\":\"'"'"'*'"'"'\"}' `
    --region $REGION | Out-Null

if ($LASTEXITCODE -ne 0) {
    Write-Host "❌ Failed to set up integration response" -ForegroundColor Red
    exit 1
}

Write-Host "✅ Set up integration response with CORS headers" -ForegroundColor Green

# Step 7: Deploy the changes
Write-Host "`n🚀 Deploying changes to 'dev' stage..." -ForegroundColor Cyan

aws apigateway create-deployment `
    --rest-api-id $API_ID `
    --stage-name dev `
    --description "Fix CORS for GET /api/profile/{userId}" `
    --region $REGION | Out-Null

if ($LASTEXITCODE -ne 0) {
    Write-Host "❌ Failed to deploy changes" -ForegroundColor Red
    exit 1
}

Write-Host "✅ Deployed changes to 'dev' stage" -ForegroundColor Green

# Step 8: Test the OPTIONS request
Write-Host "`n🧪 Testing OPTIONS request..." -ForegroundColor Cyan

$testUrl = "https://$API_ID.execute-api.$REGION.amazonaws.com/dev/api/profile/test-user-id"
Write-Host "Testing: $testUrl" -ForegroundColor Yellow

try {
    $response = curl.exe -X OPTIONS $testUrl -i -s
    
    if ($response -match "200 OK") {
        Write-Host "✅ OPTIONS request successful!" -ForegroundColor Green
        Write-Host "`nResponse headers:" -ForegroundColor Cyan
        $response | Select-String "Access-Control" | ForEach-Object { Write-Host $_ -ForegroundColor Yellow }
    } else {
        Write-Host "⚠️  OPTIONS request returned non-200 status" -ForegroundColor Yellow
        Write-Host $response
    }
} catch {
    Write-Host "⚠️  Could not test OPTIONS request: $_" -ForegroundColor Yellow
}

Write-Host "`n✅ CORS fix complete for GET /api/profile/{userId}!" -ForegroundColor Green
Write-Host "🔄 Please refresh your browser and try logging in again." -ForegroundColor Cyan
