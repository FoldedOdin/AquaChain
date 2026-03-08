@echo off
REM Setup CloudWatch Monitoring for SageMaker Endpoint
REM Creates alarms for latency, errors, and invocations

echo ========================================
echo Setting Up SageMaker Monitoring
echo ========================================
echo.

echo Creating CloudWatch Alarms...
echo.

REM High Latency Alarm
echo 1. Creating High Latency Alarm...
aws cloudwatch put-metric-alarm ^
  --alarm-name AquaChain-SageMaker-HighLatency-dev ^
  --alarm-description "Alert when SageMaker endpoint latency exceeds 1000ms" ^
  --metric-name ModelLatency ^
  --namespace AWS/SageMaker ^
  --statistic Average ^
  --period 300 ^
  --evaluation-periods 2 ^
  --threshold 1000 ^
  --comparison-operator GreaterThanThreshold ^
  --dimensions Name=EndpointName,Value=aquachain-wqi-endpoint-dev Name=VariantName,Value=AllTraffic ^
  --region ap-south-1

if %ERRORLEVEL% EQU 0 (
    echo   ✓ High Latency Alarm created
) else (
    echo   ✗ Failed to create High Latency Alarm
)

echo.

REM 4XX Error Alarm
echo 2. Creating 4XX Error Alarm...
aws cloudwatch put-metric-alarm ^
  --alarm-name AquaChain-SageMaker-4XXErrors-dev ^
  --alarm-description "Alert when SageMaker endpoint has 4XX errors" ^
  --metric-name Model4XXErrors ^
  --namespace AWS/SageMaker ^
  --statistic Sum ^
  --period 300 ^
  --evaluation-periods 1 ^
  --threshold 10 ^
  --comparison-operator GreaterThanThreshold ^
  --dimensions Name=EndpointName,Value=aquachain-wqi-endpoint-dev Name=VariantName,Value=AllTraffic ^
  --region ap-south-1

if %ERRORLEVEL% EQU 0 (
    echo   ✓ 4XX Error Alarm created
) else (
    echo   ✗ Failed to create 4XX Error Alarm
)

echo.

REM 5XX Error Alarm
echo 3. Creating 5XX Error Alarm...
aws cloudwatch put-metric-alarm ^
  --alarm-name AquaChain-SageMaker-5XXErrors-dev ^
  --alarm-description "Alert when SageMaker endpoint has 5XX errors" ^
  --metric-name Model5XXErrors ^
  --namespace AWS/SageMaker ^
  --statistic Sum ^
  --period 300 ^
  --evaluation-periods 1 ^
  --threshold 5 ^
  --comparison-operator GreaterThanThreshold ^
  --dimensions Name=EndpointName,Value=aquachain-wqi-endpoint-dev Name=VariantName,Value=AllTraffic ^
  --region ap-south-1

if %ERRORLEVEL% EQU 0 (
    echo   ✓ 5XX Error Alarm created
) else (
    echo   ✗ Failed to create 5XX Error Alarm
)

echo.

REM Invocation Count Alarm (Low Traffic)
echo 4. Creating Low Invocation Alarm...
aws cloudwatch put-metric-alarm ^
  --alarm-name AquaChain-SageMaker-LowInvocations-dev ^
  --alarm-description "Alert when SageMaker endpoint has unusually low traffic" ^
  --metric-name ModelInvocations ^
  --namespace AWS/SageMaker ^
  --statistic Sum ^
  --period 3600 ^
  --evaluation-periods 1 ^
  --threshold 10 ^
  --comparison-operator LessThanThreshold ^
  --dimensions Name=EndpointName,Value=aquachain-wqi-endpoint-dev Name=VariantName,Value=AllTraffic ^
  --region ap-south-1

if %ERRORLEVEL% EQU 0 (
    echo   ✓ Low Invocation Alarm created
) else (
    echo   ✗ Failed to create Low Invocation Alarm
)

echo.
echo ========================================
echo Monitoring Setup Complete
echo ========================================
echo.
echo Created Alarms:
echo 1. AquaChain-SageMaker-HighLatency-dev (>1000ms)
echo 2. AquaChain-SageMaker-4XXErrors-dev (>10 errors/5min)
echo 3. AquaChain-SageMaker-5XXErrors-dev (>5 errors/5min)
echo 4. AquaChain-SageMaker-LowInvocations-dev (<10 invocations/hour)
echo.
echo View alarms:
echo aws cloudwatch describe-alarms --alarm-name-prefix AquaChain-SageMaker --region ap-south-1
echo.
echo View metrics:
echo https://console.aws.amazon.com/cloudwatch/home?region=ap-south-1#metricsV2:graph=~();namespace=AWS/SageMaker
