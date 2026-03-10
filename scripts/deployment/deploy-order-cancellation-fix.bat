@echo off
REM Deploy order cancellation fix to AWS Lambda
REM This script deploys the updated validation schema for order management

echo ========================================
echo Deploying Order Cancellation Fix
echo ========================================
echo.

REM Check if AWS CLI is installed
where aws >nul 2>nul
if %ERRORLEVEL% NEQ 0 (
    echo ERROR: AWS CLI not found. Please install AWS CLI first.
    exit /b 1
)

REM Check AWS credentials
aws sts get-caller-identity >nul 2>nul
if %ERRORLEVEL% NEQ 0 (
    echo ERROR: AWS credentials not configured. Run 'aws configure' first.
    exit /b 1
)

echo Step 1: Packaging Lambda function...
cd lambda\orders
if exist function.zip del function.zip

REM Create deployment package using Python (more reliable on Windows)
python -m zipfile -c function.zip enhanced_order_management.py

if not exist function.zip (
    echo ERROR: Failed to create deployment package
    echo Trying alternative method...
    
    REM Fallback: Use tar command (available in Windows 10+)
    tar -a -c -f function.zip enhanced_order_management.py
)

if not exist function.zip (
    echo ERROR: Failed to create deployment package with all methods
    exit /b 1
)

echo Step 2: Deploying to Lambda...
aws lambda update-function-code ^
    --function-name aquachain-function-order-management-dev ^
    --zip-file fileb://function.zip

if %ERRORLEVEL% NEQ 0 (
    echo ERROR: Lambda deployment failed
    exit /b 1
)

echo.
echo Step 3: Waiting for Lambda to update...
timeout /t 5 /nobreak >nul

echo Step 4: Verifying deployment...
aws lambda get-function ^
    --function-name aquachain-function-order-management-dev ^
    --query "Configuration.[FunctionName,LastModified,State]" ^
    --output table

echo.
echo ========================================
echo Deployment Complete!
echo ========================================
echo.
echo Next steps:
echo 1. Test order cancellation in the UI
echo 2. Check CloudWatch logs: /aws/lambda/aquachain-function-order-management-dev
echo 3. Verify no validation errors
echo.
echo To test manually:
echo curl -X PUT https://vtqjfznspc.execute-api.ap-south-1.amazonaws.com/dev/api/orders/{ORDER_ID}/cancel \
echo   -H "Authorization: Bearer YOUR_TOKEN" \
echo   -H "Content-Type: application/json" \
echo   -d "{\"reason\": \"Test cancellation\"}"
echo.

REM Cleanup
del function.zip

cd ..\..
