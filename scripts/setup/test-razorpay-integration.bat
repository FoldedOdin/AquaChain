@echo off
REM Test Razorpay Integration Script
REM Performs comprehensive testing of Razorpay setup

echo ========================================
echo   Razorpay Integration Test Suite
echo ========================================
echo.

set /p ENVIRONMENT="Enter environment to test (dev/staging/prod) [dev]: "
if "%ENVIRONMENT%"=="" set ENVIRONMENT=dev

echo.
echo Testing environment: %ENVIRONMENT%
echo.

set PASS_COUNT=0
set FAIL_COUNT=0

REM Test 1: AWS Secrets Manager
echo [1/6] Testing AWS Secrets Manager...
aws secretsmanager get-secret-value ^
    --secret-id aquachain-secret-razorpay-credentials-%ENVIRONMENT% ^
    --region us-east-1 ^
    --query SecretString ^
    --output text >secret.tmp 2>nul

if errorlevel 1 (
    echo   ❌ FAIL: Cannot retrieve secret
    set /a FAIL_COUNT+=1
) else (
    findstr /C:"key_id" secret.tmp >nul
    if errorlevel 1 (
        echo   ❌ FAIL: Secret missing key_id
        set /a FAIL_COUNT+=1
    ) else (
        findstr /C:"key_secret" secret.tmp >nul
        if errorlevel 1 (
            echo   ❌ FAIL: Secret missing key_secret
            set /a FAIL_COUNT+=1
        ) else (
            echo   ✓ PASS: Secret configured correctly
            set /a PASS_COUNT+=1
        )
    )
)
del secret.tmp 2>nul

REM Test 2: Frontend Configuration
echo [2/6] Testing Frontend Configuration...
if exist "frontend\.env.local" (
    findstr /C:"REACT_APP_RAZORPAY_KEY_ID" frontend\.env.local >nul
    if errorlevel 1 (
        echo   ❌ FAIL: REACT_APP_RAZORPAY_KEY_ID not in .env.local
        set /a FAIL_COUNT+=1
    ) else (
        findstr /C:"REACT_APP_RAZORPAY_KEY_ID=rzp_" frontend\.env.local >nul
        if errorlevel 1 (
            echo   ⚠ WARNING: Key ID may not be configured
            set /a FAIL_COUNT+=1
        ) else (
            echo   ✓ PASS: Frontend configured
            set /a PASS_COUNT+=1
        )
    )
) else (
    echo   ❌ FAIL: frontend\.env.local not found
    set /a FAIL_COUNT+=1
)

REM Test 3: Lambda Function
echo [3/6] Testing Payment Service Lambda...
aws lambda get-function ^
    --function-name aquachain-function-payment-service-%ENVIRONMENT% ^
    --region us-east-1 >nul 2>&1

if errorlevel 1 (
    echo   ❌ FAIL: Payment service Lambda not found
    set /a FAIL_COUNT+=1
) else (
    echo   ✓ PASS: Payment service Lambda exists
    set /a PASS_COUNT+=1
)

REM Test 4: Webhook Lambda
echo [4/6] Testing Webhook Handler Lambda...
aws lambda get-function ^
    --function-name aquachain-function-razorpay-webhook-%ENVIRONMENT% ^
    --region us-east-1 >nul 2>&1

if errorlevel 1 (
    echo   ⚠ WARNING: Webhook Lambda not found (optional)
) else (
    echo   ✓ PASS: Webhook Lambda exists
    set /a PASS_COUNT+=1
)

REM Test 5: API Gateway
echo [5/6] Testing API Gateway...
aws cloudformation describe-stacks ^
    --stack-name AquaChain-API-%ENVIRONMENT% ^
    --query "Stacks[0].Outputs[?OutputKey=='RestApiUrl'].OutputValue" ^
    --output text >api.tmp 2>nul

if errorlevel 1 (
    echo   ❌ FAIL: API Gateway stack not found
    set /a FAIL_COUNT+=1
) else (
    set /p API_URL=<api.tmp
    if "%API_URL%"=="" (
        echo   ❌ FAIL: API Gateway URL not found
        set /a FAIL_COUNT+=1
    ) else (
        echo   ✓ PASS: API Gateway configured
        echo   URL: %API_URL%
        set /a PASS_COUNT+=1
    )
)
del api.tmp 2>nul

REM Test 6: DynamoDB Tables
echo [6/6] Testing DynamoDB Tables...
aws dynamodb describe-table ^
    --table-name aquachain-table-payments-%ENVIRONMENT% ^
    --region us-east-1 >nul 2>&1

if errorlevel 1 (
    echo   ❌ FAIL: Payments table not found
    set /a FAIL_COUNT+=1
) else (
    echo   ✓ PASS: Payments table exists
    set /a PASS_COUNT+=1
)

echo.
echo ========================================
echo   Test Results
echo ========================================
echo.
echo Passed: %PASS_COUNT%
echo Failed: %FAIL_COUNT%
echo.

if %FAIL_COUNT% EQU 0 (
    echo ✓ All tests passed! Razorpay integration is ready.
    echo.
    echo Next steps:
    echo   1. Start frontend: cd frontend ^&^& npm start
    echo   2. Create test order with test card: 4111 1111 1111 1111
    echo   3. Monitor logs: aws logs tail /aws/lambda/aquachain-function-payment-service-%ENVIRONMENT% --follow
) else (
    echo ❌ Some tests failed. Please review the errors above.
    echo.
    echo Common fixes:
    echo   - Run: scripts\setup\setup-razorpay-complete.bat
    echo   - Deploy infrastructure: cd infrastructure ^&^& python deploy-infrastructure.py %ENVIRONMENT%
    echo   - Check AWS credentials: aws sts get-caller-identity
)

echo.
pause
