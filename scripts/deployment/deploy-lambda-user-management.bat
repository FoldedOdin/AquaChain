@echo off
REM Deploy User Management Lambda Function (Windows)
REM This script packages and deploys the user_management Lambda function to AWS

setlocal enabledelayedexpansion

REM Configuration
set FUNCTION_NAME=AquaChain-Function-UserManagement-dev
set REGION=ap-south-1
set LAMBDA_DIR=lambda\user_management

echo.
echo 🚀 Deploying User Management Lambda Function
echo ==============================================
echo.

REM Check if AWS CLI is installed
where aws >nul 2>nul
if %ERRORLEVEL% NEQ 0 (
    echo ❌ AWS CLI is not installed. Please install it first.
    exit /b 1
)

REM Check if we're in the project root
if not exist "%LAMBDA_DIR%" (
    echo ❌ Lambda directory not found. Please run this script from the project root.
    exit /b 1
)

REM Navigate to Lambda directory
cd "%LAMBDA_DIR%"

echo 📦 Packaging Lambda function...

REM Remove old package if exists
if exist function.zip del function.zip

REM Package the function with ALL dependencies (using PowerShell for zip)
powershell -Command "Compress-Archive -Path handler.py,errors.py,error_handler.py,structured_logger.py,audit_logger.py,cors_utils.py,cache_service.py,user_utils.py -DestinationPath function.zip -Force"

if %ERRORLEVEL% NEQ 0 (
    echo ❌ Failed to create package
    exit /b 1
)

echo ✅ Package created: function.zip
echo.

REM Check if function exists
echo 🔍 Checking current Lambda configuration...
aws lambda get-function-configuration --function-name "%FUNCTION_NAME%" --region "%REGION%" --query "Runtime" --output text >nul 2>&1

if %ERRORLEVEL% NEQ 0 (
    echo ❌ Lambda function '%FUNCTION_NAME%' not found in region '%REGION%'
    echo    Please create the function first using CDK or AWS Console
    exit /b 1
)

echo ✅ Function found: %FUNCTION_NAME%
echo.

REM Deploy to AWS Lambda
echo 🚀 Deploying to AWS Lambda...
aws lambda update-function-code --function-name "%FUNCTION_NAME%" --zip-file fileb://function.zip --region "%REGION%" --output json >nul

if %ERRORLEVEL% NEQ 0 (
    echo ❌ Failed to upload code
    exit /b 1
)

echo ✅ Code uploaded successfully
echo.

REM Wait for function to be updated
echo ⏳ Waiting for function to be updated...
aws lambda wait function-updated --function-name "%FUNCTION_NAME%" --region "%REGION%"

echo ✅ Function updated successfully
echo.

REM Get updated function info
echo 📊 Function Information:
aws lambda get-function-configuration --function-name "%FUNCTION_NAME%" --region "%REGION%" --query "{FunctionName:FunctionName,Runtime:Runtime,LastModified:LastModified,CodeSize:CodeSize,MemorySize:MemorySize,Timeout:Timeout}" --output table

echo.
echo ✅ Deployment completed successfully!
echo.
echo 🔍 Next Steps:
echo 1. Test the email update functionality
echo 2. Check CloudWatch logs: /aws/lambda/%FUNCTION_NAME%
echo 3. Monitor for any errors in the next 15 minutes
echo.
echo 📝 CloudWatch Logs:
echo    aws logs tail /aws/lambda/%FUNCTION_NAME% --follow --region %REGION%
echo.

REM Cleanup
del function.zip

cd ..\..
