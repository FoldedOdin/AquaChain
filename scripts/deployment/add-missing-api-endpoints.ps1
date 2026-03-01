# Add Missing API Gateway Endpoints
# This script adds all missing endpoints that exist in dev-server but not in production

$apiId = "vtqjfznspc"
$region = "ap-south-1"
$authId = "1q3fsb"
$userMgmtLambda = "arn:aws:lambda:ap-south-1:758346259059:function:aquachain-function-user-management-dev"
$notificationLambda = "arn:aws:lambda:ap-south-1:758346259059:function:aquachain-function-notification-dev"

Write-Host "========================================" -ForegroundColor Cyan
Write-Host "Adding Missing API Gateway Endpoints" -ForegroundColor Cyan
Write-Host "========================================" -ForegroundColor Cyan
Write-Host ""

# Function to add CORS to a resource
function Add-CorsToResource {
    param($resourceId, $resourcePath)
    
    Write-Host "Adding CORS to $resourcePath..." -ForegroundColor Yellow
    
    # Add OPTIONS method
    aws apigateway put-method `
        --rest-api-id $apiId `
        --region $region `
        --resource-id $resourceId `
        --http-method OPTIONS `
        --authorization-type NONE | Out-Null
    
    # Add MOCK integration
    $requestTemplates = @{'application/json'='{"statusCode": 200}'} | ConvertTo-Json -Compress
    aws apigateway put-integration `
        --rest-api-id $apiId `
        --region $region `
        --resource-id $resourceId `
        --http-method OPTIONS `
        --type MOCK `
        --request-templates $requestTemplates | Out-Null
    
    # Add method response
    $methodParams = @{
        'method.response.header.Access-Control-Allow-Headers'=$false
        'method.response.header.Access-Control-Allow-Methods'=$false
        'method.response.header.Access-Control-Allow-Origin'=$false
    } | ConvertTo-Json -Compress
    
    aws apigateway put-method-response `
        --rest-api-id $apiId `
        --region $region `
        --resource-id $resourceId `
        --http-method OPTIONS `
        --status-code 200 `
        --response-parameters $methodParams | Out-Null
    
    # Add integration response
    $respParams = @{
        'method.response.header.Access-Control-Allow-Headers'="'Content-Type,Authorization,X-Amz-Date,X-Api-Key,X-Amz-Security-Token'"
        'method.response.header.Access-Control-Allow-Methods'="'GET,POST,PUT,DELETE,OPTIONS'"
        'method.response.header.Access-Control-Allow-Origin'="'*'"
    } | ConvertTo-Json -Compress
    
    aws apigateway put-integration-response `
        --rest-api-id $apiId `
        --region $region `
        --resource-id $resourceId `
        --http-method OPTIONS `
        --status-code 200 `
        --response-parameters $respParams | Out-Null
    
    Write-Host "  ✓ CORS added" -ForegroundColor Green
}

# Complete /api/profile/update setup
Write-Host "Completing /api/profile/update setup..." -ForegroundColor Cyan
$profileUpdateId = "c84ane"
Add-CorsToResource -resourceId $profileUpdateId -resourcePath "/api/profile/update"

aws lambda add-permission `
    --function-name aquachain-function-user-management-dev `
    --statement-id apigateway-profile-update `
    --action lambda:InvokeFunction `
    --principal apigateway.amazonaws.com `
    --source-arn "arn:aws:execute-api:$region:758346259059:$apiId/*/PUT/api/profile/update" `
    --region $region 2>$null | Out-Null

Write-Host "  ✓ /api/profile/update complete" -ForegroundColor Green
Write-Host ""

# Create /api/notifications and its sub-resources
Write-Host "Creating /api/notifications endpoints..." -ForegroundColor Cyan

# Get /api resource ID
$apiRootId = aws apigateway get-resources `
    --rest-api-id $apiId `
    --region $region `
    --query "items[?path=='/api'].id" `
    --output text

# Create /api/notifications
$notifResult = aws apigateway create-resource `
    --rest-api-id $apiId `
    --region $region `
    --parent-id $apiRootId `
    --path-part notifications | ConvertFrom-Json

$notifId = $notifResult.id
Write-Host "  ✓ Created /api/notifications (ID: $notifId)" -ForegroundColor Green

# Add GET /api/notifications
aws apigateway put-method `
    --rest-api-id $apiId `
    --region $region `
    --resource-id $notifId `
    --http-method GET `
    --authorization-type COGNITO_USER_POOLS `
    --authorizer-id $authId | Out-Null

aws apigateway put-integration `
    --rest-api-id $apiId `
    --region $region `
    --resource-id $notifId `
    --http-method GET `
    --type AWS_PROXY `
    --integration-http-method POST `
    --uri "arn:aws:apigateway:$region:lambda:path/2015-03-31/functions/$notificationLambda/invocations" | Out-Null

# Add POST /api/notifications
aws apigateway put-method `
    --rest-api-id $apiId `
    --region $region `
    --resource-id $notifId `
    --http-method POST `
    --authorization-type COGNITO_USER_POOLS `
    --authorizer-id $authId | Out-Null

aws apigateway put-integration `
    --rest-api-id $apiId `
    --region $region `
    --resource-id $notifId `
    --http-method POST `
    --type AWS_PROXY `
    --integration-http-method POST `
    --uri "arn:aws:apigateway:$region:lambda:path/2015-03-31/functions/$notificationLambda/invocations" | Out-Null

Add-CorsToResource -resourceId $notifId -resourcePath "/api/notifications"

# Create /api/notifications/unread-count
$unreadResult = aws apigateway create-resource `
    --rest-api-id $apiId `
    --region $region `
    --parent-id $notifId `
    --path-part unread-count | ConvertFrom-Json

$unreadId = $unreadResult.id

aws apigateway put-method `
    --rest-api-id $apiId `
    --region $region `
    --resource-id $unreadId `
    --http-method GET `
    --authorization-type COGNITO_USER_POOLS `
    --authorizer-id $authId | Out-Null

aws apigateway put-integration `
    --rest-api-id $apiId `
    --region $region `
    --resource-id $unreadId `
    --http-method GET `
    --type AWS_PROXY `
    --integration-http-method POST `
    --uri "arn:aws:apigateway:$region:lambda:path/2015-03-31/functions/$notificationLambda/invocations" | Out-Null

Add-CorsToResource -resourceId $unreadId -resourcePath "/api/notifications/unread-count"

# Create /api/notifications/read-all
$readAllResult = aws apigateway create-resource `
    --rest-api-id $apiId `
    --region $region `
    --parent-id $notifId `
    --path-part read-all | ConvertFrom-Json

$readAllId = $readAllResult.id

aws apigateway put-method `
    --rest-api-id $apiId `
    --region $region `
    --resource-id $readAllId `
    --http-method PUT `
    --authorization-type COGNITO_USER_POOLS `
    --authorizer-id $authId | Out-Null

aws apigateway put-integration `
    --rest-api-id $apiId `
    --region $region `
    --resource-id $readAllId `
    --http-method PUT `
    --type AWS_PROXY `
    --integration-http-method POST `
    --uri "arn:aws:apigateway:$region:lambda:path/2015-03-31/functions/$notificationLambda/invocations" | Out-Null

Add-CorsToResource -resourceId $readAllId -resourcePath "/api/notifications/read-all"

# Create /api/notifications/{notificationId}
$notifIdResult = aws apigateway create-resource `
    --rest-api-id $apiId `
    --region $region `
    --parent-id $notifId `
    --path-part '{notificationId}' | ConvertFrom-Json

$notifIdResourceId = $notifIdResult.id

# Add PUT /api/notifications/{notificationId}/read
$readResult = aws apigateway create-resource `
    --rest-api-id $apiId `
    --region $region `
    --parent-id $notifIdResourceId `
    --path-part read | ConvertFrom-Json

$readId = $readResult.id

aws apigateway put-method `
    --rest-api-id $apiId `
    --region $region `
    --resource-id $readId `
    --http-method PUT `
    --authorization-type COGNITO_USER_POOLS `
    --authorizer-id $authId | Out-Null

aws apigateway put-integration `
    --rest-api-id $apiId `
    --region $region `
    --resource-id $readId `
    --http-method PUT `
    --type AWS_PROXY `
    --integration-http-method POST `
    --uri "arn:aws:apigateway:$region:lambda:path/2015-03-31/functions/$notificationLambda/invocations" | Out-Null

Add-CorsToResource -resourceId $readId -resourcePath "/api/notifications/{notificationId}/read"

# Add DELETE /api/notifications/{notificationId}
aws apigateway put-method `
    --rest-api-id $apiId `
    --region $region `
    --resource-id $notifIdResourceId `
    --http-method DELETE `
    --authorization-type COGNITO_USER_POOLS `
    --authorizer-id $authId | Out-Null

aws apigateway put-integration `
    --rest-api-id $apiId `
    --region $region `
    --resource-id $notifIdResourceId `
    --http-method DELETE `
    --type AWS_PROXY `
    --integration-http-method POST `
    --uri "arn:aws:apigateway:$region:lambda:path/2015-03-31/functions/$notificationLambda/invocations" | Out-Null

Add-CorsToResource -resourceId $notifIdResourceId -resourcePath "/api/notifications/{notificationId}"

Write-Host "  ✓ All notification endpoints created" -ForegroundColor Green
Write-Host ""

# Grant Lambda permissions
Write-Host "Granting Lambda permissions..." -ForegroundColor Cyan

aws lambda add-permission `
    --function-name aquachain-function-notification-dev `
    --statement-id apigateway-notifications-all `
    --action lambda:InvokeFunction `
    --principal apigateway.amazonaws.com `
    --source-arn "arn:aws:execute-api:$region:758346259059:$apiId/*/*/api/notifications*" `
    --region $region 2>$null | Out-Null

Write-Host "  ✓ Permissions granted" -ForegroundColor Green
Write-Host ""

# Deploy API
Write-Host "Deploying API Gateway..." -ForegroundColor Cyan
aws apigateway create-deployment `
    --rest-api-id $apiId `
    --region $region `
    --stage-name dev `
    --description "Added profile/update and notifications endpoints" | Out-Null

Write-Host "  ✓ Deployed to dev stage" -ForegroundColor Green
Write-Host ""

Write-Host "========================================" -ForegroundColor Green
Write-Host "✓ All endpoints added successfully!" -ForegroundColor Green
Write-Host "========================================" -ForegroundColor Green
Write-Host ""
Write-Host "Endpoints added:" -ForegroundColor Cyan
Write-Host "  - PUT /api/profile/update" -ForegroundColor White
Write-Host "  - GET /api/notifications" -ForegroundColor White
Write-Host "  - POST /api/notifications" -ForegroundColor White
Write-Host "  - GET /api/notifications/unread-count" -ForegroundColor White
Write-Host "  - PUT /api/notifications/read-all" -ForegroundColor White
Write-Host "  - PUT /api/notifications/{notificationId}/read" -ForegroundColor White
Write-Host "  - DELETE /api/notifications/{notificationId}" -ForegroundColor White
