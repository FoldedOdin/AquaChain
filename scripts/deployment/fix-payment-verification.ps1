# Fix Payment Verification Bug
# Date: February 28, 2026
# Issue: Payment verification failing with "Payment record not found"
# Root Cause: Scan operation with Limit=1 only checked first item

Write-Host "=== Payment Verification Bug Fix ===" -ForegroundColor Cyan
Write-Host ""

Write-Host "Issue: Payment verification was failing because scan operation" -ForegroundColor Yellow
Write-Host "       used Limit=1 which only scanned the first DynamoDB item" -ForegroundColor Yellow
Write-Host ""

Write-Host "Root Cause:" -ForegroundColor White
Write-Host "  - payments_table.scan() with Limit=1 stops after scanning 1 item" -ForegroundColor Gray
Write-Host "  - If first item doesn't match filter, returns 0 results" -ForegroundColor Gray
Write-Host "  - Payment records existed but weren't being found" -ForegroundColor Gray
Write-Host ""

Write-Host "Fix Applied:" -ForegroundColor Green
Write-Host "  1. Removed Limit=1 from scan operation" -ForegroundColor Gray
Write-Host "  2. Added better error logging with scan statistics" -ForegroundColor Gray
Write-Host "  3. Fixed Decimal serialization in get_payment_status" -ForegroundColor Gray
Write-Host ""

# Package and deploy Lambda
Write-Host "Step 1: Packaging Lambda function..." -ForegroundColor Cyan

$packageDir = "lambda/payment_service/temp_package"
if (Test-Path $packageDir) {
    Remove-Item -Recurse -Force $packageDir
}
New-Item -ItemType Directory -Path $packageDir | Out-Null

Copy-Item lambda/payment_service/payment_service.py $packageDir/

Write-Host "Step 2: Creating deployment package..." -ForegroundColor Cyan
Compress-Archive -Path $packageDir/payment_service.py -DestinationPath lambda/payment_service/payment_service.zip -Force

Write-Host "Step 3: Deploying to AWS Lambda..." -ForegroundColor Cyan
$result = aws lambda update-function-code `
    --function-name aquachain-function-payment-service-dev `
    --zip-file fileb://lambda/payment_service/payment_service.zip `
    --region ap-south-1 `
    --query '{FunctionName:FunctionName,LastModified:LastModified,CodeSize:CodeSize}' `
    --output json | ConvertFrom-Json

if ($LASTEXITCODE -eq 0) {
    Write-Host "✓ Lambda deployed successfully" -ForegroundColor Green
    Write-Host "  Function: $($result.FunctionName)" -ForegroundColor Gray
    Write-Host "  Modified: $($result.LastModified)" -ForegroundColor Gray
    Write-Host "  Size: $($result.CodeSize) bytes" -ForegroundColor Gray
} else {
    Write-Host "✗ Lambda deployment failed" -ForegroundColor Red
    exit 1
}

Write-Host ""
Write-Host "Step 4: Testing payment verification..." -ForegroundColor Cyan

# Test with existing payment record
$testPayload = @{
    httpMethod = "POST"
    path = "/api/payments/verify-payment"
    body = '{"paymentId":"pay_test123","orderId":"order_SLRpoNnZGcLWSZ","signature":"test_signature"}'
} | ConvertTo-Json -Compress

$testResult = aws lambda invoke `
    --function-name aquachain-function-payment-service-dev `
    --region ap-south-1 `
    --payload $testPayload `
    --cli-binary-format raw-in-base64-out `
    response.json

if ($LASTEXITCODE -eq 0) {
    $response = Get-Content response.json | ConvertFrom-Json
    Remove-Item response.json
    
    if ($response.statusCode -eq 400 -and $response.body -like "*Invalid payment signature*") {
        Write-Host "✓ Payment record found successfully" -ForegroundColor Green
        Write-Host "  (Signature validation failed as expected with test data)" -ForegroundColor Gray
    } elseif ($response.body -like "*Payment record not found*") {
        Write-Host "✗ Still getting 'Payment record not found' error" -ForegroundColor Red
        Write-Host "  Response: $($response.body)" -ForegroundColor Gray
        exit 1
    } else {
        Write-Host "⚠ Unexpected response" -ForegroundColor Yellow
        Write-Host "  Response: $($response.body)" -ForegroundColor Gray
    }
} else {
    Write-Host "✗ Test invocation failed" -ForegroundColor Red
    exit 1
}

Write-Host ""
Write-Host "Step 5: Checking CloudWatch logs..." -ForegroundColor Cyan
$logs = aws logs tail /aws/lambda/aquachain-function-payment-service-dev `
    --since 2m `
    --format short `
    --region ap-south-1 2>&1 | Select-String -Pattern "Found payment record|Payment record not found"

if ($logs) {
    Write-Host "Recent log entries:" -ForegroundColor Gray
    $logs | ForEach-Object { Write-Host "  $_" -ForegroundColor Gray }
}

Write-Host ""
Write-Host "=== Deployment Complete ===" -ForegroundColor Green
Write-Host ""
Write-Host "Summary:" -ForegroundColor White
Write-Host "  ✓ Lambda function updated with bug fix" -ForegroundColor Green
Write-Host "  ✓ Payment verification now scans all items" -ForegroundColor Green
Write-Host "  ✓ Decimal serialization fixed" -ForegroundColor Green
Write-Host ""
Write-Host "Next Steps:" -ForegroundColor Yellow
Write-Host "  1. Test payment flow end-to-end in frontend" -ForegroundColor Gray
Write-Host "  2. Monitor CloudWatch logs for any issues" -ForegroundColor Gray
Write-Host "  3. Consider adding GSI on razorpayOrderId for better performance" -ForegroundColor Gray
Write-Host ""
Write-Host "Performance Note:" -ForegroundColor Yellow
Write-Host "  Current solution uses full table scan (inefficient for large tables)" -ForegroundColor Gray
Write-Host "  Recommended: Add GSI on razorpayOrderId for O(1) lookups" -ForegroundColor Gray
Write-Host ""
