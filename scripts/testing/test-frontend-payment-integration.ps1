# Frontend Payment Integration Testing Script
# Tests the complete payment flow from frontend to backend

$ErrorActionPreference = "Stop"

Write-Host "==================================================" -ForegroundColor Cyan
Write-Host "  Frontend Payment Integration Testing" -ForegroundColor Cyan
Write-Host "==================================================" -ForegroundColor Cyan
Write-Host ""

# Configuration
$FRONTEND_DIR = "frontend"
$API_ENDPOINT = "https://vtqjfznspc.execute-api.ap-south-1.amazonaws.com/dev"
$RAZORPAY_KEY_ID = "rzp_test_S9HvseIXJyxB2I"

# Check if frontend directory exists
if (-not (Test-Path $FRONTEND_DIR)) {
    Write-Host "❌ Frontend directory not found!" -ForegroundColor Red
    exit 1
}

Write-Host "📋 Pre-flight Checks" -ForegroundColor Yellow
Write-Host ""

# 1. Check Node.js
Write-Host "Checking Node.js installation..." -ForegroundColor Cyan
try {
    $nodeVersion = node --version
    Write-Host "  ✓ Node.js: $nodeVersion" -ForegroundColor Green
} catch {
    Write-Host "  ✗ Node.js not found. Please install Node.js" -ForegroundColor Red
    exit 1
}

# 2. Check npm
Write-Host "Checking npm installation..." -ForegroundColor Cyan
try {
    $npmVersion = npm --version
    Write-Host "  ✓ npm: v$npmVersion" -ForegroundColor Green
} catch {
    Write-Host "  ✗ npm not found" -ForegroundColor Red
    exit 1
}

# 3. Check environment files
Write-Host "Checking environment configuration..." -ForegroundColor Cyan
$envFiles = @(
    "$FRONTEND_DIR/.env.production",
    "$FRONTEND_DIR/.env.example"
)

foreach ($file in $envFiles) {
    if (Test-Path $file) {
        Write-Host "  ✓ Found: $file" -ForegroundColor Green
        
        # Check for Razorpay Key ID
        $content = Get-Content $file -Raw
        if ($content -match "REACT_APP_RAZORPAY_KEY_ID=rzp_test_\w+") {
            Write-Host "    ✓ Razorpay Key ID configured" -ForegroundColor Green
        } else {
            Write-Host "    ⚠ Razorpay Key ID not configured or invalid" -ForegroundColor Yellow
        }
        
        # Check for API endpoint
        if ($content -match "REACT_APP_API_ENDPOINT=https://") {
            Write-Host "    ✓ API endpoint configured" -ForegroundColor Green
        } else {
            Write-Host "    ⚠ API endpoint not configured" -ForegroundColor Yellow
        }
    } else {
        Write-Host "  ✗ Missing: $file" -ForegroundColor Red
    }
}

# 4. Check payment service file
Write-Host "Checking payment service..." -ForegroundColor Cyan
$paymentServicePath = "$FRONTEND_DIR/src/services/paymentService.ts"
if (Test-Path $paymentServicePath) {
    Write-Host "  ✓ Payment service exists" -ForegroundColor Green
    
    $serviceContent = Get-Content $paymentServicePath -Raw
    $methods = @("createRazorpayOrder", "verifyPayment", "createCODPayment", "getPaymentStatus")
    
    foreach ($method in $methods) {
        if ($serviceContent -match $method) {
            Write-Host "    ✓ Method: $method" -ForegroundColor Green
        } else {
            Write-Host "    ✗ Missing method: $method" -ForegroundColor Red
        }
    }
} else {
    Write-Host "  ✗ Payment service not found" -ForegroundColor Red
}

# 5. Check RazorpayCheckout component
Write-Host "Checking RazorpayCheckout component..." -ForegroundColor Cyan
$checkoutPath = "$FRONTEND_DIR/src/components/Dashboard/RazorpayCheckout.tsx"
if (Test-Path $checkoutPath) {
    Write-Host "  ✓ RazorpayCheckout component exists" -ForegroundColor Green
} else {
    Write-Host "  ⚠ RazorpayCheckout component not found" -ForegroundColor Yellow
}

