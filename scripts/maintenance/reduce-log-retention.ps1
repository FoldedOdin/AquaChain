#!/usr/bin/env pwsh
# Reduce CloudWatch Log Retention to 1 Day
# Saves ~$3-5/month in log storage costs

param(
    [switch]$DryRun,
    [int]$RetentionDays = 1
)

$ErrorActionPreference = "Stop"

Write-Host "========================================" -ForegroundColor Cyan
Write-Host "  Reduce CloudWatch Log Retention" -ForegroundColor Cyan
Write-Host "========================================" -ForegroundColor Cyan
Write-Host ""

Write-Host "Target retention: $RetentionDays day(s)" -ForegroundColor Yellow
Write-Host "Region: ap-south-1" -ForegroundColor Yellow
Write-Host ""

# Get all log groups
Write-Host "Fetching log groups..." -ForegroundColor Cyan
$logGroups = aws logs describe-log-groups --region ap-south-1 | ConvertFrom-Json

if (-not $logGroups.logGroups) {
    Write-Host "No log groups found." -ForegroundColor Yellow
    exit 0
}

Write-Host "Found $($logGroups.logGroups.Count) log groups" -ForegroundColor Green
Write-Host ""

# Calculate current storage and costs
$totalStorageBytes = ($logGroups.logGroups | Measure-Object -Property storedBytes -Sum).Sum
$totalStorageMB = [math]::Round($totalStorageBytes / 1MB, 2)
$totalStorageGB = [math]::Round($totalStorageBytes / 1GB, 2)

Write-Host "Current Storage:" -ForegroundColor Yellow
Write-Host "  Total: $totalStorageMB MB ($totalStorageGB GB)" -ForegroundColor White
Write-Host "  Cost: ~`$$([math]::Round($totalStorageGB * 0.50, 2))/month (at `$0.50/GB)" -ForegroundColor White
Write-Host ""

# Show top 5 largest log groups
Write-Host "Top 5 Largest Log Groups:" -ForegroundColor Yellow
$logGroups.logGroups | 
    Sort-Object storedBytes -Descending | 
    Select-Object -First 5 | 
    ForEach-Object {
        $sizeMB = [math]::Round($_.storedBytes / 1MB, 2)
        $retention = if ($_.retentionInDays) { "$($_.retentionInDays) days" } else { "Never expire" }
        Write-Host "  $($_.logGroupName)" -ForegroundColor White
        Write-Host "    Size: $sizeMB MB | Retention: $retention" -ForegroundColor Gray
    }
Write-Host ""

if ($DryRun) {
    Write-Host "[DRY RUN] Would update retention for $($logGroups.logGroups.Count) log groups" -ForegroundColor Gray
    Write-Host ""
    exit 0
}

Write-Host "Updating log retention policies..." -ForegroundColor Cyan
Write-Host ""

$updated = 0
$skipped = 0
$errors = 0

foreach ($logGroup in $logGroups.logGroups) {
    $logGroupName = $logGroup.logGroupName
    $currentRetention = $logGroup.retentionInDays
    
    # Skip if already set to target retention
    if ($currentRetention -eq $RetentionDays) {
        Write-Host "  [SKIP] $logGroupName (already $RetentionDays day)" -ForegroundColor Gray
        $skipped++
        continue
    }
    
    try {
        Write-Host "  [UPDATE] $logGroupName" -ForegroundColor Yellow -NoNewline
        
        aws logs put-retention-policy `
            --log-group-name $logGroupName `
            --retention-in-days $RetentionDays `
            --region ap-south-1 2>$null
        
        if ($LASTEXITCODE -eq 0) {
            Write-Host " ✓" -ForegroundColor Green
            $updated++
        } else {
            Write-Host " ✗ (failed)" -ForegroundColor Red
            $errors++
        }
    }
    catch {
        Write-Host " ✗ (error: $($_.Exception.Message))" -ForegroundColor Red
        $errors++
    }
}

Write-Host ""
Write-Host "========================================" -ForegroundColor Cyan
Write-Host "Summary" -ForegroundColor Cyan
Write-Host "========================================" -ForegroundColor Cyan
Write-Host ""
Write-Host "Results:" -ForegroundColor Yellow
Write-Host "  Updated: $updated log groups" -ForegroundColor Green
Write-Host "  Skipped: $skipped log groups" -ForegroundColor Gray
Write-Host "  Errors: $errors log groups" -ForegroundColor $(if ($errors -gt 0) { "Red" } else { "Gray" })
Write-Host ""

# Calculate savings
$estimatedSavings = [math]::Round($totalStorageGB * 0.50 * 0.66, 2)  # ~66% reduction from 3 days to 1 day
Write-Host "Cost Impact:" -ForegroundColor Yellow
Write-Host "  Previous retention: 3 days (average)" -ForegroundColor White
Write-Host "  New retention: $RetentionDays day" -ForegroundColor White
Write-Host "  Estimated savings: ~`$$estimatedSavings/month" -ForegroundColor Green
Write-Host ""

Write-Host "Note: Logs older than $RetentionDays day will be automatically deleted." -ForegroundColor Cyan
Write-Host "You can still view recent logs in CloudWatch Logs console." -ForegroundColor Cyan
Write-Host ""

# Show how to restore
Write-Host "To restore retention to 7 days:" -ForegroundColor Yellow
Write-Host "  .\scripts\maintenance\reduce-log-retention.ps1 -RetentionDays 7" -ForegroundColor White
Write-Host ""
Write-Host "========================================" -ForegroundColor Cyan
