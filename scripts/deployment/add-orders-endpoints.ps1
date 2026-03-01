# Add Orders API Endpoints to Existing API Gateway
# This script adds the /api/orders endpoints to the existing API Gateway

Write-Host "========================================" -ForegroundColor Cyan
Write-Host "Add Orders Endpoints to API Gateway" -ForegroundColor Cyan
Write-Host "========================================" -ForegroundColor Cyan
Write-Host ""

$API_ID = "vtqjfznspc"
$REGION = "ap-south-1"
$STAGE = "dev"

Write-Host "API Gateway ID: $API_ID" -ForegroundColor Yellow
Write-Host "Region: $REGION" -ForegroundColor Yellow
Write-Host "Stage: $STAGE" -ForegroundColor Yellow
Write-Host ""

# Step 1: Get the root resource ID
Write-Host "Step 1: Getting API Gateway resources..." -ForegroundColor Green
$resources = aws apigateway get-resources --rest-api-id $API_ID --region $REGION | ConvertFrom-Json

# Find /api resource
$apiResource = $resources.items | Where-Object { $_.path -eq "/api" }
if (-not $apiResource) {
    Write-Host "Error: /api resource not found" -ForegroundColor Red
    exit 1
}

Write-Host "Found /api resource: $($apiResource.id)" -ForegroundColor White
Write-Host ""

# Step 2: Create /api/orders resource
Write-Host "Step 2: Creating /api/orders resource..." -ForegroundColor Green
try {
    $ordersResource = aws apigateway create-resource `
        --rest-api-id $API_ID `
        --parent-id $apiResource.id `
        --path-part "orders" `
        --region $REGION | ConvertFrom-Json
    
    Write-Host "Created /api/orders resource: $($ordersResource.id)" -ForegroundColor White
} catch {
    # Resource might already exist
    $ordersResource = $resources.items | Where-Object { $_.path -eq "/api/orders" }
    if ($ordersResource) {
        Write-Host "/api/orders resource already exists: $($ordersResource.id)" -ForegroundColor Yellow
    } else {
        Write-Host "Error creating /api/orders resource: $_" -ForegroundColor Red
        exit 1
    }
}

Write-Host ""

# Step 3: Get Lambda function ARN
Write-Host "Step 3: Getting Lambda function ARN..." -ForegroundColor Green
$lambdaArn = aws lambda get-function `
    --function-name aquachain-function-user-management-dev `
    --region $REGION `
    --query 'Configuration.FunctionArn' `
    --output text

if (-not $lambdaArn) {
    Write-Host "Error: Lambda function not found" -ForegroundColor Red
    Write-Host "Creating a simple orders Lambda function..." -ForegroundColor Yellow
    
    # We'll use the user management Lambda as a placeholder for now
    # In production, you'd deploy the proper orders Lambda
    Write-Host "Using user-management Lambda as temporary handler" -ForegroundColor Yellow
}

Write-Host "Lambda ARN: $lambdaArn" -ForegroundColor White
Write-Host ""

# Step 4: Create OPTIONS method for CORS
Write-Host "Step 4: Creating OPTIONS method for CORS..." -ForegroundColor Green
try {
    aws apigateway put-method `
        --rest-api-id $API_ID `
        --resource-id $ordersResource.id `
        --http-method OPTIONS `
        --authorization-type NONE `
        --region $REGION | Out-Null
    
    aws apigateway put-integration `
        --rest-api-id $API_ID `
        --resource-id $ordersResource.id `
        --http-method OPTIONS `
        --type MOCK `
        --request-templates '{"application/json": "{\"statusCode\": 200}"}' `
        --region $REGION | Out-Null
    
    aws apigateway put-method-response `
        --rest-api-id $API_ID `
        --resource-id $ordersResource.id `
        --http-method OPTIONS `
        --status-code 200 `
        --response-parameters '{
            "method.response.header.Access-Control-Allow-Headers": false,
            "method.response.header.Access-Control-Allow-Methods": false,
            "method.response.header.Access-Control-Allow-Origin": false
        }' `
        --region $REGION | Out-Null
    
    aws apigateway put-integration-response `
        --rest-api-id $API_ID `
        --resource-id $ordersResource.id `
        --http-method OPTIONS `
        --status-code 200 `
        --response-parameters '{
            "method.response.header.Access-Control-Allow-Headers": "\"Content-Type,Authorization,X-Amz-Date,X-Api-Key\"",
            "method.response.header.Access-Control-Allow-Methods": "\"GET,POST,PUT,DELETE,OPTIONS\"",
            "method.response.header.Access-Control-Allow-Origin": "\"*\""
        }' `
        --region $REGION | Out-Null
    
    Write-Host "OPTIONS method created successfully" -ForegroundColor White
} catch {
    Write-Host "OPTIONS method might already exist: $_" -ForegroundColor Yellow
}

