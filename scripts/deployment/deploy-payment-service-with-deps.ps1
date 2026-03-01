# Deploy Payment Service with Dependencies
# Includes Razorpay SDK and all required packages

Write-Host "=== Deploying Payment Service with Dependencies ===" -ForegroundColor Cyan
Write-Host ""

$serviceDir = "lambda/payment_service"
$packageDir = "$serviceDir/package"
$deploymentPackage = "$serviceDir/payment-service-deployment.zip"

# Clean up previous package
Write-Host "Step 1: Cleaning up previous deployment package..." -ForegroundColor Cyan
if (Test-Path $packageDir) {
    Remove-Item -Recurse -Force $packageDir
}
if (Test-Path $deploymentPackage) {
    Remove-Item -Force $deploymentPackage
}

# Create package directory
New-Item -ItemType Directory -Path $packageDir | Out-Null

# Install dependencies
Write-Host "Step 2: Installing Python dependencies..." -ForegroundColor Cyan
Write-Host "  Installing: razorpay, boto3, requests" -ForegroundColor Gray

pip install -r $serviceDir/requirements.txt -t $packageDir --quiet

if ($LASTEXITCODE -ne 0) {
    Write-Host "✗ Failed to install dependencies" -ForegroundColor Red
    exit 1
}

Write-Host "  ✓ Dependencies installed" -ForegroundColor Green

# Copy Lambda function
Write-Host "Step 3: Copying Lambda function code..." -ForegroundColor Cyan
Copy-Item $serviceDir/payment_service.py $packageDir/

# Create deployment package
Write-Host "Step 4: Creating deployment package..." -ForegroundColor Cyan
Push-Location $packageDir
Compress-Archive -Path * -DestinationPath ../$([System.IO.Path]::GetFileName($deploymentPackage)) -Force
Pop-Location

$packageSize = (Get-Item $deploymentPackage).Length / 1MB
Write-Host "  ✓ Package created: $([math]::Round($packageSize, 2)) MB" -ForegroundColor Green

# Deploy to Lambda
Write-Host "Step 5: Deploying to AWS Lambda..." -ForegroundColor Cyan
$result = aws lambda update-function-code `
    --function-name aquachain-function-payment-service-dev `
    --zip-file fileb://$deploymentPackage `
    --region ap-south-1 `
    --query '{FunctionName:FunctionName,LastModified:LastModified,CodeSize:CodeSize}' `
    --output json | ConvertFrom-Json

if ($LASTEXITCODE -eq 0) {
    Write-Host "  ✓ Lambda deployed successfully" -ForegroundColor Green
    Write-Host "    Function: $($result.FunctionName)" -ForegroundColor Gray
    Write-Host "    Modified: $($result.LastModified)" -ForegroundColor Gray
    Write-Host "    Size: $([math]::Round($result.CodeSize / 1MB, 2)) MB" -ForegroundColor Gray
} else {
    Write-Host "  ✗ Lambda deployment failed" -ForegroundColor Red
    exit 1
}

# Wait for Lambda to be ready
Write-Host ""
Write-Host "Step 6: Waiting for Lambda to be ready..." -ForegroundColor Cyan
Start-Sleep -Seconds 3

# Test the deployment
Write-Host "Step 7: Testing Razorpay SDK..." -ForegroundColor Cyan

$testPayload = @{
    httpMethod = "POST"
    path = "/api/payments/create-razorpay-order"
    body = '{"amount":100.0,"currency":"INR"}'
    requestContext = @{
        authorizer = @{
            claims = @{
                sub = "test-user-123"
            }
        }
    }
} | ConvertTo-Json -Depth 5 -Compress

$testResult = aws lambda invoke `
    --function-name aquachain-function-payment-service-dev `
    --region ap-south-1 `
    --payload $testPayload `
    --cli-binary-format raw-in-base64-out `
    response.json

if ($LASTEXITCODE -eq 0) {
    $response = Get-Content response.json | ConvertFrom-Json
    Remove-Item response.json
    
    if ($response.statusCode -eq 200) {
        $body = $response.body | ConvertFrom-Json
        if ($body.success -and $body.data.razorpayOrderId -like "order_*" -and $body.data.razorpayOrderId -notlike "*razorpay_*") {
            Write-Host "  ✓ Razorpay SDK working correctly" -ForegroundColor Green
            Write-Host "    Created real Razorpay order: $($body.data.razorpayOrderId)" -ForegroundColor Gray
        } else {
            Write-Host "  ⚠ Still using simulation mode" -ForegroundColor Yellow
            Write-Host "    Order ID: $($body.data.razorpayOrderId)" -ForegroundColor Gray
        }
    } else {
        Write-Host "  ⚠ Unexpected status code: $($response.statusCode)" -ForegroundColor Yellow
    }
} else {
    Write-Host "  ✗ Test invocation failed" -ForegroundColor Red
}

# Check logs
Write-Host ""
Write-Host "Step 8: Checking CloudWatch logs..." -ForegroundColor Cyan
Start-Sleep -Seconds 2

$logs = aws logs tail /aws/lambda/aquachain-function-payment-service-dev `
    --since 1m `
    --format short `
    --region ap-south-1 2>&1 | Select-String -Pattern "Razorpay order created|Razorpay SDK not installed|ImportError"

if ($logs) {
    Write-Host "  Recent log entries:" -ForegroundColor Gray
    $logs | ForEach-Object { 
        if ($_ -like "*not installed*" -or $_ -like "*ImportError*") {
            Write-Host "    $_" -ForegroundColor Red
        } else {
            Write-Host "    $_" -ForegroundColor Gray
        }
    }
}

# Cleanup
Write-Host ""
Write-Host "Step 9: Cleaning up temporary files..." -ForegroundColor Cyan
Remove-Item -Recurse -Force $packageDir

Write-Host ""
Write-Host "=== Deployment Complete ===" -ForegroundColor Green
Write-Host ""
Write-Host "Summary:" -ForegroundColor White
Write-Host "  ✓ Payment service deployed with Razorpay SDK" -ForegroundColor Green
Write-Host "  ✓ All dependencies included in package" -ForegroundColor Green
Write-Host ""
Write-Host "Next Steps:" -ForegroundColor Yellow
Write-Host "  1. Test payment creation in frontend" -ForegroundColor Gray
Write-Host "  2. Verify real Razorpay order IDs are generated" -ForegroundColor Gray
Write-Host "  3. Complete payment flow with test card" -ForegroundColor Gray
Write-Host ""