# 6. Check dependencies
Write-Host "Checking package dependencies..." -ForegroundColor Cyan
$packageJsonPath = "$FRONTEND_DIR/package.json"
if (Test-Path $packageJsonPath) {
    $packageJson = Get-Content $packageJsonPath -Raw | ConvertFrom-Json
    
    $requiredDeps = @{
        "razorpay" = "Payment gateway SDK"
        "aws-amplify" = "AWS authentication"
        "react" = "React framework"
    }
    
    foreach ($dep in $requiredDeps.Keys) {
        if ($packageJson.dependencies.$dep) {
            Write-Host "  ✓ $dep ($($requiredDeps[$dep])): $($packageJson.dependencies.$dep)" -ForegroundColor Green
        } else {
            Write-Host "  ✗ Missing: $dep" -ForegroundColor Red
        }
    }
} else {
    Write-Host "  ✗ package.json not found" -ForegroundColor Red
}

Write-Host ""
Write-Host "==================================================" -ForegroundColor Cyan
Write-Host "  Configuration Summary" -ForegroundColor Cyan
Write-Host "==================================================" -ForegroundColor Cyan
Write-Host "  API Endpoint: $API_ENDPOINT" -ForegroundColor White
Write-Host "  Razorpay Key: $RAZORPAY_KEY_ID" -ForegroundColor White
Write-Host "  Region: ap-south-1" -ForegroundColor White
Write-Host ""

Write-Host "==================================================" -ForegroundColor Cyan
Write-Host "  Manual Testing Instructions" -ForegroundColor Cyan
Write-Host "==================================================" -ForegroundColor Cyan
Write-Host ""

Write-Host "1. Install Dependencies (if not already done):" -ForegroundColor Yellow
Write-Host "   cd $FRONTEND_DIR" -ForegroundColor Gray
Write-Host "   npm install" -ForegroundColor Gray
Write-Host ""

Write-Host "2. Start Development Server:" -ForegroundColor Yellow
Write-Host "   npm start" -ForegroundColor Gray
Write-Host ""
Write-Host "   The app will open at: http://localhost:3000" -ForegroundColor Cyan
Write-Host ""

Write-Host "3. Test Authentication:" -ForegroundColor Yellow
Write-Host "   a. Navigate to login page" -ForegroundColor Gray
Write-Host "   b. Log in with your credentials" -ForegroundColor Gray
Write-Host "   c. Verify JWT token is stored in localStorage" -ForegroundColor Gray
Write-Host ""

Write-Host "4. Test Payment Flow:" -ForegroundColor Yellow
Write-Host "   a. Navigate to checkout/ordering page" -ForegroundColor Gray
Write-Host "   b. Select a product/service" -ForegroundColor Gray
Write-Host "   c. Choose 'Online Payment' option" -ForegroundColor Gray
Write-Host "   d. Click 'Pay Now' button" -ForegroundColor Gray
Write-Host "   e. Razorpay checkout should open" -ForegroundColor Gray
Write-Host "   f. Complete test payment" -ForegroundColor Gray
Write-Host "   g. Verify payment verification succeeds" -ForegroundColor Gray
Write-Host ""

Write-Host "5. Test COD Payment:" -ForegroundColor Yellow
Write-Host "   a. Navigate to checkout page" -ForegroundColor Gray
Write-Host "   b. Select 'Cash on Delivery' option" -ForegroundColor Gray
Write-Host "   c. Click 'Place Order' button" -ForegroundColor Gray
Write-Host "   d. Verify COD payment record is created" -ForegroundColor Gray
Write-Host ""

Write-Host "6. Test Payment Status:" -ForegroundColor Yellow
Write-Host "   a. Navigate to orders page" -ForegroundColor Gray
Write-Host "   b. View order details" -ForegroundColor Gray
Write-Host "   c. Verify payment status is displayed correctly" -ForegroundColor Gray
Write-Host ""

Write-Host "==================================================" -ForegroundColor Cyan
Write-Host "  Browser Console Testing" -ForegroundColor Cyan
Write-Host "==================================================" -ForegroundColor Cyan
Write-Host ""

Write-Host "Open browser DevTools (F12) and run these commands:" -ForegroundColor Yellow
Write-Host ""

Write-Host "// Check Razorpay Key ID" -ForegroundColor Gray
Write-Host "console.log('Razorpay Key:', process.env.REACT_APP_RAZORPAY_KEY_ID);" -ForegroundColor Cyan
Write-Host ""

Write-Host "// Check API Endpoint" -ForegroundColor Gray
Write-Host "console.log('API Endpoint:', process.env.REACT_APP_API_ENDPOINT);" -ForegroundColor Cyan
Write-Host ""

