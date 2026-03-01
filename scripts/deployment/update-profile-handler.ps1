# Update user management Lambda function with JWT token decoding fix
# This allows the profile update endpoint to work without a Cognito authorizer

Write-Host "Updating user management Lambda function..." -ForegroundColor Cyan

# Package the Lambda function
Write-Host "`nPackaging Lambda function..." -ForegroundColor Yellow
$tempDir = "temp-lambda-package"
New-Item -ItemType Directory -Force -Path $tempDir | Out-Null

# Copy handler and shared modules
Copy-Item "lambda/user_management/handler.py" -Destination "$tempDir/" -Force
Copy-Item "lambda/shared/*.py" -Destination "$tempDir/" -Force

# Create deployment package
Compress-Archive -Path "$tempDir/*" -DestinationPath "user-management-update.zip" -Force
Remove-Item -Recurse -Force $tempDir

Write-Host "Package created: user-management-update.zip" -ForegroundColor Green

# Update Lambda function code
Write-Host "`nUpdating Lambda function code..." -ForegroundColor Yellow
aws lambda update-function-code `
    --function-name aquachain-function-user-management-dev `
    --zip-file fileb://user-management-update.zip `
    --region ap-south-1

if ($LASTEXITCODE -eq 0) {
    Write-Host "Lambda function updated successfully!" -ForegroundColor Green
    
    # Wait for update to complete
    Write-Host "`nWaiting for function update to complete..." -ForegroundColor Yellow
    Start-Sleep -Seconds 5
    
    # Verify the update
    Write-Host "`nVerifying function status..." -ForegroundColor Yellow
    $status = aws lambda get-function --function-name aquachain-function-user-management-dev --region ap-south-1 --query "Configuration.LastUpdateStatus" --output text
    Write-Host "Function status: $status" -ForegroundColor $(if ($status -eq "Successful") { "Green" } else { "Yellow" })
    
    Write-Host "`n✓ Profile update endpoint should now work!" -ForegroundColor Green
    Write-Host "  The Lambda function can now extract email from JWT tokens" -ForegroundColor Gray
    
} else {
    Write-Host "Failed to update Lambda function" -ForegroundColor Red
    exit 1
}

# Cleanup
Remove-Item "user-management-update.zip" -ErrorAction SilentlyContinue

Write-Host "`nDeployment complete!" -ForegroundColor Cyan
