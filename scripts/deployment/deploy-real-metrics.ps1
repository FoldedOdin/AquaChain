# Deploy Real Metrics Implementation
# This script performs all steps to deploy the lightweight real metrics solution

Write-Host "========================================" -ForegroundColor Cyan
Write-Host "Deploy Real Metrics Implementation" -ForegroundColor Cyan
Write-Host "========================================" -ForegroundColor Cyan
Write-Host ""

$FUNCTION_NAME = "aquachain-function-admin-service-dev"
$REGION = "ap-south-1"
$LAMBDA_DIR = "..\..\lambda\admin_service"

# Step 1: Update environment variables
Write-Host "Step 1: Update Lambda environment variables..." -ForegroundColor Yellow
Write-Host ""

& "$PSScriptRoot\update-lambda-env-vars.ps1"

if ($LASTEXITCODE -ne 0) {
    Write-Host "  ✗ Failed to update environment variables" -ForegroundColor Red
    exit 1
}

Write-Host ""

# Step 2: Add CloudWatch permissions
Write-Host "Step 2: Add CloudWatch permissions to Lambda role..." -ForegroundColor Yellow
Write-Host ""

& "$PSScriptRoot\add-cloudwatch-permissions.ps1"

if ($LASTEXITCODE -ne 0) {
    Write-Host "  ✗ Failed to add CloudWatch permissions" -ForegroundColor Red
    exit 1
}

Write-Host ""

# Step 3: Deploy Lambda code
Write-Host "Step 3: Deploy updated Lambda code..." -ForegroundColor Yellow
Write-Host ""

# Check if Lambda directory exists
if (-not (Test-Path $LAMBDA_DIR)) {
    Write-Host "  ✗ Lambda directory not found: $LAMBDA_DIR" -ForegroundColor Red
    exit 1
}

# Navigate to Lambda directory
Push-Location $LAMBDA_DIR

try {
    # Create deployment package
    Write-Host "  Creating deployment package..." -ForegroundColor Gray
    
    # Remove old zip if exists
    if (Test-Path "function.zip") {
        Remove-Item "function.zip" -Force
    }
    
    # Create zip file (exclude tests and cache)
    $filesToZip = Get-ChildItem -Path . -Exclude "function.zip","__pycache__","*.pyc",".pytest_cache","tests"
    Compress-Archive -Path $filesToZip -DestinationPath "function.zip" -Force
    
    Write-Host "  ✓ Deployment package created" -ForegroundColor Green
    Write-Host ""
    
    # Upload to Lambda
    Write-Host "  Uploading to Lambda..." -ForegroundColor Gray
    
    aws lambda update-function-code `
        --function-name $FUNCTION_NAME `
        --zip-file fileb://function.zip `
        --region $REGION `
        --output json | Out-Null
    
    if ($LASTEXITCODE -ne 0) {
        Write-Host "  ✗ Failed to upload Lambda code" -ForegroundColor Red
        exit 1
    }
    
    Write-Host "  ✓ Lambda code deployed" -ForegroundColor Green
    Write-Host ""
    
    # Wait for update to complete
    Write-Host "  Waiting for Lambda update to complete..." -ForegroundColor Gray
    Start-Sleep -Seconds 5
    
    Write-Host "  ✓ Lambda update complete" -ForegroundColor Green
    
} finally {
    # Return to original directory
    Pop-Location
}

Write-Host ""

# Step 4: Test the endpoint
Write-Host "Step 4: Test metrics endpoint..." -ForegroundColor Yellow
Write-Host ""

$API_ENDPOINT = "https://vtqjfznspc.execute-api.ap-south-1.amazonaws.com/dev/api/admin/system/metrics"

Write-Host "  Endpoint: $API_ENDPOINT" -ForegroundColor Gray
Write-Host ""
Write-Host "  Note: You need an admin JWT token to test this endpoint." -ForegroundColor Yellow
Write-Host "  Use the following command with your token:" -ForegroundColor Yellow
Write-Host ""
Write-Host "  curl -X GET $API_ENDPOINT ``" -ForegroundColor White
Write-Host "    -H `"Authorization: Bearer YOUR_ADMIN_TOKEN`"" -ForegroundColor White
Write-Host ""

Write-Host "========================================" -ForegroundColor Green
Write-Host "Deployment Complete!" -ForegroundColor Green
Write-Host "========================================" -ForegroundColor Green
Write-Host ""
Write-Host "Summary:" -ForegroundColor Cyan
Write-Host "  ✓ Environment variables updated" -ForegroundColor Green
Write-Host "  ✓ CloudWatch permissions added" -ForegroundColor Green
Write-Host "  ✓ Lambda code deployed" -ForegroundColor Green
Write-Host ""
Write-Host "Next Steps:" -ForegroundColor Yellow
Write-Host "  1. Login to admin dashboard" -ForegroundColor White
Write-Host "  2. Navigate to System Health section" -ForegroundColor White
Write-Host "  3. Verify real metrics are displayed" -ForegroundColor White
Write-Host ""
Write-Host "Documentation: DOCS/deployment/real-metrics-lightweight.md" -ForegroundColor Cyan
Write-Host ""
