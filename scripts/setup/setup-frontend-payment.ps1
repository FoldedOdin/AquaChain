# Setup Frontend Payment Integration
# This script helps configure and test the frontend payment integration

$ErrorActionPreference = "Stop"

Write-Host "=== AquaChain Frontend Payment Setup ===" -ForegroundColor Cyan
Write-Host ""

# Check if we're in the right directory
if (-not (Test-Path "frontend/package.json")) {
    Write-Host "ERROR: Please run this script from the project root directory" -ForegroundColor Red
    exit 1
}

# Step 1: Check Razorpay Key ID
Write-Host "Step 1: Checking Razorpay Configuration" -ForegroundColor Cyan
Write-Host "----------------------------------------" -ForegroundColor Cyan

$envProdFile = "frontend/.env.production"
$envLocalFile = "frontend/.env"

if (Test-Path $envProdFile) {
    $razorpayKey = Select-String -Path $envProdFile -Pattern "REACT_APP_RAZORPAY_KEY_ID=(.+)" | ForEach-Object { $_.Matches.Groups[1].Value }
    
    if ($razorpayKey -and $razorpayKey -ne "rzp_test_YOUR_KEY_ID_HERE") {
        Write-Host "✓ Razorpay Key ID configured: $razorpayKey" -ForegroundColor Green
    } else {
        Write-Host "⚠ Razorpay Key ID not configured" -ForegroundColor Yellow
        Write-Host ""
        Write-Host "To configure Razorpay:" -ForegroundColor Yellow
        Write-Host "  1. Log in to https://dashboard.razorpay.com/" -ForegroundColor Gray
        Write-Host "  2. Go to Settings > API Keys" -ForegroundColor Gray
        Write-Host "  3. Copy your Key ID (starts with rzp_test_)" -ForegroundColor Gray
        Write-Host "  4. Update $envProdFile" -ForegroundColor Gray
        Write-Host "     REACT_APP_RAZORPAY_KEY_ID=rzp_test_YOUR_ACTUAL_KEY" -ForegroundColor Gray
        Write-Host ""
    }
} else {
    Write-Host "⚠ Production environment file not found" -ForegroundColor Yellow
}

Write-Host ""

# Step 2: Check API Endpoint
Write-Host "Step 2: Checking API Endpoint Configuration" -ForegroundColor Cyan
Write-Host "--------------------------------------------" -ForegroundColor Cyan

$apiEndpoint = Select-String -Path $envProdFile -Pattern "REACT_APP_API_ENDPOINT=(.+)" | ForEach-Object { $_.Matches.Groups[1].Value }

if ($apiEndpoint -eq "https://vtqjfznspc.execute-api.ap-south-1.amazonaws.com/dev") {
    Write-Host "✓ API Endpoint configured correctly" -ForegroundColor Green
    Write-Host "  $apiEndpoint" -ForegroundColor Gray
} else {
    Write-Host "⚠ API Endpoint may be incorrect" -ForegroundColor Yellow
    Write-Host "  Current: $apiEndpoint" -ForegroundColor Gray
    Write-Host "  Expected: https://vtqjfznspc.execute-api.ap-south-1.amazonaws.com/dev" -ForegroundColor Gray
}

Write-Host ""

# Step 3: Check if payment service exists
Write-Host "Step 3: Checking Payment Service Files" -ForegroundColor Cyan
Write-Host "---------------------------------------" -ForegroundColor Cyan

$paymentServiceFile = "frontend/src/services/paymentService.ts"
if (Test-Path $paymentServiceFile) {
    Write-Host "✓ Payment service exists: $paymentServiceFile" -ForegroundColor Green
} else {
    Write-Host "✗ Payment service not found: $paymentServiceFile" -ForegroundColor Red
}

$razorpayCheckoutFile = "frontend/src/components/Dashboard/RazorpayCheckout.tsx"
if (Test-Path $razorpayCheckoutFile) {
    Write-Host "✓ RazorpayCheckout component exists: $razorpayCheckoutFile" -ForegroundColor Green
} else {
    Write-Host "✗ RazorpayCheckout component not found: $razorpayCheckoutFile" -ForegroundColor Red
}

Write-Host ""

