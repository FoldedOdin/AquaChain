# Deploy Device DELETE Endpoint Fix
# Adds missing DELETE endpoint for device removal

Write-Host "========================================" -ForegroundColor Cyan
Write-Host "Device DELETE Endpoint Deployment" -ForegroundColor Cyan
Write-Host "========================================" -ForegroundColor Cyan
Write-Host ""

# Check if AWS CLI is configured
Write-Host "Checking AWS CLI configuration..." -ForegroundColor Yellow
try {
    $awsIdentity = aws sts get-caller-identity 2>&1
    if ($LASTEXITCODE -ne 0) {
        Write-Host "ERROR: AWS CLI not configured properly" -ForegroundColor Red
        Write-Host "Please run 'aws configure' first" -ForegroundColor Red
        exit 1
    }
    Write-Host "✓ AWS CLI configured" -ForegroundColor Green
} catch {
    Write-Host "ERROR: AWS CLI not found" -ForegroundColor Red
    exit 1
}

Write-Host ""
Write-Host "Deploying device management Lambda with DELETE endpoint..." -ForegroundColor Yellow

# Navigate to infrastructure directory
Push-Location infrastructure/cdk

try {
    # Deploy the device management stack
    Write-Host ""
    Write-Host "Running CDK deploy for device management..." -ForegroundColor Cyan
    cdk deploy AquaChain-Devices-dev --require-approval never
    
    if ($LASTEXITCODE -eq 0) {
        Write-Host ""
        Write-Host "========================================" -ForegroundColor Green
        Write-Host "✓ Deployment Successful!" -ForegroundColor Green
        Write-Host "========================================" -ForegroundColor Green
        Write-Host ""
        Write-Host "Changes deployed:" -ForegroundColor Cyan
        Write-Host "  • Added DELETE /api/devices/{deviceId} endpoint" -ForegroundColor White
        Write-Host "  • Ownership verification before deletion" -ForegroundColor White
        Write-Host "  • Audit logging for device deletions" -ForegroundColor White
        Write-Host "  • Cache invalidation on delete" -ForegroundColor White
        Write-Host "  • Proper CORS headers for DELETE method" -ForegroundColor White
        Write-Host ""
        Write-Host "You can now delete devices from the frontend!" -ForegroundColor Green
        Write-Host ""
    } else {
        Write-Host ""
        Write-Host "ERROR: Deployment failed" -ForegroundColor Red
        Write-Host "Check the error messages above for details" -ForegroundColor Red
        exit 1
    }
} finally {
    Pop-Location
}

Write-Host ""
Write-Host "Testing the DELETE endpoint..." -ForegroundColor Yellow
Write-Host ""
Write-Host "To test manually:" -ForegroundColor Cyan
Write-Host "1. Go to your dashboard" -ForegroundColor White
Write-Host "2. Navigate to 'My Devices'" -ForegroundColor White
Write-Host "3. Try deleting a demo device" -ForegroundColor White
Write-Host "4. The device should be removed successfully" -ForegroundColor White
Write-Host ""
