# Create DELETE /api/devices/{deviceId} endpoint with CORS
# This creates the full endpoint structure and integrates with Lambda

$ErrorActionPreference = "Stop"

$API_ID = "vtqjfznspc"
$REGION = "ap-south-1"
$LAMBDA_ARN = "arn:aws:lambda:ap-south-1:211125763856:function:aquachain-function-device-management-dev"
$ACCOUNT_ID = "211125763856"

Write-Host "========================================" -ForegroundColor Cyan
Write-Host "Create Device DELETE Endpoint" -ForegroundColor Cyan
Write-Host "========================================" -ForegroundColor Cyan
Write-Host ""

# Step 1: Find /api/devices resource
Write-Host "Step 1: Finding /api/devices resource..." -ForegroundColor Yellow

$resources = aws apigateway get-resources --rest-api-id $API_ID --region $REGION | ConvertFrom-Json
$devicesResource = $resources.items | Where-Object { $_.path -eq "/api/devices" }

if (-not $devicesResource) {
    Write-Host "ERROR: /api/devices resource not found" -ForegroundColor Red
    exit 1
}

$DEVICES_RESOURCE_ID = $devicesResource.id
Write-Host "✓ Found /api/devices (ID: $DEVICES_RESOURCE_ID)" -ForegroundColor Green

# Step 2: Create {deviceId} resource
Write-Host ""
Write-Host "Step 2: Creating {deviceId} resource..." -ForegroundColor Yellow

# Check if it already exists
$deviceIdResource = $resources.items | Where-Object { 
    $_.pathPart -eq "{deviceId}" -and $_.parentId -eq $DEVICES_RESOURCE_ID 
}

if ($deviceIdResource) {
    Write-Host "⚠ {deviceId} resource already exists (ID: $($deviceIdResource.id))" -ForegroundColor Yellow
    $DEVICE_ID_RESOURCE_ID = $deviceIdResource.id
} else {
    $newResource = aws apigateway create-resource `
        --rest-api-id $API_ID `
        --parent-id $DEVICES_RESOURCE_ID `
        --path-part "{deviceId}" `
        --region $REGION | ConvertFrom-Json
    
    $DEVICE_ID_RESOURCE_ID = $newResource.id
    Write-Host "✓ Created {deviceId} resource (ID: $DEVICE_ID_RESOURCE_ID)" -ForegroundColor Green
}

# Step 3: Create DELETE method
Write-Host ""
Write-Host "Step 3: Creating DELETE method..." -ForegroundColor Yellow

try {
    aws apigateway delete-method `
        --rest-api-id $API_ID `
        --resource-id $DEVICE_ID_RESOURCE_ID `
        --http-method DELETE `
        --region $REGION 2>$null | Out-Null
    Write-Host "⚠ Deleted existing DELETE method" -ForegroundColor Yellow
} catch {}

aws apigateway put-method `
    --rest-api-id $API_ID `
    --resource-id $DEVICE_ID_RESOURCE_ID `
    --http-method DELETE `
    --authorization-type COGNITO_USER_POOLS `
    --authorizer-id "arn:aws:cognito-idp:ap-south-1:211125763856:userpool/ap-south-1_QUDl7hG8u" `
    --request-parameters '{\"method.request.path.deviceId\":true}' `
    --region $REGION | Out-Null

Write-Host "✓ Created DELETE method with Cognito authorization" -ForegroundColor Green

# Step 4: Create Lambda integration
Write-Host ""
Write-Host "Step 4: Creating Lambda integration..." -ForegroundColor Yellow

aws apigateway put-integration `
    --rest-api-id $API_ID `
    --resource-id $DEVICE_ID_RESOURCE_ID `
    --http-method DELETE `
    --type AWS_PROXY `
    --integration-http-method POST `
    --uri "arn:aws:apigateway:${REGION}:lambda:path/2015-03-31/functions/${LAMBDA_ARN}/invocations" `
    --region $REGION | Out-Null

Write-Host "✓ Created Lambda integration" -ForegroundColor Green

# Step 5: Add Lambda permission
Write-Host ""
Write-Host "Step 5: Adding Lambda invoke permission..." -ForegroundColor Yellow

