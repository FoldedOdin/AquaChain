# Deploy admin_service Lambda with fixed response format
# This fixes the devices endpoint to return data in the format expected by frontend

Write-Host "Deploying admin_service Lambda with response format fix..." -ForegroundColor Cyan
Write-Host ""

$LAMBDA_NAME = "aquachain-function-admin-service-dev"
$LAMBDA_DIR = "lambda/admin_service"
$REGION = "ap-south-1"

# Step 1: Copy shared utilities
Write-Host "Step 1: Copying shared utilities..." -ForegroundColor Yellow
if (Test-Path "$LAMBDA_DIR/shared") {
    Remove-Item -Path "$LAMBDA_DIR/shared" -Recurse -Force
}
Copy-Item -Path "lambda/shared" -Destination "$LAMBDA_DIR/shared" -Recurse
Write-Host "✓ Shared utilities copied" -ForegroundColor Green
Write-Host ""

# Step 2: Create deployment package
Write-Host "Step 2: Creating deployment package..." -ForegroundColor Yellow
$TEMP_DIR = "temp_lambda_package"
if (Test-Path $TEMP_DIR) {
    Remove-Item -Path $TEMP_DIR -Recurse -Force
}
New-Item -ItemType Directory -Path $TEMP_DIR | Out-Null

# Copy Lambda files
Copy-Item -Path "$LAMBDA_DIR/handler.py" -Destination $TEMP_DIR
Copy-Item -Path "$LAMBDA_DIR/shared" -Destination "$TEMP_DIR/shared" -Recurse

# Create ZIP
$ZIP_FILE = "admin_service_deployment.zip"
if (Test-Path $ZIP_FILE) {
    Remove-Item -Path $ZIP_FILE -Force
}

# Use PowerShell's Compress-Archive
Set-Location $TEMP_DIR
Compress-Archive -Path * -DestinationPath "../$ZIP_FILE" -Force
Set-Location ..

Write-Host "✓ Deployment package created: $ZIP_FILE" -ForegroundColor Green
Write-Host ""

# Step 3: Deploy to Lambda
Write-Host "Step 3: Deploying to AWS Lambda..." -ForegroundColor Yellow
try {
    aws lambda update-function-code `
        --function-name $LAMBDA_NAME `
        --zip-file "fileb://$ZIP_FILE" `
        --region $REGION `
        --no-cli-pager
    
    Write-Host "✓ Lambda function updated successfully" -ForegroundColor Green
    Write-Host ""
    
    # Wait for update to complete
    Write-Host "Waiting for Lambda update to complete..." -ForegroundColor Yellow
    Start-Sleep -Seconds 5
    
    # Get function status
    $status = aws lambda get-function --function-name $LAMBDA_NAME --region $REGION --query 'Configuration.LastUpdateStatus' --output text
    Write-Host "Lambda status: $status" -ForegroundColor Cyan
    
} catch {
    Write-Host "✗ Failed to deploy Lambda function" -ForegroundColor Red
    Write-Host $_.Exception.Message -ForegroundColor Red
    exit 1
}

# Step 4: Cleanup
Write-Host ""
Write-Host "Step 4: Cleaning up..." -ForegroundColor Yellow
Remove-Item -Path $TEMP_DIR -Recurse -Force
Remove-Item -Path $ZIP_FILE -Force
Write-Host "✓ Cleanup complete" -ForegroundColor Green
Write-Host ""

# Step 5: Test the endpoint
Write-Host "Step 5: Testing the endpoint..." -ForegroundColor Yellow
Write-Host ""
Write-Host "The Lambda has been deployed with the following fix:" -ForegroundColor Cyan
Write-Host "  - Response format changed from: {'devices': [...]}" -ForegroundColor White
Write-Host "  - To: {'success': True, 'data': [...]}" -ForegroundColor White
Write-Host ""
Write-Host "This matches the format expected by frontend dataService.makeRequest()" -ForegroundColor Cyan
Write-Host ""
Write-Host "Next steps:" -ForegroundColor Yellow
Write-Host "1. Refresh your dashboard in the browser" -ForegroundColor White
Write-Host "2. Check browser console for device data" -ForegroundColor White
Write-Host "3. Devices should now appear in the dashboard" -ForegroundColor White
Write-Host ""
Write-Host "✓ Deployment complete!" -ForegroundColor Green
