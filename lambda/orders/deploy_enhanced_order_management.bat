@echo off
REM Deploy enhanced_order_management Lambda function

echo ========================================
echo Deploying Enhanced Order Management Lambda
echo ========================================

REM Set variables
set FUNCTION_NAME=aquachain-function-order-management-dev
set REGION=ap-south-1
set PACKAGE_FILE=enhanced-order-management-deployment.zip

echo.
echo Step 1: Creating deployment package...
echo ----------------------------------------

REM Remove old package if exists
if exist %PACKAGE_FILE% del %PACKAGE_FILE%

REM Create zip with handler and requirements
powershell -Command "Compress-Archive -Path enhanced_order_management.py,requirements.txt -DestinationPath %PACKAGE_FILE% -Force"

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
echo Step 3: Waiting for update to complete...
echo ----------------------------------------
timeout /t 5 /nobreak >nul

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
echo   1. Test the function: GET /dev/api/orders
echo   2. Check CloudWatch logs: /aws/lambda/%FUNCTION_NAME%
echo   3. Verify orders are returned correctly
echo.
echo CloudWatch Logs Command:
echo   aws logs tail /aws/lambda/%FUNCTION_NAME% --follow --region %REGION%
echo.

pause
