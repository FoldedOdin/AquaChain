@echo off
REM Simple deployment using Python zipfile (no PowerShell dependencies)

echo ========================================
echo Deploying Order Status Update Fix
echo ========================================
echo.

set AWS_REGION=ap-south-1
set FUNCTION_NAME=aquachain-update-order-status-dev

echo Step 1: Creating deployment package with Python...
python -c "import zipfile; z = zipfile.ZipFile('update_status_package.zip', 'w'); z.write('update_order_status.py'); z.close(); print('✅ Package created')"

if not exist update_status_package.zip (
    echo ERROR: Failed to create deployment package
    echo Make sure Python is installed
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
    del update_status_package.zip
    exit /b 1
)

echo.
echo Step 3: Waiting for function to update...
timeout /t 3 /nobreak >nul

echo.
echo Step 4: Verifying deployment...
aws lambda get-function ^
    --function-name %FUNCTION_NAME% ^
    --region %AWS_REGION% ^
    --query "Configuration.[FunctionName,LastModified,State]" ^
    --output table

echo.
echo ========================================
echo ✅ Deployment Complete!
echo ========================================
echo.
echo Test now:
echo 1. Go to My Orders page
echo 2. Click any order progress button
echo 3. Status should update without 500 error
echo.

del update_status_package.zip
echo Cleanup done.
pause
