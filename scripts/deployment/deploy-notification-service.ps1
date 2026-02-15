# Deploy Notification Service Lambda
# This script packages and deploys the notification service Lambda function

$ErrorActionPreference = "Stop"
$region = "ap-south-1"
$functionName = "aquachain-notification-api-dev"
$lambdaDir = "lambda/notification_service"

Write-Host "Deploying Notification Service Lambda..." -ForegroundColor Cyan

# Check if function exists
$functionExists = aws lambda get-function --function-name $functionName --region $region 2>$null
$exists = $LASTEXITCODE -eq 0

if (-not $exists) {
    Write-Host "Lambda function does not exist. This requires CDK deployment." -ForegroundColor Yellow
    Write-Host ""
    Write-Host "The notification service needs to be deployed via CDK stack." -ForegroundColor Yellow
    Write-Host "However, the app will continue to work without it." -ForegroundColor Green
    Write-Host ""
    Write-Host "Options:" -ForegroundColor Cyan
    Write-Host "1. Continue using the app without notifications (recommended)" -ForegroundColor White
    Write-Host "2. Deploy the full infrastructure stack (may incur costs)" -ForegroundColor White
    Write-Host ""
    Write-Host "The frontend has been updated to handle missing notification service gracefully." -ForegroundColor Green
    exit 0
}

Write-Host "✓ Function exists, updating code..." -ForegroundColor Green

# Package Lambda
Write-Host "Packaging Lambda function..." -ForegroundColor Yellow
Push-Location $lambdaDir

# Create deployment package
if (Test-Path "function.zip") {
    Remove-Item "function.zip"
}

# Add Python files
$files = @(
    "api_handler.py",
    "handler.py",
    "cors_utils.py",
    "error_handler.py",
    "errors.py",
    "structured_logger.py"
)

foreach ($file in $files) {
    if (Test-Path $file) {
        Compress-Archive -Path $file -Update -DestinationPath "function.zip"
    }
}

# Update Lambda function
Write-Host "Updating Lambda function code..." -ForegroundColor Yellow
aws lambda update-function-code `
    --function-name $functionName `
    --region $region `
    --zip-file fileb://function.zip

if ($LASTEXITCODE -eq 0) {
    Write-Host "✓ Lambda function updated successfully" -ForegroundColor Green
} else {
    Write-Host "✗ Failed to update Lambda function" -ForegroundColor Red
    Pop-Location
    exit 1
}

Pop-Location

Write-Host ""
Write-Host "Notification service deployment complete!" -ForegroundColor Green
