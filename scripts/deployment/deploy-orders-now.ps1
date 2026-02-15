# Deploy Orders Service - Direct Approach
# This deploys a working COD orders system in 10-15 minutes

$ErrorActionPreference = "Continue"

Write-Host "========================================" -ForegroundColor Cyan
Write-Host "Orders Service Direct Deployment" -ForegroundColor Cyan
Write-Host "========================================" -ForegroundColor Cyan
Write-Host ""

$API_ID = "vtqjfznspc"
$REGION = "ap-south-1"
$ACCOUNT_ID = "758346259059"

# Step 1: Verify Orders table exists
Write-Host "Step 1: Verifying Orders table..." -ForegroundColor Green
$tableStatus = aws dynamodb describe-table --table-name aquachain-orders --region $REGION 2>&1

if ($LASTEXITCODE -ne 0) {
    Write-Host "Creating Orders table..." -ForegroundColor Yellow
    
    aws dynamodb create-table `
        --table-name aquachain-orders `
        --attribute-definitions `
            AttributeName=orderId,AttributeType=S `
            AttributeName=userId,AttributeType=S `
            AttributeName=createdAt,AttributeType=S `
            AttributeName=status,AttributeType=S `
        --key-schema AttributeName=orderId,KeyType=HASH `
        --billing-mode PAY_PER_REQUEST `
        --global-secondary-indexes `
            "[{\"IndexName\":\"userId-createdAt-index\",\"KeySchema\":[{\"AttributeName\":\"userId\",\"KeyType\":\"HASH\"},{\"AttributeName\":\"createdAt\",\"KeyType\":\"RANGE\"}],\"Projection\":{\"ProjectionType\":\"ALL\"}},{\"IndexName\":\"status-createdAt-index\",\"KeySchema\":[{\"AttributeName\":\"status\",\"KeyType\":\"HASH\"},{\"AttributeName\":\"createdAt\",\"KeyType\":\"RANGE\"}],\"Projection\":{\"ProjectionType\":\"ALL\"}}]" `
        --region $REGION
    
    Write-Host "Waiting for table to be active..." -ForegroundColor Yellow
    aws dynamodb wait table-exists --table-name aquachain-orders --region $REGION
}

Write-Host "✅ Orders table ready" -ForegroundColor Green

# Step 2: Package Lambda function
Write-Host ""
Write-Host "Step 2: Packaging Lambda function..." -ForegroundColor Green

Push-Location lambda/orders

# Clean up
if (Test-Path "package") { Remove-Item -Recurse -Force package }
if (Test-Path "orders-lambda.zip") { Remove-Item -Force orders-lambda.zip }

# Create package
New-Item -ItemType Directory -Path package -Force | Out-Null
pip install boto3 -t package -q
Copy-Item create_order.py package/

# Zip it
Compress-Archive -Path package/* -DestinationPath orders-lambda.zip -Force

Pop-Location

Write-Host "✅ Lambda packaged" -ForegroundColor Green

# Step 3: Deploy or update Lambda
Write-Host ""
Write-Host "Step 3: Deploying Lambda function..." -ForegroundColor Green

$lambdaExists = aws lambda get-function --function-name aquachain-orders-api-dev --region $REGION 2>&1

if ($LASTEXITCODE -eq 0) {
    Write-Host "Updating existing Lambda..." -ForegroundColor Yellow
    aws lambda update-function-code `
        --function-name aquachain-orders-api-dev `
        --zip-file fileb://lambda/orders/orders-lambda.zip `
        --region $REGION | Out-Null
} else {
    Write-Host "Creating new Lambda..." -ForegroundColor Yellow
    aws lambda create-function `
        --function-name aquachain-orders-api-dev `
        --runtime python3.11 `
        --role arn:aws:iam::${ACCOUNT_ID}:role/aquachain-lambda-execution-role `
        --handler create_order.handler `
        --zip-file fileb://lambda/orders/orders-lambda.zip `
        --timeout 30 `
        --memory-size 512 `
        --environment "Variables={ORDERS_TABLE=aquachain-orders,USERS_TABLE=AquaChain-Users}" `
        --region $REGION | Out-Null
    
    Start-Sleep -Seconds 5
}

Write-Host "✅ Lambda deployed" -ForegroundColor Green

# Step 4: Configure API Gateway
Write-Host ""
Write-Host "Step 4: Configuring API Gateway..." -ForegroundColor Green

# Get resources
$resources = aws apigateway get-resources --rest-api-id $API_ID --region $REGION | ConvertFrom-Json
$apiResource = $resources.items | Where-Object { $_.path -eq "/api" }

# Check if /api/orders exists
$ordersResource = $resources.items | Where-Object { $_.path -eq "/api/orders" }

if (-not $ordersResource) {
    Write-Host "Creating /api/orders resource..." -ForegroundColor Yellow
    $ordersResource = aws apigateway create-resource `
        --rest-api-id $API_ID `
        --parent-id $apiResource.id `
        --path-part "orders" `
        --region $REGION | ConvertFrom-Json
}

# Get authorizer
$authorizers = aws apigateway get-authorizers --rest-api-id $API_ID --region $REGION | ConvertFrom-Json
$authorizerId = $authorizers.items[0].id

# Configure OPTIONS for CORS
Write-Host "Configuring CORS..." -ForegroundColor Yellow

aws apigateway put-method `
    --rest-api-id $API_ID `
    --resource-id $ordersResource.id `
    --http-method OPTIONS `
    --authorization-type NONE `
    --region $REGION 2>$null | Out-Null

aws apigateway put-integration `
    --rest-api-id $API_ID `
    --resource-id $ordersResource.id `
    --http-method OPTIONS `
    --type MOCK `
    --request-templates '{\"application/json\":\"{\\\"statusCode\\\": 200}\"}' `
    --region $REGION 2>$null | Out-Null

aws apigateway put-method-response `
    --rest-api-id $API_ID `
    --resource-id $ordersResource.id `
    --http-method OPTIONS `
    --status-code 200 `
    --response-parameters '{\"method.response.header.Access-Control-Allow-Headers\":false,\"method.response.header.Access-Control-Allow-Methods\":false,\"method.response.header.Access-Control-Allow-Origin\":false}' `
    --region $REGION 2>$null | Out-Null

aws apigateway put-integration-response `
    --rest-api-id $API_ID `
    --resource-id $ordersResource.id `
    --http-method OPTIONS `
    --status-code 200 `
    --response-parameters '{\"method.response.header.Access-Control-Allow-Headers\":\"\\\"Content-Type,Authorization,X-Amz-Date,X-Api-Key\\\"\",\"method.response.header.Access-Control-Allow-Methods\":\"\\\"GET,POST,PUT,DELETE,OPTIONS\\\"\",\"method.response.header.Access-Control-Allow-Origin\":\"\\\"*\\\"\"}' `
    --region $REGION 2>$null | Out-Null

# Configure POST method
Write-Host "Adding POST method..." -ForegroundColor Yellow

aws apigateway put-method `
    --rest-api-id $API_ID `
    --resource-id $ordersResource.id `
    --http-method POST `
    --authorization-type COGNITO_USER_POOLS `
    --authorizer-id $authorizerId `
    --region $REGION 2>$null | Out-Null

$lambdaArn = "arn:aws:lambda:${REGION}:${ACCOUNT_ID}:function:aquachain-orders-api-dev"
$integrationUri = "arn:aws:apigateway:${REGION}:lambda:path/2015-03-31/functions/${lambdaArn}/invocations"

aws apigateway put-integration `
    --rest-api-id $API_ID `
    --resource-id $ordersResource.id `
    --http-method POST `
    --type AWS_PROXY `
    --integration-http-method POST `
    --uri $integrationUri `
    --region $REGION 2>$null | Out-Null

# Add Lambda permission
Write-Host "Adding Lambda permission..." -ForegroundColor Yellow
$randomId = Get-Random -Minimum 1000 -Maximum 9999
aws lambda add-permission `
    --function-name aquachain-orders-api-dev `
    --statement-id "apigateway-invoke-$randomId" `
    --action lambda:InvokeFunction `
    --principal apigateway.amazonaws.com `
    --source-arn "arn:aws:execute-api:${REGION}:${ACCOUNT_ID}:${API_ID}/*/POST/api/orders" `
    --region $REGION 2>$null | Out-Null

# Deploy API
Write-Host "Deploying API..." -ForegroundColor Yellow
aws apigateway create-deployment `
    --rest-api-id $API_ID `
    --stage-name dev `
    --description "Added orders endpoint" `
    --region $REGION | Out-Null

Write-Host "✅ API Gateway configured" -ForegroundColor Green

# Step 5: Enable feature flag in frontend
Write-Host ""
Write-Host "Step 5: Enabling orders feature..." -ForegroundColor Green

$contextFile = "frontend/src/contexts/OrderingContext.tsx"
$content = Get-Content $contextFile -Raw
$content = $content -replace "const ORDERS_FEATURE_ENABLED = false;", "const ORDERS_FEATURE_ENABLED = true;"
$content | Set-Content $contextFile -NoNewline

Write-Host "✅ Feature flag enabled" -ForegroundColor Green

# Summary
Write-Host ""
Write-Host "========================================" -ForegroundColor Green
Write-Host "Deployment Complete!" -ForegroundColor Green
Write-Host "========================================" -ForegroundColor Green
Write-Host ""
Write-Host "Orders service is now live:" -ForegroundColor Cyan
Write-Host "  Endpoint: https://$API_ID.execute-api.$REGION.amazonaws.com/dev/api/orders" -ForegroundColor White
Write-Host "  Table: aquachain-orders" -ForegroundColor White
Write-Host "  Lambda: aquachain-orders-api-dev" -ForegroundColor White
Write-Host ""
Write-Host "Next steps:" -ForegroundColor Yellow
Write-Host "  1. Restart dev server: cd frontend && npm start" -ForegroundColor White
Write-Host "  2. Test creating a COD order" -ForegroundColor White
Write-Host "  3. Check CloudWatch logs if issues occur" -ForegroundColor White
Write-Host ""
Write-Host "CloudWatch logs:" -ForegroundColor Yellow
Write-Host "  aws logs tail /aws/lambda/aquachain-orders-api-dev --follow --region $REGION" -ForegroundColor Gray
Write-Host ""
