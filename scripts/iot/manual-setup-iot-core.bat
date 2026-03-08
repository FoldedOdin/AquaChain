@echo off
REM Manual IoT Core Setup Script
REM This script creates IoT Core resources manually via AWS CLI
REM Use this as a workaround for CDK CloudFormation validation issues

echo ========================================
echo AquaChain IoT Core Manual Setup
echo ========================================
echo.
echo This script will create IoT Core resources manually
echo due to CloudFormation Early Validation issues with CDK.
echo.

REM Check if AWS CLI is installed
where aws >nul 2>nul
if %ERRORLEVEL% NEQ 0 (
    echo ERROR: AWS CLI not found. Please install AWS CLI first.
    exit /b 1
)

REM Set environment (default to dev)
set ENVIRONMENT=%1
if "%ENVIRONMENT%"=="" set ENVIRONMENT=dev

echo Environment: %ENVIRONMENT%
echo.

REM Get AWS account ID
for /f "tokens=*" %%i in ('aws sts get-caller-identity --query Account --output text') do set ACCOUNT_ID=%%i
echo AWS Account ID: %ACCOUNT_ID%
echo.

REM Get AWS region
for /f "tokens=*" %%i in ('aws configure get region') do set REGION=%%i
if "%REGION%"=="" set REGION=ap-south-1
echo AWS Region: %REGION%
echo.

pause
echo.

REM Step 1: Create Thing Type
echo [1/7] Creating Thing Type...
aws iot create-thing-type ^
    --thing-type-name aquachain-sensor-%ENVIRONMENT% ^
    --thing-type-properties "thingTypeDescription=AquaChain Water Quality Sensor Device,searchableAttributes=deviceId,userId,status,firmwareVersion"

if %ERRORLEVEL% EQU 0 (
    echo Thing Type created successfully
) else (
    echo WARNING: Thing Type creation failed (may already exist)
)
echo.

REM Step 2: Create Thing Groups
echo [2/7] Creating Thing Groups...

REM Active devices group
aws iot create-thing-group ^
    --thing-group-name aquachain-active-%ENVIRONMENT% ^
    --thing-group-properties "thingGroupDescription=Active AquaChain devices sending data"

if %ERRORLEVEL% EQU 0 (
    echo Active Thing Group created successfully
) else (
    echo WARNING: Active Thing Group creation failed (may already exist)
)

REM Maintenance devices group
aws iot create-thing-group ^
    --thing-group-name aquachain-maintenance-%ENVIRONMENT% ^
    --thing-group-properties "thingGroupDescription=Devices under maintenance"

if %ERRORLEVEL% EQU 0 (
    echo Maintenance Thing Group created successfully
) else (
    echo WARNING: Maintenance Thing Group creation failed (may already exist)
)

REM Offline devices group
aws iot create-thing-group ^
    --thing-group-name aquachain-offline-%ENVIRONMENT% ^
    --thing-group-properties "thingGroupDescription=Devices that haven't reported in >10 minutes"

if %ERRORLEVEL% EQU 0 (
    echo Offline Thing Group created successfully
) else (
    echo WARNING: Offline Thing Group creation failed (may already exist)
)
echo.

REM Step 3: Create IoT Policy
echo [3/7] Creating IoT Policy...

REM Update policy document with correct account ID and region
powershell -Command "(Get-Content device-policy.json) -replace '758346259059', '%ACCOUNT_ID%' -replace 'ap-south-1', '%REGION%' | Set-Content device-policy-%ENVIRONMENT%.json"

aws iot create-policy ^
    --policy-name aquachain-device-policy-%ENVIRONMENT% ^
    --policy-document file://device-policy-%ENVIRONMENT%.json

if %ERRORLEVEL% EQU 0 (
    echo IoT Policy created successfully
) else (
    echo WARNING: IoT Policy creation failed (may already exist)
)

REM Cleanup
del device-policy-%ENVIRONMENT%.json
echo.

