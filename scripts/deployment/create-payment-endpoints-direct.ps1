# Create Payment API Endpoints Directly via AWS CLI
# This script creates payment endpoints in API Gateway without requiring CDK deployment

$ErrorActionPreference = "Stop"

$API_ID = "vtqjfznspc"
$REGION = "ap-south-1"
$STAGE = "dev"
$LAMBDA_ARN = "arn:aws:lambda:ap-south-1:637423326645:function:aquachain-function-payment-service-dev"
$ACCOUNT_ID = "637423326645"

Write-Host "Creating Payment API Endpoints..." -ForegroundColor Cyan

# Get the /api resource ID
Write-Host "`nFinding /api resource..." -ForegroundColor Yellow
$apiResource = aws apigateway get-resources --rest-api-id $API_ID --region $REGION --query "items[?path=='/api'].id" --output text

if (-not $apiResource) {
    Write-Host "ERROR: /api resource not found" -ForegroundColor Red
    exit 1
}

Write-Host "Found /api resource: $apiResource" -ForegroundColor Green

# Create /api/payments resource
Write-Host "`nCreating /api/payments resource..." -ForegroundColor Yellow
try {
    $paymentsResource = aws apigateway create-resource `
        --rest-api-id $API_ID `
        --region $REGION `
        --parent-id $apiResource `
        --path-part "payments" `
        --query 'id' `
        --output text
    
    Write-Host "Created /api/payments: $paymentsResource" -ForegroundColor Green
} catch {
    # Resource might already exist
    $paymentsResource = aws apigateway get-resources --rest-api-id $API_ID --region $REGION --query "items[?path=='/api/payments'].id" --output text
    Write-Host "Using existing /api/payments: $paymentsResource" -ForegroundColor Yellow
}

# Get Cognito authorizer ID
Write-Host "`nFinding Cognito authorizer..." -ForegroundColor Yellow
$authorizerId = aws apigateway get-authorizers --rest-api-id $API_ID --region $REGION --query "items[?name=='AquaChainAuthorizer'].id" --output text

if (-not $authorizerId) {
    Write-Host "ERROR: Cognito authorizer not found" -ForegroundColor Red
    exit 1
}

Write-Host "Found authorizer: $authorizerId" -ForegroundColor Green

