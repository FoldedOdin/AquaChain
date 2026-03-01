# Deploy OTP Fix - API and Compute Only
# Skips Data stack to avoid dependency issues

Write-Host "========================================" -ForegroundColor Cyan
Write-Host "  Deploy OTP Email Fix (API + Compute)" -ForegroundColor Cyan
Write-Host "========================================" -ForegroundColor Cyan
Write-Host ""

# Check AWS CLI
Write-Host "[1/3] Checking AWS CLI..." -ForegroundColor Yellow
$awsAccount = aws sts get-caller-identity --query Account --output text 2>$null
if ($LASTEXITCODE -ne 0) {
    Write-Host "ERROR: AWS CLI not configured" -ForegroundColor Red
    exit 1
}
Write-Host "✓ AWS Account: $awsAccount" -ForegroundColor Green

$region = aws configure get region
if ([string]::IsNullOrEmpty($region)) {
    $region = "ap-south-1"
}
Write-Host "✓ Region: $region" -ForegroundColor Green
Write-Host ""

# Deploy stacks
Write-Host "[2/3] Deploying API and Compute stacks..." -ForegroundColor Yellow
Push-Location infrastructure/cdk
try {
    Write-Host "Deploying AquaChain-API-dev..." -ForegroundColor Cyan
    cdk deploy AquaChain-API-dev --require-approval never --exclusively
    
    if ($LASTEXITCODE -ne 0) {
        Write-Host "ERROR: API deployment failed" -ForegroundColor Red
        Pop-Location
        exit 1
    }
    
    Write-Host ""
    Write-Host "Deploying AquaChain-Compute-dev..." -ForegroundColor Cyan
    cdk deploy AquaChain-Compute-dev --require-approval never --exclusively
    
    if ($LASTEXITCODE -ne 0) {
        Write-Host "ERROR: Compute deployment failed" -ForegroundColor Red
        Pop-Location
        exit 1
    }
    
    Write-Host "✓ Deployments successful" -ForegroundColor Green
} finally {
    Pop-Location
}

Write-Host ""

# Test endpoint
Write-Host "[3/3] Verifying deployment..." -ForegroundColor Yellow
$apiEndpoint = aws cloudformation describe-stacks `
    --stack-name AquaChain-API-dev `
    --query "Stacks[0].Outputs[?OutputKey=='ApiEndpoint'].OutputValue" `
    --output text 2>$null

if ([string]::IsNullOrEmpty($apiEndpoint)) {
    Write-Host "⚠ Could not retrieve API endpoint" -ForegroundColor Yellow
} else {
    Write-Host "✓ API Endpoint: $apiEndpoint" -ForegroundColor Green
}

Write-Host ""
Write-Host "========================================" -ForegroundColor Green
Write-Host "  Deployment Complete!" -ForegroundColor Green
Write-Host "========================================" -ForegroundColor Green
Write-Host ""
Write-Host "Changes deployed:" -ForegroundColor Cyan
Write-Host "  ✓ OTP email functionality via AWS SES" -ForegroundColor Green
Write-Host "  ✓ Updated Lambda IAM permissions" -ForegroundColor Green
Write-Host "  ✓ API Gateway routes configured" -ForegroundColor Green
Write-Host ""
Write-Host "Next steps:" -ForegroundColor Yellow
Write-Host "  1. Verify contact.aquachain@gmail.com in AWS SES" -ForegroundColor Yellow
Write-Host "  2. Test profile update in the dashboard" -ForegroundColor Yellow
Write-Host "  3. Check email for OTP" -ForegroundColor Yellow
Write-Host ""
Write-Host "If OTP still fails, check CloudWatch logs:" -ForegroundColor Yellow
Write-Host "  aws logs tail /aws/lambda/AquaChain-UserManagement-dev --follow" -ForegroundColor Cyan
Write-Host ""
