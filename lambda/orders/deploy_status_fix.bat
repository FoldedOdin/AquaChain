@echo off
REM Deploy ONLY the update_order_status Lambda function with DynamoDB fix
REM This fixes the DATABASE_ERROR 500 issue

echo ========================================
echo Deploying Order Status Update Fix
echo ========================================
echo.

REM Set AWS region
set AWS_REGION=ap-south-1
set FUNCTION_NAME=AquaChain-Function-UpdateOrderStatus-dev

echo Step 1: Creating deployment package...
if exist update_status_package.zip del update_status_package.zip
powershell -Command "Compress-Archive -Path update_order_status.py -DestinationPath update_status_package.zip -Force"

if not exist update_status_package.zip (
    echo ERROR: Failed to create deployment package
    exit /b 1
)

echo.
echo Step 2: Deploying to AWS Lambda...
aws lambda update-function-code ^
    --function-name %FUNCTION_NAME% ^
    --zip-file fileb://update_status_package.zip ^
    --region %AWS_REGION%

if %ERRORLEVEL% NEQ 0 (
    echo.
    echo ERROR: Lambda deployment failed
    echo.
    echo Possible issues:
    echo 1. AWS CLI not configured - run: aws configure
    echo 2. Function name incorrect - check AWS Console
    echo 3. Insufficient IAM permissions
    exit /b 1
)

echo.
echo Step 3: Waiting for function to update...
timeout /t 5 /nobreak >nul

echo.
echo Step 4: Verifying deployment...
aws lambda get-function ^
    --function-name %FUNCTION_NAME% ^
    --region %AWS_REGION% ^
    --query "Configuration.[FunctionName,LastModified,State]" ^
    --output table

echo.
echo ========================================
echo Deployment Complete!
echo ========================================
echo.
echo Fixed Issues:
echo - DynamoDB atomic list_append for statusHistory
echo - Proper error handling for missing orders
echo - Better exception handling with error codes
echo.
echo Test the fix:
echo 1. Go to My Orders page
echo 2. Click any order progress button
echo 3. Status should update without 500 error
echo.
echo Cleanup...
del update_status_package.zip

echo.
echo Done! The DATABASE_ERROR should be resolved.
pause