REM Step 4: Enable IoT Logging
echo [4/7] Enabling IoT Core logging...
echo NOTE: This requires an IAM role. Creating role first...

REM Create IoT logging role
aws iam create-role ^
    --role-name AquaChain-IoT-Logging-Role-%ENVIRONMENT% ^
    --assume-role-policy-document "{\"Version\":\"2012-10-17\",\"Statement\":[{\"Effect\":\"Allow\",\"Principal\":{\"Service\":\"iot.amazonaws.com\"},\"Action\":\"sts:AssumeRole\"}]}"

REM Attach CloudWatch Logs policy
aws iam attach-role-policy ^
    --role-name AquaChain-IoT-Logging-Role-%ENVIRONMENT% ^
    --policy-arn arn:aws:iam::aws:policy/CloudWatchLogsFullAccess

REM Wait for role to propagate
echo Waiting for IAM role to propagate...
timeout /t 10 /nobreak >nul

REM Get role ARN
for /f "tokens=*" %%i in ('aws iam get-role --role-name AquaChain-IoT-Logging-Role-%ENVIRONMENT% --query Role.Arn --output text') do set LOGGING_ROLE_ARN=%%i

REM Enable logging
aws iot set-v2-logging-options ^
    --role-arn %LOGGING_ROLE_ARN% ^
    --default-log-level INFO

if %ERRORLEVEL% EQU 0 (
    echo IoT logging enabled successfully
) else (
    echo WARNING: IoT logging enablement failed
)
echo.

REM Step 5: Enable Fleet Indexing
echo [5/7] Enabling fleet indexing...
aws iot update-indexing-configuration ^
    --thing-indexing-configuration thingIndexingMode=REGISTRY_AND_SHADOW

if %ERRORLEVEL% EQU 0 (
    echo Fleet indexing enabled successfully
) else (
    echo WARNING: Fleet indexing enablement failed
)
echo.

REM Step 6: Create IoT Rules (via AWS Console)
echo [6/7] Creating IoT Rules...
echo.
echo NOTE: IoT Rules must be created via AWS Console due to CLI limitations.
echo.
echo Please create the following rules manually:
echo.
echo Rule 1: aquachain_data_ingestion_%ENVIRONMENT%
echo   SQL: SELECT * FROM 'aquachain/+/data'
echo   Action: Lambda function - aquachain-data-processing-%ENVIRONMENT%
echo.
echo Rule 2: aquachain_telemetry_%ENVIRONMENT%
echo   SQL: SELECT * FROM 'aquachain/+/telemetry'
echo   Action: Lambda function - aquachain-data-processing-%ENVIRONMENT%
echo.
echo Press any key after creating the rules in AWS Console...
pause >nul
echo.

REM Step 7: Verify Setup
echo [7/7] Verifying setup...

aws iot describe-thing-type --thing-type-name aquachain-sensor-%ENVIRONMENT% >nul 2>nul
if %ERRORLEVEL% EQU 0 (
    echo Thing Type: OK
) else (
    echo Thing Type: FAILED
)

aws iot describe-thing-group --thing-group-name aquachain-active-%ENVIRONMENT% >nul 2>nul
if %ERRORLEVEL% EQU 0 (
    echo Thing Group (Active): OK
) else (
    echo Thing Group (Active): FAILED
)

aws iot get-policy --policy-name aquachain-device-policy-%ENVIRONMENT% >nul 2>nul
if %ERRORLEVEL% EQU 0 (
    echo IoT Policy: OK
) else (
    echo IoT Policy: FAILED
)

echo.
echo ========================================
echo Manual Setup Complete!
echo ========================================
echo.
echo Next Steps:
echo 1. Create IoT Rules in AWS Console (if not done yet)
echo 2. Deploy device provisioning Lambda
echo 3. Test device connectivity with simulator
echo.
echo Documentation: DOCS/iot/IOT-DEPLOYMENT-STATUS.md
echo.

pause
