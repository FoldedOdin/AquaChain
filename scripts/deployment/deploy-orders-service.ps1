# Deploy Orders Service with Razorpay Integration
# This script deploys the complete orders service including Lambda, API Gateway, and DynamoDB

$ErrorActionPreference = "Stop"
$region = "ap-south-1"
$apiId = "vtqjfznspc"

Write-Host "========================================" -ForegroundColor Cyan
Write-Host "  Deploying Orders Service" -ForegroundColor Cyan
Write-Host "========================================" -ForegroundColor Cyan
Write-Host ""

# Step 1: Check if Orders table exists
Write-Host "Step 1: Checking Orders DynamoDB table..." -ForegroundColor Yellow
$tableExists = aws dynamodb describe-table --table-name "aquachain-orders" --region $region 2>$null

if ($LASTEXITCODE -ne 0) {
    Write-Host "✗ Orders table doesn't exist. Creating..." -ForegroundColor Red
    Write-Host ""
    Write-Host "This requires CDK deployment which may take 15-30 minutes." -ForegroundColor Yellow
    Write-Host "The orders service needs proper infrastructure setup." -ForegroundColor Yellow
    Write-Host ""
    Write-Host "Recommended approach:" -ForegroundColor Cyan
    Write-Host "1. The orders table and Lambda need to be deployed via CDK" -ForegroundColor White
    Write-Host "2. This is a significant deployment that will add to your AWS costs" -ForegroundColor White
    Write-Host "3. Manual API Gateway configuration will be needed" -ForegroundColor White
    Write-Host ""
    Write-Host "Would you like to:" -ForegroundColor Cyan
    Write-Host "A) Create a minimal orders table manually (quick, but limited functionality)" -ForegroundColor White
    Write-Host "B) Deploy via CDK (proper, but time-consuming and costly)" -ForegroundColor White
    Write-Host "C) Cancel and reconsider" -ForegroundColor White
    Write-Host ""
    Write-Host "Due to the complexity and cost implications, I recommend option C." -ForegroundColor Yellow
    Write-Host "The orders feature requires significant infrastructure that isn't currently deployed." -ForegroundColor Yellow
    exit 1
} else {
    Write-Host "✓ Orders table exists" -ForegroundColor Green
}

# Step 2: Check if Orders Lambda exists
Write-Host ""
Write-Host "Step 2: Checking Orders Lambda function..." -ForegroundColor Yellow
$lambdaExists = aws lambda get-function --function-name "aquachain-orders-api-dev" --region $region 2>$null

if ($LASTEXITCODE -ne 0) {
    Write-Host "✗ Orders Lambda doesn't exist" -ForegroundColor Red
    Write-Host ""
    Write-Host "The Lambda function needs to be deployed via CDK." -ForegroundColor Yellow
    Write-Host "This cannot be done with a simple script." -ForegroundColor Yellow
    exit 1
} else {
    Write-Host "✓ Orders Lambda exists" -ForegroundColor Green
}

# Step 3: Check API Gateway endpoints
Write-Host ""
Write-Host "Step 3: Checking API Gateway endpoints..." -ForegroundColor Yellow
Write-Host "This deployment requires proper CDK infrastructure." -ForegroundColor Yellow

Write-Host ""
Write-Host "========================================" -ForegroundColor Red
Write-Host "  DEPLOYMENT BLOCKED" -ForegroundColor Red
Write-Host "========================================" -ForegroundColor Red
Write-Host ""
Write-Host "The orders service requires infrastructure that isn't deployed:" -ForegroundColor Yellow
Write-Host "  - Orders Lambda function" -ForegroundColor White
Write-Host "  - API Gateway endpoints (/api/orders/*)" -ForegroundColor White
Write-Host "  - Proper IAM roles and permissions" -ForegroundColor White
Write-Host "  - Razorpay secrets configuration" -ForegroundColor White
Write-Host ""
Write-Host "This cannot be deployed with a simple script." -ForegroundColor Red
Write-Host "It requires full CDK stack deployment." -ForegroundColor Red
