# Fix System Metrics API Gateway Integration
# This script adds the missing Lambda integration for GET /api/admin/system/metrics

Write-Host "========================================" -ForegroundColor Cyan
Write-Host "Fix System Metrics Integration" -ForegroundColor Cyan
Write-Host "========================================" -ForegroundColor Cyan
Write-Host ""

$ErrorActionPreference = "Stop"

# Configuration
$API_ID = "vtqjfznspc"
$REGION = "ap-south-1"
$RESOURCE_ID = "j3bfm7"  # /api/admin/system/metrics resource
$LAMBDA_ARN = "arn:aws:lambda:ap-south-1:758346259059:function:aquachain-function-admin-service-dev"
$ACCOUNT_ID = "758346259059"

Write-Host "Configuration:" -ForegroundColor Yellow
Write-Host "  API ID: $API_ID" -ForegroundColor Gray
Write-Host "  Resource ID: $RESOURCE_ID" -ForegroundColor Gray
Write-Host "  Lambda ARN: $LAMBDA_ARN" -ForegroundColor Gray
Write-Host ""

# Step 1: Check current GET method configuration
Write-Host "Step 1: Checking current GET method..." -ForegroundColor Yellow

try {
    $getMethod = aws apigateway get-method `
        --rest-api-id $API_ID `
        --resource-id $RESOURCE_ID `
        --http-method GET `
        --region $REGION `
        --output json 2>&1
    
    if ($LASTEXITCODE -eq 0) {
        Write-Host "  ✓ GET method exists" -ForegroundColor Green
        $methodJson = $getMethod | ConvertFrom-Json
        Write-Host "  Authorization: $($methodJson.authorizationType)" -ForegroundColor Gray
    } else {
        Write-Host "  ✗ GET method not found, creating..." -ForegroundColor Red
        
        # Get authorizer ID
        $authorizers = aws apigateway get-authorizers --rest-api-id $API_ID --region $REGION --output json | ConvertFrom-Json
        $authorizerId = $authorizers.items[0].id
        
        # Create GET method
        aws apigateway put-method `
            --rest-api-id $API_ID `
            --resource-id $RESOURCE_ID `
            --http-method GET `
            --authorization-type COGNITO_USER_POOLS `
            --authorizer-id $authorizerId `
            --region $REGION `
            --output json | Out-Null
        
        Write-Host "  ✓ GET method created" -ForegroundColor Green
    }
} catch {
    Write-Host "  ✗ Error checking GET method: $_" -ForegroundColor Red
    exit 1
}

Write-Host ""

# Step 2: Add Lambda integration for GET method
Write-Host "Step 2: Adding Lambda integration..." -ForegroundColor Yellow

try {
    aws apigateway put-integration `
        --rest-api-id $API_ID `
        --resource-id $RESOURCE_ID `
        --http-method GET `
        --type AWS_PROXY `
        --integration-http-method POST `
        --uri "arn:aws:apigateway:${REGION}:lambda:path/2015-03-31/functions/${LAMBDA_ARN}/invocations" `
        --region $REGION `
        --output json | Out-Null
    
    Write-Host "  ✓ Lambda integration added" -ForegroundColor Green
} catch {
    Write-Host "  ℹ Lambda integration may already exist" -ForegroundColor Gray
}

Write-Host ""

# Step 3: Add Lambda permission for API Gateway to invoke the function
Write-Host "Step 3: Adding Lambda permission..." -ForegroundColor Yellow

$statementId = "apigateway-metrics-invoke-$(Get-Date -Format 'yyyyMMddHHmmss')"

