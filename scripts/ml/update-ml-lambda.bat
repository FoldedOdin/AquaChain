@echo off
REM Update ML Inference Lambda to use SageMaker Endpoint
REM Deploys the SageMaker-enabled Lambda function

echo ========================================
echo Updating ML Inference Lambda
echo ========================================
echo.

cd lambda\ml_inference

echo Step 1: Installing dependencies...
pip install -r requirements.txt -t package/ --upgrade

echo.
echo Step 2: Copying Lambda code...
copy handler_sagemaker.py package\handler.py
copy structured_logger.py package\
copy model_performance_monitor.py package\

echo.
echo Step 3: Creating deployment package...
cd package
powershell -Command "Compress-Archive -Path * -DestinationPath ..\ml-inference-sagemaker.zip -Force"
cd ..

echo.
echo Step 4: Deploying to AWS Lambda...
aws lambda update-function-code ^
  --function-name AquaChain-Function-MLInference-dev ^
  --region ap-south-1 ^
  --zip-file fileb://ml-inference-sagemaker.zip

if %ERRORLEVEL% EQU 0 (
    echo.
    echo Step 5: Updating environment variables...
    aws lambda update-function-configuration ^
      --function-name AquaChain-Function-MLInference-dev ^
      --region ap-south-1 ^
      --environment Variables={SAGEMAKER_ENDPOINT_NAME=aquachain-wqi-endpoint-dev,ENABLE_MONITORING=true}
    
    echo.
    echo ========================================
    echo SUCCESS! Lambda updated
    echo ========================================
    echo.
    echo Function: AquaChain-Function-MLInference-dev
    echo Endpoint: aquachain-wqi-endpoint-dev
    echo.
    echo Next steps:
    echo 1. Test Lambda: aws lambda invoke --function-name AquaChain-Function-MLInference-dev test-output.json
    echo 2. Monitor CloudWatch logs
    echo 3. Set up alarms: scripts\ml\setup-monitoring.bat
) else (
    echo.
    echo ========================================
    echo ERROR! Lambda update failed
    echo ========================================
)

echo.
echo Cleaning up...
rmdir /s /q package
del ml-inference-sagemaker.zip

cd ..\..
