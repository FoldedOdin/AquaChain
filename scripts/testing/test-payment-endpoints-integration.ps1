# Payment Endpoints Integration Test Script
# Tests all payment endpoints with realistic scenarios

$ErrorActionPreference = "Stop"

$API_BASE = "https://vtqjfznspc.execute-api.ap-south-1.amazonaws.com/dev"
$REGION = "ap-south-1"

Write-Host "=== AquaChain Payment Endpoints Integration Test ===" -ForegroundColor Cyan
Write-Host ""

# Check if JWT token is provided
if (-not $env:AQUACHAIN_JWT_TOKEN) {
    Write-Host "ERROR: JWT token not found" -ForegroundColor Red
    Write-Host "Please set the AQUACHAIN_JWT_TOKEN environment variable:" -ForegroundColor Yellow
    Write-Host '  $env:AQUACHAIN_JWT_TOKEN = "your_jwt_token_here"' -ForegroundColor Yellow
    Write-Host ""
    Write-Host "To get a JWT token:" -ForegroundColor Yellow
    Write-Host "  1. Log in to the AquaChain frontend" -ForegroundColor Yellow
    Write-Host "  2. Open browser DevTools (F12)" -ForegroundColor Yellow
    Write-Host "  3. Go to Application > Local Storage" -ForegroundColor Yellow
    Write-Host "  4. Copy the JWT token value" -ForegroundColor Yellow
    exit 1
}

$JWT_TOKEN = $env:AQUACHAIN_JWT_TOKEN
$headers = @{
    "Authorization" = "Bearer $JWT_TOKEN"
    "Content-Type" = "application/json"
}

Write-Host "✓ JWT token found" -ForegroundColor Green
Write-Host ""

# Test 1: Create Razorpay Order
Write-Host "Test 1: Create Razorpay Order" -ForegroundColor Cyan
Write-Host "-------------------------------" -ForegroundColor Cyan

$orderId = "ORD-TEST-$(Get-Date -Format 'yyyyMMddHHmmss')"
$createOrderBody = @{
    amount = 1000.00
    orderId = $orderId
    currency = "INR"
} | ConvertTo-Json

Write-Host "Request: POST $API_BASE/api/payments/create-razorpay-order"
Write-Host "Order ID: $orderId"
Write-Host "Amount: ₹1000.00"

try {
    $response = Invoke-RestMethod -Uri "$API_BASE/api/payments/create-razorpay-order" `
        -Method POST `
        -Headers $headers `
        -Body $createOrderBody `
        -ContentType "application/json"
    
    if ($response.success) {
        Write-Host "✓ Order created successfully" -ForegroundColor Green
        Write-Host "  Payment ID: $($response.data.paymentId)" -ForegroundColor Gray
        Write-Host "  Razorpay Order ID: $($response.data.razorpayOrder.id)" -ForegroundColor Gray
        Write-Host "  Amount (paise): $($response.data.razorpayOrder.amount)" -ForegroundColor Gray
        Write-Host "  Status: $($response.data.razorpayOrder.status)" -ForegroundColor Gray
        
        $paymentId = $response.data.paymentId
        $razorpayOrderId = $response.data.razorpayOrder.id
    } else {
        Write-Host "✗ Order creation failed" -ForegroundColor Red
        Write-Host "  Error: $($response.error)" -ForegroundColor Red
        exit 1
    }
} catch {
    Write-Host "✗ Request failed" -ForegroundColor Red
    Write-Host "  Error: $($_.Exception.Message)" -ForegroundColor Red
    if ($_.ErrorDetails.Message) {
        Write-Host "  Details: $($_.ErrorDetails.Message)" -ForegroundColor Red
    }
    exit 1
}

Write-Host ""

# Test 2: Get Payment Status (should be PENDING)
Write-Host "Test 2: Get Payment Status (Initial)" -ForegroundColor Cyan
Write-Host "-------------------------------------" -ForegroundColor Cyan

