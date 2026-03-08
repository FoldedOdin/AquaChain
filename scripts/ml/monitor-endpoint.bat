@echo off
REM Monitor SageMaker Endpoint Status
REM Polls endpoint status every 30 seconds until InService

echo ========================================
echo SageMaker Endpoint Status Monitor
echo ========================================
echo.
echo Endpoint: aquachain-wqi-endpoint-dev
echo Region: ap-south-1
echo.
echo Checking status every 30 seconds...
echo Press Ctrl+C to stop monitoring
echo.

:LOOP
echo [%TIME%] Checking endpoint status...
aws sagemaker describe-endpoint --endpoint-name aquachain-wqi-endpoint-dev --region ap-south-1 --query "EndpointStatus" --output text > temp_status.txt
set /p STATUS=<temp_status.txt
del temp_status.txt

echo [%TIME%] Status: %STATUS%

if "%STATUS%"=="InService" (
    echo.
    echo ========================================
    echo SUCCESS! Endpoint is InService
    echo ========================================
    echo.
    echo Next steps:
    echo 1. Test inference: scripts\ml\test-inference.bat
    echo 2. Update Lambda: scripts\ml\update-ml-lambda.bat
    echo 3. Deploy monitoring: scripts\ml\setup-monitoring.bat
    echo.
    goto END
)

if "%STATUS%"=="Failed" (
    echo.
    echo ========================================
    echo ERROR! Endpoint creation failed
    echo ========================================
    echo.
    echo Check CloudWatch logs for details:
    aws logs tail /aws/sagemaker/Endpoints/aquachain-wqi-endpoint-dev --region ap-south-1 --follow
    goto END
)

echo Waiting 30 seconds before next check...
timeout /t 30 /nobreak > nul
goto LOOP

:END
