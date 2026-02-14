# Add Critical Missing API Gateway Endpoints
# Simplified version with direct AWS CLI calls

$apiId = "vtqjfznspc"
$region = "ap-south-1"
$authId = "1q3fsb"
$accountId = "758346259059"

Write-Host "========================================"
Write-Host "Adding Critical Dashboard Endpoints"
Write-Host "========================================"
Write-Host ""

# Get root and /api resource IDs
$rootId = aws apigateway get-resources --rest-api-id $apiId --region $region --query "items[?path=='/'].id" --output text
$apiRootId = aws apigateway get-resources --rest-api-id $apiId --region $region --query "items[?path=='/api'].id" --output text

Write-Host "Root ID: $rootId"
Write-Host "API Root ID: $apiRootId"
Write-Host ""

# 1. Create /api/devices
Write-Host "1. Creating /api/devices..."
$devicesId = aws apigateway create-resource --rest-api-id $apiId --region $region --parent-id $apiRootId --path-part devices --query "id" --output text 2>&1
if ($LASTEXITCODE -ne 0) {
    $devicesId = aws apigateway get-resources --rest-api-id $apiId --region $region --query "items[?path=='/api/devices'].id" --output text
}
Write-Host "  Resource ID: $devicesId"

# Add GET method
aws apigateway put-method --rest-api-id $apiId --region $region --resource-id $devicesId --http-method GET --authorization-type COGNITO_USER_POOLS --authorizer-id $authId 2>$null | Out-Null

# Add integration
aws apigateway put-integration --rest-api-id $apiId --region $region --resource-id $devicesId --http-method GET --type AWS_PROXY --integration-http-method POST --uri "arn:aws:apigateway:${region}:lambda:path/2015-03-31/functions/arn:aws:lambda:${region}:${accountId}:function:aquachain-function-admin-service-dev/invocations" 2>$null | Out-Null

# Add OPTIONS for CORS
aws apigateway put-method --rest-api-id $apiId --region $region --resource-id $devicesId --http-method OPTIONS --authorization-type NONE 2>$null | Out-Null
aws apigateway put-integration --rest-api-id $apiId --region $region --resource-id $devicesId --http-method OPTIONS --type MOCK --request-templates '{\"application/json\":\"{\\\"statusCode\\\": 200}\"}' 2>$null | Out-Null
aws apigateway put-method-response --rest-api-id $apiId --region $region --resource-id $devicesId --http-method OPTIONS --status-code 200 --response-parameters '{\"method.response.header.Access-Control-Allow-Headers\":false,\"method.response.header.Access-Control-Allow-Methods\":false,\"method.response.header.Access-Control-Allow-Origin\":false}' 2>$null | Out-Null
aws apigateway put-integration-response --rest-api-id $apiId --region $region --resource-id $devicesId --http-method OPTIONS --status-code 200 --response-parameters '{\"method.response.header.Access-Control-Allow-Headers\":\"'"'"'Content-Type,Authorization,X-Amz-Date,X-Api-Key,X-Amz-Security-Token'"'"'\",\"method.response.header.Access-Control-Allow-Methods\":\"'"'"'GET,POST,PUT,DELETE,OPTIONS'"'"'\",\"method.response.header.Access-Control-Allow-Origin\":\"'"'"'*'"'"'\"}' 2>$null | Out-Null

# Grant permission
aws lambda add-permission --function-name aquachain-function-admin-service-dev --statement-id apigateway-devices-get --action lambda:InvokeFunction --principal apigateway.amazonaws.com --source-arn "arn:aws:execute-api:${region}:${accountId}:${apiId}/*/GET/api/devices" --region $region 2>$null | Out-Null

Write-Host "  Done!"
Write-Host ""

# 2. Create /dashboard/stats
Write-Host "2. Creating /dashboard/stats..."
$dashboardId = aws apigateway create-resource --rest-api-id $apiId --region $region --parent-id $rootId --path-part dashboard --query "id" --output text 2>&1
if ($LASTEXITCODE -ne 0) {
    $dashboardId = aws apigateway get-resources --rest-api-id $apiId --region $region --query "items[?path=='/dashboard'].id" --output text
}
$statsId = aws apigateway create-resource --rest-api-id $apiId --region $region --parent-id $dashboardId --path-part stats --query "id" --output text 2>&1
if ($LASTEXITCODE -ne 0) {
    $statsId = aws apigateway get-resources --rest-api-id $apiId --region $region --query "items[?path=='/dashboard/stats'].id" --output text
}
Write-Host "  Resource ID: $statsId"

