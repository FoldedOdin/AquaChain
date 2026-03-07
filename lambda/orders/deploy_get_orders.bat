@echo off
REM Deploy get_orders Lambda function

echo ========================================
echo Deploying get_orders Lambda Function
echo ========================================

REM Set variables
set FUNCTION_NAME=aquachain-get-orders
set REGION=us-east-1
set PACKAGE_FILE=get-orders-deployment.zip

echo.
echo Step 1: Creating deployment package...
echo ----------------------------------------

REM Remove old package if exists
if exist %PACKAGE_FILE% del %PACKAGE_FILE%

REM Create zip with just the handler (no external dependencies needed)
powershell -Command "Compress-Archive -Path get_orders.py -DestinationPath %PACKAGE_FILE% -Force"

if not exist %PACKAGE_FILE% (
    echo ERROR: Failed to create deployment package
    exit /b 1
)

echo SUCCESS: Created %PACKAGE_FILE%

echo.
echo Step 2: Deploying to AWS Lambda...
echo ----------------------------------------

aws lambda update-function-code ^
    --function-name %FUNCTION_NAME% ^
    --zip-file fileb://%PACKAGE_FILE% ^
    --region %REGION%

if %ERRORLEVEL% NEQ 0 (
    echo ERROR: Failed to deploy Lambda function
    echo.
    echo Troubleshooting:
    echo   1. Check if function exists: aws lambda get-function --function-name %FUNCTION_NAME% --region %REGION%
    echo   2. Verify AWS credentials: aws sts get-caller-identity
    echo   3. Check IAM permissions for lambda:UpdateFunctionCode
    exit /b 1
)

echo.
echo ========================================
echo SUCCESS: Lambda function deployed!
echo ========================================
echo.
echo Function: %FUNCTION_NAME%
echo Region: %REGION%
echo Package: %PACKAGE_FILE%
echo.
echo Next steps:
echo   1. Test the function in AWS Console
echo   2. Check CloudWatch logs: /aws/lambda/%FUNCTION_NAME%
echo   3. Test from frontend: GET /dev/api/orders?consumerId=YOUR_ID
echo.

pause
