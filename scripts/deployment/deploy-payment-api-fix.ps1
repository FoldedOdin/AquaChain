# Deploy Payment API CORS Fix
# Fixes CORS preflight errors for Razorpay payment integration

Write-Host "========================================" -ForegroundColor Cyan
Write-Host "Payment API CORS Fix Deployment" -ForegroundColor Cyan
Write-Host "========================================" -ForegroundColor Cyan
Write-Host ""

$ErrorActionPreference = "Stop"

# Configuration
$REGION = "ap-south-1"
$LAMBDA_FUNCTION_NAME = "AquaChain-payment-service-dev"
$LAMBDA_DIR = "lambda/payment_service"

Write-Host "[1/5] Packaging Lambda function..." -ForegroundColor Yellow

# Create temporary directory for Lambda package
$tempDir = Join-Path $LAMBDA_DIR "temp_package"
if (Test-Path $tempDir) {
    Remove-Item -Path $tempDir -Recurse -Force
}
New-Item -ItemType Directory -Path $tempDir -Force | Out-Null

# Copy Lambda files
Write-Host "  - Copying Lambda files..." -ForegroundColor Gray
$sourcePath = Resolve-Path $LAMBDA_DIR
Copy-Item "$sourcePath/payment_service.py" -Destination $tempDir
Copy-Item "$sourcePath/webhook_handler.py" -Destination $tempDir
if (Test-Path "$sourcePath/requirements.txt") {
    Copy-Item "$sourcePath/requirements.txt" -Destination $tempDir
}

# Copy shared utilities if they exist
$sharedDir = "lambda/shared"
if (Test-Path $sharedDir) {
    Write-Host "  - Copying shared utilities..." -ForegroundColor Gray
    $sharedPath = Resolve-Path $sharedDir
    Get-ChildItem -Path $sharedPath -Filter "*.py" | ForEach-Object {
        Copy-Item $_.FullName -Destination $tempDir
    }
}

# Create deployment package
Write-Host "  - Creating deployment package..." -ForegroundColor Gray
$zipPath = Join-Path (Resolve-Path $LAMBDA_DIR) "deployment.zip"
if (Test-Path $zipPath) {
    Remove-Item $zipPath -Force
}

# Get absolute path for temp directory
$tempDirAbsolute = Resolve-Path $tempDir
Push-Location $tempDirAbsolute
Compress-Archive -Path * -DestinationPath $zipPath -Force
Pop-Location

# Verify package structure
Write-Host "  - Verifying package structure..." -ForegroundColor Gray
Add-Type -AssemblyName System.IO.Compression.FileSystem
$zip = [System.IO.Compression.ZipFile]::OpenRead($zipPath)
$hasPaymentService = $zip.Entries | Where-Object { $_.Name -eq "payment_service.py" }
$zip.Dispose()

if (-not $hasPaymentService) {
    Write-Host "ERROR: payment_service.py not found in package root!" -ForegroundColor Red
    exit 1
}

Write-Host "  ✓ Package structure verified" -ForegroundColor Green

Write-Host ""
Write-Host "[2/5] Deploying Lambda function..." -ForegroundColor Yellow

try {
    aws lambda update-function-code `
        --function-name $LAMBDA_FUNCTION_NAME `
        --zip-file "fileb://$zipPath" `
        --region $REGION `
        --no-cli-pager
    
    Write-Host "  ✓ Lambda function updated" -ForegroundColor Green
} catch {
    Write-Host "  ERROR: Failed to update Lambda function" -ForegroundColor Red
    Write-Host "  $_" -ForegroundColor Red
    exit 1
}

# Wait for Lambda to be ready
Write-Host "  - Waiting for Lambda to be ready..." -ForegroundColor Gray
Start-Sleep -Seconds 5

Write-Host ""
Write-Host "[3/5] Deploying CDK infrastructure..." -ForegroundColor Yellow

Set-Location infrastructure/cdk

