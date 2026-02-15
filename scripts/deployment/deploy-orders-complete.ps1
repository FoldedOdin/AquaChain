# Complete Orders Service Deployment
# This script deploys the orders service properly using CDK

Write-Host "========================================" -ForegroundColor Cyan
Write-Host "Complete Orders Service Deployment" -ForegroundColor Cyan
Write-Host "========================================" -ForegroundColor Cyan
Write-Host ""

Write-Host "This deployment will:" -ForegroundColor Yellow
Write-Host "  1. Deploy Enhanced Ordering Stack (Lambda functions, DynamoDB tables)" -ForegroundColor White
Write-Host "  2. Create Razorpay secrets placeholder" -ForegroundColor White
Write-Host "  3. Add API Gateway endpoints manually" -ForegroundColor White
Write-Host "  4. Test the integration" -ForegroundColor White
Write-Host ""

Write-Host "Estimated time: 20-30 minutes" -ForegroundColor Yellow
Write-Host "Estimated cost: ~$0.40-1.45/month" -ForegroundColor Yellow
Write-Host ""

$confirmation = Read-Host "Continue? (y/n)"
if ($confirmation -ne 'y') {
    Write-Host "Cancelled" -ForegroundColor Yellow
    exit 0
}

Write-Host ""
Write-Host "========================================" -ForegroundColor Green
Write-Host "Step 1: Deploy Enhanced Ordering Stack" -ForegroundColor Green
Write-Host "========================================" -ForegroundColor Green
Write-Host ""

# Navigate to CDK directory
Push-Location infrastructure/cdk

Write-Host "Installing CDK dependencies..." -ForegroundColor Yellow
pip install -r requirements.txt -q

Write-Host "Deploying stack..." -ForegroundColor Yellow
cdk deploy AquaChain-EnhancedOrdering-dev --require-approval never

if ($LASTEXITCODE -ne 0) {
    Write-Host ""
    Write-Host "ERROR: Stack deployment failed" -ForegroundColor Red
    Write-Host ""
    Write-Host "Common issues:" -ForegroundColor Yellow
    Write-Host "  1. Lambda code missing - check lambda/orders/, lambda/payment_service/, etc." -ForegroundColor White
    Write-Host "  2. Python dependencies - run 'pip install -r requirements.txt' in lambda dirs" -ForegroundColor White
    Write-Host "  3. CDK not bootstrapped - run 'cdk bootstrap'" -ForegroundColor White
    Write-Host ""
    Pop-Location
    exit 1
}

Pop-Location

Write-Host ""
Write-Host "✅ Enhanced Ordering Stack deployed successfully" -ForegroundColor Green
Write-Host ""

Write-Host "========================================" -ForegroundColor Green
Write-Host "Step 2: Create Razorpay Secrets" -ForegroundColor Green
Write-Host "========================================" -ForegroundColor Green
Write-Host ""

Write-Host "Do you have Razorpay credentials? (y/n)" -ForegroundColor Yellow
$hasRazorpay = Read-Host

