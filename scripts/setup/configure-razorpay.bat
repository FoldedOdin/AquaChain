@echo off
REM Razorpay Credentials Configuration Script
REM This script helps configure Razorpay API credentials in AWS Secrets Manager

echo ========================================
echo   AquaChain - Razorpay Configuration
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

echo This script will configure Razorpay credentials in AWS Secrets Manager.
echo.
echo You will need:
echo   1. Razorpay Key ID (starts with rzp_test_ or rzp_live_)
echo   2. Razorpay Key Secret
echo   3. AWS credentials configured (aws configure)
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

REM Get Razorpay credentials
:get_key_id
set /p KEY_ID="Enter Razorpay Key ID: "
if "%KEY_ID%"=="" goto get_key_id

REM Validate Key ID format
echo %KEY_ID% | findstr /R "^rzp_test_" >nul
if not errorlevel 1 (
    set KEY_TYPE=test
    goto key_id_valid
)

echo %KEY_ID% | findstr /R "^rzp_live_" >nul
if not errorlevel 1 (
    set KEY_TYPE=live
    goto key_id_valid
)

echo WARNING: Key ID does not match expected format (rzp_test_* or rzp_live_*)
set /p CONTINUE="Continue anyway? (y/n): "
if /i not "%CONTINUE%"=="y" goto get_key_id

:key_id_valid

:get_key_secret
set /p KEY_SECRET="Enter Razorpay Key Secret: "
if "%KEY_SECRET%"=="" goto get_key_secret

REM Optional webhook secret
echo.
echo Webhook Secret (optional - press Enter to skip):
set /p WEBHOOK_SECRET="Enter Razorpay Webhook Secret: "

echo.
echo ========================================
echo   Configuration Summary
echo ========================================
echo Environment: %ENVIRONMENT%
echo Key ID: %KEY_ID%
echo Key Secret: ********** (hidden)
if not "%WEBHOOK_SECRET%"=="" (
    echo Webhook Secret: ********** (hidden)
) else (
    echo Webhook Secret: (not configured)
)
echo.
echo Secret Name: aquachain-secret-razorpay-credentials-%ENVIRONMENT%
echo.

set /p CONFIRM="Proceed with configuration? (y/n): "
if /i not "%CONFIRM%"=="y" (
    echo Configuration cancelled.
    pause
    exit /b 0
)

echo.
echo Configuring AWS Secrets Manager...

REM Build JSON payload
if not "%WEBHOOK_SECRET%"=="" (
    set "SECRET_JSON={\"key_id\":\"%KEY_ID%\",\"key_secret\":\"%KEY_SECRET%\",\"webhook_secret\":\"%WEBHOOK_SECRET%\"}"
) else (
    set "SECRET_JSON={\"key_id\":\"%KEY_ID%\",\"key_secret\":\"%KEY_SECRET%\"}"
)

REM Update secret in AWS Secrets Manager
aws secretsmanager put-secret-value ^
    --secret-id aquachain-secret-razorpay-credentials-%ENVIRONMENT% ^
    --secret-string "%SECRET_JSON%" ^
    --region us-east-1 2>error.log

if errorlevel 1 (
    echo.
    echo ERROR: Failed to update secret in AWS Secrets Manager
    echo.
    type error.log
    del error.log
    echo.
    echo Possible causes:
    echo   1. AWS credentials not configured (run: aws configure)
    echo   2. Insufficient IAM permissions
    echo   3. Secret does not exist (deploy infrastructure first)
    echo   4. Incorrect AWS region
    pause
    exit /b 1
)

del error.log 2>nul

echo.
echo ========================================
echo   Configuration Successful!
echo ========================================
echo.
echo Razorpay credentials have been securely stored in AWS Secrets Manager.
echo.
echo Next steps:
echo   1. Configure frontend environment variable:
echo      REACT_APP_RAZORPAY_KEY_ID=%KEY_ID%
echo.
echo   2. Restart Lambda functions to pick up new credentials:
echo      aws lambda update-function-configuration --function-name aquachain-function-payment-service-%ENVIRONMENT% --environment Variables={FORCE_REFRESH=true}
echo.
echo   3. Test the integration:
echo      - Create a test order
echo      - Proceed to checkout
echo      - Use test card: 4111 1111 1111 1111
echo.
echo For detailed setup instructions, see:
echo   DOCS/guides/RAZORPAY_SETUP.md
echo.

pause
