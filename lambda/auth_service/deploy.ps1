# Lambda Deployment Script with Dependencies
# Run this from lambda/auth_service directory

Write-Host "🚀 Starting Lambda deployment with dependencies..." -ForegroundColor Cyan

# Clean up old files
Write-Host "🧹 Cleaning up old files..." -ForegroundColor Yellow
if (Test-Path "python") { Remove-Item -Recurse -Force "python" }
if (Test-Path "package") { Remove-Item -Recurse -Force "package" }
if (Test-Path "package.zip") { Remove-Item -Force "package.zip" }

# Create package directory structure
Write-Host "📦 Creating package directory..." -ForegroundColor Yellow
New-Item -ItemType Directory -Path "package" | Out-Null

# Install dependencies directly into package directory
Write-Host "📥 Installing dependencies (PyJWT, requests)..." -ForegroundColor Yellow
pip install -t package PyJWT requests --quiet

if ($LASTEXITCODE -ne 0) {
    Write-Host "❌ Failed to install dependencies" -ForegroundColor Red
    exit 1
}

# Copy Lambda code to package directory
Write-Host "📋 Copying Lambda code..." -ForegroundColor Yellow
Copy-Item handler.py package/
Copy-Item google_oauth_handler.py package/

# Copy shared modules
Write-Host "📋 Copying shared modules..." -ForegroundColor Yellow
$sharedPath = Join-Path $PSScriptRoot ".." "shared"
if (Test-Path $sharedPath) {
    Copy-Item (Join-Path $sharedPath "errors.py") package/ -ErrorAction SilentlyContinue
    Copy-Item (Join-Path $sharedPath "error_handler.py") package/ -ErrorAction SilentlyContinue
    Copy-Item (Join-Path $sharedPath "audit_logger.py") package/ -ErrorAction SilentlyContinue
    Copy-Item (Join-Path $sharedPath "structured_logger.py") package/ -ErrorAction SilentlyContinue
    Write-Host "✅ Shared modules copied" -ForegroundColor Green
} else {
    Write-Host "⚠️  Warning: Shared modules directory not found at $sharedPath" -ForegroundColor Yellow
}

# Create deployment package from package directory
Write-Host "📦 Creating deployment package..." -ForegroundColor Yellow
Compress-Archive -Path package/* -DestinationPath package.zip -Force

Write-Host "✅ Deployment package created: package.zip" -ForegroundColor Green

# Deploy to AWS Lambda
Write-Host "☁️  Deploying to AWS Lambda..." -ForegroundColor Yellow
aws lambda update-function-code `
    --function-name aquachain-function-auth-service-dev `
    --zip-file fileb://package.zip `
    --region ap-south-1 `
    --query "LastUpdateStatus" `
    --output text

if ($LASTEXITCODE -ne 0) {
    Write-Host "❌ Lambda deployment failed" -ForegroundColor Red
    exit 1
}

Write-Host "⏳ Waiting for deployment to complete..." -ForegroundColor Yellow
Start-Sleep -Seconds 5

# Check deployment status
$status = aws lambda get-function `
    --function-name aquachain-function-auth-service-dev `
    --region ap-south-1 `
    --query "Configuration.LastUpdateStatus" `
    --output text

if ($status -eq "Successful") {
    Write-Host "✅ Lambda deployment successful!" -ForegroundColor Green
} else {
    Write-Host "⚠️  Lambda deployment status: $status" -ForegroundColor Yellow
}

# Clean up
Write-Host "🧹 Cleaning up temporary files..." -ForegroundColor Yellow
Remove-Item -Recurse -Force "package"
Remove-Item -Force "package.zip"

Write-Host "✅ Deployment complete!" -ForegroundColor Green
Write-Host ""
Write-Host "Next steps:" -ForegroundColor Cyan
Write-Host "1. Clear browser localStorage and cookies" -ForegroundColor White
Write-Host "2. Log in again to test" -ForegroundColor White
Write-Host "3. Check CloudWatch logs if issues occur:" -ForegroundColor White
Write-Host "   aws logs tail /aws/lambda/aquachain-function-auth-service-dev --follow --region ap-south-1" -ForegroundColor Gray
