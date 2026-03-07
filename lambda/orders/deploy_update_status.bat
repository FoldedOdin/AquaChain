@echo off
echo ========================================
echo Deploying Update Order Status Lambda
echo ========================================

cd /d "%~dp0"

REM Create deployment package
echo Creating deployment package...
if exist update-status-package.zip del update-status-package.zip
powershell -Command "Compress-Archive -Path update_order_status.py -DestinationPath update-status-package.zip -Force"

REM Check if Lambda function exists
echo Checking if Lambda function exists...
aws lambda get-function --function-name aquachain-update-order-status-dev --region ap-south-1 >nul 2>&1

if %ERRORLEVEL% EQU 0 (
    echo Lambda function exists, updating code...
    aws lambda update-function-code ^
        --function-name aquachain-update-order-status-dev ^
        --zip-file fileb://update-status-package.zip ^
        --region ap-south-1
) else (
    echo Lambda function does not exist, creating...
    aws lambda create-function ^
        --function-name aquachain-update-order-status-dev ^
        --runtime python3.11 ^
        --role arn:aws:iam::758346259059:role/aquachain-lambda-execution-role ^
        --handler update_order_status.handler ^
        --zip-file fileb://update-status-package.zip ^
        --timeout 30 ^
        --memory-size 512 ^
        --environment Variables={ORDERS_TABLE=aquachain-orders} ^
        --region ap-south-1
)

echo.
echo ========================================
echo Deployment Complete!
echo ========================================
echo Function: aquachain-update-order-status-dev
echo Region: ap-south-1
echo ========================================
