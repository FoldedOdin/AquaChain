# Deploy Minimal Orders Service (Pragmatic Approach)
# This creates a simple COD-only orders system without the complexity of the full stack

Write-Host "========================================" -ForegroundColor Cyan
Write-Host "Minimal Orders Service Deployment" -ForegroundColor Cyan
Write-Host "========================================" -ForegroundColor Cyan
Write-Host ""

Write-Host "This will deploy:" -ForegroundColor Yellow
Write-Host "  - Orders DynamoDB table (if not exists)" -ForegroundColor White
Write-Host "  - Simple orders Lambda function" -ForegroundColor White
Write-Host "  - API Gateway /api/orders endpoint" -ForegroundColor White
Write-Host ""
Write-Host "Time: 10-15 minutes" -ForegroundColor Yellow
Write-Host "Cost: $0.00/month (free tier)" -ForegroundColor Yellow
Write-Host ""

$confirmation = Read-Host "Continue? (y/n)"
if ($confirmation -ne 'y') {
    Write-Host "Cancelled" -ForegroundColor Yellow
    exit 0
}

$API_ID = "vtqjfznspc"
$REGION = "ap-south-1"
$ACCOUNT_ID = "758346259059"

# Step 1: Check if Orders table exists
Write-Host ""
Write-Host "Step 1: Checking Orders table..." -ForegroundColor Green
$tableExists = aws dynamodb describe-table --table-name aquachain-orders --region $REGION 2>$null

if ($tableExists) {
    Write-Host "✅ Orders table already exists" -ForegroundColor Green
} else {
    Write-Host "Creating Orders table..." -ForegroundColor Yellow
    
    aws dynamodb create-table `
        --table-name aquachain-orders `
        --attribute-definitions `
            AttributeName=orderId,AttributeType=S `
            AttributeName=userId,AttributeType=S `
            AttributeName=createdAt,AttributeType=S `
            AttributeName=status,AttributeType=S `
        --key-schema `
            AttributeName=orderId,KeyType=HASH `
        --billing-mode PAY_PER_REQUEST `
        --global-secondary-indexes `
            "[{
                \"IndexName\": \"userId-createdAt-index\",
                \"KeySchema\": [{\"AttributeName\":\"userId\",\"KeyType\":\"HASH\"},{\"AttributeName\":\"createdAt\",\"KeyType\":\"RANGE\"}],
                \"Projection\":{\"ProjectionType\":\"ALL\"}
            },{
                \"IndexName\": \"status-createdAt-index\",
                \"KeySchema\": [{\"AttributeName\":\"status\",\"KeyType\":\"HASH\"},{\"AttributeName\":\"createdAt\",\"KeyType\":\"RANGE\"}],
                \"Projection\":{\"ProjectionType\":\"ALL\"}
            }]" `
        --region $REGION | Out-Null
    
    Write-Host "✅ Orders table created" -ForegroundColor Green
    Write-Host "Waiting for table to be active..." -ForegroundColor Yellow
    aws dynamodb wait table-exists --table-name aquachain-orders --region $REGION
}

# Step 2: Check if Lambda execution role exists
Write-Host ""
Write-Host "Step 2: Checking Lambda execution role..." -ForegroundColor Green
$roleExists = aws iam get-role --role-name aquachain-lambda-execution-role 2>$null

