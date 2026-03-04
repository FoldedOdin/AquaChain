@echo off
REM Deploy Auth Service Lambda with Google OAuth Support
REM This script packages and deploys the auth service Lambda function

echo ========================================
echo Deploying Auth Service Lambda Function
echo ========================================
echo.

REM Configuration
set FUNCTION_NAME=aquachain-function-auth-service-dev
set LAMBDA_DIR=lambda\auth_service
set PACKAGE_DIR=%LAMBDA_DIR%\package
set ZIP_FILE=%LAMBDA_DIR%\function.zip

echo Step 1: Cleaning previous build...
if exist "%ZIP_FILE%" del "%ZIP_FILE%"
if exist "%PACKAGE_DIR%" rmdir /s /q "%PACKAGE_DIR%"
mkdir "%PACKAGE_DIR%"

echo Step 2: Installing dependencies...
pip install -r "%LAMBDA_DIR%\requirements.txt" -t "%PACKAGE_DIR%" --upgrade

echo Step 3: Copying Lambda function files...
copy "%LAMBDA_DIR%\handler.py" "%PACKAGE_DIR%\"
copy "%LAMBDA_DIR%\google_oauth_handler.py" "%PACKAGE_DIR%\"
copy "%LAMBDA_DIR%\auth_utils.py" "%PACKAGE_DIR%\"
copy "%LAMBDA_DIR%\recaptcha_verifier.py" "%PACKAGE_DIR%\"

echo Step 4: Copying shared utilities...
xcopy "lambda\shared\*.py" "%PACKAGE_DIR%\" /Y

echo Step 5: Creating deployment package...
cd "%PACKAGE_DIR%"
tar -a -c -f ..\function.zip *
cd ..\..\..\

echo Step 6: Deploying to AWS Lambda...
aws lambda update-function-code ^
  --function-name %FUNCTION_NAME% ^
  --zip-file fileb://%ZIP_FILE% ^
  --region ap-south-1

if %ERRORLEVEL% EQU 0 (
    echo.
    echo ========================================
    echo Deployment Successful!
    echo ========================================
    echo Function: %FUNCTION_NAME%
    echo Region: ap-south-1
    echo.
    echo Waiting for function to be active...
    aws lambda wait function-updated --function-name %FUNCTION_NAME% --region ap-south-1
    
    echo.
    echo Verifying deployment...
    aws lambda get-function --function-name %FUNCTION_NAME% --region ap-south-1 --query "Configuration.[FunctionName,LastModified,CodeSize,State]" --output table
    
    echo.
    echo ========================================
    echo Next Steps:
    echo ========================================
    echo 1. Configure Google OAuth credentials in Google Cloud Console
    echo 2. Store Google Client Secret in AWS Secrets Manager
    echo 3. Update Lambda environment variables with Secret ARN
    echo 4. Test the /api/auth/google/callback endpoint
    echo 5. Verify user creation in DynamoDB
    echo.
    echo See DOCS/guides/GOOGLE_OAUTH_SETUP_GUIDE.md for details
    echo ========================================
) else (
    echo.
    echo ========================================
    echo Deployment Failed!
    echo ========================================
    echo Please check the error message above
    echo.
    exit /b 1
)

echo.
echo Cleaning up...
rmdir /s /q "%PACKAGE_DIR%"

echo Done!
pause
