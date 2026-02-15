# Deploy Minimal Working Infrastructure
# Only deploys stacks that are known to work with AWS Educate/limited accounts

Write-Host "=== AquaChain Minimal Deployment ===" -ForegroundColor Cyan
Write-Host ""
Write-Host "This script deploys only the core stacks needed for the application." -ForegroundColor Yellow
Write-Host "Skipping stacks that require premium AWS services." -ForegroundColor Yellow
Write-Host ""

$stacks = @(
    "AquaChain-Security-dev",
    "AquaChain-Core-dev"
)

Write-Host "Deploying stacks:" -ForegroundColor Cyan
$stacks | ForEach-Object {
    Write-Host "  - $_" -ForegroundColor White
}
Write-Host ""

$stackList = $stacks -join " "

Push-Location infrastructure/cdk

Write-Host "Starting deployment..." -ForegroundColor Yellow
cdk deploy $stackList --require-approval never

if ($LASTEXITCODE -eq 0) {
    Write-Host ""
    Write-Host "✓ Deployment successful!" -ForegroundColor Green
    Write-Host ""
    Write-Host "Note: Some stacks were skipped due to AWS account limitations." -ForegroundColor Yellow
    Write-Host "Your application may have limited functionality." -ForegroundColor Yellow
} else {
    Write-Host ""
    Write-Host "✗ Deployment failed" -ForegroundColor Red
}

Pop-Location
