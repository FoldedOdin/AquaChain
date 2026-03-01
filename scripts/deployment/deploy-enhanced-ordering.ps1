# Deploy Enhanced Consumer Ordering Stack
# This script deploys the complete ordering system with Lambda functions, DynamoDB tables, and API Gateway endpoints

Write-Host "========================================" -ForegroundColor Cyan
Write-Host "Enhanced Consumer Ordering Deployment" -ForegroundColor Cyan
Write-Host "========================================" -ForegroundColor Cyan
Write-Host ""

# Check if we're in the right directory
if (-not (Test-Path "infrastructure/cdk")) {
    Write-Host "Error: Must run from project root directory" -ForegroundColor Red
    exit 1
}

# Navigate to CDK directory
Set-Location infrastructure/cdk

Write-Host "Step 1: Installing CDK dependencies..." -ForegroundColor Yellow
pip install -r requirements.txt

Write-Host ""
Write-Host "Step 2: Deploying Enhanced Ordering Stack..." -ForegroundColor Yellow
Write-Host "This will create:" -ForegroundColor White
Write-Host "  - Orders DynamoDB table" -ForegroundColor White
Write-Host "  - Payments DynamoDB table" -ForegroundColor White
Write-Host "  - Technicians DynamoDB table" -ForegroundColor White
Write-Host "  - Order Management Lambda" -ForegroundColor White
Write-Host "  - Payment Service Lambda" -ForegroundColor White
Write-Host "  - Technician Assignment Lambda" -ForegroundColor White
Write-Host "  - WebSocket API for real-time updates" -ForegroundColor White
Write-Host "  - EventBridge rules for order processing" -ForegroundColor White
Write-Host "  - Razorpay secrets in Secrets Manager" -ForegroundColor White
Write-Host ""

$confirmation = Read-Host "Continue with deployment? (y/n)"
if ($confirmation -ne 'y') {
    Write-Host "Deployment cancelled" -ForegroundColor Yellow
    Set-Location ../..
    exit 0
}

Write-Host ""
Write-Host "Deploying stack..." -ForegroundColor Green
cdk deploy AquaChain-EnhancedOrdering-dev --require-approval never

if ($LASTEXITCODE -eq 0) {
    Write-Host ""
    Write-Host "========================================" -ForegroundColor Green
    Write-Host "Deployment Successful!" -ForegroundColor Green
    Write-Host "========================================" -ForegroundColor Green
    Write-Host ""
    Write-Host "Next Steps:" -ForegroundColor Cyan
    Write-Host "1. Add Razorpay credentials to Secrets Manager" -ForegroundColor White
    Write-Host "2. Configure API Gateway endpoints for orders" -ForegroundColor White
    Write-Host "3. Test order creation from frontend" -ForegroundColor White
    Write-Host ""
    Write-Host "To add Razorpay secrets:" -ForegroundColor Yellow
    Write-Host "  aws secretsmanager put-secret-value --secret-id aquachain-razorpay-credentials-dev --secret-string '{\"key_id\":\"YOUR_KEY\",\"key_secret\":\"YOUR_SECRET\"}'" -ForegroundColor Gray
} else {
    Write-Host ""
    Write-Host "========================================" -ForegroundColor Red
    Write-Host "Deployment Failed" -ForegroundColor Red
    Write-Host "========================================" -ForegroundColor Red
    Write-Host ""
    Write-Host "Common issues:" -ForegroundColor Yellow
    Write-Host "1. Lambda function code missing - check lambda/orders/ directory" -ForegroundColor White
    Write-Host "2. Python dependencies not installed - run pip install in lambda directories" -ForegroundColor White
    Write-Host "3. CDK bootstrap not done - run 'cdk bootstrap'" -ForegroundColor White
}

# Return to project root
Set-Location ../..
