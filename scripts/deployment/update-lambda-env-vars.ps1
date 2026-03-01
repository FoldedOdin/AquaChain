# Update Lambda Environment Variables for Real Metrics
# This script adds the required environment variables for the lightweight metrics implementation

Write-Host "========================================" -ForegroundColor Cyan
Write-Host "Update Lambda Environment Variables" -ForegroundColor Cyan
Write-Host "========================================" -ForegroundColor Cyan
Write-Host ""

$FUNCTION_NAME = "aquachain-function-admin-service-dev"
$REGION = "ap-south-1"

Write-Host "Step 1: Get current environment variables..." -ForegroundColor Yellow

# Get current environment variables
$currentConfig = aws lambda get-function-configuration `
    --function-name $FUNCTION_NAME `
    --region $REGION `
    --output json | ConvertFrom-Json

if ($LASTEXITCODE -ne 0) {
    Write-Host "  ✗ Failed to get current configuration" -ForegroundColor Red
    exit 1
}

Write-Host "  ✓ Current configuration retrieved" -ForegroundColor Green
Write-Host ""

# Extract current environment variables
$currentVars = $currentConfig.Environment.Variables

# Add new variables (preserve existing ones)
$currentVars | Add-Member -NotePropertyName "API_GATEWAY_ID" -NotePropertyValue "vtqjfznspc" -Force
$currentVars | Add-Member -NotePropertyName "API_STAGE" -NotePropertyValue "dev" -Force
$currentVars | Add-Member -NotePropertyName "ALERTS_TABLE" -NotePropertyValue "AquaChain-Alerts" -Force

Write-Host "Step 2: Update Lambda environment variables..." -ForegroundColor Yellow

# Convert to JSON for AWS CLI
$envVarsJson = $currentVars | ConvertTo-Json -Compress

# Update Lambda configuration
aws lambda update-function-configuration `
    --function-name $FUNCTION_NAME `
    --region $REGION `
    --environment "Variables=$envVarsJson" `
    --output json | Out-Null

if ($LASTEXITCODE -ne 0) {
    Write-Host "  ✗ Failed to update environment variables" -ForegroundColor Red
    exit 1
}

Write-Host "  ✓ Environment variables updated successfully" -ForegroundColor Green
Write-Host ""

Write-Host "Step 3: Verify new configuration..." -ForegroundColor Yellow

# Wait a moment for update to propagate
Start-Sleep -Seconds 2

# Get updated configuration
$updatedConfig = aws lambda get-function-configuration `
    --function-name $FUNCTION_NAME `
    --region $REGION `
    --output json | ConvertFrom-Json

Write-Host ""
Write-Host "Updated Environment Variables:" -ForegroundColor Cyan
Write-Host "  API_GATEWAY_ID: $($updatedConfig.Environment.Variables.API_GATEWAY_ID)" -ForegroundColor White
Write-Host "  API_STAGE: $($updatedConfig.Environment.Variables.API_STAGE)" -ForegroundColor White
Write-Host "  ALERTS_TABLE: $($updatedConfig.Environment.Variables.ALERTS_TABLE)" -ForegroundColor White
Write-Host ""

Write-Host "========================================" -ForegroundColor Green
Write-Host "Environment Variables Updated!" -ForegroundColor Green
Write-Host "========================================" -ForegroundColor Green
Write-Host ""
Write-Host "Next Steps:" -ForegroundColor Yellow
Write-Host "  1. Update IAM role with CloudWatch permissions" -ForegroundColor White
Write-Host "  2. Deploy updated Lambda code" -ForegroundColor White
Write-Host "  3. Test the metrics endpoint" -ForegroundColor White
Write-Host ""
