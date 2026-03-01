@echo off
REM Enable DynamoDB Streams on existing tables for Global Monitoring Dashboard
REM Requirements: 15.8, 19.8, 3.2

setlocal enabledelayedexpansion

echo Enabling DynamoDB Streams for Global Monitoring Dashboard
echo ==========================================================

REM Check if AWS CLI is installed
where aws >nul 2>nul
if %ERRORLEVEL% NEQ 0 (
    echo Error: AWS CLI is not installed
    exit /b 1
)

REM Get AWS region from environment or use default
if "%AWS_REGION%"=="" (
    set REGION=us-east-1
) else (
    set REGION=%AWS_REGION%
)
echo Using region: %REGION%

REM Function to enable stream on AquaChain-Readings
echo.
echo Enabling stream on AquaChain-Readings...
echo Purpose: Trigger incremental aggregation Lambda

REM Check if table exists
aws dynamodb describe-table --table-name AquaChain-Readings --region %REGION% >nul 2>nul
if %ERRORLEVEL% NEQ 0 (
    echo Error: Table AquaChain-Readings does not exist
    goto :enable_alerts
)

REM Check if stream is already enabled
for /f "tokens=*" %%i in ('aws dynamodb describe-table --table-name AquaChain-Readings --region %REGION% --query "Table.StreamSpecification.StreamEnabled" --output text 2^>nul') do set STREAM_STATUS=%%i

if "%STREAM_STATUS%"=="True" (
    echo [OK] Stream already enabled on AquaChain-Readings
    
    REM Get stream ARN
    for /f "tokens=*" %%i in ('aws dynamodb describe-table --table-name AquaChain-Readings --region %REGION% --query "Table.LatestStreamArn" --output text') do set STREAM_ARN=%%i
    echo   Stream ARN: !STREAM_ARN!
    goto :enable_alerts
)

REM Enable stream
aws dynamodb update-table --table-name AquaChain-Readings --region %REGION% --stream-specification StreamEnabled=true,StreamViewType=NEW_IMAGE

if %ERRORLEVEL% EQU 0 (
    echo [OK] Successfully enabled stream on AquaChain-Readings
    
    REM Wait a moment for stream to be created
    timeout /t 2 /nobreak >nul
    
    REM Get stream ARN
    for /f "tokens=*" %%i in ('aws dynamodb describe-table --table-name AquaChain-Readings --region %REGION% --query "Table.LatestStreamArn" --output text') do set STREAM_ARN=%%i
    echo   Stream ARN: !STREAM_ARN!
) else (
    echo [ERROR] Failed to enable stream on AquaChain-Readings
)

:enable_alerts
REM Function to enable stream on AquaChain-Alerts
echo.
echo Enabling stream on AquaChain-Alerts...
echo Purpose: Trigger alert stream Lambda for WebSocket push

REM Check if table exists
aws dynamodb describe-table --table-name AquaChain-Alerts --region %REGION% >nul 2>nul
if %ERRORLEVEL% NEQ 0 (
    echo Error: Table AquaChain-Alerts does not exist
    goto :complete
)

REM Check if stream is already enabled
for /f "tokens=*" %%i in ('aws dynamodb describe-table --table-name AquaChain-Alerts --region %REGION% --query "Table.StreamSpecification.StreamEnabled" --output text 2^>nul') do set STREAM_STATUS=%%i

if "%STREAM_STATUS%"=="True" (
    echo [OK] Stream already enabled on AquaChain-Alerts
    
    REM Get stream ARN
    for /f "tokens=*" %%i in ('aws dynamodb describe-table --table-name AquaChain-Alerts --region %REGION% --query "Table.LatestStreamArn" --output text') do set STREAM_ARN=%%i
    echo   Stream ARN: !STREAM_ARN!
    goto :complete
)

REM Enable stream
aws dynamodb update-table --table-name AquaChain-Alerts --region %REGION% --stream-specification StreamEnabled=true,StreamViewType=NEW_IMAGE

if %ERRORLEVEL% EQU 0 (
    echo [OK] Successfully enabled stream on AquaChain-Alerts
    
    REM Wait a moment for stream to be created
    timeout /t 2 /nobreak >nul
    
    REM Get stream ARN
    for /f "tokens=*" %%i in ('aws dynamodb describe-table --table-name AquaChain-Alerts --region %REGION% --query "Table.LatestStreamArn" --output text') do set STREAM_ARN=%%i
    echo   Stream ARN: !STREAM_ARN!
) else (
    echo [ERROR] Failed to enable stream on AquaChain-Alerts
)

:complete
echo.
echo ==========================================================
echo DynamoDB Streams configuration complete!
echo ==========================================================
echo.
echo Next steps:
echo 1. Deploy the Global Monitoring Dashboard stack:
echo    cd infrastructure\cdk
echo    cdk deploy AquaChain-GlobalMonitoringDashboard-dev
echo.
echo 2. Verify the new tables were created:
echo    aws dynamodb list-tables --region %REGION%
echo.
echo 3. Check stream ARNs for Lambda trigger configuration:
echo    aws dynamodb describe-table --table-name AquaChain-Readings --region %REGION%
echo    aws dynamodb describe-table --table-name AquaChain-Alerts --region %REGION%

endlocal
