# Check current AWS costs and forecast
$ErrorActionPreference = "Stop"

Write-Host "Checking AWS Costs..." -ForegroundColor Cyan
Write-Host ""

# Get current month costs
$startDate = (Get-Date -Day 1).ToString("yyyy-MM-dd")
$endDate = (Get-Date).ToString("yyyy-MM-dd")

Write-Host "Current month costs ($(Get-Date -Format 'MMMM yyyy')):" -ForegroundColor Yellow

aws ce get-cost-and-usage `
    --time-period Start=$startDate,End=$endDate `
    --granularity MONTHLY `
    --metrics "UnblendedCost" `
    --query "ResultsByTime[0].Total.UnblendedCost" `
    --output table

Write-Host ""
Write-Host "Cost by service:" -ForegroundColor Yellow

aws ce get-cost-and-usage `
    --time-period Start=$startDate,End=$endDate `
    --granularity MONTHLY `
    --metrics "UnblendedCost" `
    --group-by Type=DIMENSION,Key=SERVICE `
    --query "ResultsByTime[0].Groups[?Metrics.UnblendedCost.Amount > '0.01'].[Keys[0], Metrics.UnblendedCost.Amount]" `
    --output table

Write-Host ""
Write-Host "Forecast for next 30 days:" -ForegroundColor Yellow

$forecastStart = (Get-Date).ToString("yyyy-MM-dd")
$forecastEnd = (Get-Date).AddDays(30).ToString("yyyy-MM-dd")

aws ce get-cost-forecast `
    --time-period Start=$forecastStart,End=$forecastEnd `
    --metric UNBLENDED_COST `
    --granularity MONTHLY `
    --query "Total" `
    --output table

Write-Host ""
Write-Host "💡 Tips to reduce costs:" -ForegroundColor Cyan
Write-Host "  - Delete unused CloudWatch log groups" -ForegroundColor White
Write-Host "  - Reduce DynamoDB provisioned capacity if not needed" -ForegroundColor White
Write-Host "  - Clean up old S3 objects" -ForegroundColor White
Write-Host "  - Stop unused Lambda functions" -ForegroundColor White
