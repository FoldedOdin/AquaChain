@echo off
REM Configure ML Inference Lambda to use SageMaker Endpoint
REM This script updates the Lambda environment variables and IAM permissions

echo ============================================================
echo Configure ML Inference Lambda for SageMaker Integration
echo ============================================================
echo.

set FUNCTION_NAME=aquachain-function-ml-inference-dev
set ENDPOINT_NAME=aquachain-wqi-endpoint-dev
set REGION=ap-south-1
set ACCOUNT_ID=758346259059

echo Step 1: Update Lambda Environment Variables
echo ------------------------------------------------------------
aws lambda update-function-configuration ^
  --function-name %FUNCTION_NAME% ^
  --environment "Variables={SAGEMAKER_ENDPOINT_NAME=%ENDPOINT_NAME%,ENABLE_MONITORING=true,ENVIRONMENT=dev,REGION=%REGION%}" ^
  --region %REGION%

if %ERRORLEVEL% NEQ 0 (
    echo ERROR: Failed to update Lambda environment variables
    exit /b 1
)

echo.
echo SUCCESS: Lambda environment variables updated
echo.

echo Step 2: Get Lambda Execution Role
echo ------------------------------------------------------------
for /f "tokens=*" %%i in ('aws lambda get-function-configuration --function-name %FUNCTION_NAME% --region %REGION% --query "Role" --output text') do set LAMBDA_ROLE_ARN=%%i

REM Extract role name from ARN (format: arn:aws:iam::ACCOUNT:role/ROLE_NAME)
for /f "tokens=2 delims=/" %%a in ("%LAMBDA_ROLE_ARN%") do set ROLE_NAME=%%a

echo Lambda Role ARN: %LAMBDA_ROLE_ARN%
echo Lambda Role Name: %ROLE_NAME%
echo.

echo Step 3: Create SageMaker Invoke Policy
echo ------------------------------------------------------------

REM Create temporary policy file
echo { > %TEMP%\sagemaker-policy.json
echo   "Version": "2012-10-17", >> %TEMP%\sagemaker-policy.json
echo   "Statement": [ >> %TEMP%\sagemaker-policy.json
echo     { >> %TEMP%\sagemaker-policy.json
echo       "Effect": "Allow", >> %TEMP%\sagemaker-policy.json
echo       "Action": [ >> %TEMP%\sagemaker-policy.json
echo         "sagemaker:InvokeEndpoint" >> %TEMP%\sagemaker-policy.json
echo       ], >> %TEMP%\sagemaker-policy.json
echo       "Resource": "arn:aws:sagemaker:%REGION%:%ACCOUNT_ID%:endpoint/%ENDPOINT_NAME%" >> %TEMP%\sagemaker-policy.json
echo     } >> %TEMP%\sagemaker-policy.json
echo   ] >> %TEMP%\sagemaker-policy.json
echo } >> %TEMP%\sagemaker-policy.json

echo Policy created at: %TEMP%\sagemaker-policy.json
echo.

echo Step 4: Attach Policy to Lambda Role
echo ------------------------------------------------------------
aws iam put-role-policy ^
  --role-name %ROLE_NAME% ^
  --policy-name SageMakerInvokePolicy ^
  --policy-document file://%TEMP%\sagemaker-policy.json

if %ERRORLEVEL% NEQ 0 (
    echo ERROR: Failed to attach policy to role
    exit /b 1
)

echo.
echo SUCCESS: SageMaker invoke policy attached
echo.

echo Step 5: Verify Configuration
echo ------------------------------------------------------------
echo Checking Lambda configuration...
aws lambda get-function-configuration ^
  --function-name %FUNCTION_NAME% ^
  --region %REGION% ^
  --query "Environment.Variables" ^
  --output json

echo.
echo Checking SageMaker endpoint status...
aws sagemaker describe-endpoint ^
  --endpoint-name %ENDPOINT_NAME% ^
  --region %REGION% ^
  --query "EndpointStatus" ^
  --output text

echo.
echo ============================================================
echo Configuration Complete!
echo ============================================================
echo.
echo Lambda Function: %FUNCTION_NAME%
echo SageMaker Endpoint: %ENDPOINT_NAME%
echo Region: %REGION%
echo.
echo Next Steps:
echo 1. Test inference: .\test-inference.bat
echo 2. Monitor endpoint: .\monitor-endpoint.bat
echo 3. Check logs: aws logs tail /aws/lambda/%FUNCTION_NAME% --follow
echo.
echo ============================================================

REM Cleanup
del %TEMP%\sagemaker-policy.json

exit /b 0
