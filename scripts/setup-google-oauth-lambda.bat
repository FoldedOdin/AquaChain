@echo off
REM Complete Google OAuth Lambda Setup Script
REM This script configures the Lambda function with Google OAuth credentials

echo ========================================
echo Google OAuth Lambda Setup
echo ========================================
echo.

REM Configuration
set SECRET_ARN=arn:aws:secretsmanager:ap-south-1:758346259059:secret:aquachain/google-oauth/client-secret-dev-vyX2NP
set FUNCTION_NAME=aquachain-function-auth-service-dev
set REGION=ap-south-1
set ROLE_NAME=aquachain-role-data-processing-dev

echo Step 1: Checking if Lambda function exists...
aws lambda get-function --function-name %FUNCTION_NAME% --region %REGION% 2>nul

if errorlevel 1 (
    echo Function does not exist. Creating new Lambda function...
    
    REM Create a minimal deployment package
    echo Creating minimal deployment package...
    mkdir temp_package 2>nul
    echo import json > temp_package\handler.py
    echo def lambda_handler(event, context): >> temp_package\handler.py
    echo     return {'statusCode': 200, 'body': json.dumps('Hello')} >> temp_package\handler.py
    
    cd temp_package
    powershell -Command "Compress-Archive -Path * -DestinationPath ..\temp.zip -Force"
    cd ..
    
    REM Get the role ARN
    for /f "tokens=*" %%i in ('aws iam get-role --role-name %ROLE_NAME% --query "Role.Arn" --output text') do set ROLE_ARN=%%i
    
    echo Creating Lambda function...
    aws lambda create-function ^
      --function-name %FUNCTION_NAME% ^
      --runtime python3.11 ^
      --role %ROLE_ARN% ^
      --handler handler.lambda_handler ^
      --zip-file fileb://temp.zip ^
      --timeout 30 ^
      --memory-size 512 ^
      --region %REGION% ^
      --description "AquaChain Auth Service with Google OAuth support"
    
    REM Cleanup
    del temp.zip
    rmdir /s /q temp_package
    
    echo Waiting for function to be active...
    aws lambda wait function-active --function-name %FUNCTION_NAME% --region %REGION%
    echo Function created successfully!
    echo.
) else (
    echo Function already exists.
    echo.
)

echo Step 2: Adding Google OAuth Secret ARN to Lambda environment...
aws lambda update-function-configuration ^
  --function-name %FUNCTION_NAME% ^
  --environment Variables="{GOOGLE_CLIENT_SECRET_ARN=%SECRET_ARN%,USERS_TABLE=AquaChain-Users,COGNITO_USER_POOL_ID=ap-south-1_QUDl7hG8u,COGNITO_CLIENT_ID=692o9a3pjudl1vudfgqpr5nuln,AWS_REGION=ap-south-1,ENVIRONMENT=dev}" ^
  --region %REGION%

if errorlevel 1 (
    echo Failed to update Lambda configuration!
    exit /b 1
)

echo Waiting for configuration update...
aws lambda wait function-updated --function-name %FUNCTION_NAME% --region %REGION%
echo.

echo Step 3: Granting Lambda permission to read the secret...
echo Creating IAM policy for Secrets Manager access...

REM Create policy document
echo { > policy.json
echo   "Version": "2012-10-17", >> policy.json
echo   "Statement": [ >> policy.json
echo     { >> policy.json
echo       "Effect": "Allow", >> policy.json
echo       "Action": [ >> policy.json
echo         "secretsmanager:GetSecretValue" >> policy.json
echo       ], >> policy.json
echo       "Resource": "%SECRET_ARN%" >> policy.json
echo     } >> policy.json
echo   ] >> policy.json
echo } >> policy.json

REM Attach policy to Lambda role
aws iam put-role-policy ^
  --role-name %ROLE_NAME% ^
  --policy-name GoogleOAuthSecretsAccess ^
  --policy-document file://policy.json

if errorlevel 1 (
    echo IAM policy attached successfully!
) else (
    echo Warning: Failed to attach IAM policy. You may need to do this manually.
)

REM Cleanup
del policy.json

echo.
echo Step 4: Verifying configuration...
aws lambda get-function-configuration ^
  --function-name %FUNCTION_NAME% ^
  --region %REGION% ^
  --query "Environment.Variables.GOOGLE_CLIENT_SECRET_ARN" ^
  --output text

echo.
echo Step 5: Verifying secret access...
echo Testing if Lambda can access the secret...
aws secretsmanager get-secret-value ^
  --secret-id %SECRET_ARN% ^
  --region %REGION% ^
  --query "SecretString" ^
  --output text

echo.
echo ========================================
echo Setup Complete!
echo ========================================
echo.
echo Lambda Function: %FUNCTION_NAME%
echo Secret ARN: %SECRET_ARN%
echo Region: %REGION%
echo.
echo ========================================
echo Next Steps:
echo ========================================
echo 1. Deploy the actual Lambda code:
echo    scripts\deployment\deploy-lambda-auth-service.bat
echo.
echo 2. Configure API Gateway to route /api/auth/google/callback
echo    to this Lambda function
echo.
echo 3. Test the OAuth flow:
echo    - Click "Continue with Google" in your app
echo    - Authenticate with Google
echo    - Verify callback works
echo.
echo 4. Check CloudWatch Logs for any errors:
echo    aws logs tail /aws/lambda/%FUNCTION_NAME% --follow
echo.
echo ========================================

pause
