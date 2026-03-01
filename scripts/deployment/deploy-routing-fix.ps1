# Deploy routing fix for profile update endpoints
# This fixes the path conflict between /api/profile/update and /api/profile/verify-and-update

Write-Host "========================================" -ForegroundColor Cyan
Write-Host "Deploying Profile Update Routing Fix" -ForegroundColor Cyan
Write-Host "========================================" -ForegroundColor Cyan
Write-Host ""

# Navigate to CDK directory
Set-Location infrastructure/cdk

Write-Host "Deploying AquaChain-Compute-dev stack..." -ForegroundColor Yellow
cdk deploy AquaChain-Compute-dev --exclusively --require-approval never

if ($LASTEXITCODE -eq 0) {
    Write-Host ""
    Write-Host "========================================" -ForegroundColor Green
    Write-Host "Deployment Successful!" -ForegroundColor Green
    Write-Host "========================================" -ForegroundColor Green
    Write-Host ""
    Write-Host "The routing fix has been deployed." -ForegroundColor Green
    Write-Host ""
    Write-Host "Changes:" -ForegroundColor Cyan
    Write-Host "  - Line 945: Changed to exact path match (path == '/api/profile/update')" -ForegroundColor White
    Write-Host "  - This prevents /api/profile/verify-and-update from matching the wrong endpoint" -ForegroundColor White
    Write-Host ""
    Write-Host "Next Steps:" -ForegroundColor Cyan
    Write-Host "  1. Test OTP generation: Edit profile in UI" -ForegroundColor White
    Write-Host "  2. Check email for OTP code" -ForegroundColor White
    Write-Host "  3. Enter OTP and verify profile updates successfully" -ForegroundColor White
    Write-Host "  4. Check CloudWatch logs for 'DEBUG EVENT STRUCTURE' messages" -ForegroundColor White
} else {
    Write-Host ""
    Write-Host "========================================" -ForegroundColor Red
    Write-Host "Deployment Failed!" -ForegroundColor Red
    Write-Host "========================================" -ForegroundColor Red
    Write-Host ""
    Write-Host "Please check the error messages above." -ForegroundColor Red
}

# Return to root directory
Set-Location ../..
