@echo off
REM Deploy profile OTP endpoint fix
REM This script updates the user management Lambda with OTP functionality

echo ========================================
echo Deploying Profile OTP Endpoint Fix
echo ========================================
echo.

REM Check if AWS CLI is available
where aws >nul 2>nul
if %ERRORLEVEL% NEQ 0 (
    echo ERROR: AWS CLI not found. Please install AWS CLI first.
    exit /b 1
)

echo Step 1: Packaging user management Lambda...
cd lambda\user_management

REM Create deployment package
if exist package.zip del package.zip
powershell -Command "Compress-Archive -Path handler.py,encrypted_user_service.py -DestinationPath package.zip -Force"

echo.
echo Step 2: Updating Lambda function...
aws lambda update-function-code ^
    --function-name aquachain-user-management-dev ^
    --zip-file fileb://package.zip ^
    --region ap-south-1

if %ERRORLEVEL% NEQ 0 (
    echo ERROR: Failed to update Lambda function
    cd ..\..
    exit /b 1
)

echo.
echo Step 3: Waiting for Lambda update to complete...
timeout /t 5 /nobreak >nul

echo.
echo Step 4: Testing OPTIONS endpoint...
curl -X OPTIONS ^
    -H "Origin: http://localhost:3000" ^
    -H "Access-Control-Request-Method: POST" ^
    -H "Access-Control-Request-Headers: Content-Type,Authorization" ^
    https://vtqjfznspc.execute-api.ap-south-1.amazonaws.com/dev/api/profile/request-otp

echo.
echo.
echo ========================================
echo Deployment Complete!
echo ========================================
echo.
echo Next steps:
echo 1. Test the profile update flow in the frontend
echo 2. Check CloudWatch logs for any errors
echo 3. Monitor the OTP generation in logs
echo.
echo Note: The /api/profile/request-otp endpoint should now handle CORS properly
echo.

cd ..\..
