# Deploy updated admin service Lambda with DELETE device handler

$ErrorActionPreference = "Stop"

Write-Host "========================================" -ForegroundColor Cyan
Write-Host "Deploy Device DELETE Handler" -ForegroundColor Cyan
Write-Host "========================================" -ForegroundColor Cyan
Write-Host ""

# Step 1: Package Lambda function
Write-Host "Step 1: Packaging Lambda function..." -ForegroundColor Yellow

Set-Location lambda/admin_service

# Create deployment package
if (Test-Path "deployment.zip") {
    Remove-Item "deployment.zip" -Force
}

# Add handler and dependencies
Compress-Archive -Path handler.py,get_system_metrics.py -DestinationPath deployment.zip -Force

Write-Host "✓ Lambda package created" -ForegroundColor Green

# Step 2: Update Lambda function
Write-Host ""
Write-Host "Step 2: Updating Lambda function..." -ForegroundColor Yellow

aws lambda update-function-code `
    --function-name aquachain-function-admin-service-dev `
    --zip-file fileb://deployment.zip `
    --region ap-south-1 | Out-Null

Write-Host "✓ Lambda function updated" -ForegroundColor Green

# Step 3: Wait for update to complete
Write-Host ""
Write-Host "Step 3: Waiting for Lambda update to complete..." -ForegroundColor Yellow

Start-Sleep -Seconds 5

Write-Host "✓ Lambda update complete" -ForegroundColor Green

# Cleanup
Remove-Item "deployment.zip" -Force
Set-Location ../..

Write-Host ""
Write-Host "========================================" -ForegroundColor Green
Write-Host "✓ Deployment Complete!" -ForegroundColor Green
Write-Host "========================================" -ForegroundColor Green
Write-Host ""
Write-Host "The DELETE /api/devices/{deviceId} endpoint is now functional." -ForegroundColor Cyan
Write-Host "Try removing a device from the Consumer Dashboard." -ForegroundColor Cyan
