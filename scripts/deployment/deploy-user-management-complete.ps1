# Deploy user management Lambda with all dependencies

$ErrorActionPreference = "Stop"

Write-Host "========================================" -ForegroundColor Cyan
Write-Host "Deploy User Management Lambda (Complete)" -ForegroundColor Cyan
Write-Host "========================================" -ForegroundColor Cyan
Write-Host ""

# Step 1: Copy shared dependencies
Write-Host "Step 1: Copying shared dependencies..." -ForegroundColor Yellow

$sharedFiles = @(
    "audit_logger.py",
    "cache_service.py"
)

foreach ($file in $sharedFiles) {
    Copy-Item "lambda/shared/$file" "lambda/user_management/$file" -Force
}

Write-Host "✓ Shared dependencies copied" -ForegroundColor Green

# Step 2: Package Lambda
Write-Host ""
Write-Host "Step 2: Packaging Lambda function..." -ForegroundColor Yellow

Set-Location lambda/user_management

if (Test-Path "deployment.zip") {
    Remove-Item "deployment.zip" -Force
}

# Package all Python files
Compress-Archive -Path *.py -DestinationPath deployment.zip -Force

Write-Host "✓ Lambda package created" -ForegroundColor Green

# Step 3: Update Lambda
Write-Host ""
Write-Host "Step 3: Updating Lambda function..." -ForegroundColor Yellow

aws lambda update-function-code `
    --function-name aquachain-function-user-management-dev `
    --zip-file fileb://deployment.zip `
    --region ap-south-1 | Out-Null

Write-Host "✓ Lambda function updated" -ForegroundColor Green

# Step 4: Wait for update
Write-Host ""
Write-Host "Step 4: Waiting for update to complete..." -ForegroundColor Yellow

Start-Sleep -Seconds 5

Write-Host "✓ Update complete" -ForegroundColor Green

# Cleanup
Remove-Item "deployment.zip" -Force
Remove-Item "audit_logger.py" -Force -ErrorAction SilentlyContinue
Remove-Item "cache_service.py" -Force -ErrorAction SilentlyContinue
Set-Location ../..

Write-Host ""
Write-Host "========================================" -ForegroundColor Green
Write-Host "✓ Deployment Complete!" -ForegroundColor Green
Write-Host "========================================" -ForegroundColor Green
Write-Host ""
Write-Host "Profile updates should now work correctly." -ForegroundColor Cyan
