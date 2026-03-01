# Complete API Gateway setup for registration endpoints
# Run this after Lambda functions are deployed

$ErrorActionPreference = "Stop"

$REGION = "ap-south-1"
$API_ID = "vtqjfznspc"
$STAGE = "dev"
$ACCOUNT_ID = "758346259059"

Write-Host "=== Completing API Gateway Setup ===" -ForegroundColor Cyan
Write-Host ""

# Get root resource ID
$ROOT_ID = aws apigateway get-resources --rest-api-id $API_ID --region $REGION --query 'items[?path==`/`].id' --output text

# Get or create /api resource
$apiResourceId = aws apigateway get-resources --rest-api-id $API_ID --region $REGION --query 'items[?path==`/api`].id' --output text

if ([string]::IsNullOrEmpty($apiResourceId)) {
    Write-Host "Creating /api resource..." -ForegroundColor Cyan
    $apiResourceId = aws apigateway create-resource `
        --rest-api-id $API_ID `
        --parent-id $ROOT_ID `
        --path-part "api" `
        --region $REGION `
        --query 'id' --output text
    Write-Host "✓ /api created" -ForegroundColor Green
}

# Get or create /api/auth resource
$authResourceId = aws apigateway get-resources --rest-api-id $API_ID --region $REGION --query 'items[?path==`/api/auth`].id' --output text

if ([string]::IsNullOrEmpty($authResourceId)) {
    Write-Host "Creating /api/auth resource..." -ForegroundColor Cyan
    $authResourceId = aws apigateway create-resource `
        --rest-api-id $API_ID `
        --parent-id $apiResourceId `
        --path-part "auth" `
        --region $REGION `
        --query 'id' --output text
    Write-Host "✓ /api/auth created" -ForegroundColor Green
}

Write-Host ""

# Define endpoints
$endpoints = @(
    @{
        Path = "register"
        FunctionName = "aquachain-register-dev"
    },
    @{
        Path = "request-otp"
        FunctionName = "aquachain-request-otp-dev"
    },
    @{
        Path = "verify-otp"
        FunctionName = "aquachain-verify-otp-dev"
    }
)

foreach ($endpoint in $endpoints) {
    Write-Host "Setting up /api/auth/$($endpoint.Path)..." -ForegroundColor Yellow
    
    # Get or create resource
    $resourceId = aws apigateway get-resources --rest-api-id $API_ID --region $REGION --query "items[?path==``/api/auth/$($endpoint.Path)``].id" --output text
    
    if ([string]::IsNullOrEmpty($resourceId)) {
        Write-Host "  Creating resource..." -ForegroundColor Cyan
        $resourceId = aws apigateway create-resource `
            --rest-api-id $API_ID `
            --parent-id $authResourceId `
            --path-part $endpoint.Path `
            --region $REGION `
            --query 'id' --output text
    }
    
    # Get Lambda ARN
    $lambdaArn = aws lambda get-function --function-name $endpoint.FunctionName --region $REGION --query 'Configuration.FunctionArn' --output text
    $lambdaUri = "arn:aws:apigateway:${REGION}:lambda:path/2015-03-31/functions/${lambdaArn}/invocations"
    
    # Create OPTIONS method (CORS preflight)
    Write-Host "  Creating OPTIONS method..." -ForegroundColor Cyan
    aws apigateway put-method `
        --rest-api-id $API_ID `
        --resource-id $resourceId `
        --http-method OPTIONS `
        --authorization-type NONE `
        --region $REGION 2>$null
    
    aws apigateway put-integration `
        --rest-api-id $API_ID `
        --resource-id $resourceId `
        --http-method OPTIONS `
        --type MOCK `
        --request-templates '{"application/json":"{\"statusCode\": 200}"}' `
        --region $REGION 2>$null
    
    aws apigateway put-method-response `
        --rest-api-id $API_ID `
        --resource-id $resourceId `
        --http-method OPTIONS `
        --status-code 200 `
        --response-parameters "method.response.header.Access-Control-Allow-Headers=false,method.response.header.Access-Control-Allow-Methods=false,method.response.header.Access-Control-Allow-Origin=false" `
        --region $REGION 2>$null
    
    aws apigateway put-integration-response `
        --rest-api-id $API_ID `
        --resource-id $resourceId `
        --http-method OPTIONS `
        --status-code 200 `
        --response-parameters '{\"method.response.header.Access-Control-Allow-Headers\":\"'"'"'Content-Type,Authorization'"'"'\",\"method.response.header.Access-Control-Allow-Methods\":\"'"'"'POST,OPTIONS'"'"'\",\"method.response.header.Access-Control-Allow-Origin\":\"'"'"'*'"'"'\"}' `
        --region $REGION 2>$null
    
    # Create POST method
    Write-Host "  Creating POST method..." -ForegroundColor Cyan
    aws apigateway put-method `
        --rest-api-id $API_ID `
        --resource-id $resourceId `
        --http-method POST `
        --authorization-type NONE `
        --region $REGION 2>$null
    
    aws apigateway put-integration `
        --rest-api-id $API_ID `
        --resource-id $resourceId `
        --http-method POST `
        --type AWS_PROXY `
        --integration-http-method POST `
        --uri $lambdaUri `
        --region $REGION 2>$null
    
    Write-Host "✓ /api/auth/$($endpoint.Path) complete" -ForegroundColor Green
    Write-Host ""
}

# Deploy API
Write-Host "Deploying API to $STAGE stage..." -ForegroundColor Yellow

aws apigateway create-deployment `
    --rest-api-id $API_ID `
    --stage-name $STAGE `
    --description "Registration flow deployment" `
    --region $REGION

if ($LASTEXITCODE -eq 0) {
    Write-Host "✓ API deployed successfully" -ForegroundColor Green
} else {
    Write-Host "✗ API deployment failed" -ForegroundColor Red
    exit 1
}

Write-Host ""
Write-Host "=== Deployment Complete ===" -ForegroundColor Green
Write-Host ""
Write-Host "API Endpoints:" -ForegroundColor Cyan
Write-Host "  POST https://${API_ID}.execute-api.${REGION}.amazonaws.com/${STAGE}/api/auth/register" -ForegroundColor White
Write-Host "  POST https://${API_ID}.execute-api.${REGION}.amazonaws.com/${STAGE}/api/auth/request-otp" -ForegroundColor White
Write-Host "  POST https://${API_ID}.execute-api.${REGION}.amazonaws.com/${STAGE}/api/auth/verify-otp" -ForegroundColor White
Write-Host ""
Write-Host "Test the endpoints:" -ForegroundColor Yellow
Write-Host "  .\scripts\testing\test-registration-flow.ps1" -ForegroundColor White
Write-Host ""
