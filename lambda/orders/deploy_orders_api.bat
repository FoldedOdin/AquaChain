@echo off
REM Deploy orders API Lambda function
REM This script packages and deploys the working orders Lambda

echo ========================================
echo Deploying Orders API Lambda
echo ========================================

REM Set variables
set FUNCTION_NAME=aquachain-orders-api-dev
set PACKAGE_FILE=orders-api-deployment.zip

echo.
echo Step 1: Cleaning up old package...
if exist %PACKAGE_FILE% del %PACKAGE_FILE%
if exist package rmdir /s /q package

echo.
echo Step 2: Creating package directory...
mkdir package

echo.
echo Step 3: Installing dependencies...
pip install -r requirements.txt -t package --quiet

echo.
echo Step 4: Copying Lambda code...
copy lambda_function.py package\
copy create_order.py package\
copy get_orders.py package\
copy update_order_status.py package\
copy cancel_order.py package\

echo.
echo Step 5: Creating deployment package...
python create_deployment_package.py

echo.
echo Step 6: Deploying to AWS Lambda...
aws lambda update-function-code ^
    --function-name %FUNCTION_NAME% ^
    --zip-file fileb://%PACKAGE_FILE% ^
    --region ap-south-1

if %ERRORLEVEL% EQU 0 (
    echo.
    echo ========================================
    echo Deployment successful!
    echo ========================================
    echo.
    echo Function: %FUNCTION_NAME%
    echo Package: %PACKAGE_FILE%
    echo.
    echo Testing the deployment...
    timeout /t 3 /nobreak >nul
    aws lambda get-function --function-name %FUNCTION_NAME% --query "Configuration.[FunctionName,LastModified,Handler]" --output table
) else (
    echo.
    echo ========================================
    echo Deployment failed!
    echo ========================================
    exit /b 1
)

echo.
echo Step 7: Cleaning up...
rmdir /s /q package

echo.
echo Done!
