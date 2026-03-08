@echo off
REM Complete SageMaker Deployment - All Steps

echo ========================================
echo AquaChain SageMaker Complete Deployment
echo ========================================
echo.
echo This script will:
echo 1. Prepare and upload trained models to S3
echo 2. Deploy SageMaker infrastructure (CDK)
echo 3. Wait for endpoint to be InService
echo 4. Update ML inference Lambda function
echo 5. Test the deployment
echo.
pause

REM Save current directory and set paths
set SCRIPT_DIR=%~dp0
set PROJECT_ROOT=%SCRIPT_DIR%..\..

echo.
echo Project root: %PROJECT_ROOT%
echo Script directory: %SCRIPT_DIR%

REM Step 1: Prepare and upload models
echo.
echo ========================================
echo Step 1: Preparing Models
echo ========================================
call "%SCRIPT_DIR%prepare_and_upload_model.bat"
if %ERRORLEVEL% NEQ 0 (
    echo Model preparation failed!
    exit /b 1
)

REM Step 2: Deploy SageMaker stack
echo.
echo ========================================
echo Step 2: Deploying SageMaker Stack
echo ========================================
call "%SCRIPT_DIR%deploy_sagemaker_stack.bat"
if %ERRORLEVEL% NEQ 0 (
    echo SageMaker stack deployment failed!
    exit /b 1
)

REM Step 3: Wait for endpoint
echo.
echo ========================================
echo Step 3: Waiting for Endpoint
echo ========================================
echo Checking endpoint status...
echo This may take 10-15 minutes...
echo.

:check_endpoint
aws sagemaker describe-endpoint --endpoint-name aquachain-wqi-endpoint-dev --query "EndpointStatus" --output text > endpoint_status.txt
set /p ENDPOINT_STATUS=<endpoint_status.txt
del endpoint_status.txt

echo Current status: %ENDPOINT_STATUS%

if "%ENDPOINT_STATUS%"=="InService" (
    echo Endpoint is ready!
    goto endpoint_ready
)

if "%ENDPOINT_STATUS%"=="Failed" (
    echo Endpoint creation failed!
    echo Check CloudWatch logs for details
    exit /b 1
)

echo Waiting 30 seconds before next check...
timeout /t 30 /nobreak
goto check_endpoint

:endpoint_ready

REM Step 4: Update Lambda
echo.
echo ========================================
echo Step 4: Updating ML Inference Lambda
echo ========================================
call "%SCRIPT_DIR%update_ml_lambda.bat"
if %ERRORLEVEL% NEQ 0 (
    echo Lambda update failed!
    exit /b 1
)

REM Step 5: Test deployment
echo.
echo ========================================
echo Step 5: Testing Deployment
echo ========================================
echo Creating test payload...

echo { > test_payload.json
echo   "deviceId": "ESP32-TEST-001", >> test_payload.json
echo   "timestamp": "2024-01-15T10:30:00Z", >> test_payload.json
echo   "readings": { >> test_payload.json
echo     "pH": 7.2, >> test_payload.json
echo     "turbidity": 3.5, >> test_payload.json
echo     "tds": 450, >> test_payload.json
echo     "temperature": 25.0 >> test_payload.json
echo   }, >> test_payload.json
echo   "location": { >> test_payload.json
echo     "latitude": 10.0, >> test_payload.json
echo     "longitude": 76.0 >> test_payload.json
echo   } >> test_payload.json
echo } >> test_payload.json

echo Invoking Lambda function...
aws lambda invoke ^
    --function-name AquaChain-Function-MLInference-dev ^
    --payload file://test_payload.json ^
    response.json

echo.
echo Response:
type response.json
echo.

del test_payload.json
del response.json

echo.
echo ========================================
echo Deployment Complete!
echo ========================================
echo.
echo SageMaker endpoint is running and Lambda is configured.
echo.
echo Next steps:
echo 1. Monitor CloudWatch metrics for endpoint performance
echo 2. Check Lambda logs for any errors
echo 3. Test with real device data
echo 4. Set up CloudWatch alarms for monitoring
echo.
echo Cost: ~$47/month for dev environment (ml.t2.medium)
echo.
echo To view endpoint details:
echo   aws sagemaker describe-endpoint --endpoint-name aquachain-wqi-endpoint-dev
echo.
echo To view Lambda logs:
echo   aws logs tail /aws/lambda/AquaChain-Function-MLInference-dev --follow
echo.