$statementId = "apigateway-delete-device-$(Get-Random)"
try {
    aws lambda add-permission `
        --function-name $LAMBDA_ARN `
        --statement-id $statementId `
        --action lambda:InvokeFunction `
        --principal apigateway.amazonaws.com `
        --source-arn "arn:aws:execute-api:${REGION}:${ACCOUNT_ID}:${API_ID}/*/DELETE/api/devices/*" `
        --region $REGION 2>$null | Out-Null
    Write-Host "✓ Added Lambda permission" -ForegroundColor Green
} catch {
    Write-Host "⚠ Lambda permission may already exist (this is OK)" -ForegroundColor Yellow
}

# Step 6: Create OPTIONS method for CORS
Write-Host ""
Write-Host "Step 6: Creating OPTIONS method for CORS..." -ForegroundColor Yellow

try {
    aws apigateway delete-method `
        --rest-api-id $API_ID `
        --resource-id $DEVICE_ID_RESOURCE_ID `
        --http-method OPTIONS `
        --region $REGION 2>$null | Out-Null
} catch {}

aws apigateway put-method `
    --rest-api-id $API_ID `
    --resource-id $DEVICE_ID_RESOURCE_ID `
    --http-method OPTIONS `
    --authorization-type NONE `
    --region $REGION | Out-Null

Write-Host "✓ Created OPTIONS method" -ForegroundColor Green

# Step 7: Create MOCK integration for OPTIONS
Write-Host ""
Write-Host "Step 7: Creating MOCK integration for OPTIONS..." -ForegroundColor Yellow

aws apigateway put-integration `
    --rest-api-id $API_ID `
    --resource-id $DEVICE_ID_RESOURCE_ID `
    --http-method OPTIONS `
    --type MOCK `
    --request-templates '{\"application/json\": \"{\\\"statusCode\\\": 200}\"}' `
    --region $REGION | Out-Null

Write-Host "✓ Created MOCK integration" -ForegroundColor Green

# Step 8: Create method response for OPTIONS
Write-Host ""
Write-Host "Step 8: Creating method response for OPTIONS..." -ForegroundColor Yellow

aws apigateway put-method-response `
    --rest-api-id $API_ID `
    --resource-id $DEVICE_ID_RESOURCE_ID `
    --http-method OPTIONS `
    --status-code 200 `
    --response-parameters '{\"method.response.header.Access-Control-Allow-Headers\":false,\"method.response.header.Access-Control-Allow-Methods\":false,\"method.response.header.Access-Control-Allow-Origin\":false}' `
    --region $REGION | Out-Null

Write-Host "✓ Created method response" -ForegroundColor Green

# Step 9: Create integration response for OPTIONS with CORS headers
Write-Host ""
Write-Host "Step 9: Creating integration response with CORS headers..." -ForegroundColor Yellow

aws apigateway put-integration-response `
    --rest-api-id $API_ID `
    --resource-id $DEVICE_ID_RESOURCE_ID `
    --http-method OPTIONS `
    --status-code 200 `
    --response-parameters '{\"method.response.header.Access-Control-Allow-Headers\":\"'"'"'Content-Type,X-Amz-Date,Authorization,X-Api-Key,X-Amz-Security-Token'"'"'\",\"method.response.header.Access-Control-Allow-Methods\":\"'"'"'GET,POST,PUT,DELETE,OPTIONS'"'"'\",\"method.response.header.Access-Control-Allow-Origin\":\"'"'"'*'"'"'\"}' `
    --region $REGION | Out-Null

Write-Host "✓ Created integration response with CORS headers" -ForegroundColor Green

# Step 10: Deploy to dev stage
Write-Host ""
Write-Host "Step 10: Deploying to dev stage..." -ForegroundColor Yellow

$deployment = aws apigateway create-deployment `
    --rest-api-id $API_ID `
    --stage-name dev `
    --description "Add DELETE /api/devices/{deviceId} endpoint" `
    --region $REGION | ConvertFrom-Json

Write-Host "✓ Deployed to dev stage (Deployment ID: $($deployment.id))" -ForegroundColor Green

Write-Host ""
Write-Host "========================================" -ForegroundColor Green
Write-Host "✓ Endpoint Created Successfully!" -ForegroundColor Green
Write-Host "========================================" -ForegroundColor Green
Write-Host ""
Write-Host "Endpoint: DELETE https://vtqjfznspc.execute-api.ap-south-1.amazonaws.com/dev/api/devices/{deviceId}" -ForegroundColor Cyan
Write-Host "Authorization: Cognito User Pools" -ForegroundColor Cyan
Write-Host "CORS: Enabled" -ForegroundColor Cyan
Write-Host ""
Write-Host "Test by removing a device from the Consumer Dashboard." -ForegroundColor Yellow
