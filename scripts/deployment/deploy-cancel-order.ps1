# Deploy DELETE /api/orders/{orderId} endpoint for order cancellation

Write-Host "Deploying order cancellation endpoint..." -ForegroundColor Cyan

$apiId = "vtqjfznspc"
$region = "ap-south-1"
$ordersResourceId = "eqsswe"  # /api/orders resource ID

# 1. Package Lambda
Write-Host "`n1. Packaging Lambda function..." -ForegroundColor Yellow
Remove-Item -Path lambda\orders\cancel-order-package.zip -ErrorAction SilentlyContinue
Compress-Archive -Path lambda\orders\cancel_order.py -DestinationPath lambda\orders\cancel-order-package.zip -Force

# 2. Create or update Lambda function
Write-Host "`n2. Deploying Lambda function..." -ForegroundColor Yellow
$lambdaExists = aws lambda get-function --function-name aquachain-cancel-order-dev 2>$null
if ($LASTEXITCODE -eq 0) {
    Write-Host "Updating existing Lambda..." -ForegroundColor Green
    aws lambda update-function-code `
        --function-name aquachain-cancel-order-dev `
        --zip-file fileb://lambda/orders/cancel-order-package.zip
} else {
    Write-Host "Creating new Lambda..." -ForegroundColor Green
    aws lambda create-function `
        --function-name aquachain-cancel-order-dev `
        --runtime python3.11 `
        --role arn:aws:iam::758346259059:role/aquachain-lambda-execution-role `
        --handler cancel_order.handler `
        --zip-file fileb://lambda/orders/cancel-order-package.zip `
        --timeout 30 `
        --memory-size 512 `
        --environment "Variables={ORDERS_TABLE=aquachain-orders}"
}

Start-Sleep -Seconds 3

# 3. Get Lambda ARN
$lambdaArn = aws lambda get-function --function-name aquachain-cancel-order-dev --query 'Configuration.FunctionArn' --output text
Write-Host "Lambda ARN: $lambdaArn" -ForegroundColor Green

# 4. Create {orderId} resource under /api/orders
Write-Host "`n4. Creating {orderId} resource..." -ForegroundColor Yellow
$orderIdResource = aws apigateway create-resource `
    --rest-api-id $apiId `
    --parent-id $ordersResourceId `
    --path-part "{orderId}" `
    --region $region 2>$null | ConvertFrom-Json

if (-not $orderIdResource) {
    # Resource might already exist, get it
    $resources = aws apigateway get-resources --rest-api-id $apiId --region $region | ConvertFrom-Json
    $orderIdResource = $resources.items | Where-Object { $_.pathPart -eq "{orderId}" }
}

$orderIdResourceId = $orderIdResource.id
Write-Host "OrderId resource ID: $orderIdResourceId" -ForegroundColor Green

# 5. Create DELETE method
Write-Host "`n5. Creating DELETE method..." -ForegroundColor Yellow
aws apigateway put-method `
    --rest-api-id $apiId `
    --resource-id $orderIdResourceId `
    --http-method DELETE `
    --authorization-type COGNITO_USER_POOLS `
    --authorizer-id 1q3fsb `
    --region $region

# 6. Create Lambda integration
Write-Host "`n6. Creating Lambda integration..." -ForegroundColor Yellow
aws apigateway put-integration `
    --rest-api-id $apiId `
    --resource-id $orderIdResourceId `
    --http-method DELETE `
    --type AWS_PROXY `
    --integration-http-method POST `
    --uri "arn:aws:apigateway:${region}:lambda:path/2015-03-31/functions/${lambdaArn}/invocations" `
    --region $region

# 7. Add Lambda permission
Write-Host "`n7. Adding Lambda permission..." -ForegroundColor Yellow
aws lambda add-permission `
    --function-name aquachain-cancel-order-dev `
    --statement-id apigateway-cancel-order `
    --action lambda:InvokeFunction `
    --principal apigateway.amazonaws.com `
    --source-arn "arn:aws:execute-api:${region}:758346259059:${apiId}/*/DELETE/api/orders/*" `
    2>$null

# 8. Create OPTIONS method for CORS
Write-Host "`n8. Creating OPTIONS method..." -ForegroundColor Yellow
aws apigateway put-method `
    --rest-api-id $apiId `
    --resource-id $orderIdResourceId `
    --http-method OPTIONS `
    --authorization-type NONE `
    --region $region

# 9. Deploy API
Write-Host "`n9. Deploying API..." -ForegroundColor Yellow
aws apigateway create-deployment `
    --rest-api-id $apiId `
    --stage-name dev `
    --region $region

Write-Host "`n✅ Order cancellation endpoint deployed!" -ForegroundColor Green
Write-Host "Endpoint: DELETE https://${apiId}.execute-api.${region}.amazonaws.com/dev/api/orders/{orderId}" -ForegroundColor Cyan
Write-Host "`nNote: You need to manually configure OPTIONS method CORS in AWS Console" -ForegroundColor Yellow
