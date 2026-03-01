#!/usr/bin/env pwsh
# Ultra Minimal Mode - Absolute bare minimum to make credits last
# Target: <$35/month (~$1.15/day) to last until April 30

param(
    [switch]$DryRun
)

$ErrorActionPreference = "Stop"

Write-Host "========================================" -ForegroundColor Red
Write-Host "  ULTRA MINIMAL COST MODE" -ForegroundColor Red
Write-Host "========================================" -ForegroundColor Red
Write-Host ""
Write-Host "WARNING: This will significantly reduce functionality!" -ForegroundColor Red
Write-Host ""

Write-Host "Current Status:" -ForegroundColor Yellow
Write-Host "  Credits: `$69.86 | Days: 61 | Need: `$1.15/day" -ForegroundColor White
Write-Host ""
Write-Host "This will destroy:" -ForegroundColor Red
Write-Host "  - ElastiCache Redis (~`$12/month)" -ForegroundColor White
Write-Host "  - Global Monitoring Dashboard (~`$9/month)" -ForegroundColor White
Write-Host "  - VPC Stack - forces Lambda to public mode (~`$15/month)" -ForegroundColor White
Write-Host "  - IoT Core stack (~`$3-5/month)" -ForegroundColor White
Write-Host "  - Most Lambda functions except core auth/API (~`$5-10/month)" -ForegroundColor White
Write-Host ""
Write-Host "Total savings: ~`$44-51/month" -ForegroundColor Green
Write-Host "New cost: ~`$25-35/month (~`$0.85-1.15/day)" -ForegroundColor Green
Write-Host ""
Write-Host "What will still work:" -ForegroundColor Yellow
Write-Host "  - User authentication (Cognito)" -ForegroundColor White
Write-Host "  - Basic API Gateway" -ForegroundColor White
Write-Host "  - DynamoDB data storage" -ForegroundColor White
Write-Host "  - S3 storage" -ForegroundColor White
Write-Host "  - Core Lambda functions (auth, user management)" -ForegroundColor White
Write-Host ""
Write-Host "What will NOT work:" -ForegroundColor Red
Write-Host "  - IoT device connectivity" -ForegroundColor White
Write-Host "  - Real-time monitoring dashboard" -ForegroundColor White
Write-Host "  - Redis caching (slower performance)" -ForegroundColor White
Write-Host "  - Advanced Lambda functions" -ForegroundColor White
Write-Host ""

if (-not $DryRun) {
    Write-Host "Type 'DESTROY' to proceed with ultra minimal mode: " -ForegroundColor Red -NoNewline
    $confirm = Read-Host
    if ($confirm -ne "DESTROY") {
        Write-Host "Cancelled." -ForegroundColor Yellow
        exit 0
    }
}

Write-Host ""
Write-Host "Proceeding with destruction..." -ForegroundColor Red
Write-Host ""

cd infrastructure/cdk

# Destroy in dependency order
$stacks = @(
    "AquaChain-GlobalMonitoring-dev",
    "AquaChain-IoTSecurity-dev",
    "AquaChain-Cache-dev",
    "AquaChain-VPC-dev"
)

$i = 1
foreach ($stack in $stacks) {
    Write-Host "[$i/$($stacks.Count)] Destroying $stack..." -ForegroundColor Yellow
    if (-not $DryRun) {
        cdk destroy $stack --force
    } else {
        Write-Host "  [DRY RUN] Would destroy $stack" -ForegroundColor Gray
    }
    $i++
}

cd ../..

Write-Host ""
Write-Host "========================================" -ForegroundColor Green
Write-Host "Ultra Minimal Mode Active" -ForegroundColor Green
Write-Host "========================================" -ForegroundColor Green
Write-Host ""
Write-Host "Estimated cost: ~`$25-35/month" -ForegroundColor Green
Write-Host "Your `$69.86 should now last until April 30!" -ForegroundColor Green
Write-Host ""
Write-Host "IMPORTANT: Use local development mode for testing" -ForegroundColor Yellow
Write-Host "  cd frontend && npm start" -ForegroundColor White
Write-Host ""
