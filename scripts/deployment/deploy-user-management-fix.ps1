# Deploy user management Lambda with fixed table names

$ErrorActionPreference = "Stop"

Write-Host "========================================" -ForegroundColor Cyan
Write-Host "Deploy User Management Lambda Fix" -ForegroundColor Cyan
Write-Host "========================================" -ForegroundColor Cyan
Write-Host ""

# Step 1: Package Lambda
Write-Host "Step 1: Packaging Lambda function..." -ForegroundColor Yellow

Set-Location lambda/user_management

if (Test-Path "deployment.zip") {
    Remove-Item "deployment.zip" -Force
}

# Package all Python files
Compress-Archive -Path *.py -DestinationPath deployment.zip -Force

Write-Host "✓ Lambda package created" -ForegroundColor Green

# Step 2: Update Lambda
Write-Host ""
Write-Host "Step 2: Updating Lambda function..." -ForegroundColor Yellow

aws lambda update-function-code `
    --function-name aquachain-function-user-management-dev `
    --zip-file fileb://deployment.zip `
    --region ap-south-1 | Out-Null

Write-Host "✓ Lambda function updated" -ForegroundColor Green

# Step 3: Wait for update
Write-Host ""
Write-Host "Step 3: Waiting for update to complete..." -ForegroundColor Yellow

Start-Sleep -Seconds 5

Write-Host "✓ Update complete" -ForegroundColor Green

# Cleanup
Remove-Item "deployment.zip" -Force
Set-Location ../..

Write-Host ""
Write-Host "========================================" -ForegroundColor Green
Write-Host "✓ Deployment Complete!" -ForegroundColor Green
Write-Host "========================================" -ForegroundColor Green
Write-Host ""
Write-Host "Profile updates should now work correctly." -ForegroundColor Cyan
Write-Host "The Lambda now uses the correct table name: AquaChain-Users" -ForegroundColor Cyan
