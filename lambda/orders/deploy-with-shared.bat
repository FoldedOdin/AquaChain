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

echo Step 2: Creating deployment package...
REM Use Python to create zip (more reliable than PowerShell)
python -c "import zipfile, os; z = zipfile.ZipFile('function.zip', 'w', zipfile.ZIP_DEFLATED); z.write('enhanced_order_management.py'); [z.write(os.path.join('shared', f), os.path.join('shared', f)) for f in os.listdir('shared') if f.endswith('.py')]; z.close(); print('✓ ZIP created')"

REM Cleanup shared directory
rmdir /s /q shared

if not exist function.zip (
    echo ERROR: Failed to create deployment package
    exit /b 1
)

echo ✓ Package created successfully
dir function.zip

echo.
echo Step 3: Deploying to Lambda...
aws lambda update-function-code ^
    --function-name aquachain-function-order-management-dev ^
    --zip-file fileb://function.zip

if %ERRORLEVEL% NEQ 0 (
    echo ERROR: Deployment failed
    exit /b 1
)

echo.
echo ✓ Deployment complete!
echo.
echo Step 4: Waiting for Lambda to initialize...
timeout /t 5 /nobreak >nul

echo.
echo Step 5: Testing the deployment...
echo Run this command to test:
echo.
echo curl -X PUT https://vtqjfznspc.execute-api.ap-south-1.amazonaws.com/dev/api/orders/YOUR_ORDER_ID/cancel ^
echo   -H "Authorization: Bearer YOUR_TOKEN" ^
echo   -H "Content-Type: application/json" ^
echo   -d "{\"reason\": \"Test cancellation\"}"
echo.

REM Cleanup
del function.zip

echo Done!
pause
