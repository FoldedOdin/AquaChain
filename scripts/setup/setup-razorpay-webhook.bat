@echo off
REM Razorpay Webhook Setup Script
REM This script helps you configure webhooks in Razorpay dashboard

echo ========================================
echo   AquaChain - Razorpay Webhook Setup
echo ========================================
echo.

REM Check if AWS CLI is installed
aws --version >nul 2>&1
if errorlevel 1 (
    echo ERROR: AWS CLI is not installed or not in PATH
    echo Please install AWS CLI: https://aws.amazon.com/cli/
    pause
    exit /b 1
)

echo This script will help you set up Razorpay webhooks.
echo.

REM Get environment
:get_environment
set /p ENVIRONMENT="Enter environment (dev/staging/prod): "
if "%ENVIRONMENT%"=="" goto get_environment
if not "%ENVIRONMENT%"=="dev" if not "%ENVIRONMENT%"=="staging" if not "%ENVIRONMENT%"=="prod" (
    echo Invalid environment. Please enter dev, staging, or prod.
    goto get_environment
)

echo.
echo Selected environment: %ENVIRONMENT%
echo.

REM Get API Gateway URL
echo Fetching API Gateway URL...
aws cloudformation describe-stacks ^
    --stack-name AquaChain-API-%ENVIRONMENT% ^
    --query "Stacks[0].Outputs[?OutputKey=='RestApiUrl'].OutputValue" ^
    --output text >api_url.tmp 2>error.log

if errorlevel 1 (
    echo WARNING: Could not automatically fetch API Gateway URL
    echo.
    set /p API_URL="Enter your API Gateway URL manually: "
) else (
    set /p API_URL=<api_url.tmp
    echo Found API Gateway URL: %API_URL%
)

del api_url.tmp error.log 2>nul

REM Construct webhook URL
set "WEBHOOK_URL=%API_URL%/api/webhooks/razorpay"

echo.
echo ========================================
echo   Webhook Configuration
echo ========================================
echo.
echo Your webhook URL is:
echo   %WEBHOOK_URL%
echo.
echo Please follow these steps to configure the webhook in Razorpay:
echo.
echo 1. Log in to Razorpay Dashboard: https://dashboard.razorpay.com
echo.
echo 2. Navigate to: Settings ^> Webhooks
echo.
echo 3. Click "Create Webhook" or "Add New Webhook"
echo.
echo 4. Enter the webhook URL:
echo    %WEBHOOK_URL%
echo.
echo 5. Select the following events:
echo    [x] payment.authorized
echo    [x] payment.captured
echo    [x] payment.failed
echo    [x] order.paid
echo.
echo 6. Set "Active" to ON
echo.
echo 7. Click "Create Webhook"
echo.
echo 8. Copy the "Webhook Secret" that Razorpay generates
echo.

set /p WEBHOOK_SECRET="Enter the Webhook Secret from Razorpay: "

if "%WEBHOOK_SECRET%"=="" (
    echo.
    echo WARNING: No webhook secret provided.
    echo You can add it later using the configure-razorpay.bat script.
    echo.
    pause
    exit /b 0
)

echo.
echo Updating webhook secret in AWS Secrets Manager...

REM Get existing secret
aws secretsmanager get-secret-value ^
    --secret-id aquachain-secret-razorpay-credentials-%ENVIRONMENT% ^
    --query SecretString ^
    --output text >secret.tmp 2>error.log

if errorlevel 1 (
    echo ERROR: Could not retrieve existing secret
    type error.log
    del error.log secret.tmp 2>nul
    pause
    exit /b 1
)

REM Parse existing secret and add webhook_secret
REM Note: This is a simple approach. For production, use jq or Python for JSON manipulation
echo.
echo Please manually update the secret to include webhook_secret:
echo.
echo Current secret value:
type secret.tmp
echo.
echo.
echo Add the following field to the JSON:
echo   "webhook_secret": "%WEBHOOK_SECRET%"
echo.
echo You can update it using AWS Console or run:
echo   aws secretsmanager put-secret-value --secret-id aquachain-secret-razorpay-credentials-%ENVIRONMENT% --secret-string "{\"key_id\":\"YOUR_KEY_ID\",\"key_secret\":\"YOUR_KEY_SECRET\",\"webhook_secret\":\"%WEBHOOK_SECRET%\"}"
echo.

del secret.tmp error.log 2>nul

echo.
echo ========================================
echo   Testing Webhook
echo ========================================
echo.
echo To test your webhook:
echo.
echo 1. In Razorpay Dashboard, go to the webhook you just created
echo.
echo 2. Click "Send Test Webhook"
echo.
echo 3. Select "payment.captured" event
echo.
echo 4. Click "Send"
echo.
echo 5. Check AWS CloudWatch Logs for the webhook Lambda:
echo    aws logs tail /aws/lambda/aquachain-function-razorpay-webhook-%ENVIRONMENT% --follow
echo.
echo 6. You should see a log entry indicating the webhook was received
echo.
echo ========================================
echo   Important Security Notes
echo ========================================
echo.
echo - The webhook endpoint does NOT require authentication
echo - Security is provided by HMAC signature verification
echo - Never disable signature verification in production
echo - Rotate webhook secrets periodically
echo - Monitor webhook logs for suspicious activity
echo.
echo For more information, see: DOCS/guides/RAZORPAY_SETUP.md
echo.

pause