if (-not $roleExists) {
    Write-Host "Creating Lambda execution role..." -ForegroundColor Yellow
    
    $trustPolicy = @"
{
  "Version": "2012-10-17",
  "Statement": [{
    "Effect": "Allow",
    "Principal": {"Service": "lambda.amazonaws.com"},
    "Action": "sts:AssumeRole"
  }]
}
"@
    
    $trustPolicy | Out-File -FilePath "trust-policy.json" -Encoding UTF8
    
    aws iam create-role `
        --role-name aquachain-lambda-execution-role `
        --assume-role-policy-document file://trust-policy.json `
        --region $REGION | Out-Null
    
    # Attach basic execution policy
    aws iam attach-role-policy `
        --role-name aquachain-lambda-execution-role `
        --policy-arn arn:aws:iam::aws:policy/service-role/AWSLambdaBasicExecutionRole
    
    # Create DynamoDB access policy
    $dynamoPolicy = @"
{
  "Version": "2012-10-17",
  "Statement": [{
    "Effect": "Allow",
    "Action": [
      "dynamodb:PutItem",
      "dynamodb:GetItem",
      "dynamodb:UpdateItem",
      "dynamodb:Query",
      "dynamodb:Scan"
    ],
    "Resource": [
      "arn:aws:dynamodb:ap-south-1:758346259059:table/aquachain-orders",
      "arn:aws:dynamodb:ap-south-1:758346259059:table/aquachain-orders/index/*",
      "arn:aws:dynamodb:ap-south-1:758346259059:table/AquaChain-Users",
      "arn:aws:dynamodb:ap-south-1:758346259059:table/AquaChain-Users/index/*"
    ]
  }]
}
"@
    
    $dynamoPolicy | Out-File -FilePath "dynamo-policy.json" -Encoding UTF8
    
    aws iam put-role-policy `
        --role-name aquachain-lambda-execution-role `
        --policy-name DynamoDBAccess `
        --policy-document file://dynamo-policy.json
    
    Remove-Item trust-policy.json, dynamo-policy.json
    
    Write-Host "✅ Lambda execution role created" -ForegroundColor Green
    Write-Host "Waiting for role to propagate..." -ForegroundColor Yellow
    Start-Sleep -Seconds 10
} else {
    Write-Host "✅ Lambda execution role already exists" -ForegroundColor Green
}

# Step 3: Package and deploy Lambda function
Write-Host ""
Write-Host "Step 3: Packaging Lambda function..." -ForegroundColor Green

Push-Location lambda/orders

# Clean up old package
if (Test-Path "package") { Remove-Item -Recurse -Force package }
if (Test-Path "orders-lambda.zip") { Remove-Item -Force orders-lambda.zip }

# Create package directory
New-Item -ItemType Directory -Path package | Out-Null

# Install dependencies
Write-Host "Installing dependencies..." -ForegroundColor Yellow
pip install -r requirements.txt -t package -q

# Copy Lambda code
Copy-Item create_order.py package/

# Create zip
Write-Host "Creating deployment package..." -ForegroundColor Yellow
Compress-Archive -Path package/* -DestinationPath orders-lambda.zip -Force

Pop-Location

Write-Host "✅ Lambda package created" -ForegroundColor Green

# Step 4: Deploy Lambda function
Write-Host ""
Write-Host "Step 4: Deploying Lambda function..." -ForegroundColor Green

$lambdaExists = aws lambda get-function --function-name aquachain-orders-api-dev --region $REGION 2>$null

if ($lambdaExists) {
    Write-Host "Updating existing Lambda function..." -ForegroundColor Yellow
    aws lambda update-function-code `
        --function-name aquachain-orders-api-dev `
        --zip-file fileb://lambda/orders/orders-lambda.zip `
        --region $REGION | Out-Null
    
    aws lambda update-function-configuration `
        --function-name aquachain-orders-api-dev `
        --environment "Variables={ORDERS_TABLE=aquachain-orders,USERS_TABLE=AquaChain-Users}" `
        --region $REGION | Out-Null
} else {
    Write-Host "Creating Lambda function..." -ForegroundColor Yellow
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
}

Write-Host "✅ Lambda function deployed" -ForegroundColor Green

# Step 5: Configure API Gateway
Write-Host ""
Write-Host "Step 5: Configuring API Gateway..." -ForegroundColor Green

# Get resources
$resources = aws apigateway get-resources --rest-api-id $API_ID --region $REGION | ConvertFrom-Json

# Find /api resource
$apiResource = $resources.items | Where-Object { $_.path -eq "/api" }

if (-not $apiResource) {
    Write-Host "Error: /api resource not found" -ForegroundColor Red
    exit 1
}

# Check if /api/orders exists
$ordersResource = $resources.items | Where-Object { $_.path -eq "/api/orders" }

if (-not $ordersResource) {
    Write-Host "Creating /api/orders resource..." -ForegroundColor Yellow
    $ordersResource = aws apigateway create-resource `
        --rest-api-id $API_ID `
        --parent-id $apiResource.id `
        --path-part "orders" `
        --region $REGION | ConvertFrom-Json
} else {
    Write-Host "/api/orders resource already exists" -ForegroundColor Yellow
}

# Add OPTIONS method for CORS
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

# Get authorizer ID
$authorizers = aws apigateway get-authorizers --rest-api-id $API_ID --region $REGION | ConvertFrom-Json
$authorizerId = $authorizers.items[0].id

# Add POST method
Write-Host "Adding POST method..." -ForegroundColor Yellow
aws apigateway put-method `
    --rest-api-id $API_ID `
    --resource-id $ordersResource.id `
    --http-method POST `
    --authorization-type COGNITO_USER_POOLS `
    --authorizer-id $authorizerId `
    --region $REGION 2>$null | Out-Null

# Add Lambda integration
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
aws lambda add-permission `
    --function-name aquachain-orders-api-dev `
    --statement-id apigateway-invoke-$(Get-Random) `
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

# Summary
Write-Host ""
Write-Host "========================================" -ForegroundColor Green
Write-Host "Deployment Complete!" -ForegroundColor Green
Write-Host "========================================" -ForegroundColor Green
Write-Host ""
Write-Host "Endpoint: https://$API_ID.execute-api.$REGION.amazonaws.com/dev/api/orders" -ForegroundColor Cyan
Write-Host ""
Write-Host "Test it:" -ForegroundColor Yellow
Write-Host "  1. Login to your app" -ForegroundColor White
Write-Host "  2. Try creating a COD order" -ForegroundColor White
Write-Host "  3. Check CloudWatch logs if issues occur" -ForegroundColor White
Write-Host ""
Write-Host "CloudWatch logs:" -ForegroundColor Yellow
Write-Host "  aws logs tail /aws/lambda/aquachain-orders-api-dev --follow --region $REGION" -ForegroundColor Gray
Write-Host ""
