# Deploy Updated Admin Service Lambda
# Adds support for /api/devices path (in addition to /api/admin/devices)

$functionName = "aquachain-function-admin-service-dev"
$region = "ap-south-1"

Write-Host "========================================"
Write-Host "Deploying Admin Service Lambda"
Write-Host "========================================"
Write-Host ""

# Navigate to admin service directory
$originalPath = Get-Location
Set-Location "$PSScriptRoot\..\..\lambda\admin_service"

Write-Host "Creating deployment package..."

# Create deployment package
if (Test-Path "function.zip") {
    Remove-Item "function.zip" -Force
}

Compress-Archive -Path "handler.py" -DestinationPath "function.zip" -Force

if ($LASTEXITCODE -ne 0 -or !(Test-Path "function.zip")) {
    Write-Host "✗ Failed to create deployment package"
    Set-Location $originalPath
    exit 1
}

Write-Host "✓ Deployment package created"
Write-Host ""

# Update Lambda function
Write-Host "Updating Lambda function..."
aws lambda update-function-code `
    --function-name $functionName `
    --zip-file fileb://function.zip `
    --region $region `
    --output json | Out-Null

if ($LASTEXITCODE -ne 0) {
    Write-Host "✗ Failed to update Lambda function"
    Remove-Item "function.zip" -Force
    Set-Location $originalPath
    exit 1
}

Write-Host "✓ Lambda function update initiated"
Write-Host ""

# Wait for update to complete
Write-Host "Waiting for update to complete..."
aws lambda wait function-updated `
    --function-name $functionName `
    --region $region

if ($LASTEXITCODE -eq 0) {
    Write-Host "✓ Lambda function updated successfully"
} else {
    Write-Host "⚠ Wait command timed out, but update may still succeed"
}

Write-Host ""

# Clean up
Remove-Item "function.zip" -Force
Set-Location $originalPath

Write-Host "========================================"
Write-Host "Deployment Complete!"
Write-Host "========================================"
Write-Host ""
Write-Host "Changes deployed:"
Write-Host "  - Admin service now accepts /api/devices path"
Write-Host "  - Maintains backward compatibility with /api/admin/devices"
Write-Host ""
Write-Host "Test the endpoint:"
Write-Host "  curl -H 'Authorization: Bearer YOUR_TOKEN' \"
Write-Host "    https://vtqjfznspc.execute-api.ap-south-1.amazonaws.com/dev/api/devices"
Write-Host ""
Write-Host "Next steps:"
Write-Host "  1. Fix OPTIONS 500 errors in AWS Console (see FIX_OPTIONS_500_ERROR.md)"
Write-Host "  2. Create HTTP handlers for data processing and alert detection"
Write-Host "  3. Test dashboard"