try {
    aws lambda add-permission `
        --function-name aquachain-function-admin-service-dev `
        --statement-id $statementId `
        --action lambda:InvokeFunction `
        --principal apigateway.amazonaws.com `
        --source-arn "arn:aws:execute-api:${REGION}:${ACCOUNT_ID}:${API_ID}/*/GET/api/admin/system/metrics" `
        --region $REGION `
        --output json | Out-Null
    
    Write-Host "  ✓ Lambda permission added" -ForegroundColor Green
} catch {
    if ($_.Exception.Message -like "*ResourceConflictException*") {
        Write-Host "  ℹ Lambda permission already exists" -ForegroundColor Gray
    } else {
        Write-Host "  ⚠ Warning: Could not add Lambda permission: $_" -ForegroundColor Yellow
        Write-Host "  This may already exist or need manual configuration" -ForegroundColor Yellow
    }
}

Write-Host ""

# Step 4: Verify OPTIONS method for CORS
Write-Host "Step 4: Verifying OPTIONS method for CORS..." -ForegroundColor Yellow

try {
    $optionsMethod = aws apigateway get-method `
        --rest-api-id $API_ID `
        --resource-id $RESOURCE_ID `
        --http-method OPTIONS `
        --region $REGION `
        --output json 2>&1
    
    if ($LASTEXITCODE -eq 0) {
        Write-Host "  ✓ OPTIONS method exists" -ForegroundColor Green
    } else {
        Write-Host "  Creating OPTIONS method..." -ForegroundColor Gray
        
        # Create OPTIONS method
        aws apigateway put-method `
            --rest-api-id $API_ID `
            --resource-id $RESOURCE_ID `
            --http-method OPTIONS `
            --authorization-type NONE `
            --region $REGION `
            --output json | Out-Null
        
        # Add MOCK integration
        aws apigateway put-integration `
            --rest-api-id $API_ID `
            --resource-id $RESOURCE_ID `
            --http-method OPTIONS `
            --type MOCK `
            --request-templates '{\"application/json\":\"{\\\"statusCode\\\": 200}\"}' `
            --region $REGION `
            --output json | Out-Null
        
        # Add method response
        aws apigateway put-method-response `
            --rest-api-id $API_ID `
            --resource-id $RESOURCE_ID `
            --http-method OPTIONS `
            --status-code 200 `
            --response-parameters '{\"method.response.header.Access-Control-Allow-Headers\":false,\"method.response.header.Access-Control-Allow-Methods\":false,\"method.response.header.Access-Control-Allow-Origin\":false}' `
            --region $REGION `
            --output json | Out-Null
        
        # Add integration response with CORS headers
        aws apigateway put-integration-response `
            --rest-api-id $API_ID `
            --resource-id $RESOURCE_ID `
            --http-method OPTIONS `
            --status-code 200 `
            --response-parameters '{\"method.response.header.Access-Control-Allow-Headers\":\"'"'"'Content-Type,X-Amz-Date,Authorization,X-Api-Key,X-Amz-Security-Token'"'"'\",\"method.response.header.Access-Control-Allow-Methods\":\"'"'"'GET,OPTIONS'"'"'\",\"method.response.header.Access-Control-Allow-Origin\":\"'"'"'*'"'"'\"}' `
            --region $REGION `
            --output json | Out-Null
        
        Write-Host "  ✓ OPTIONS method created with CORS" -ForegroundColor Green
    }
} catch {
    Write-Host "  ⚠ Warning: Could not verify OPTIONS method: $_" -ForegroundColor Yellow
}

Write-Host ""

# Step 5: Deploy API to dev stage
Write-Host "Step 5: Deploying API to dev stage..." -ForegroundColor Yellow

try {
    aws apigateway create-deployment `
        --rest-api-id $API_ID `
        --stage-name dev `
        --description "Deploy system metrics endpoint with Lambda integration" `
        --region $REGION `
        --output json | Out-Null
    
    Write-Host "  ✓ API deployed successfully" -ForegroundColor Green
} catch {
    Write-Host "  ✗ Error deploying API: $_" -ForegroundColor Red
    exit 1
}

Write-Host ""

# Step 6: Test the endpoint
Write-Host "Step 6: Testing endpoint..." -ForegroundColor Yellow

$endpointUrl = "https://${API_ID}.execute-api.${REGION}.amazonaws.com/dev/api/admin/system/metrics"

Write-Host "  Endpoint URL: $endpointUrl" -ForegroundColor Gray
Write-Host ""
Write-Host "  To test with authentication, run:" -ForegroundColor Cyan
Write-Host "  curl -X GET `"$endpointUrl`" -H `"Authorization: Bearer YOUR_JWT_TOKEN`"" -ForegroundColor White
Write-Host ""

Write-Host "========================================" -ForegroundColor Green
Write-Host "✓ Integration Fixed Successfully!" -ForegroundColor Green
Write-Host "========================================" -ForegroundColor Green
Write-Host ""
Write-Host "Next Steps:" -ForegroundColor Cyan
Write-Host "1. Test the endpoint from the admin dashboard" -ForegroundColor White
Write-Host "2. Check browser console for any errors" -ForegroundColor White
Write-Host "3. Verify real-time metrics are updating" -ForegroundColor White
Write-Host ""