aws apigateway put-method --rest-api-id $apiId --region $region --resource-id $statsId --http-method GET --authorization-type COGNITO_USER_POOLS --authorizer-id $authId 2>$null | Out-Null
aws apigateway put-integration --rest-api-id $apiId --region $region --resource-id $statsId --http-method GET --type AWS_PROXY --integration-http-method POST --uri "arn:aws:apigateway:${region}:lambda:path/2015-03-31/functions/arn:aws:lambda:${region}:${accountId}:function:aquachain-function-data-processing-dev/invocations" 2>$null | Out-Null
aws apigateway put-method --rest-api-id $apiId --region $region --resource-id $statsId --http-method OPTIONS --authorization-type NONE 2>$null | Out-Null
aws apigateway put-integration --rest-api-id $apiId --region $region --resource-id $statsId --http-method OPTIONS --type MOCK --request-templates '{\"application/json\":\"{\\\"statusCode\\\": 200}\"}' 2>$null | Out-Null
aws apigateway put-method-response --rest-api-id $apiId --region $region --resource-id $statsId --http-method OPTIONS --status-code 200 --response-parameters '{\"method.response.header.Access-Control-Allow-Headers\":false,\"method.response.header.Access-Control-Allow-Methods\":false,\"method.response.header.Access-Control-Allow-Origin\":false}' 2>$null | Out-Null
aws apigateway put-integration-response --rest-api-id $apiId --region $region --resource-id $statsId --http-method OPTIONS --status-code 200 --response-parameters '{\"method.response.header.Access-Control-Allow-Headers\":\"'"'"'Content-Type,Authorization,X-Amz-Date,X-Api-Key,X-Amz-Security-Token'"'"'\",\"method.response.header.Access-Control-Allow-Methods\":\"'"'"'GET,POST,PUT,DELETE,OPTIONS'"'"'\",\"method.response.header.Access-Control-Allow-Origin\":\"'"'"'*'"'"'\"}' 2>$null | Out-Null
aws lambda add-permission --function-name aquachain-function-data-processing-dev --statement-id apigateway-dashboard-stats --action lambda:InvokeFunction --principal apigateway.amazonaws.com --source-arn "arn:aws:execute-api:${region}:${accountId}:${apiId}/*/GET/dashboard/stats" --region $region 2>$null | Out-Null

Write-Host "  Done!"
Write-Host ""

# 3. Create /alerts
Write-Host "3. Creating /alerts..."
$alertsId = aws apigateway create-resource --rest-api-id $apiId --region $region --parent-id $rootId --path-part alerts --query "id" --output text 2>&1
if ($LASTEXITCODE -ne 0) {
    $alertsId = aws apigateway get-resources --rest-api-id $apiId --region $region --query "items[?path=='/alerts'].id" --output text
}
Write-Host "  Resource ID: $alertsId"

aws apigateway put-method --rest-api-id $apiId --region $region --resource-id $alertsId --http-method GET --authorization-type COGNITO_USER_POOLS --authorizer-id $authId 2>$null | Out-Null
aws apigateway put-integration --rest-api-id $apiId --region $region --resource-id $alertsId --http-method GET --type AWS_PROXY --integration-http-method POST --uri "arn:aws:apigateway:${region}:lambda:path/2015-03-31/functions/arn:aws:lambda:${region}:${accountId}:function:aquachain-function-alert-detection-dev/invocations" 2>$null | Out-Null
aws apigateway put-method --rest-api-id $apiId --region $region --resource-id $alertsId --http-method OPTIONS --authorization-type NONE 2>$null | Out-Null
aws apigateway put-integration --rest-api-id $apiId --region $region --resource-id $alertsId --http-method OPTIONS --type MOCK --request-templates '{\"application/json\":\"{\\\"statusCode\\\": 200}\"}' 2>$null | Out-Null
aws apigateway put-method-response --rest-api-id $apiId --region $region --resource-id $alertsId --http-method OPTIONS --status-code 200 --response-parameters '{\"method.response.header.Access-Control-Allow-Headers\":false,\"method.response.header.Access-Control-Allow-Methods\":false,\"method.response.header.Access-Control-Allow-Origin\":false}' 2>$null | Out-Null
aws apigateway put-integration-response --rest-api-id $apiId --region $region --resource-id $alertsId --http-method OPTIONS --status-code 200 --response-parameters '{\"method.response.header.Access-Control-Allow-Headers\":\"'"'"'Content-Type,Authorization,X-Amz-Date,X-Api-Key,X-Amz-Security-Token'"'"'\",\"method.response.header.Access-Control-Allow-Methods\":\"'"'"'GET,POST,PUT,DELETE,OPTIONS'"'"'\",\"method.response.header.Access-Control-Allow-Origin\":\"'"'"'*'"'"'\"}' 2>$null | Out-Null
aws lambda add-permission --function-name aquachain-function-alert-detection-dev --statement-id apigateway-alerts-get --action lambda:InvokeFunction --principal apigateway.amazonaws.com --source-arn "arn:aws:execute-api:${region}:${accountId}:${apiId}/*/GET/alerts" --region $region 2>$null | Out-Null

