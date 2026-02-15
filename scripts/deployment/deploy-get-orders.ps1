# Deploy GET /api/orders/history endpoint

Write-Host "Deploying GET orders endpoint..." -ForegroundColor Cyan

# Package Lambda
Write-Host "`n1. Packaging Lambda function..." -ForegroundColor Yellow
Remove-Item -Path lambda\orders\get-orders-package.zip -ErrorAction SilentlyContinue
Compress-Archive -Path lambda\orders\get_orders.py -DestinationPath lambda\orders\get-orders-package.zip -Force

# Create or update Lambda function
Write-Host "`n2. Deploying Lambda function..." -ForegroundColor Yellow
$lambdaExists = aws lambda get-function --function-name aquachain-get-orders-dev 2>$null
if ($LASTEXITCODE -eq 0) {
    Write-Host "Updating existing Lambda function..." -ForegroundColor Green
    aws lambda update-function-code `
        --function-name aquachain-get-orders-dev `
        --zip-file fileb://lambda/orders/get-orders-package.zip
} else {
    Write-Host "Creating new Lambda function..." -ForegroundColor Green
    aws lambda create-function `
        --function-name aquachain-get-orders-dev `
        --runtime python3.11 `
        --role arn:aws:iam::758346259059:role/aquachain-lambda-execution-role `
        --handler get_orders.handler `
        --zip-file fileb://lambda/orders/get-orders-package.zip `
        --timeout 30 `
        --memory-size 512 `
        --environment "Variables={ORDERS_TABLE=aquachain-orders}"
}

# Wait for Lambda to be ready
Write-Host "`n3. Waiting for Lambda to be ready..." -ForegroundColor Yellow
Start-Sleep -Seconds 5

# Get Lambda ARN
$lambdaArn = aws lambda get-function --function-name aquachain-get-orders-dev --query 'Configuration.FunctionArn' --output text
Write-Host "Lambda ARN: $lambdaArn" -ForegroundColor Green

# API Gateway configuration
$apiId = "vtqjfznspc"
$region = "ap-south-1"

# Check if /api/orders/history resource exists
Write-Host "`n4. Checking API Gateway resources..." -ForegroundColor Yellow
$resources = aws apigateway get-resources --rest-api-id $apiId --region $region | ConvertFrom-Json

# Find /api resource
$apiResource = $resources.items | Where-Object { $_.path -eq "/api" }
if (-not $apiResource) {
    Write-Host "ERROR: /api resource not found" -ForegroundColor Red
    exit 1
}

# Find /api/orders resource
$ordersResource = $resources.items | Where-Object { $_.path -eq "/api/orders" }
if (-not $ordersResource) {
    Write-Host "Creating /api/orders resource..." -ForegroundColor Yellow
    $ordersResource = aws apigateway create-resource `
        --rest-api-id $apiId `
        --parent-id $apiResource.id `
        --path-part "orders" `
        --region $region | ConvertFrom-Json
}

# Find /api/orders/history resource
$historyResource = $resources.items | Where-Object { $_.path -eq "/api/orders/history" }
if (-not $historyResource) {
    Write-Host "Creating /api/orders/history resource..." -ForegroundColor Yellow
    $historyResource = aws apigateway create-resource `
        --rest-api-id $apiId `
        --parent-id $ordersResource.id `
        --path-part "history" `
        --region $region | ConvertFrom-Json
}

$historyResourceId = $historyResource.id
Write-Host "History resource ID: $historyResourceId" -ForegroundColor Green

# Create GET method
Write-Host "`n5. Creating GET method..." -ForegroundColor Yellow
aws apigateway put-method `
    --rest-api-id $apiId `
    --resource-id $historyResourceId `
    --http-method GET `
    --authorization-type COGNITO_USER_POOLS `
    --authorizer-id "arn:aws:cognito-idp:ap-south-1:758346259059:userpool/ap-south-1_QUDl7hG8u" `
    --region $region 2>$null

# Create Lambda integration
Write-Host "`n6. Creating Lambda integration..." -ForegroundColor Yellow
aws apigateway put-integration `
    --rest-api-id $apiId `
    --resource-id $historyResourceId `
    --http-method GET `
    --type AWS_PROXY `
    --integration-http-method POST `
    --uri "arn:aws:apigateway:${region}:lambda:path/2015-03-31/functions/${lambdaArn}/invocations" `
    --region $region

# Add Lambda permission
Write-Host "`n7. Adding Lambda permission..." -ForegroundColor Yellow
aws lambda add-permission `
    --function-name aquachain-get-orders-dev `
    --statement-id apigateway-get-orders-history `
    --action lambda:InvokeFunction `
    --principal apigateway.amazonaws.com `
    --source-arn "arn:aws:execute-api:${region}:758346259059:${apiId}/*/GET/api/orders/history" `
    2>$null

# Create OPTIONS method for CORS
Write-Host "`n8. Creating OPTIONS method for CORS..." -ForegroundColor Yellow
aws apigateway put-method `
    --rest-api-id $apiId `
    --resource-id $historyResourceId `
    --http-method OPTIONS `
    --authorization-type NONE `
    --region $region 2>$null

# Create MOCK integration for OPTIONS
aws apigateway put-integration `
    --rest-api-id $apiId `
    --resource-id $historyResourceId `
    --http-method OPTIONS `
    --type MOCK `
    --request-templates '{\"application/json\": \"{\\\"statusCode\\\": 200}\"}' `
    --region $region 2>$null

# Set OPTIONS method response
aws apigateway put-method-response `
    --rest-api-id $apiId `
    --resource-id $historyResourceId `
    --http-method OPTIONS `
    --status-code 200 `
    --response-parameters '{\"method.response.header.Access-Control-Allow-Headers\":false,\"method.response.header.Access-Control-Allow-Methods\":false,\"method.response.header.Access-Control-Allow-Origin\":false}' `
    --region $region 2>$null

# Set OPTIONS integration response
aws apigateway put-integration-response `
    --rest-api-id $apiId `
    --resource-id $historyResourceId `
    --http-method OPTIONS `
    --status-code 200 `
    --response-parameters '{\"method.response.header.Access-Control-Allow-Headers\":\"'"'"'Content-Type,Authorization'"'"'\",\"method.response.header.Access-Control-Allow-Methods\":\"'"'"'GET,OPTIONS'"'"'\",\"method.response.header.Access-Control-Allow-Origin\":\"'"'"'*'"'"'\"}' `
    --region $region 2>$null

# Deploy API
Write-Host "`n9. Deploying API..." -ForegroundColor Yellow
aws apigateway create-deployment `
    --rest-api-id $apiId `
    --stage-name dev `
    --region $region

Write-Host "`n✅ Deployment complete!" -ForegroundColor Green
Write-Host "Endpoint: https://${apiId}.execute-api.${region}.amazonaws.com/dev/api/orders/history" -ForegroundColor Cyan
