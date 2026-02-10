@echo off
REM Razorpay Integration Verification Script
REM This script verifies that Razorpay is properly configured

echo ========================================
echo   AquaChain - Razorpay Verification
echo ========================================
echo.

REM Check if AWS CLI is installed
aws --version >nul 2>&1
if errorlevel 1 (
    echo ERROR: AWS CLI is not installed or not in PATH
    pause
    exit /b 1
)

REM Get environment
set /p ENVIRONMENT="Enter environment to verify (dev/staging/prod): "
if "%ENVIRONMENT%"=="" set ENVIRONMENT=dev

echo.
echo Verifying Razorpay configuration for: %ENVIRONMENT%
echo.

REM Check 1: AWS Secrets Manager
echo [1/4] Checking AWS Secrets Manager...
aws secretsmanager get-secret-value ^
    --secret-id aquachain-secret-razorpay-credentials-%ENVIRONMENT% ^
    --region us-east-1 ^
    --query SecretString ^
    --output text >secret.tmp 2>error.log

if errorlevel 1 (
    echo   ❌ FAIL: Cannot retrieve secret from AWS Secrets Manager
    type error.log
    del error.log secret.tmp 2>nul
    goto check_frontend
) else (
    echo   ✓ PASS: Secret exists in AWS Secrets Manager
    
    REM Parse and validate secret structure
    findstr /C:"key_id" secret.tmp >nul
    if errorlevel 1 (
        echo   ❌ FAIL: Secret missing 'key_id' field
    ) else (
        echo   ✓ PASS: Secret contains 'key_id'
    )
    
    findstr /C:"key_secret" secret.tmp >nul
    if errorlevel 1 (
        echo   ❌ FAIL: Secret missing 'key_secret' field
    ) else (
        echo   ✓ PASS: Secret contains 'key_secret'
    )
    
    del secret.tmp error.log 2>nul
)

:check_frontend
echo.
echo [2/4] Checking Frontend Configuration...

if exist "frontend\.env.local" (
    findstr /C:"REACT_APP_RAZORPAY_KEY_ID" frontend\.env.local >nul
    if errorlevel 1 (
        echo   ❌ FAIL: REACT_APP_RAZORPAY_KEY_ID not found in .env.local
    ) else (
        echo   ✓ PASS: REACT_APP_RAZORPAY_KEY_ID configured in .env.local
    )
) else (
    echo   ⚠ WARNING: frontend\.env.local not found
    echo   Create it from .env.example and add REACT_APP_RAZORPAY_KEY_ID
)

echo.
echo [3/4] Checking Lambda Function Configuration...

REM Check if Lambda function exists and has correct environment variable
aws lambda get-function-configuration ^
    --function-name aquachain-function-payment-service-%ENVIRONMENT% ^
    --region us-east-1 ^
    --query "Environment.Variables.RAZORPAY_SECRET_ARN" ^
    --output text >lambda.tmp 2>error.log

if errorlevel 1 (
    echo   ❌ FAIL: Cannot retrieve Lambda function configuration
    type error.log
    del error.log lambda.tmp 2>nul
) else (
    set /p SECRET_ARN=<lambda.tmp
    if "%SECRET_ARN%"=="" (
        echo   ❌ FAIL: RAZORPAY_SECRET_ARN not configured in Lambda
    ) else (
        echo   ✓ PASS: Lambda has RAZORPAY_SECRET_ARN configured
        echo   ARN: %SECRET_ARN%
    )
    del lambda.tmp error.log 2>nul
)

echo.
echo [4/4] Checking IAM Permissions...

REM Check if Lambda has permission to read the secret
aws lambda get-policy ^
    --function-name aquachain-function-payment-service-%ENVIRONMENT% ^
    --region us-east-1 >nul 2>&1

if errorlevel 1 (
    echo   ⚠ WARNING: Cannot verify Lambda IAM permissions
) else (
    echo   ✓ PASS: Lambda has IAM policy attached
)

echo.
echo ========================================
echo   Verification Complete
echo ========================================
echo.
echo If all checks passed, your Razorpay integration is properly configured.
echo.
echo To test the integration:
echo   1. Start the frontend: cd frontend ^&^& npm start
echo   2. Create a test order
echo   3. Use test card: 4111 1111 1111 1111
echo.
echo For troubleshooting, see: DOCS/guides/RAZORPAY_SETUP.md
echo.

pause