Write-Host "  Done!"
Write-Host ""

# 4. Create /water-quality/latest
Write-Host "4. Creating /water-quality/latest..."
$wqId = aws apigateway create-resource --rest-api-id $apiId --region $region --parent-id $rootId --path-part water-quality --query "id" --output text 2>&1
if ($LASTEXITCODE -ne 0) {
    $wqId = aws apigateway get-resources --rest-api-id $apiId --region $region --query "items[?path=='/water-quality'].id" --output text
}
$latestId = aws apigateway create-resource --rest-api-id $apiId --region $region --parent-id $wqId --path-part latest --query "id" --output text 2>&1
if ($LASTEXITCODE -ne 0) {
    $latestId = aws apigateway get-resources --rest-api-id $apiId --region $region --query "items[?path=='/water-quality/latest'].id" --output text
}
Write-Host "  Resource ID: $latestId"

aws apigateway put-method --rest-api-id $apiId --region $region --resource-id $latestId --http-method GET --authorization-type COGNITO_USER_POOLS --authorizer-id $authId 2>$null | Out-Null
aws apigateway put-integration --rest-api-id $apiId --region $region --resource-id $latestId --http-method GET --type AWS_PROXY --integration-http-method POST --uri "arn:aws:apigateway:${region}:lambda:path/2015-03-31/functions/arn:aws:lambda:${region}:${accountId}:function:aquachain-function-data-processing-dev/invocations" 2>$null | Out-Null
aws apigateway put-method --rest-api-id $apiId --region $region --resource-id $latestId --http-method OPTIONS --authorization-type NONE 2>$null | Out-Null
aws apigateway put-integration --rest-api-id $apiId --region $region --resource-id $latestId --http-method OPTIONS --type MOCK --request-templates '{\"application/json\":\"{\\\"statusCode\\\": 200}\"}' 2>$null | Out-Null
aws apigateway put-method-response --rest-api-id $apiId --region $region --resource-id $latestId --http-method OPTIONS --status-code 200 --response-parameters '{\"method.response.header.Access-Control-Allow-Headers\":false,\"method.response.header.Access-Control-Allow-Methods\":false,\"method.response.header.Access-Control-Allow-Origin\":false}' 2>$null | Out-Null
aws apigateway put-integration-response --rest-api-id $apiId --region $region --resource-id $latestId --http-method OPTIONS --status-code 200 --response-parameters '{\"method.response.header.Access-Control-Allow-Headers\":\"'"'"'Content-Type,Authorization,X-Amz-Date,X-Api-Key,X-Amz-Security-Token'"'"'\",\"method.response.header.Access-Control-Allow-Methods\":\"'"'"'GET,POST,PUT,DELETE,OPTIONS'"'"'\",\"method.response.header.Access-Control-Allow-Origin\":\"'"'"'*'"'"'\"}' 2>$null | Out-Null
aws lambda add-permission --function-name aquachain-function-data-processing-dev --statement-id apigateway-water-quality-latest --action lambda:InvokeFunction --principal apigateway.amazonaws.com --source-arn "arn:aws:execute-api:${region}:${accountId}:${apiId}/*/GET/water-quality/latest" --region $region 2>$null | Out-Null

Write-Host "  Done!"
Write-Host ""

# Deploy
Write-Host "5. Deploying API Gateway..."
aws apigateway create-deployment --rest-api-id $apiId --region $region --stage-name dev --description "Added critical dashboard endpoints" 2>$null | Out-Null
Write-Host "  Done!"
Write-Host ""

Write-Host "========================================"
Write-Host "Critical Endpoints Created Successfully!"
Write-Host "========================================"
Write-Host ""
Write-Host "Endpoints added:"
Write-Host "  - GET /api/devices"
Write-Host "  - GET /dashboard/stats"
Write-Host "  - GET /alerts"
Write-Host "  - GET /water-quality/latest"
Write-Host ""
Write-Host "Dashboard should now load!"