# Function to create endpoint
function Create-PaymentEndpoint {
    param(
        [string]$ParentId,
        [string]$PathPart,
        [string]$Method
    )
    
    Write-Host "`nCreating /$PathPart endpoint..." -ForegroundColor Yellow
    
    # Create resource
    try {
        $resourceId = aws apigateway create-resource `
            --rest-api-id $API_ID `
            --region $REGION `
            --parent-id $ParentId `
            --path-part $PathPart `
            --query 'id' `
            --output text
        
        Write-Host "Created resource: $resourceId" -ForegroundColor Green
    } catch {
        # Resource might already exist
        $resourceId = aws apigateway get-resources --rest-api-id $API_ID --region $REGION --query "items[?pathPart=='$PathPart' && parentId=='$ParentId'].id" --output text
        Write-Host "Using existing resource: $resourceId" -ForegroundColor Yellow
    }
    
    # Create POST method
    Write-Host "Creating $Method method..." -ForegroundColor Yellow
    try {
        aws apigateway put-method `
            --rest-api-id $API_ID `
            --region $REGION `
            --resource-id $resourceId `
            --http-method $Method `
            --authorization-type "COGNITO_USER_POOLS" `
            --authorizer-id $authorizerId `
            --request-parameters "method.request.header.Authorization=true" | Out-Null
        
        Write-Host "Created $Method method" -ForegroundColor Green
    } catch {
        Write-Host "Method might already exist, continuing..." -ForegroundColor Yellow
    }
    
    # Create Lambda integration
    Write-Host "Creating Lambda integration..." -ForegroundColor Yellow
    try {
        aws apigateway put-integration `
            --rest-api-id $API_ID `
            --region $REGION `
            --resource-id $resourceId `
            --http-method $Method `
            --type "AWS_PROXY" `
            --integration-http-method "POST" `
            --uri "arn:aws:apigateway:${REGION}:lambda:path/2015-03-31/functions/${LAMBDA_ARN}/invocations" | Out-Null
        
        Write-Host "Created Lambda integration" -ForegroundColor Green
    } catch {
        Write-Host "Integration might already exist, continuing..." -ForegroundColor Yellow
    }
    
    # Grant Lambda permission
    Write-Host "Granting Lambda permission..." -ForegroundColor Yellow
    $statementId = "apigateway-$PathPart-$Method-$(Get-Date -Format 'yyyyMMddHHmmss')"
    try {
        aws lambda add-permission `
            --function-name "aquachain-function-payment-service-dev" `
            --region $REGION `
            --statement-id $statementId `
            --action "lambda:InvokeFunction" `
            --principal "apigateway.amazonaws.com" `
            --source-arn "arn:aws:execute-api:${REGION}:${ACCOUNT_ID}:${API_ID}/*/${Method}/api/payments/${PathPart}" | Out-Null
        
        Write-Host "Granted Lambda permission" -ForegroundColor Green
    } catch {
        Write-Host "Permission might already exist, continuing..." -ForegroundColor Yellow
    }
    
    # Create OPTIONS method for CORS
    Write-Host "Creating OPTIONS method for CORS..." -ForegroundColor Yellow
    try {
        aws apigateway put-method `
            --rest-api-id $API_ID `
            --region $REGION `
            --resource-id $resourceId `
            --http-method "OPTIONS" `
            --authorization-type "NONE" | Out-Null
        
        # Mock integration for OPTIONS
        aws apigateway put-integration `
            --rest-api-id $API_ID `
            --region $REGION `
            --resource-id $resourceId `
            --http-method "OPTIONS" `
            --type "MOCK" `
            --request-templates '{"application/json": "{\"statusCode\": 200}"}' | Out-Null
        
        # Method response for OPTIONS
        aws apigateway put-method-response `
            --rest-api-id $API_ID `
            --region $REGION `
            --resource-id $resourceId `
            --http-method "OPTIONS" `
            --status-code "200" `
            --response-parameters "method.response.header.Access-Control-Allow-Headers=true,method.response.header.Access-Control-Allow-Methods=true,method.response.header.Access-Control-Allow-Origin=true" | Out-Null
        
        # Integration response for OPTIONS
        aws apigateway put-integration-response `
            --rest-api-id $API_ID `
            --region $REGION `
            --resource-id $resourceId `
            --http-method "OPTIONS" `
            --status-code "200" `
            --response-parameters '{\"method.response.header.Access-Control-Allow-Headers\":\"'"'"'Content-Type,Authorization,X-Amz-Date,X-Api-Key,X-Amz-Security-Token'"'"'\",\"method.response.header.Access-Control-Allow-Methods\":\"'"'"'GET,POST,OPTIONS'"'"'\",\"method.response.header.Access-Control-Allow-Origin\":\"'"'"'*'"'"'\"}' | Out-Null
        
        Write-Host "Created OPTIONS method" -ForegroundColor Green
    } catch {
        Write-Host "OPTIONS method might already exist, continuing..." -ForegroundColor Yellow
    }
    
    return $resourceId
}

# Create payment endpoints
Create-PaymentEndpoint -ParentId $paymentsResource -PathPart "create-razorpay-order" -Method "POST"
Create-PaymentEndpoint -ParentId $paymentsResource -PathPart "verify-payment" -Method "POST"
Create-PaymentEndpoint -ParentId $paymentsResource -PathPart "create-cod-payment" -Method "POST"

# Create payment-status endpoint (GET method)
Write-Host "`nCreating /payment-status endpoint (GET)..." -ForegroundColor Yellow
try {
    $statusResourceId = aws apigateway create-resource `
        --rest-api-id $API_ID `
        --region $REGION `
        --parent-id $paymentsResource `
        --path-part "payment-status" `
        --query 'id' `
        --output text
    
    Write-Host "Created resource: $statusResourceId" -ForegroundColor Green
} catch {
    $statusResourceId = aws apigateway get-resources --rest-api-id $API_ID --region $REGION --query "items[?pathPart=='payment-status' && parentId=='$paymentsResource'].id" --output text
    Write-Host "Using existing resource: $statusResourceId" -ForegroundColor Yellow
}

# Create GET method
try {
    aws apigateway put-method `
        --rest-api-id $API_ID `
        --region $REGION `
        --resource-id $statusResourceId `
        --http-method "GET" `
        --authorization-type "COGNITO_USER_POOLS" `
        --authorizer-id $authorizerId `
        --request-parameters "method.request.header.Authorization=true,method.request.querystring.orderId=true" | Out-Null
    
    Write-Host "Created GET method" -ForegroundColor Green
} catch {
    Write-Host "Method might already exist, continuing..." -ForegroundColor Yellow
}

# Create Lambda integration for GET
try {
    aws apigateway put-integration `
        --rest-api-id $API_ID `
        --region $REGION `
        --resource-id $statusResourceId `
        --http-method "GET" `
        --type "AWS_PROXY" `
        --integration-http-method "POST" `
        --uri "arn:aws:apigateway:${REGION}:lambda:path/2015-03-31/functions/${LAMBDA_ARN}/invocations" | Out-Null
    
    Write-Host "Created Lambda integration" -ForegroundColor Green
} catch {
    Write-Host "Integration might already exist, continuing..." -ForegroundColor Yellow
}

# Grant Lambda permission for GET
$statementId = "apigateway-payment-status-GET-$(Get-Date -Format 'yyyyMMddHHmmss')"
try {
    aws lambda add-permission `
        --function-name "aquachain-function-payment-service-dev" `
        --region $REGION `
        --statement-id $statementId `
        --action "lambda:InvokeFunction" `
        --principal "apigateway.amazonaws.com" `
        --source-arn "arn:aws:execute-api:${REGION}:${ACCOUNT_ID}:${API_ID}/*/GET/api/payments/payment-status" | Out-Null
    
    Write-Host "Granted Lambda permission" -ForegroundColor Green
} catch {
    Write-Host "Permission might already exist, continuing..." -ForegroundColor Yellow
}

# Deploy API
Write-Host "`nDeploying API to $STAGE stage..." -ForegroundColor Cyan
aws apigateway create-deployment `
    --rest-api-id $API_ID `
    --region $REGION `
    --stage-name $STAGE `
    --description "Payment endpoints deployment - $(Get-Date -Format 'yyyy-MM-dd HH:mm:ss')" | Out-Null

Write-Host "`n✅ Payment endpoints created successfully!" -ForegroundColor Green
Write-Host "`nEndpoints available at:" -ForegroundColor Cyan
Write-Host "  POST https://vtqjfznspc.execute-api.ap-south-1.amazonaws.com/dev/api/payments/create-razorpay-order"
Write-Host "  POST https://vtqjfznspc.execute-api.ap-south-1.amazonaws.com/dev/api/payments/verify-payment"
Write-Host "  POST https://vtqjfznspc.execute-api.ap-south-1.amazonaws.com/dev/api/payments/create-cod-payment"
Write-Host "  GET  https://vtqjfznspc.execute-api.ap-south-1.amazonaws.com/dev/api/payments/payment-status"

Write-Host "`nVerifying endpoints..." -ForegroundColor Yellow
aws apigateway get-resources --rest-api-id $API_ID --region $REGION --query "items[?contains(path, 'payment')].[path,id]" --output table
