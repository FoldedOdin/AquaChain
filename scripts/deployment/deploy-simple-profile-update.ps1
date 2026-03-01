# Deploy simple, reliable profile update Lambda function
# This replaces the complex handler with a minimal, working version

Write-Host "Deploying simple profile update Lambda..." -ForegroundColor Cyan

# Package the Lambda function
Write-Host "`nPackaging Lambda function..." -ForegroundColor Yellow
$tempDir = "temp-simple-lambda"
New-Item -ItemType Directory -Force -Path $tempDir | Out-Null

# Copy the simple handler
Copy-Item "lambda/user_management/profile_update_simple.py" -Destination "$tempDir/lambda_function.py" -Force

# Create deployment package
Compress-Archive -Path "$tempDir/*" -DestinationPath "profile-update-simple.zip" -Force
Remove-Item -Recurse -Force $tempDir

Write-Host "Package created: profile-update-simple.zip" -ForegroundColor Green

# Update Lambda function code
Write-Host "`nUpdating Lambda function code..." -ForegroundColor Yellow
aws lambda update-function-code `
    --function-name aquachain-function-user-management-dev `
    --zip-file fileb://profile-update-simple.zip `
    --region ap-south-1

if ($LASTEXITCODE -eq 0) {
    Write-Host "`nLambda function updated successfully!" -ForegroundColor Green
    
    # Update handler configuration
    Write-Host "`nUpdating handler configuration..." -ForegroundColor Yellow
    aws lambda update-function-configuration `
        --function-name aquachain-function-user-management-dev `
        --handler lambda_function.lambda_handler `
        --region ap-south-1 | Out-Null
    
    # Wait for update to complete
    Write-Host "Waiting for function update to complete..." -ForegroundColor Yellow
    Start-Sleep -Seconds 5
    
    # Verify the update
    $status = aws lambda get-function `
        --function-name aquachain-function-user-management-dev `
        --region ap-south-1 `
        --query "Configuration.LastUpdateStatus" `
        --output text
    
    Write-Host "Function status: $status" -ForegroundColor $(if ($status -eq "Successful") { "Green" } else { "Yellow" })
    
    Write-Host "`n✓ Simple profile update endpoint deployed!" -ForegroundColor Green
    Write-Host "  - Minimal dependencies" -ForegroundColor Gray
    Write-Host "  - Clear error handling" -ForegroundColor Gray
    Write-Host "  - JWT token support" -ForegroundColor Gray
    
} else {
    Write-Host "`nFailed to update Lambda function" -ForegroundColor Red
    exit 1
}

# Cleanup
Remove-Item "profile-update-simple.zip" -ErrorAction SilentlyContinue

Write-Host "`nDeployment complete! Test the profile update from the frontend." -ForegroundColor Cyan
