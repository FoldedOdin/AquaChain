# Deploy Lambda Function Code Only (No Docker Required)
# This script updates just the Lambda function code without rebuilding infrastructure

Write-Host "========================================" -ForegroundColor Cyan
Write-Host "  Deploy Lambda Code (No Docker)" -ForegroundColor Cyan
Write-Host "========================================" -ForegroundColor Cyan
Write-Host ""

$functionName = "AquaChain-UserManagement-dev"
$lambdaPath = "lambda/user_management"

Write-Host "[1/3] Checking AWS CLI configuration..." -ForegroundColor Yellow
$awsAccount = aws sts get-caller-identity --query Account --output text 2>$null
if ($LASTEXITCODE -ne 0) {
    Write-Host "ERROR: AWS CLI not configured" -ForegroundColor Red
    exit 1
}
Write-Host "✓ AWS Account: $awsAccount" -ForegroundColor Green

Write-Host ""
Write-Host "[2/3] Creating deployment package..." -ForegroundColor Yellow
Push-Location $lambdaPath

# Create a temporary directory for the package
$tempDir = "temp_deploy"
if (Test-Path $tempDir) {
    Remove-Item -Recurse -Force $tempDir
}
New-Item -ItemType Directory -Path $tempDir | Out-Null

# Copy Lambda code
Copy-Item -Path "*.py" -Destination $tempDir -Force
Copy-Item -Path "../shared" -Destination 