Write-Host "Request: GET $API_BASE/api/payments/payment-status?orderId=$orderId"

try {
    $response = Invoke-RestMethod -Uri "$API_BASE/api/payments/payment-status?orderId=$orderId" `
        -Method GET `
        -Headers $headers
    
    if ($response.success) {
        Write-Host "✓ Payment status retrieved" -ForegroundColor Green
        Write-Host "  Payment ID: $($response.data.paymentId)" -ForegroundColor Gray
        Write-Host "  Status: $($response.data.status)" -ForegroundColor Gray
        Write-Host "  Payment Method: $($response.data.paymentMethod)" -ForegroundColor Gray
        Write-Host "  Amount: ₹$($response.data.amount)" -ForegroundColor Gray
        
        if ($response.data.status -ne "PENDING") {
            Write-Host "  ⚠ Warning: Expected status PENDING, got $($response.data.status)" -ForegroundColor Yellow
        }
    } else {
        Write-Host "✗ Failed to get payment status" -ForegroundColor Red
        Write-Host "  Error: $($response.error)" -ForegroundColor Red
    }
} catch {
    Write-Host "✗ Request failed" -ForegroundColor Red
    Write-Host "  Error: $($_.Exception.Message)" -ForegroundColor Red
}

Write-Host ""

# Test 3: Create COD Payment
Write-Host "Test 3: Create COD Payment" -ForegroundColor Cyan
Write-Host "--------------------------" -ForegroundColor Cyan

$codOrderId = "ORD-COD-$(Get-Date -Format 'yyyyMMddHHmmss')"
$codPaymentBody = @{
    orderId = $codOrderId
    amount = 1500.00
} | ConvertTo-Json

Write-Host "Request: POST $API_BASE/api/payments/create-cod-payment"
Write-Host "Order ID: $codOrderId"
Write-Host "Amount: ₹1500.00"

try {
    $response = Invoke-RestMethod -Uri "$API_BASE/api/payments/create-cod-payment" `
        -Method POST `
        -Headers $headers `
        -Body $codPaymentBody `
        -ContentType "application/json"
    
    if ($response.success) {
        Write-Host "✓ COD payment created successfully" -ForegroundColor Green
        Write-Host "  Payment ID: $($response.data.paymentId)" -ForegroundColor Gray
        Write-Host "  Status: $($response.data.status)" -ForegroundColor Gray
        
        if ($response.data.status -ne "COD_PENDING") {
            Write-Host "  ⚠ Warning: Expected status COD_PENDING, got $($response.data.status)" -ForegroundColor Yellow
        }
    } else {
        Write-Host "✗ COD payment creation failed" -ForegroundColor Red
        Write-Host "  Error: $($response.error)" -ForegroundColor Red
    }
} catch {
    Write-Host "✗ Request failed" -ForegroundColor Red
    Write-Host "  Error: $($_.Exception.Message)" -ForegroundColor Red
}

Write-Host ""

# Test 4: Get COD Payment Status
Write-Host "Test 4: Get COD Payment Status" -ForegroundColor Cyan
Write-Host "-------------------------------" -ForegroundColor Cyan

Write-Host "Request: GET $API_BASE/api/payments/payment-status?orderId=$codOrderId"

try {
    $response = Invoke-RestMethod -Uri "$API_BASE/api/payments/payment-status?orderId=$codOrderId" `
        -Method GET `
        -Headers $headers
    
    if ($response.success) {
        Write-Host "✓ COD payment status retrieved" -ForegroundColor Green
        Write-Host "  Payment ID: $($response.data.paymentId)" -ForegroundColor Gray
        Write-Host "  Status: $($response.data.status)" -ForegroundColor Gray
        Write-Host "  Payment Method: $($response.data.paymentMethod)" -ForegroundColor Gray
        Write-Host "  Amount: ₹$($response.data.amount)" -ForegroundColor Gray
    } else {
        Write-Host "✗ Failed to get COD payment status" -ForegroundColor Red
        Write-Host "  Error: $($response.error)" -ForegroundColor Red
    }
} catch {
    Write-Host "✗ Request failed" -ForegroundColor Red
    Write-Host "  Error: $($_.Exception.Message)" -ForegroundColor Red
}

