@echo off
REM Test SageMaker Endpoint Inference
REM Sends sample water quality data to endpoint

echo ========================================
echo Testing SageMaker Endpoint Inference
echo ========================================
echo.

REM Create test payload
echo Creating test payload...
echo { > test-payload.json
echo   "deviceId": "ESP32-TEST-001", >> test-payload.json
echo   "timestamp": "2026-03-08T12:00:00Z", >> test-payload.json
echo   "readings": { >> test-payload.json
echo     "pH": 7.2, >> test-payload.json
echo     "turbidity": 3.5, >> test-payload.json
echo     "tds": 450, >> test-payload.json
echo     "temperature": 25.0 >> test-payload.json
echo   }, >> test-payload.json
echo   "location": { >> test-payload.json
echo     "latitude": 19.0760, >> test-payload.json
echo     "longitude": 72.8777 >> test-payload.json
echo   } >> test-payload.json
echo } >> test-payload.json

echo.
echo Test Payload:
type test-payload.json
echo.

echo Invoking SageMaker endpoint...
aws sagemaker-runtime invoke-endpoint ^
  --endpoint-name aquachain-wqi-endpoint-dev ^
  --region ap-south-1 ^
  --content-type application/json ^
  --body file://test-payload.json ^
  test-response.json

if %ERRORLEVEL% EQU 0 (
    echo.
    echo ========================================
    echo SUCCESS! Inference completed
    echo ========================================
    echo.
    echo Response:
    type test-response.json
    echo.
    echo.
    echo Cleaning up...
    del test-payload.json
    del test-response.json
) else (
    echo.
    echo ========================================
    echo ERROR! Inference failed
    echo ========================================
    echo.
    echo Check endpoint status:
    aws sagemaker describe-endpoint --endpoint-name aquachain-wqi-endpoint-dev --region ap-south-1
)