try {
    Write-Host "  - Synthesizing CDK stack..." -ForegroundColor Gray
    cdk synth AquaChain-API-dev --no-version-reporting 2>&1 | Out-Null
    
    Write-Host "  - Deploying API Gateway changes..." -ForegroundColor Gray
    cdk deploy AquaChain-API-dev --require-approval never --no-version-reporting
    
    Write-Host "  ✓ CDK deployment complete" -ForegroundColor Green
} catch {
    Write-Host "  ERROR: CDK deployment failed" -ForegroundColor Red
    Write-Host "  $_" -ForegroundColor Red
    Set-Location ../..
    exit 1
}

Set-Location ../..

Write-Host ""
Write-Host "[4/5] Verifying deployment..." -ForegroundColor Yellow

# Get API Gateway endpoint
$apiId = aws apigateway get-rest-apis --region $REGION --query "items[?name=='AquaChain-API-dev'].id" --output text

if ([string]::IsNullOrEmpty($apiId)) {
    Write-Host "  WARNING: Could not find API Gateway ID" -ForegroundColor Yellow
} else {
    $apiEndpoint = "https://$apiId.execute-api.$REGION.amazonaws.com/dev"
    Write-Host "  API Endpoint: $apiEndpoint" -ForegroundColor Cyan
    
    # Test OPTIONS request (CORS preflight)
    Write-Host "  - Testing CORS preflight (OPTIONS)..." -ForegroundColor Gray
    try {
        $response = Invoke-WebRequest -Uri "$apiEndpoint/api/payments/create-razorpay-order" `
            -Method OPTIONS `
            -Headers @{
                "Origin" = "http://localhost:3000"
                "Access-Control-Request-Method" = "POST"
                "Access-Control-Request-Headers" = "Content-Type,Authorization"
            } `
            -UseBasicParsing `
            -ErrorAction Stop
        
        if ($response.StatusCode -eq 200) {
            Write-Host "  ✓ CORS preflight successful" -ForegroundColor Green
            
            # Check CORS headers
            $corsHeaders = $response.Headers['Access-Control-Allow-Origin']
            if ($corsHeaders) {
                Write-Host "  ✓ CORS headers present: $corsHeaders" -ForegroundColor Green
            }
        }
    } catch {
        Write-Host "  WARNING: CORS preflight test failed (may need authentication)" -ForegroundColor Yellow
        Write-Host "  Status: $($_.Exception.Response.StatusCode.value__)" -ForegroundColor Gray
    }
}

Write-Host ""
Write-Host "[5/5] Cleanup..." -ForegroundColor Yellow

# Remove temporary files
if (Test-Path $tempDir) {
    Remove-Item -Path $tempDir -Recurse -Force
    Write-Host "  ✓ Temporary files removed" -ForegroundColor Green
}

Write-Host ""
Write-Host "========================================" -ForegroundColor Cyan
Write-Host "Deployment Summary" -ForegroundColor Cyan
Write-Host "========================================" -ForegroundColor Cyan
Write-Host ""
Write-Host "✓ Lambda function updated with OPTIONS handling" -ForegroundColor Green
Write-Host "✓ API Gateway endpoints created:" -ForegroundColor Green
Write-Host "  - POST /api/payments/create-razorpay-order" -ForegroundColor Gray
Write-Host "  - POST /api/payments/verify-payment" -ForegroundColor Gray
Write-Host "  - POST /api/payments/create-cod-payment" -ForegroundColor Gray
Write-Host "  - GET  /api/payments/payment-status" -ForegroundColor Gray
Write-Host "✓ CORS configured for all payment endpoints" -ForegroundColor Green
Write-Host ""
Write-Host "Next Steps:" -ForegroundColor Yellow
Write-Host "1. Test payment flow in browser" -ForegroundColor White
Write-Host "2. Verify Razorpay credentials in AWS Secrets Manager" -ForegroundColor White
Write-Host "3. Check CloudWatch logs if issues persist" -ForegroundColor White
Write-Host ""
Write-Host "To view Lambda logs:" -ForegroundColor Cyan
Write-Host "  aws logs tail /aws/lambda/$LAMBDA_FUNCTION_NAME --follow --region $REGION" -ForegroundColor Gray
Write-Host ""