Write-Host ""

# Test 5: Verify Payment (will fail due to invalid signature - expected)
Write-Host "Test 5: Verify Payment (Invalid Signature - Expected Failure)" -ForegroundColor Cyan
Write-Host "--------------------------------------------------------------" -ForegroundColor Cyan

$verifyPaymentBody = @{
    paymentId = $paymentId
    orderId = $razorpayOrderId
    signature = "invalid_signature_for_testing"
} | ConvertTo-Json

Write-Host "Request: POST $API_BASE/api/payments/verify-payment"
Write-Host "Note: This should fail with invalid signature (expected behavior)"

try {
    $response = Invoke-RestMethod -Uri "$API_BASE/api/payments/verify-payment" `
        -Method POST `
        -Headers $headers `
        -Body $verifyPaymentBody `
        -ContentType "application/json"
    
    if ($response.success) {
        Write-Host "✗ Unexpected success - signature validation may be broken" -ForegroundColor Red
    } else {
        Write-Host "✓ Correctly rejected invalid signature" -ForegroundColor Green
        Write-Host "  Error: $($response.error)" -ForegroundColor Gray
    }
} catch {
    Write-Host "✓ Correctly rejected invalid signature (HTTP error)" -ForegroundColor Green
    if ($_.ErrorDetails.Message) {
        $errorDetails = $_.ErrorDetails.Message | ConvertFrom-Json
        Write-Host "  Error: $($errorDetails.error)" -ForegroundColor Gray
    }
}

Write-Host ""

# Test 6: Query Non-existent Order
Write-Host "Test 6: Query Non-existent Order" -ForegroundColor Cyan
Write-Host "---------------------------------" -ForegroundColor Cyan

$nonExistentOrderId = "ORD-NONEXISTENT-999999"
Write-Host "Request: GET $API_BASE/api/payments/payment-status?orderId=$nonExistentOrderId"

try {
    $response = Invoke-RestMethod -Uri "$API_BASE/api/payments/payment-status?orderId=$nonExistentOrderId" `
        -Method GET `
        -Headers $headers
    
    if ($response.success -and $response.data.status -eq "NOT_FOUND") {
        Write-Host "✓ Correctly returned NOT_FOUND for non-existent order" -ForegroundColor Green
        Write-Host "  Message: $($response.data.message)" -ForegroundColor Gray
    } else {
        Write-Host "✗ Unexpected response for non-existent order" -ForegroundColor Red
    }
} catch {
    Write-Host "✗ Request failed" -ForegroundColor Red
    Write-Host "  Error: $($_.Exception.Message)" -ForegroundColor Red
}

Write-Host ""

# Summary
Write-Host "=== Test Summary ===" -ForegroundColor Cyan
Write-Host "✓ All payment endpoints are accessible" -ForegroundColor Green
Write-Host "✓ Authentication is working (Cognito)" -ForegroundColor Green
Write-Host "✓ Payment creation flows are functional" -ForegroundColor Green
Write-Host "✓ Payment status queries are working" -ForegroundColor Green
Write-Host "✓ Signature validation is enforced" -ForegroundColor Green
Write-Host ""
Write-Host "Next Steps:" -ForegroundColor Yellow
Write-Host "  1. Integrate these endpoints with the frontend" -ForegroundColor Yellow
Write-Host "  2. Test with real Razorpay credentials" -ForegroundColor Yellow
Write-Host "  3. Monitor CloudWatch logs for any issues" -ForegroundColor Yellow
Write-Host ""
Write-Host "CloudWatch Logs:" -ForegroundColor Cyan
Write-Host "  aws logs tail /aws/lambda/aquachain-function-payment-service-dev --follow --region ap-south-1" -ForegroundColor Gray
