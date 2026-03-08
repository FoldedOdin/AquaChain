@echo off
REM Update ML Inference Lambda to use SageMaker endpoint

echo ========================================
echo Updating ML Inference Lambda
echo ========================================

set FUNCTION_NAME=AquaChain-Function-MLInference-dev
set ENDPOINT_NAME=aquachain-wqi-endpoint-dev

REM Save current directory and set paths
set SCRIPT_DIR=%~dp0
set PROJECT_ROOT=%SCRIPT_DIR%..\..

echo.
echo Step 1: Packaging Lambda function...
cd /d "%PROJECT_ROOT%\lambda\ml_inference"

REM Create deployment package
if exist deployment.zip del deployment.zip
powershell Compress-Archive -Path handler_sagemaker.py -DestinationPath deployment.zip -Force

echo.
echo Step 2: Updating Lambda function code...
aws lambda update-function-code ^
    --function-name %FUNCTION_NAME% ^
    --zip-file fileb://deployment.zip

echo.
echo Step 3: Updating Lambda environment variables...
aws lambda update-function-configuration ^
    --function-name %FUNCTION_NAME% ^
    --environment Variables="{SAGEMAKER_ENDPOINT_NAME=%ENDPOINT_NAME%,ENABLE_MONITORING=true}" ^
    --handler handler_sagemaker.lambda_handler

if %ERRORLEVEL% EQU 0 (
    echo.
    echo ========================================
    echo Lambda Update Complete!
    echo ========================================
    echo.
    echo Function: %FUNCTION_NAME%
    echo Endpoint: %ENDPOINT_NAME%
) else (
    echo.
    echo ========================================
    echo Lambda Update Failed!
    echo ========================================
    cd /d "%SCRIPT_DIR%"
    exit /b 1
)

cd /d "%SCRIPT_DIR%"
