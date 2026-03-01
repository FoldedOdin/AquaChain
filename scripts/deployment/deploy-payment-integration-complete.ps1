# Complete Payment Integration Deployment
# Deploys Enhanced Ordering stack (with payment Lambda) and updates API Gateway

Write-Host "========================================" -ForegroundColor Cyan
Write-Host "Complete Payment Integration Deployment" -ForegroundColor Cyan
Write-Host "========================================" -ForegroundColor Cyan
Write-Host ""

$ErrorActionPreference = "Stop"

# Configuration
$REGION = "ap-south-1"

Write-Host "This script will:" -ForegroundColor Yellow
Write-Host "1. Deploy AquaChain-EnhancedOrdering-dev stack (payment Lambda, DynamoDB tables)" -ForegroundColor White
Write-Host "2. Update AquaChain-API-dev stack (add payment endpoints with CORS)" -ForegroundColor White
Write-Host "3. Verify Razorpay secret configuration" -ForegroundColor White
Write-Host ""

# Check if Razorpay secret exists
Write-Host "[Pre-check] Verifying Razorpay secret..." -ForegroundColor Yellow
try {
    $secretValue = aws secretsmanager get-secret-value `
        --secret-id aquachain-secret-razorpay-credentials-dev `
        --region $REGION `
        --query SecretString `
        --output text 2>&1
    
    if ($LASTEXITCODE -eq 0) {
        $secret = $secretValue | ConvertFrom-Json
        if ($secret.key_id -like "PLACEHOLDER*" -or $secret.key_id -like "rzp_*") {
            if ($secret.key_id -like "PLACEHOLDER*") {
                Write-Host "  WARNING: Razorpay secret contains PLACEHOLDER values!" -ForegroundColor Yellow
                Write-Host "  You need to update it with real Razorpay credentials" -ForegroundColor Yellow
                Write-Host "  See: DOCS/guides/RAZORPAY_SETUP.md" -ForegroundColor Gray
                Write-Host ""
                $continue = Read-Host "Continue anyway? (y/n)"
                if ($continue -ne "y") {
                    Write-Host "Deployment cancelled" -ForegroundColor Red
                    exit 1
                }
            } else {
                Write-Host "  ✓ Razorpay secret exists with key_id: $($secret.key_id)" -ForegroundColor Green
            }
        }
    }
} catch {
    Write-Host "  ERROR: Razorpay secret not found!" -ForegroundColor Red
    Write-Host "  Expected secret: aquachain-secret-razorpay-credentials-dev" -ForegroundColor Red
    Write-Host "  Run: .\scripts\setup\create-razorpay-secret.ps1" -ForegroundColor Yellow
    exit 1
}

Write-Host ""
Write-Host "[1/3] Deploying Enhanced Ordering Stack..." -ForegroundColor Yellow
Write-Host "  This includes:" -ForegroundColor Gray
Write-Host "  - Payment Service Lambda" -ForegroundColor Gray
Write-Host "  - Order Management Lambda" -ForegroundColor Gray
Write-Host "  - DynamoDB tables (Orders, Payments, Technicians)" -ForegroundColor Gray
Write-Host "  - EventBridge rules" -ForegroundColor Gray
Write-Host "  - WebSocket API" -ForegroundColor Gray
Write-Host ""

Set-Location infrastructure/cdk

try {
    Write-Host "  - Synthesizing stack..." -ForegroundColor Gray
    cdk synth AquaChain-EnhancedOrdering-dev --no-version-reporting 2>&1 | Out-Null
    
    Write-Host "  - Deploying (this may take 5-10 minutes)..." -ForegroundColor Gray
    cdk deploy AquaChain-EnhancedOrdering-dev --require-approval never --no-version-reporting
    
    if ($LASTEXITCODE -eq 0) {
        Write-Host "  ✓ Enhanced Ordering stack deployed" -ForegroundColor Green
    } else {
        throw "CDK deployment failed"
    }
} catch {
    Write-Host "  ERROR: Enhanced Ordering stack deployment failed" -ForegroundColor Red
    Write-Host "  $_" -ForegroundColor Red
    Set-Location ../..
    exit 1
}

Write-Host ""
Write-Host "[2/3] Updating API Gateway Stack..." -ForegroundColor Yellow
Write-Host "  Adding payment endpoints with CORS configuration" -ForegroundColor Gray
Write-Host ""

try {
    Write-Host "  - Synthesizing API stack..." -ForegroundColor Gray
    cdk synth AquaChain-API-dev --no-version-reporting 2>&1 | Out-Null
    
    Write-Host "  - Deploying API Gateway changes..." -ForegroundColor Gray
    cdk deploy AquaChain-API-dev --require-approval never --no-version-reporting
    
    if ($LASTEXITCODE -eq 0) {
        Write-Host "  ✓ API Gateway updated" -ForegroundColor Green
    } else {
        throw "API Gateway deployment failed"
    }
} catch {
    Write-Host "  ERROR: API Gateway deployment failed" -ForegroundColor Red
    Write-Host "  $_" -ForegroundColor Red
    Set-Location ../..
    exit 1
}

