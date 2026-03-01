# Update Device Management Lambda Function
# Quick update without full CDK deployment

Write-Host "========================================" -ForegroundColor Cyan
Write-Host "Update Device Management Lambda" -ForegroundColor Cyan
Write-Host "========================================" -ForegroundColor Cyan
Write-Host ""

$FUNCTION_NAME = "AquaChain-Compute-dev-DeviceManagementFunction"
$LAMBDA_DIR = "lambda/device_management"

Write-Host "Creating deployment package..." -ForegroundColor Yellow

# Create temp directory
$TEMP_DIR = "temp_lambda_package"
if (Test-Path $TEMP_DIR) {
    Remove-Item -Recurse -Force $TEMP_DIR
}
New-Item -ItemType Directory -Path $TEMP_DIR | Out-Null

# Copy Lambda files
Copy-Item "$LAMBDA_DIR/handler.py" -Destination "$TEMP_DIR/"
Copy-Item "$LAMBDA_DIR/requirements.txt" -Destination "$TEMP_DIR/"

# Copy shared utilities
Copy-Item "lambda/shared" -Destination "$TEMP_DIR/" -Recurse

# Create ZIP
Write-Host "Creating ZIP file..." -ForegroundColor Yellow
Push-Location $TEMP_DIR
Compress-Archive -Path * -DestinationPath "../function.zip" -Force
Pop-Location

# Update Lambda function
Write-Host "Updating Lambda function..." -ForegroundColor Yellow
aws lambda update-function-code `
    --function-name $FUNCTION_NAME `
    --zip-file fileb://function.zip

if ($LASTEXITCODE -eq 0) {
    Write-Host ""
    Write-Host "========================================" -ForegroundColor Green
    Write-Host "✓ Lambda Updated Successfully!" -ForegroundColor Green
    Write-Host "========================================" -ForegroundColor Green
    Write-Host ""
    Write-Host "DELETE endpoint is now available!" -ForegroundColor Green
    Write-Host "You can now delete devices from the dashboard." -ForegroundColor White
} else {
    Write-Host ""
    Write-Host "ERROR: Failed to update Lambda function" -ForegroundColor Red
}

# Cleanup
Remove-Item -Recurse -Force $TEMP_DIR
Remove-Item function.zip

Write-Host ""