Write-Host "// Check JWT Token" -ForegroundColor Gray
Write-Host "console.log('JWT Token:', localStorage.getItem('aquachain_token'));" -ForegroundColor Cyan
Write-Host ""

Write-Host "// Test Payment Service (after login)" -ForegroundColor Gray
Write-Host "import { PaymentService } from './services/paymentService';" -ForegroundColor Cyan
Write-Host "PaymentService.createRazorpayOrder(1000, 'TEST-ORDER-001')" -ForegroundColor Cyan
Write-Host "  .then(res => console.log('Order created:', res))" -ForegroundColor Cyan
Write-Host "  .catch(err => console.error('Error:', err));" -ForegroundColor Cyan
Write-Host ""

Write-Host "==================================================" -ForegroundColor Cyan
Write-Host "  Troubleshooting" -ForegroundColor Cyan
Write-Host "==================================================" -ForegroundColor Cyan
Write-Host ""

Write-Host "Issue: 401 Unauthorized" -ForegroundColor Yellow
Write-Host "  Solution: Ensure you're logged in and JWT token is valid" -ForegroundColor Gray
Write-Host "  Check: localStorage.getItem('aquachain_token')" -ForegroundColor Gray
Write-Host ""

Write-Host "Issue: CORS Error" -ForegroundColor Yellow
Write-Host "  Solution: Payment Lambda handles CORS automatically" -ForegroundColor Gray
Write-Host "  Check: API Gateway CORS configuration" -ForegroundColor Gray
Write-Host ""

Write-Host "Issue: Razorpay not loading" -ForegroundColor Yellow
Write-Host "  Solution: Verify Razorpay script is loaded in public/index.html" -ForegroundColor Gray
Write-Host "  Check: <script src='https://checkout.razorpay.com/v1/checkout.js'></script>" -ForegroundColor Gray
Write-Host ""

Write-Host "Issue: Payment verification fails" -ForegroundColor Yellow
Write-Host "  Solution: Ensure signature is from Razorpay (not manually generated)" -ForegroundColor Gray
Write-Host "  Check: Razorpay webhook secret in AWS Secrets Manager" -ForegroundColor Gray
Write-Host ""

Write-Host "==================================================" -ForegroundColor Cyan
Write-Host "  Backend Verification" -ForegroundColor Cyan
Write-Host "==================================================" -ForegroundColor Cyan
Write-Host ""

Write-Host "View Lambda Logs:" -ForegroundColor Yellow
Write-Host "  aws logs tail /aws/lambda/aquachain-function-payment-service-dev --follow --region ap-south-1" -ForegroundColor Gray
Write-Host ""

Write-Host "Check CloudWatch Alarms:" -ForegroundColor Yellow
Write-Host "  aws cloudwatch describe-alarms --alarm-name-prefix 'AquaChain-Payment' --region ap-south-1" -ForegroundColor Gray
Write-Host ""

Write-Host "Test Backend Endpoints:" -ForegroundColor Yellow
Write-Host "  cd scripts/testing" -ForegroundColor Gray
Write-Host "  ./test-payment-endpoints-integration.ps1" -ForegroundColor Gray
Write-Host ""

Write-Host "==================================================" -ForegroundColor Cyan
Write-Host "  Next Steps" -ForegroundColor Cyan
Write-Host "==================================================" -ForegroundColor Cyan
Write-Host ""

Write-Host "1. Start the frontend development server" -ForegroundColor White
Write-Host "2. Log in to the application" -ForegroundColor White
Write-Host "3. Test the complete payment flow" -ForegroundColor White
Write-Host "4. Monitor CloudWatch logs for any errors" -ForegroundColor White
Write-Host "5. Report any issues found" -ForegroundColor White
Write-Host ""

Write-Host "✅ Pre-flight checks complete!" -ForegroundColor Green
Write-Host "   Ready for frontend integration testing" -ForegroundColor Green
Write-Host ""

# Ask if user wants to start the dev server
$response = Read-Host "Do you want to start the frontend development server now? (yes/no)"
if ($response -eq "yes") {
    Write-Host ""
    Write-Host "Starting frontend development server..." -ForegroundColor Cyan
    Write-Host "Press Ctrl+C to stop the server" -ForegroundColor Yellow
    Write-Host ""
    
    Set-Location $FRONTEND_DIR
    npm start
}
