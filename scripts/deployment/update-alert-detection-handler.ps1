# Update Alert Detection Lambda to use HTTP API handler
# This script updates the Lambda function handler configuration

$ErrorActionPreference = "Stop"

$REGION = "ap-south-1"
$FUNCTION_NAME = "aquachain-function-alert-detection-dev"
$NEW_HANDLER = "api_handler.lambda_handler"

Write-Host "========================================" -ForegroundColor Cyan
Write-Host "Update Alert Detection Lambda Handler" -ForegroundColor Cyan
Write-Host "========================================" -ForegroundColor Cyan
Write-Host ""

# Step 1: Package the Lambda function
Write-Host "[1/4] Packaging Lambda function..." -ForegroundColor Yellow
Push-Location lambda/alert_detection

# Create deployment package
if (Test-Path "deployment-package.zip") {
    Remove-Item "deployment-package.zip"
}

# Add Python files
Compress-Archive -Path "*.py" -DestinationPath "deployment-package.zip"

Write-Host "✓ Package created" -ForegroundColor Green

# Step 2: Update Lambda function code
Write-Host "[2/4] Updating Lambda function code..." -ForegroundColor Yellow

aws lambda update-function-code `
    --function-name $FUNCTION_NAME `
    --zip-file fileb://deployment-package.zip `
    --region $REGION `
    --output json | Out-Null

if ($LASTEXITCODE -ne 0) {
    Write-Host "✗ Failed to update function code" -ForegroundColor Red
    Pop-Location
    exit 1
}

Write-Host "✓ Function code updated" -ForegroundColor Green

# Wait for update to complete
Write-Host "  Waiting for update to complete..." -ForegroundColor Gray
Start-Sleep -Seconds 5

# Step 3: Update handler configuration
Write-Host "[3/4] Updating handler configuration..." -ForegroundColor Yellow

aws lambda update-function-configuration `
    --function-name $FUNCTION_NAME `
    --handler $NEW_HANDLER `
    --region $REGION `
    --output json | Out-Null

if ($LASTEXITCODE -ne 0) {
    Write-Host "✗ Failed to update handler configuration" -ForegroundColor Red
    Pop-Location
    exit 1
}

Write-Host "✓ Handler updated to: $NEW_HANDLER" -ForegroundColor Green

# Wait for configuration update
Write-Host "  Waiting for configuration update..." -ForegroundColor Gray
Start-Sleep -Seconds 5

# Step 4: Verify the update
Write-Host "[4/4] Verifying update..." -ForegroundColor Yellow

$config = aws lambda get-function-configuration `
    --function-name $FUNCTION_NAME `
    --region $REGION `
    --output json | ConvertFrom-Json

if ($config.Handler -eq $NEW_HANDLER) {
    Write-Host "✓ Handler verified: $($config.Handler)" -ForegroundColor Green
} else {
    Write-Host "✗ Handler mismatch. Expected: $NEW_HANDLER, Got: $($config.Handler)" -ForegroundColor Red
    Pop-Location
    exit 1
}

# Cleanup
Remove-Item "deployment-package.zip"
Pop-Location

Write-Host ""
Write-Host "========================================" -ForegroundColor Green
Write-Host "✓ Alert Detection Lambda Updated!" -ForegroundColor Green
Write-Host "========================================" -ForegroundColor Green
Write-Host ""
Write-Host "Function: $FUNCTION_NAME" -ForegroundColor Cyan
Write-Host "Handler: $NEW_HANDLER" -ForegroundColor Cyan
Write-Host "Region: $REGION" -ForegroundColor Cyan
Write-Host ""
Write-Host "Next steps:" -ForegroundColor Yellow
Write-Host "1. Test the endpoints:" -ForegroundColor White
Write-Host "   GET /alerts" -ForegroundColor Gray
Write-Host "   GET /alerts/{alertId}" -ForegroundColor Gray
Write-Host "   PUT /alerts/{alertId}/acknowledge" -ForegroundColor Gray
Write-Host "   PUT /alerts/{alertId}/resolve" -ForegroundColor Gray
Write-Host "2. Check CloudWatch logs for any errors" -ForegroundColor White
Write-Host "3. Proceed to Phase 1, Step 4: Disable WebSocket" -ForegroundColor White
Write-Host ""