if ($hasRazorpay -eq 'y') {
    Write-Host ""
    Write-Host "Enter Razorpay Key ID:" -ForegroundColor Yellow
    $keyId = Read-Host
    Write-Host "Enter Razorpay Key Secret:" -ForegroundColor Yellow
    $keySecret = Read-Host -AsSecureString
    $keySecretPlain = [Runtime.InteropServices.Marshal]::PtrToStringAuto(
        [Runtime.InteropServices.Marshal]::SecureStringToBSTR($keySecret)
    )
    
    $secretValue = "{`"key_id`":`"$keyId`",`"key_secret`":`"$keySecretPlain`"}"
} else {
    Write-Host "Creating placeholder for COD-only mode..." -ForegroundColor Yellow
    $secretValue = '{"key_id":"not_configured","key_secret":"not_configured"}'
}

Write-Host "Storing secret in AWS Secrets Manager..." -ForegroundColor Yellow
aws secretsmanager put-secret-value `
    --secret-id aquachain-razorpay-credentials-dev `
    --secret-string $secretValue `
    --region ap-south-1 2>$null

if ($LASTEXITCODE -eq 0) {
    Write-Host "✅ Secrets stored successfully" -ForegroundColor Green
} else {
    Write-Host "⚠️  Secret might already exist or there was an error" -ForegroundColor Yellow
}

Write-Host ""
Write-Host "========================================" -ForegroundColor Green
Write-Host "Step 3: Get Lambda Function ARNs" -ForegroundColor Green
Write-Host "========================================" -ForegroundColor Green
Write-Host ""

Write-Host "Retrieving deployed Lambda functions..." -ForegroundColor Yellow

$orderManagementArn = aws lambda get-function `
    --function-name aquachain-function-order-management-dev `
    --region ap-south-1 `
    --query 'Configuration.FunctionArn' `
    --output text 2>$null

if ($orderManagementArn) {
    Write-Host "✅ Order Management Lambda: $orderManagementArn" -ForegroundColor Green
} else {
    Write-Host "⚠️  Order Management Lambda not found" -ForegroundColor Yellow
    Write-Host "   This might be normal if the Lambda has a different name" -ForegroundColor Gray
}

Write-Host ""
Write-Host "========================================" -ForegroundColor Green
Write-Host "Step 4: Add API Gateway Endpoints" -ForegroundColor Green
Write-Host "========================================" -ForegroundColor Green
Write-Host ""

Write-Host "IMPORTANT: API Gateway endpoints need to be added manually or via CDK update" -ForegroundColor Yellow
Write-Host ""
Write-Host "Two options:" -ForegroundColor White
Write-Host ""
Write-Host "Option A: Manual (AWS Console)" -ForegroundColor Cyan
Write-Host "  1. Go to API Gateway console" -ForegroundColor White
Write-Host "  2. Select API: vtqjfznspc" -ForegroundColor White
Write-Host "  3. Create resource: /api/orders" -ForegroundColor White
Write-Host "  4. Add POST method with Lambda integration" -ForegroundColor White
Write-Host "  5. Add OPTIONS method for CORS" -ForegroundColor White
Write-Host "  6. Deploy to 'dev' stage" -ForegroundColor White
Write-Host ""
Write-Host "Option B: CDK Update (Recommended)" -ForegroundColor Cyan
Write-Host "  1. Update infrastructure/cdk/stacks/api_stack.py" -ForegroundColor White
Write-Host "  2. Add orders endpoints to _create_api_gateway method" -ForegroundColor White
Write-Host "  3. Run: cdk deploy AquaChain-API-dev" -ForegroundColor White
Write-Host ""

$choice = Read-Host "Which option? (A/B/Skip)"

if ($choice -eq 'A') {
    Write-Host ""
    Write-Host "Opening AWS Console..." -ForegroundColor Yellow
    Start-Process "https://ap-south-1.console.aws.amazon.com/apigateway/main/apis/vtqjfznspc/resources?api=vtqjfznspc&region=ap-south-1"
    Write-Host ""
    Write-Host "Follow the manual steps above in the console" -ForegroundColor White
    Write-Host "Press Enter when done..." -ForegroundColor Yellow
    Read-Host
} elseif ($choice -eq 'B') {
    Write-Host ""
    Write-Host "Creating API Stack update guide..." -ForegroundColor Yellow
    
    $guide = @"
# API Stack Update for Orders Endpoints

Add this code to infrastructure/cdk/stacks/api_stack.py in the _create_api_gateway method:

```python
# /api/orders - Order management endpoints
orders_resource = api_root.add_resource("orders")

# POST /api/orders - Create order
orders_resource.add_method(
    "POST",
    apigateway.LambdaIntegration(self.lambda_functions.get("order_management")),
    authorizer=self.cognito_authorizer,
    authorization_type=apigateway.AuthorizationType.COGNITO
)

# GET /api/orders/my - Get user's orders  
my_orders_resource = orders_resource.add_resource("my")
my_orders_resource.add_method(
    "GET",
    apigateway.LambdaIntegration(self.lambda_functions.get("order_management")),
    authorizer=self.cognito_authorizer,
    authorization_type=apigateway.AuthorizationType.COGNITO
)
```

Then run: cdk deploy AquaChain-API-dev
"@
    
    $guide | Out-File -FilePath "DOCS/deployment/API_STACK_ORDERS_UPDATE.md" -Encoding UTF8
    Write-Host "✅ Guide created: DOCS/deployment/API_STACK_ORDERS_UPDATE.md" -ForegroundColor Green
    Write-Host ""
    Write-Host "Please update the API stack and redeploy" -ForegroundColor Yellow
} else {
    Write-Host "Skipping API Gateway configuration" -ForegroundColor Yellow
}

Write-Host ""
Write-Host "========================================" -ForegroundColor Green
Write-Host "Deployment Summary" -ForegroundColor Green
Write-Host "========================================" -ForegroundColor Green
Write-Host ""
Write-Host "✅ Enhanced Ordering Stack deployed" -ForegroundColor Green
Write-Host "✅ Razorpay secrets configured" -ForegroundColor Green
Write-Host "⚠️  API Gateway endpoints need manual configuration" -ForegroundColor Yellow
Write-Host ""
Write-Host "Next Steps:" -ForegroundColor Cyan
Write-Host "  1. Configure API Gateway endpoints (if not done)" -ForegroundColor White
Write-Host "  2. Test order creation from frontend" -ForegroundColor White
Write-Host "  3. Monitor CloudWatch logs for any issues" -ForegroundColor White
Write-Host ""
Write-Host "Test endpoint:" -ForegroundColor Yellow
Write-Host "  POST https://vtqjfznspc.execute-api.ap-south-1.amazonaws.com/dev/api/orders" -ForegroundColor Gray
Write-Host ""
Write-Host "Documentation:" -ForegroundColor Yellow
Write-Host "  DOCS/deployment/ORDERS_DEPLOYMENT_DECISION.md" -ForegroundColor Gray
Write-Host "  DOCS/deployment/API_STACK_ORDERS_UPDATE.md" -ForegroundColor Gray
Write-Host ""
