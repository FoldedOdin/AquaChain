#!/usr/bin/env pwsh
# Minimal Cost Mode - Reduce AWS costs to bare minimum
# Target: <$40/month to make credits last until April 30

param(
    [switch]$DryRun,
    [switch]$Restore
)

$ErrorActionPreference = "Stop"

Write-Host "========================================" -ForegroundColor Cyan
Write-Host "  AquaChain - Minimal Cost Mode" -ForegroundColor Cyan
Write-Host "========================================" -ForegroundColor Cyan
Write-Host ""

if ($Restore) {
    Write-Host "Restoring full infrastructure..." -ForegroundColor Yellow
    Write-Host ""
    
    # Restore ElastiCache
    Write-Host "[1/3] Restoring ElastiCache Redis..." -ForegroundColor Green
    if (-not $DryRun) {
        cd infrastructure/cdk
        cdk deploy AquaChain-Cache-dev --require-approval never
        cd ../..
    }
    
    # Restore Global Monitoring
    Write-Host "[2/3] Restoring Global Monitoring Dashboard..." -ForegroundColor Green
    if (-not $DryRun) {
        cd infrastructure/cdk
        cdk deploy AquaChain-GlobalMonitoring-dev --require-approval never
        cd ../..
    }
    
    # Restore CloudWatch log retention
    Write-Host "[3/3] Restoring CloudWatch log retention to 7 days..." -ForegroundColor Green
    if (-not $DryRun) {
        aws logs describe-log-groups --region ap-south-1 | ConvertFrom-Json | ForEach-Object { $_.logGroups } | ForEach-Object {
            aws logs put-retention-policy --log-group-name $_.logGroupName --retention-in-days 7 --region ap-south-1
        }
    }
    
    Write-Host ""
    Write-Host "Restoration complete!" -ForegroundColor Green
    Write-Host "Estimated monthly cost: ~$70-100" -ForegroundColor Yellow
    exit 0
}

Write-Host "Current Status:" -ForegroundColor Yellow
Write-Host "  Credits remaining: `$69.86" -ForegroundColor White
Write-Host "  Days remaining: 61 days (until April 30)" -ForegroundColor White
Write-Host "  Current burn rate: ~`$2.98/day" -ForegroundColor Red
Write-Host "  Target burn rate: ~`$1.15/day" -ForegroundColor Green
Write-Host ""
Write-Host "This script will:" -ForegroundColor Yellow
Write-Host "  1. Destroy ElastiCache Redis (saves ~`$12/month)" -ForegroundColor White
Write-Host "  2. Destroy Global Monitoring Dashboard (saves ~`$9/month)" -ForegroundColor White
Write-Host "  3. Reduce CloudWatch log retention to 1 day (saves ~`$3-5/month)" -ForegroundColor White
Write-Host "  4. Keep core services: Lambda, DynamoDB, API Gateway, Cognito" -ForegroundColor White
Write-Host ""
Write-Host "Estimated savings: ~`$24-26/month" -ForegroundColor Green
Write-Host "New monthly cost: ~`$45-55/month (~`$1.50/day)" -ForegroundColor Green
Write-Host ""

if (-not $DryRun) {
    $confirm = Read-Host "Type 'REDUCE' to proceed"
    if ($confirm -ne "REDUCE") {
        Write-Host "Cancelled." -ForegroundColor Yellow
        exit 0
    }
}

Write-Host ""
Write-Host "========================================" -ForegroundColor Cyan
Write-Host "Step 1: Backup Current Configuration" -ForegroundColor Cyan
Write-Host "========================================" -ForegroundColor Cyan
Write-Host ""

$backupDir = "backups/minimal-cost-mode-$(Get-Date -Format 'yyyyMMdd-HHmmss')"
if (-not $DryRun) {
    New-Item -ItemType Directory -Path $backupDir -Force | Out-Null
    
    # Backup ElastiCache config
    aws elasticache describe-cache-clusters --region ap-south-1 | Out-File "$backupDir/elasticache-config.json"
    
    # Backup CloudWatch dashboard config
    aws cloudwatch list-dashboards --region ap-south-1 | Out-File "$backupDir/cloudwatch-dashboards.json"
    
    Write-Host "Backup saved to: $backupDir" -ForegroundColor Green
}

Write-Host ""
Write-Host "========================================" -ForegroundColor Cyan
Write-Host "Step 2: Destroy Non-Essential Services" -ForegroundColor Cyan
Write-Host "========================================" -ForegroundColor Cyan
Write-Host ""