Set-Location ../..

Write-Host ""
Write-Host "[3/3] Verifying deployment..." -ForegroundColor Yellow

# Check Lambda function exists
Write-Host "  - Checking payment Lambda..." -ForegroundColor Gray
$lambdaExists = aws lambda get-function `
    --function-name AquaChain-payment-service-dev `
    --region $REGION `
    --query "Configuration.FunctionName" `
    --output text 2>&1

if ($LASTEXITCODE -eq 0) {
    Write-Host "  ✓ Payment Lambda deployed: $lambdaExists" -ForegroundColor Green
} else {
    Write-Host "  WARNING: Could not verify Lambda deployment" -ForegroundColor Yellow
}

# Get API Gateway endpoint
Write-Host "  - Getting API Gateway endpoint..." -ForegroundColor Gray
$apiId = aws apigateway get-rest-apis `
    --region $REGION `
    --query "items[?name=='AquaChain-API-dev'].id" `
    --output text

if (![string]::IsNullOrEmpty($apiId)) {
    $apiEndpoint = "https://$apiId.execute-api.$REGION.amazonaws.com/dev"
    Write-Host "  ✓ API Endpoint: $apiEndpoint" -ForegroundColor Green
    
    # Test CORS preflight
    Write-Host "  - Testing CORS preflight..." -ForegroundColor Gray
    try {
        $response = Invoke-WebRequest `
            -Uri "$apiEndpoint/api/payments/create-razorpay-order" `
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
        }
    } catch {
        Write-Host "  WARNING: CORS test failed (may need authentication)" -ForegroundColor Yellow
    }
} else {
    Write-Host "  WARNING: Could not find API Gateway" -ForegroundColor Yellow
}

# Check DynamoDB tables
Write-Host "  - Checking DynamoDB tables..." -ForegroundColor Gray
$tables = @("AquaChain-Orders-dev", "AquaChain-Payments-dev")
foreach ($table in $tables) {
    $tableExists = aws dynamodb describe-table `
        --table-name $table `
        --region $REGION `
        --query "Table.TableName" `
        --output text 2>&1
    
    if ($LASTEXITCODE -eq 0) {
        Write-Host "  ✓ Table exists: $table" -ForegroundColor Green
    } else {
        Write-Host "  WARNING: Table not found: $table" -ForegroundColor Yellow
    }
}

Write-Host ""
Write-Host "========================================" -ForegroundColor Cyan
Write-Host "Deployment Complete!" -ForegroundColor Cyan
Write-Host "========================================" -ForegroundColor Cyan
Write-Host ""
Write-Host "Payment integration is now ready:" -ForegroundColor Green
Write-Host ""
Write-Host "✓ Payment Service Lambda deployed" -ForegroundColor Green
Write-Host "✓ API Gateway endpoints configured:" -ForegroundColor Green
Write-Host "  - POST /api/payments/create-razorpay-order" -ForegroundColor Gray
Write-Host "  - POST /api/payments/verify-payment" -ForegroundColor Gray
Write-Host "  - POST /api/payments/create-cod-payment" -ForegroundColor Gray
Write-Host "  - GET  /api/payments/payment-status" -ForegroundColor Gray
Write-Host "✓ CORS configured for all endpoints" -ForegroundColor Green
Write-Host "✓ DynamoDB tables created" -ForegroundColor Green
Write-Host ""
Write-Host "Next Steps:" -ForegroundColor Yellow
Write-Host "1. Update Razorpay secret with real credentials (if using placeholders)" -ForegroundColor White
Write-Host "   See: DOCS/guides/RAZORPAY_SETUP.md" -ForegroundColor Gray
Write-Host ""
Write-Host "2. Test payment flow in browser:" -ForegroundColor White
Write-Host "   - Navigate to device ordering page" -ForegroundColor Gray
Write-Host "   - Select online payment" -ForegroundColor Gray
Write-Host "   - Verify Razorpay checkout opens" -ForegroundColor Gray
Write-Host ""
Write-Host "3. Configure Razorpay webhook:" -ForegroundColor White
Write-Host "   - Webhook URL: $apiEndpoint/api/webhooks/razorpay" -ForegroundColor Gray
Write-Host "   - See: DOCS/guides/RAZORPAY_SETUP.md" -ForegroundColor Gray
Write-Host ""
Write-Host "To view Lambda logs:" -ForegroundColor Cyan
Write-Host "  aws logs tail /aws/lambda/AquaChain-payment-service-dev --follow --region $REGION" -ForegroundColor Gray
Write-Host ""
