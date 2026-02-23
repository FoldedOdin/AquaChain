# Tail Lambda CloudWatch Logs in Real-Time
# This script shows live logs from the user management Lambda

$ErrorActionPreference = "Stop"

$FUNCTION_NAME = "aquachain-function-user-management-dev"
$REGION = "ap-south-1"
$LOG_GROUP = "/aws/lambda/$FUNCTION_NAME"

Write-Host "========================================" -ForegroundColor Cyan
Write-Host "Tailing Lambda Logs" -ForegroundColor Cyan
Write-Host "========================================" -ForegroundColor Cyan
Write-Host ""
Write-Host "Function: $FUNCTION_NAME" -ForegroundColor White
Write-Host "Region: $REGION" -ForegroundColor White
Write-Host ""
Write-Host "Press Ctrl+C to stop" -ForegroundColor Yellow
Write-Host ""
Write-Host "Logs:" -ForegroundColor Cyan
Write-Host "----------------------------------------" -ForegroundColor Gray

try {
    # Use AWS CLI to tail logs
    aws logs tail $LOG_GROUP --follow --region $REGION --format short
} catch {
    Write-Host ""
    Write-Host "❌ Failed to tail logs" -ForegroundColor Red
    Write-Host $_.Exception.Message -ForegroundColor Red
    Write-Host ""
    Write-Host "Make sure:" -ForegroundColor Yellow
    Write-Host "1. AWS CLI is installed and configured" -ForegroundColor White
    Write-Host "2. You have permissions to read CloudWatch logs" -ForegroundColor White
    Write-Host "3. The Lambda function exists in the specified region" -ForegroundColor White
}