# Step 4: Check Node modules
Write-Host "Step 4: Checking Dependencies" -ForegroundColor Cyan
Write-Host "------------------------------" -ForegroundColor Cyan

if (Test-Path "frontend/node_modules") {
    Write-Host "✓ Node modules installed" -ForegroundColor Green
    
    # Check for razorpay package
    if (Test-Path "frontend/node_modules/razorpay") {
        Write-Host "✓ Razorpay package installed" -ForegroundColor Green
    } else {
        Write-Host "⚠ Razorpay package not found (optional)" -ForegroundColor Yellow
    }
} else {
    Write-Host "⚠ Node modules not installed" -ForegroundColor Yellow
    Write-Host "  Run: cd frontend && npm install" -ForegroundColor Gray
}

Write-Host ""

# Step 5: Test API Endpoints
Write-Host "Step 5: Testing API Endpoints" -ForegroundColor Cyan
Write-Host "------------------------------" -ForegroundColor Cyan

Write-Host "Checking if payment endpoints are accessible..." -ForegroundColor Yellow

try {
    $response = Invoke-WebRequest -Uri "https://vtqjfznspc.execute-api.ap-south-1.amazonaws.com/dev/api/payments/payment-status?orderId=TEST" -Method GET -ErrorAction Stop
    Write-Host "⚠ Endpoint accessible but returned: $($response.StatusCode)" -ForegroundColor Yellow
    Write-Host "  (401 Unauthorized is expected without JWT token)" -ForegroundColor Gray
} catch {
    if ($_.Exception.Response.StatusCode -eq 401) {
        Write-Host "✓ Payment endpoints are accessible (401 Unauthorized - expected)" -ForegroundColor Green
    } else {
        Write-Host "✗ Payment endpoints may not be accessible" -ForegroundColor Red
        Write-Host "  Error: $($_.Exception.Message)" -ForegroundColor Red
    }
}

Write-Host ""

# Summary
Write-Host "=== Setup Summary ===" -ForegroundColor Cyan
Write-Host ""

$allGood = $true

if (-not $razorpayKey -or $razorpayKey -eq "rzp_test_YOUR_KEY_ID_HERE") {
    Write-Host "[ ] Configure Razorpay Key ID" -ForegroundColor Yellow
    $allGood = $false
} else {
    Write-Host "[✓] Razorpay Key ID configured" -ForegroundColor Green
}

if (Test-Path $paymentServiceFile) {
    Write-Host "[✓] Payment service created" -ForegroundColor Green
} else {
    Write-Host "[ ] Payment service missing" -ForegroundColor Yellow
    $allGood = $false
}

if (Test-Path "frontend/node_modules") {
    Write-Host "[✓] Dependencies installed" -ForegroundColor Green
} else {
    Write-Host "[ ] Install dependencies (npm install)" -ForegroundColor Yellow
    $allGood = $false
}

Write-Host ""

if ($allGood) {
    Write-Host "✅ Frontend payment integration is ready!" -ForegroundColor Green
    Write-Host ""
    Write-Host "Next steps:" -ForegroundColor Cyan
    Write-Host "  1. Start the frontend: cd frontend && npm start" -ForegroundColor Gray
    Write-Host "  2. Log in to the application" -ForegroundColor Gray
    Write-Host "  3. Test the payment flow" -ForegroundColor Gray
    Write-Host ""
    Write-Host "To test endpoints directly:" -ForegroundColor Cyan
    Write-Host "  cd scripts/testing" -ForegroundColor Gray
    Write-Host "  `$env:AQUACHAIN_JWT_TOKEN = 'your_jwt_token'" -ForegroundColor Gray
    Write-Host "  ./test-payment-endpoints-integration.ps1" -ForegroundColor Gray
} else {
    Write-Host "⚠ Some configuration is still needed" -ForegroundColor Yellow
    Write-Host ""
    Write-Host "Please complete the items marked with [ ] above" -ForegroundColor Yellow
    Write-Host ""
    Write-Host "For detailed instructions, see:" -ForegroundColor Cyan
    Write-Host "  FRONTEND_PAYMENT_INTEGRATION_STATUS.md" -ForegroundColor Gray
}

Write-Host ""
