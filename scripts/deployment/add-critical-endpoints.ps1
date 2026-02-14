# Add Critical Missing API Gateway Endpoints
# This script creates the Priority 1 endpoints needed for dashboard functionality

$apiId = "vtqjfznspc"
$region = "ap-south-1"
$authId = "1q3fsb"
$accountId = "758346259059"

Write-Host "========================================" -ForegroundColor Cyan
Write-Host "Adding Critical Dashboard Endpoints" -ForegroundColor Cyan
Write-Host "========================================" -ForegroundColor Cyan
Write-Host ""

# Lambda ARNs
$dataProcessingLambda = "arn:aws:lambda:$region:${accountId}:function:aquachain-function-data-processing-dev"
$alertDetectionLambda = "arn:aws:lambda:$region:${accountId}:function:aquachain-function-alert-detection-dev"
$adminServiceLambda = "arn:aws:lambda:$region:${accountId}:function:aquachain-function-admin-service-dev"

# Function to add CORS to a resource
function Add-CorsToResource {
    param($resourceId, $resourcePath)
    
    Write-Host "  Adding CORS to $resourcePath..." -ForegroundColor Yellow
    
    # Add OPTIONS method
    aws apigateway put-method `
        --rest-api-id $apiId `
        --region $region `
        --resource-id $resourceId `
        --http-method OPTIONS `
        --authorization-type NONE 2>$null | Out-Null
    
    # Add MOCK integration
    aws apigateway put-integration `
        --rest-api-id $apiId `
        --region $region `
        --resource-id $resourceId `
        --http-method OPTIONS `
        --type MOCK `
        --request-templates '{\"application/json\":\"{\\\"statusCode\\\": 200}\"}' 2>$null | Out-Null
    
    # Add method response
    aws apigateway put-method-response `
        --rest-api-id $apiId `
        --region $region `
        --resource-id $resourceId `
        --http-method OPTIONS `
        --status-code 200 `
        --response-parameters '{\"method.response.header.Access-Control-Allow-Headers\":false,\"method.response.header.Access-Control-Allow-Methods\":false,\"method.response.header.Access-Control-Allow-Origin\":false}' 2>$null | Out-Null
    
    # Add integration response
    aws apigateway put-integration-response `
        --rest-api-id $apiId `
        --region $region `
        --resource-id $resourceId `
        --http-method OPTIONS `
        --status-code 200 `
        --response-parameters '{\"method.response.header.Access-Control-Allow-Headers\":\"'"'"'Content-Type,Authorization,X-Amz-Date,X-Api-Key,X-Amz-Security-Token'"'"'\",\"method.response.header.Access-Control-Allow-Methods\":\"'"'"'GET,POST,PUT,DELETE,OPTIONS'"'"'\",\"method.response.header.Access-Control-Allow-Origin\":\"'"'"'*'"'"'\"}' 2>$null | Out-Null
    
    Write-Host "  ✓ CORS added" -ForegroundColor Green
}

# Get /api resource ID
$apiRootId = aws apigateway get-resources `
    --rest-api-id $apiId `
    --region $region `
    --query "items[?path=='/api'].id" `
    --output text

Write-Host "1. Creating /api/devices endpoint..." -ForegroundColor Cyan

# Create /api/devices resource
$devicesResult = aws apigateway create-resource `
    --rest-api-id $apiId `
    --region $region `
    --parent-id $apiRootId `
    --path-part devices 2>&1

if ($LASTEXITCODE -ne 0) {
    if ($devicesResult -match "ConflictException") {
        Write-Host "  Resource already exists, getting ID..." -ForegroundColor Yellow
        $devicesId = aws apigateway get-resources `
            --rest-api-id $apiId `
            --region $region `
            --query "items[?path=='/api/devices'].id" `
            --output text
    } else {
        Write-Host "  ✗ Failed to create resource: $devicesResult" -ForegroundColor Red
        exit 1
    }
} else {
    $devicesId = ($devicesResult | ConvertFrom-Json).id
}

Write-Host "  Resource ID: $devicesId" -ForegroundColor White

# Add GET method to /api/devices
aws apigateway put-method `
    --rest-api-id $apiId `
    --region $region `
    --resource-id $devicesId `
    --http-method GET `
    --authorization-type COGNITO_USER_POOLS `
    --authorizer-id $authId 2>$null | Out-Null

# Add Lambda integration
aws apigateway put-integration `
    --rest-api-id $apiId `
    --region $region `
    --resource-id $devicesId `
    --http-method GET `
    --type AWS_PROXY `
    --integration-http-method POST `
    --uri "arn:aws:apigateway:${region}:lambda:path/2015-03-31/functions/${adminServiceLambda}/invocations" 2>$null | Out-Null

Add-CorsToResource -resourceId $devicesId -resourcePath "/api/devices"

# Grant Lambda permission
aws lambda add-permission `
    --function-name aquachain-function-admin-service-dev `
    --statement-id apigateway-devices-get `
    --action lambda:InvokeFunction `
    --principal apigateway.amazonaws.com `
    --source-arn "arn:aws:execute-api:${region}:${accountId}:${apiId}/*/GET/api/devices" `
    --region $region 2>$null | Out-Null

Write-Host "  ✓ GET /api/devices created" -ForegroundColor Green
Write-Host ""

# Create /dashboard resource
Write-Host "2. Creating /dashboard/stats endpoint..." -ForegroundColor Cyan

$rootId = aws apigateway get-resources `
    --rest-api-id $apiId `
    --region $region `
    --query "items[?path=='/'].id" `
    --output text

$dashboardResult = aws apigateway create-resource `
    --rest-api-id $apiId `
    --region $region `
    --parent-id $rootId `
    --path-part dashboard 2>&1

if ($LASTEXITCODE -ne 0 -and $dashboardResult -match "ConflictException") {
    $dashboardId = aws apigateway get-resources `
        --rest-api-id $apiId `
        --region $region `
        --query "items[?path=='/dashboard'].id" `
        --output text
} else {
    $dashboardId = ($dashboardResult | ConvertFrom-Json).id
}

$statsResult = aws apigateway create-resource `
    --rest-api-id $apiId `
    --region $region `
    --parent-id $dashboardId `
    --path-part stats 2>&1

if ($LASTEXITCODE -ne 0 -and $statsResult -match "ConflictException") {
    $statsId = aws apigateway get-resources `
        --rest-api-id $apiId `
        --region $region `
        --query "items[?path=='/dashboard/stats'].id" `
        --output text
} else {
    $statsId = ($statsResult | ConvertFrom-Json).id
}

# Add GET method
aws apigateway put-method `
    --rest-api-id $apiId `
    --region $region `
    --resource-id $statsId `
    --http-method GET `
    --authorization-type COGNITO_USER_POOLS `
    --authorizer-id $authId 2>$null | Out-Null

aws apigateway put-integration `
    --rest-api-id $apiId `
    --region $region `
    --resource-id $statsId `
    --http-method GET `
    --type AWS_PROXY `
    --integration-http-method POST `
    --uri "arn:aws:apigateway:${region}:lambda:path/2015-03-31/functions/${dataProcessingLambda}/invocations" 2>$null | Out-Null

Add-CorsToResource -resourceId $statsId -resourcePath "/dashboard/stats"

aws lambda add-permission `
    --function-name aquachain-function-data-processing-dev `
    --statement-id apigateway-dashboard-stats `
    --action lambda:InvokeFunction `
    --principal apigateway.amazonaws.com `
    --source-arn "arn:aws:execute-api:${region}:${accountId}:${apiId}/*/GET/dashboard/stats" `
    --region $region 2>$null | Out-Null

Write-Host "  ✓ GET /dashboard/stats created" -ForegroundColor Green
Write-Host ""

# Create /alerts endpoint
Write-Host "3. Creating /alerts endpoint..." -ForegroundColor Cyan

$alertsResult = aws apigateway create-resource `
    --rest-api-id $apiId `
    --region $region `
    --parent-id $rootId `
    --path-part alerts 2>&1

if ($LASTEXITCODE -ne 0 -and $alertsResult -match "ConflictException") {
    $alertsId = aws apigateway get-resources `
        --rest-api-id $apiId `
        --region $region `
        --query "items[?path=='/alerts'].id" `
        --output text
} else {
    $alertsId = ($alertsResult | ConvertFrom-Json).id
}

aws apigateway put-method `
    --rest-api-id $apiId `
    --region $region `
    --resource-id $alertsId `
    --http-method GET `
    --authorization-type COGNITO_USER_POOLS `
    --authorizer-id $authId 2>$null | Out-Null

aws apigateway put-integration `
    --rest-api-id $apiId `
    --region $region `
    --resource-id $alertsId `
    --http-method GET `
    --type AWS_PROXY `
    --integration-http-method POST `
    --uri "arn:aws:apigateway:${region}:lambda:path/2015-03-31/functions/${alertDetectionLambda}/invocations" 2>$null | Out-Null

Add-CorsToResource -resourceId $alertsId -resourcePath "/alerts"

aws lambda add-permission `
    --function-name aquachain-function-alert-detection-dev `
    --statement-id apigateway-alerts-get `
    --action lambda:InvokeFunction `
    --principal apigateway.amazonaws.com `
    --source-arn "arn:aws:execute-api:${region}:${accountId}:${apiId}/*/GET/alerts" `
    --region $region 2>$null | Out-Null

Write-Host "  ✓ GET /alerts created" -ForegroundColor Green
Write-Host ""

# Create /water-quality/latest endpoint
Write-Host "4. Creating /water-quality/latest endpoint..." -ForegroundColor Cyan

$wqResult = aws apigateway create-resource `
    --rest-api-id $apiId `
    --region $region `
    --parent-id $rootId `
    --path-part water-quality 2>&1

if ($LASTEXITCODE -ne 0 -and $wqResult -match "ConflictException") {
    $wqId = aws apigateway get-resources `
        --rest-api-id $apiId `
        --region $region `
        --query "items[?path=='/water-quality'].id" `
        --output text
} else {
    $wqId = ($wqResult | ConvertFrom-Json).id
}

$latestResult = aws apigateway create-resource `
    --rest-api-id $apiId `
    --region $region `
    --parent-id $wqId `
    --path-part latest 2>&1

if ($LASTEXITCODE -ne 0 -and $latestResult -match "ConflictException") {
    $latestId = aws apigateway get-resources `
        --rest-api-id $apiId `
        --region $region `
        --query "items[?path=='/water-quality/latest'].id" `
        --output text
} else {
    $latestId = ($latestResult | ConvertFrom-Json).id
}

aws apigateway put-method `
    --rest-api-id $apiId `
    --region $region `
    --resource-id $latestId `
    --http-method GET `
    --authorization-type COGNITO_USER_POOLS `
    --authorizer-id $authId 2>$null | Out-Null

aws apigateway put-integration `
    --rest-api-id $apiId `
    --region $region `
    --resource-id $latestId `
    --http-method GET `
    --type AWS_PROXY `
    --integration-http-method POST `
    --uri "arn:aws:apigateway:${region}:lambda:path/2015-03-31/functions/${dataProcessingLambda}/invocations" `
    --region $region 2>$null | Out-Null

Add-CorsToResource -resourceId $latestId -resourcePath "/water-quality/latest"

aws lambda add-permission `
    --function-name aquachain-function-data-processing-dev `
    --statement-id apigateway-water-quality-latest `
    --action lambda:InvokeFunction `
    --principal apigateway.amazonaws.com `
    --source-arn "arn:aws:execute-api:${region}:${accountId}:${apiId}/*/GET/water-quality/latest" `
    --region $region 2>$null | Out-Null

Write-Host "  ✓ GET /water-quality/latest created" -ForegroundColor Green
Write-Host ""

# Deploy API
Write-Host "5. Deploying API Gateway..." -ForegroundColor Cyan
aws apigateway create-deployment `
    --rest-api-id $apiId `
    --region $region `
    --stage-name dev `
    --description "Added critical dashboard endpoints" 2>$null | Out-Null

Write-Host "  ✓ Deployed to dev stage" -ForegroundColor Green
Write-Host ""

Write-Host "========================================" -ForegroundColor Green
Write-Host "✓ Critical Endpoints Created!" -ForegroundColor Green
Write-Host "========================================" -ForegroundColor Green
Write-Host ""
Write-Host "Endpoints added:" -ForegroundColor Cyan
Write-Host "  - GET /api/devices" -ForegroundColor White
Write-Host "  - GET /dashboard/stats" -ForegroundColor White
Write-Host "  - GET /alerts" -ForegroundColor White
Write-Host "  - GET /water-quality/latest" -ForegroundColor White
Write-Host ""
Write-Host "Dashboard should now load successfully!" -ForegroundColor Green
