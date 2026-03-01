# Complete Real-Time Metrics Deployment
# This script deploys the entire real-time metrics feature

Write-Host ""
Write-Host "╔════════════════════════════════════════════════════════════╗" -ForegroundColor Cyan
Write-Host "║                                                            ║" -ForegroundColor Cyan
Write-Host "║     AquaChain Real-Time Metrics Deployment                ║" -ForegroundColor Cyan
Write-Host "║                                                            ║" -ForegroundColor Cyan
Write-Host "╚════════════════════════════════════════════════════════════╝" -ForegroundColor Cyan
Write-Host ""

$ErrorActionPreference = "Stop"

# Step 1: Attach IAM permissions
Write-Host "═══════════════════════════════════════════════════════════" -ForegroundColor Yellow
Write-Host "STEP 1: Attaching IAM Permissions" -ForegroundColor Yellow
Write-Host "═══════════════════════════════════════════════════════════" -ForegroundColor Yellow
Write-Host ""

& ".\scripts\deployment\attach-metrics-policy.ps1"

if ($LASTEXITCODE -ne 0) {
    Write-Host ""
    Write-Host "✗ Failed to attach IAM permissions" -ForegroundColor Red
    exit 1
}

Write-Host ""
Write-Host "Press any key to continue to Lambda deployment..." -ForegroundColor Yellow
$null = $Host.UI.RawUI.ReadKey("NoEcho,IncludeKeyDown")
Write-Host ""

# Step 2: Deploy Lambda function
Write-Host "═══════════════════════════════════════════════════════════" -ForegroundColor Yellow
Write-Host "STEP 2: Deploying Lambda Function" -ForegroundColor Yellow
Write-Host "═══════════════════════════════════════════════════════════" -ForegroundColor Yellow
Write-Host ""

& ".\scripts\deployment\deploy-system-metrics.ps1"

if ($LASTEXITCODE -ne 0) {
    Write-Host ""
    Write-Host "✗ Failed to deploy Lambda function" -ForegroundColor Red
    exit 1
}

Write-Host ""
Write-Host "═══════════════════════════════════════════════════════════" -ForegroundColor Green
Write-Host "✓ DEPLOYMENT COMPLETE!" -ForegroundColor Green
Write-Host "═══════════════════════════════════════════════════════════" -ForegroundColor Green
Write-Host ""

Write-Host "Summary of Changes:" -ForegroundColor Cyan
Write-Host ""
Write-Host "Backend:" -ForegroundColor Yellow
Write-Host "  ✓ Lambda function updated with metrics endpoint" -ForegroundColor Green
Write-Host "  ✓ IAM permissions added for Cognito and CloudWatch" -ForegroundColor Green
Write-Host "  ✓ Environment variables configured" -ForegroundColor Green
Write-Host ""
Write-Host "Frontend:" -ForegroundColor Yellow
Write-Host "  ✓ System metrics service created" -ForegroundColor Green
Write-Host "  ✓ Admin dashboard updated to fetch real-time data" -ForegroundColor Green
Write-Host "  ✓ Auto-refresh every 30 seconds enabled" -ForegroundColor Green
Write-Host ""
Write-Host "Metrics Available:" -ForegroundColor Yellow
Write-Host "  • Total Users (from Cognito User Pool)" -ForegroundColor White
Write-Host "  • API Success Rate (from CloudWatch)" -ForegroundColor White
Write-Host "  • System Uptime (from CloudWatch)" -ForegroundColor White
Write-Host ""
Write-Host "API Endpoint:" -ForegroundColor Yellow
Write-Host "  GET /api/admin/system/metrics" -ForegroundColor White
Write-Host "  https://vtqjfznspc.execute-api.ap-south-1.amazonaws.com/dev/api/admin/system/metrics" -ForegroundColor Gray
Write-Host ""
Write-Host "Testing:" -ForegroundColor Yellow
Write-Host "  1. Log in to the admin dashboard" -ForegroundColor White
Write-Host "  2. Check the metrics cards at the top" -ForegroundColor White
Write-Host "  3. Metrics will update every 30 seconds" -ForegroundColor White
Write-Host ""
Write-Host "Troubleshooting:" -ForegroundColor Yellow
Write-Host "  • Check CloudWatch Logs: /aws/lambda/aquachain-admin-service-dev" -ForegroundColor White
Write-Host "  • Verify IAM permissions are attached" -ForegroundColor White
Write-Host "  • Ensure User Pool ID is correct in environment variables" -ForegroundColor White
Write-Host ""
Write-Host "═══════════════════════════════════════════════════════════" -ForegroundColor Cyan
Write-Host ""