# Destroy ElastiCache
Write-Host "[1/2] Destroying ElastiCache Redis..." -ForegroundColor Yellow
if (-not $DryRun) {
    cd infrastructure/cdk
    cdk destroy AquaChain-Cache-dev --force
    cd ../..
    Write-Host "  ElastiCache destroyed. Savings: ~`$12/month" -ForegroundColor Green
} else {
    Write-Host "  [DRY RUN] Would destroy ElastiCache" -ForegroundColor Gray
}

# Destroy Global Monitoring Dashboard
Write-Host "[2/2] Destroying Global Monitoring Dashboard..." -ForegroundColor Yellow
if (-not $DryRun) {
    cd infrastructure/cdk
    cdk destroy AquaChain-GlobalMonitoring-dev --force
    cd ../..
    Write-Host "  Dashboard destroyed. Savings: ~`$9/month" -ForegroundColor Green
} else {
    Write-Host "  [DRY RUN] Would destroy Global Monitoring Dashboard" -ForegroundColor Gray
}

Write-Host ""
Write-Host "========================================" -ForegroundColor Cyan
Write-Host "Step 3: Optimize CloudWatch Logs" -ForegroundColor Cyan
Write-Host "========================================" -ForegroundColor Cyan
Write-Host ""

Write-Host "Reducing log retention to 1 day..." -ForegroundColor Yellow
if (-not $DryRun) {
    $logGroups = aws logs describe-log-groups --region ap-south-1 | ConvertFrom-Json
    $count = 0
    foreach ($logGroup in $logGroups.logGroups) {
        aws logs put-retention-policy --log-group-name $logGroup.logGroupName --retention-in-days 1 --region ap-south-1
        $count++
    }
    Write-Host "  Updated $count log groups. Savings: ~`$3-5/month" -ForegroundColor Green
} else {
    Write-Host "  [DRY RUN] Would reduce log retention to 1 day" -ForegroundColor Gray
}

Write-Host ""
Write-Host "========================================" -ForegroundColor Cyan
Write-Host "Summary" -ForegroundColor Cyan
Write-Host "========================================" -ForegroundColor Cyan
Write-Host ""
Write-Host "Services Removed:" -ForegroundColor Yellow
Write-Host "  - ElastiCache Redis" -ForegroundColor White
Write-Host "  - Global Monitoring Dashboard" -ForegroundColor White
Write-Host "  - Extended CloudWatch log retention" -ForegroundColor White
Write-Host ""
Write-Host "Services Retained:" -ForegroundColor Green
Write-Host "  - Lambda functions (core functionality)" -ForegroundColor White
Write-Host "  - DynamoDB tables (data storage)" -ForegroundColor White
Write-Host "  - API Gateway (REST + WebSocket)" -ForegroundColor White
Write-Host "  - Cognito (authentication)" -ForegroundColor White
Write-Host "  - VPC with optimized NAT Gateway (1 instead of 2)" -ForegroundColor White
Write-Host "  - S3 buckets (data lake, ML models)" -ForegroundColor White
Write-Host ""
Write-Host "Cost Impact:" -ForegroundColor Yellow
Write-Host "  Previous: ~`$70-100/month (~`$2.50/day)" -ForegroundColor Red
Write-Host "  New: ~`$45-55/month (~`$1.50/day)" -ForegroundColor Green
Write-Host "  Savings: ~`$24-26/month" -ForegroundColor Green
Write-Host ""
Write-Host "Credits Projection:" -ForegroundColor Yellow
Write-Host "  Credits remaining: `$69.86" -ForegroundColor White
Write-Host "  Days to April 30: 61 days" -ForegroundColor White
Write-Host "  At `$1.50/day: `$91.50 needed (SHORT by ~`$22)" -ForegroundColor Red
Write-Host ""
Write-Host "Additional Recommendations:" -ForegroundColor Yellow
Write-Host "  1. Stop IoT simulator when not testing" -ForegroundColor White
Write-Host "  2. Minimize Lambda invocations during development" -ForegroundColor White
Write-Host "  3. Use local development mode when possible" -ForegroundColor White
Write-Host "  4. Consider pausing development for 1-2 weeks if needed" -ForegroundColor White
Write-Host ""
Write-Host "To restore full infrastructure:" -ForegroundColor Cyan
Write-Host "  .\scripts\deployment\minimal-cost-mode.ps1 -Restore" -ForegroundColor White
Write-Host ""
Write-Host "========================================" -ForegroundColor Cyan
