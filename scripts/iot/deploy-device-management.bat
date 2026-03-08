@echo off
REM Deploy Device Management Lambda Function
REM This script packages and deploys the device management Lambda

echo ========================================
echo AquaChain Device Management Deployment
echo ========================================
echo.

set FUNCTION_NAME=aquachain-function-device-management-dev
set REGION=ap-south-1
set LAMBDA_DIR=lambda\device_management

echo Step 1: Packaging Lambda function...
cd %LAMBDA_DIR%

REM Create deployment package
if exist package.zip del package.zip
powershell -Command "Compress-Archive -Path handler.py,requirements.txt -DestinationPath package.zip -Force"

echo.
echo Step 2: Deploying to AWS Lambda...
aws lambda update-function-code ^
    --function-name %FUNCTION_NAME% ^
    --zip-file fileb://package.zip ^
    --region %REGION%

if %ERRORLEVEL% EQU 0 (
    echo.
    echo ✓ Deployment successful!
    echo.
    echo Function: %FUNCTION_NAME%
    echo Region: %REGION%
    echo.
    echo Testing the function...
    aws lambda invoke ^
        --function-name %FUNCTION_NAME% ^
        --payload "{\"httpMethod\":\"GET\",\"path\":\"/devices\"}" ^
        --region %REGION% ^
        response.json
    
    echo.
    echo Response:
    type response.json
    echo.
) else (
    echo.
    echo ✗ Deployment failed!
    echo Check AWS credentials and function name.
)

cd ..\..
pause
