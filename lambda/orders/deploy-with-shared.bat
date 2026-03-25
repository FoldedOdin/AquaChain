@echo off
REM Deploy enhanced_order_management with shared dependencies

echo ========================================
echo Deploying Order Management Lambda
echo (with shared dependencies)
echo ========================================
echo.

REM Clean up old files
if exist function.zip del function.zip
if exist shared rmdir /s /q shared

echo Step 1: Copying shared dependencies...
xcopy /E /I /Y ..\shared shared
echo.

echo Step 2: Creating deployment package...
python create_zip.py
if %ERRORLEVEL% NEQ 0 (
    echo ERROR: Failed to create deployment package
    rmdir /s /q shared
    exit /b 1
)

REM Cleanup shared directory
rmdir /s /q shared

if not exist function.zip (
    echo ERROR: function.zip not found
    exit /b 1
)

echo Package created:
dir function.zip
echo.

echo Step 3: Deploying to Lambda...
aws lambda update-function-code ^
    --function-name aquachain-function-order-management-dev ^
    --zip-file fileb://function.zip ^
    --region ap-south-1

if %ERRORLEVEL% NEQ 0 (
    echo ERROR: Deployment failed
    del function.zip
    exit /b 1
)

echo.
echo Waiting for Lambda to be active...
aws lambda wait function-updated ^
    --function-name aquachain-function-order-management-dev ^
    --region ap-south-1

echo.
echo Deployment complete!

del function.zip
pause
