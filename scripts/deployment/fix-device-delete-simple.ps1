# Simple fix for DELETE /api/devices/{deviceId} endpoint
# Uses AWS CLI with proper JSON handling

$ErrorActionPreference = "Stop"

$API_ID = "vtqjfznspc"
$REGION = "ap-south-1"
$LAMBDA_ARN = "arn:aws:lambda:ap-south-1:211125763856:function:aquachain-function-device-management-dev"
$DEVICE_ID_RESOURCE_ID = "mlu5yv"  # From previous script output

Write-Host "========================================" -ForegroundColor Cyan
Write-Host "Fix Device DELETE Endpoint (Simple)" -ForegroundColor Cyan
Write-Host "========================================" -ForegroundColor Cyan
Write-Host ""

# Step 1: Create DELETE method (retry without request parameters)
Write-Host "Step 1: Creating DELETE method..." -ForegroundColor Yellow

try {
    aws apigateway delete-method `
        --rest-api-id $API_ID `
        --resource-id $DEVICE_ID_RESOURCE_ID `
        --http-method DELETE `
        --region $REGION 2>$null | Out-Null
} catch {}

# Find authorizer ID
$authorizers = aws apigateway get-authorizers --rest-api-id $API_ID --region $REGION | ConvertFrom-Json
$cognitoAuth = $authorizers.items | Where-Object { $_.type -eq "COGNITO_USER_POOLS" } | Select-Object -First 1

if ($cognitoAuth) {
    Write-Host "✓ Found Cognito authorizer: $($cognitoAuth.id)" -ForegroundColor Green
    
    aws apigateway put-method `
        --rest-api-id $API_ID `
        --resource-id $DEVICE_ID_RESOURCE_ID `
        --http-method DELETE `
        --authorization-type COGNITO_USER_POOLS `
        --authorizer-id $cognitoAuth.id `
        --region $REGION | Out-Null
} else {
    Write-Host "⚠ No Cognito authorizer found, using NONE" -ForegroundColor Yellow
    
    aws apigateway put-method `
        --rest-api-id $API_ID `
        --resource-id $DEVICE_ID_RESOURCE_ID `
        --http-method DELETE `
        --authorization-type NONE `
        --region $REGION | Out-Null
}

Write-Host "✓ Created DELETE method" -ForegroundColor Green

# Step 2: Create Lambda integration
Write-Host ""
Write-Host "Step 2: Creating Lambda integration..." -ForegroundColor Yellow

aws apigateway put-integration `
    --rest-api-id $API_ID `
    --resource-id $DEVICE_ID_RESOURCE_ID `
    --http-method DELETE `
    --type AWS_PROXY `
    --integration-http-method POST `
    --uri "arn:aws:apigateway:${REGION}:lambda:path/2015-03-31/functions/${LAMBDA_ARN}/invocations" `
    --region $REGION | Out-Null

Write-Host "✓ Created Lambda integration" -ForegroundColor Green

# Step 3: Create OPTIONS method
Write-Host ""
Write-Host "Step 3: Creating OPTIONS method..." -ForegroundColor Yellow

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

# Step 4: Create MOCK integration for OPTIONS
Write-Host ""
Write-Host "Step 4: Creating MOCK integration..." -ForegroundColor Yellow

# Create temp JSON file for request templates
$requestTemplate = @{
    "application/json" = '{"statusCode": 200}'
}
$requestTemplate | ConvertTo-Json -Compress | Out-File -FilePath "temp-request-template.json" -Encoding utf8

aws apigateway put-integration `
    --rest-api-id $API_ID `
    --resource-id $DEVICE_ID_RESOURCE_ID `
    --http-method OPTIONS `
    --type MOCK `
    --request-templates file://temp-request-template.json `
    --region $REGION | Out-Null

Remove-Item "temp-request-template.json" -Force

Write-Host "✓ Created MOCK integration" -ForegroundColor Green

# Step 5: Create method response
Write-Host ""
Write-Host "Step 5: Creating method response..." -ForegroundColor Yellow

$responseParams = @{
    "method.response.header.Access-Control-Allow-Headers" = $false
    "method.response.header.Access-Control-Allow-Methods" = $false
    "method.response.header.Access-Control-Allow-Origin" = $false
}
$responseParams | ConvertTo-Json -Compress | Out-File -FilePath "temp-response-params.json" -Encoding utf8

aws apigateway put-method-response `
    --rest-api-id $API_ID `
    --resource-id $DEVICE_ID_RESOURCE_ID `
    --http-method OPTIONS `
    --status-code 200 `
    --response-parameters file://temp-response-params.json `
    --region $REGION | Out-Null

Remove-Item "temp-response-params.json" -Force

Write-Host "✓ Created method response" -ForegroundColor Green

# Step 6: Create integration response with CORS
Write-Host ""
Write-Host "Step 6: Creating integration response with CORS..." -ForegroundColor Yellow

$integrationResponseParams = @{
    "method.response.header.Access-Control-Allow-Headers" = "'Content-Type,X-Amz-Date,Authorization,X-Api-Key,X-Amz-Security-Token'"
    "method.response.header.Access-Control-Allow-Methods" = "'GET,POST,PUT,DELETE,OPTIONS'"
    "method.response.header.Access-Control-Allow-Origin" = "'*'"
}
$integrationResponseParams | ConvertTo-Json -Compress | Out-File -FilePath "temp-integration-response.json" -Encoding utf8

aws apigateway put-integration-response `
    --rest-api-id $API_ID `
    --resource-id $DEVICE_ID_RESOURCE_ID `
    --http-method OPTIONS `
    --status-code 200 `
    --response-parameters file://temp-integration-response.json `
    --region $REGION | Out-Null

Remove-Item "temp-integration-response.json" -Force

Write-Host "✓ Created integration response with CORS" -ForegroundColor Green

# Step 7: Deploy
Write-Host ""
Write-Host "Step 7: Deploying to dev stage..." -ForegroundColor Yellow

$deployment = aws apigateway create-deployment `
    --rest-api-id $API_ID `
    --stage-name dev `
    --description "Fix DELETE /api/devices/{deviceId}" `
    --region $REGION | ConvertFrom-Json

Write-Host "✓ Deployed (ID: $($deployment.id))" -ForegroundColor Green

Write-Host ""
Write-Host "========================================" -ForegroundColor Green
Write-Host "✓ Complete!" -ForegroundColor Green
Write-Host "========================================" -ForegroundColor Green
Write-Host ""
Write-Host "Endpoint: DELETE https://vtqjfznspc.execute-api.ap-south-1.amazonaws.com/dev/api/devices/{deviceId}" -ForegroundColor Cyan