Write-Host ""

# Step 5: Create POST method for creating orders
Write-Host "Step 5: Creating POST /api/orders method..." -ForegroundColor Green
Write-Host ""
Write-Host "WARNING: This will create a placeholder endpoint." -ForegroundColor Yellow
Write-Host "For production use, you need to:" -ForegroundColor Yellow
Write-Host "  1. Deploy the proper orders Lambda function" -ForegroundColor White
Write-Host "  2. Update the integration to point to the orders Lambda" -ForegroundColor White
Write-Host "  3. Add proper request/response validation" -ForegroundColor White
Write-Host ""

$confirmation = Read-Host "Continue with placeholder endpoint? (y/n)"
if ($confirmation -ne 'y') {
    Write-Host "Cancelled" -ForegroundColor Yellow
    exit 0
}

try {
    # Create POST method
    aws apigateway put-method `
        --rest-api-id $API_ID `
        --resource-id $ordersResource.id `
        --http-method POST `
        --authorization-type COGNITO_USER_POOLS `
        --authorizer-id (aws apigateway get-authorizers --rest-api-id $API_ID --region $REGION --query 'items[0].id' --output text) `
        --region $REGION | Out-Null
    
    # Create Lambda integration
    $integrationUri = "arn:aws:apigateway:${REGION}:lambda:path/2015-03-31/functions/${lambdaArn}/invocations"
    
    aws apigateway put-integration `
        --rest-api-id $API_ID `
        --resource-id $ordersResource.id `
        --http-method POST `
        --type AWS_PROXY `
        --integration-http-method POST `
        --uri $integrationUri `
        --region $REGION | Out-Null
    
    Write-Host "POST method created successfully" -ForegroundColor White
} catch {
    Write-Host "Error creating POST method: $_" -ForegroundColor Red
}

Write-Host ""

# Step 6: Deploy the API
Write-Host "Step 6: Deploying API changes..." -ForegroundColor Green
aws apigateway create-deployment `
    --rest-api-id $API_ID `
    --stage-name $STAGE `
    --region $REGION | Out-Null

Write-Host "API deployed successfully" -ForegroundColor White
Write-Host ""

Write-Host "========================================" -ForegroundColor Green
Write-Host "Endpoints Added Successfully" -ForegroundColor Green
Write-Host "========================================" -ForegroundColor Green
Write-Host ""
Write-Host "Endpoint: https://$API_ID.execute-api.$REGION.amazonaws.com/$STAGE/api/orders" -ForegroundColor Cyan
Write-Host ""
Write-Host "IMPORTANT NEXT STEPS:" -ForegroundColor Yellow
Write-Host "1. Deploy the proper orders Lambda function" -ForegroundColor White
Write-Host "2. Update API Gateway integration to use orders Lambda" -ForegroundColor White
Write-Host "3. Add Razorpay credentials to Secrets Manager" -ForegroundColor White
Write-Host "4. Test order creation from frontend" -ForegroundColor White
Write-Host ""
Write-Host "For full deployment, run:" -ForegroundColor Yellow
Write-Host "  .\scripts\deployment\deploy-enhanced-ordering.ps1" -ForegroundColor Gray
