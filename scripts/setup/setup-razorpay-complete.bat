@echo off
REM Complete Razorpay Setup Script for AquaChain
REM This script performs end-to-end Razorpay integration setup

echo ========================================
echo   AquaChain - Complete Razorpay Setup
echo ========================================
echo.

REM Check AWS CLI
aws --version >nul 2>&1
if errorlevel 1 (
    echo ERROR: AWS CLI not installed
    echo Install from: https://aws.amazon.com/cli/
    pause
    exit /b 1
)

echo This script will set up Razorpay integration completely.
echo.
echo You will need:
echo   1. Razorpay Key ID (from dashboard.razorpay.com)
echo   2. Razorpay Key Secret
echo   3. AWS credentials configured
echo.

REM Step 1: Get environment
:get_environment
set /p ENVIRONMENT="Enter environment (dev/staging/prod) [dev]: "
if "%ENVIRONMENT%"=="" set ENVIRONMENT=dev

echo.
echo Selected environment: %ENVIRONMENT%
echo.

REM Step 2: Get Razorpay credentials
echo ========================================
echo   Step 1: Razorpay Credentials
echo ========================================
echo.
echo Get your credentials from: https://dashboard.razorpay.com/app/keys
echo.

:get_key_id
set /p KEY_ID="Enter Razorpay Key ID (rzp_test_* or rzp_live_*): "
if "%KEY_ID%"=="" goto get_key_id

:get_key_secret
set /p KEY_SECRET="Enter Razorpay Key Secret: "
if "%KEY_SECRET%"=="" goto get_key_secret

REM Step 3: Store in AWS Secrets Manager
echo.
echo ========================================
echo   Step 2: Storing in AWS Secrets Manager
echo ========================================
echo.

set "SECRET_JSON={\"key_id\":\"%KEY_ID%\",\"key_secret\":\"%KEY_SECRET%\"}"

aws secretsmanager put-secret-value ^
    --secret-id aquachain-secret-razorpay-credentials-%ENVIRONMENT% ^
    --secret-string "%SECRET_JSON%" ^
    --region us-east-1 2>error.log

if errorlevel 1 (
    echo ERROR: Failed to store credentials in AWS Secrets Manager
    type error.log
    del error.log
    echo.
    echo Possible causes:
    echo   1. Secret does not exist - deploy infrastructure first
    echo   2. Insufficient IAM permissions
    echo   3. AWS credentials not configured
    pause
    exit /b 1
)

del error.log 2>nul
echo ✓ Credentials stored in AWS Secrets Manager
echo.

REM Step 4: Configure frontend
echo ========================================
echo   Step 3: Configuring Frontend
echo ========================================
echo.

REM Check if .env.local exists
if exist "frontend\.env.local" (
    echo Found existing frontend\.env.local
    findstr /C:"REACT_APP_RAZORPAY_KEY_ID" frontend\.env.local >nul
    if errorlevel 1 (
        echo Adding REACT_APP_RAZORPAY_KEY_ID to .env.local
        echo REACT_APP_RAZORPAY_KEY_ID=%KEY_ID% >> frontend\.env.local
    ) else (
        echo Updating REACT_APP_RAZORPAY_KEY_ID in .env.local
        powershell -Command "(Get-Content frontend\.env.local) -replace 'REACT_APP_RAZORPAY_KEY_ID=.*', 'REACT_APP_RAZORPAY_KEY_ID=%KEY_ID%' | Set-Content frontend\.env.local"
    )
) else (
    echo Creating frontend\.env.local from .env.example
    copy frontend\.env.example frontend\.env.local >nul
    echo REACT_APP_RAZORPAY_KEY_ID=%KEY_ID% >> frontend\.env.local
)

echo ✓ Frontend configured with Razorpay Key ID
echo.

REM Step 5: Get API Gateway URL for webhook
echo ========================================
echo   Step 4: Webhook Configuration
echo ========================================
echo.

echo Fetching API Gateway URL...
for /f "delims=" %%i in ('aws cloudformation describe-stacks --stack-name AquaChain-API-%ENVIRONMENT% --query "Stacks[0].Outputs[?OutputKey=='RestApiUrl'].OutputValue" --output text 2^>nul') do set API_URL=%%i

if "%API_URL%"=="" (
    echo WARNING: Could not fetch API Gateway URL
    echo Infrastructure may not be deployed yet
    echo.
    echo You can configure webhooks later using:
    echo   scripts\setup\setup-razorpay-webhook.bat
    echo.
) else (
    set WEBHOOK_URL=%API_URL%/api/webhooks/razorpay
    echo.
    echo ✓ API Gateway URL found
    echo.
    echo ========================================
    echo   Webhook URL (copy this):
    echo ========================================
    echo.
    echo %WEBHOOK_URL%
    echo.
    echo ========================================
    echo.
    echo Next: Configure webhook in Razorpay Dashboard
    echo.
    echo 1. Go to: https://dashboard.razorpay.com/app/webhooks
    echo 2. Click "Create Webhook"
    echo 3. Paste the URL above
    echo 4. Select events:
    echo    - payment.authorized
    echo    - payment.captured
    echo    - payment.failed
    echo    - order.paid
    echo 5. Set Active: ON
    echo 6. Click "Create"
    echo 7. Copy the Webhook Secret
    echo.
    
    set /p WEBHOOK_SECRET="Enter Webhook Secret (or press Enter to skip): "
    
    if not "%WEBHOOK_SECRET%"=="" (
        echo.
        echo Updating secret with webhook secret...
        set "SECRET_JSON_WITH_WEBHOOK={\"key_id\":\"%KEY_ID%\",\"key_secret\":\"%KEY_SECRET%\",\"webhook_secret\":\"%WEBHOOK_SECRET%\"}"
        
        aws secretsmanager put-secret-value ^
            --secret-id aquachain-secret-razorpay-credentials-%ENVIRONMENT% ^
            --secret-string "%SECRET_JSON_WITH_WEBHOOK%" ^
            --region us-east-1 2>nul
        
        if errorlevel 1 (
            echo WARNING: Failed to update webhook secret
        ) else (
            echo ✓ Webhook secret stored
        )
    )
)

echo.
echo ========================================
echo   Setup Complete!
echo ========================================
echo.
echo ✓ Razorpay credentials stored in AWS Secrets Manager
echo ✓ Frontend configured with Key ID
if not "%WEBHOOK_URL%"=="" (
    echo ✓ Webhook URL ready for configuration
)
echo.
echo Next Steps:
echo.
echo 1. Test the integration:
echo    cd frontend
echo    npm start
echo.
echo 2. Create a test order and use test card:
echo    Card: 4111 1111 1111 1111
echo    CVV: Any 3 digits
echo    Expiry: Any future date
echo.
echo 3. Monitor webhook processing:
echo    aws logs tail /aws/lambda/aquachain-function-razorpay-webhook-%ENVIRONMENT% --follow
echo.
echo 4. Verify setup:
echo    scripts\setup\verify-razorpay.bat
echo.
echo For detailed documentation, see:
echo   DOCS/guides/RAZORPAY_SETUP.md
echo.

pause
