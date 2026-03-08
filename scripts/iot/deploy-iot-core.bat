@echo off
REM Deploy IoT Core Infrastructure
REM This script deploys the complete IoT Core stack including:
REM - Thing Types and Thing Groups
REM - IoT Rules for data ingestion
REM - Fleet provisioning template
REM - Device provisioning Lambda

echo ========================================
echo AquaChain IoT Core Deployment
echo ========================================
echo.

REM Check if AWS CLI is installed
where aws >nul 2>nul
if %ERRORLEVEL% NEQ 0 (
    echo ERROR: AWS CLI not found. Please install AWS CLI first.
    exit /b 1
)

REM Check if CDK is installed
where cdk >nul 2>nul
if %ERRORLEVEL% NEQ 0 (
    echo ERROR: AWS CDK not found. Please install CDK: npm install -g aws-cdk
    exit /b 1
)

REM Set environment (default to dev)
set ENVIRONMENT=%1
if "%ENVIRONMENT%"=="" set ENVIRONMENT=dev

echo Environment: %ENVIRONMENT%
echo.

REM Step 1: Deploy IoT Core Stack
echo [1/5] Deploying IoT Core Stack...
cd ..\..\infrastructure\cdk
call cdk deploy AquaChain-IoTCore-%ENVIRONMENT% --require-approval never
if %ERRORLEVEL% NEQ 0 (
    echo ERROR: Failed to deploy IoT Core stack
    exit /b 1
)
echo IoT Core stack deployed successfully
echo.

REM Step 2: Enable IoT Logging
echo [2/5] Enabling IoT Core logging...
for /f "tokens=*" %%i in ('aws cloudformation describe-stacks --stack-name AquaChain-IoTCore-%ENVIRONMENT% --query "Stacks[0].Outputs[?OutputKey=='IoTLoggingRoleArn'].OutputValue" --output text') do set IOT_ROLE_ARN=%%i

if not "%IOT_ROLE_ARN%"=="" (
    aws iot set-v2-logging-options --role-arn %IOT_ROLE_ARN% --default-log-level INFO
    echo IoT logging enabled
) else (
    echo WARNING: Could not find IoT logging role ARN
)
echo.

REM Step 3: Enable Fleet Indexing
echo [3/5] Enabling fleet indexing...
aws iot update-indexing-configuration --thing-indexing-configuration thingIndexingMode=REGISTRY_AND_SHADOW
if %ERRORLEVEL% EQU 0 (
    echo Fleet indexing enabled
) else (
    echo WARNING: Failed to enable fleet indexing
)
echo.

REM Step 4: Deploy Device Provisioning Lambda
echo [4/6] Deploying device provisioning Lambda...
cd ..\..\lambda\device_provisioning

REM Install dependencies
if exist package (
    rmdir /s /q package
)
mkdir package
pip install -r requirements.txt -t package

REM Create deployment package
if exist function.zip (
    del function.zip
)
cd package
powershell -Command "Compress-Archive -Path * -DestinationPath ..\function.zip"
cd ..
powershell -Command "Compress-Archive -Path handler.py -Update -DestinationPath function.zip"

REM Update Lambda function
aws lambda update-function-code ^
    --function-name aquachain-device-provisioning-%ENVIRONMENT% ^
    --zip-file fileb://function.zip
if %ERRORLEVEL% EQU 0 (
    echo Device provisioning Lambda deployed
) else (
    echo WARNING: Failed to deploy Lambda function
)

REM Cleanup
rmdir /s /q package
del function.zip
echo.

REM Step 5: Create Provisioning Template
echo [5/6] Creating IoT provisioning template...
cd ..\..\scripts\iot

REM Get provisioning role ARN
for /f "tokens=*" %%i in ('aws cloudformation describe-stacks --stack-name AquaChain-IoTCore-%ENVIRONMENT% --query "Stacks[0].Outputs[?OutputKey=='ProvisioningRoleArn'].OutputValue" --output text') do set ROLE_ARN=%%i

if not "%ROLE_ARN%"=="" (
    REM Update template with environment
    powershell -Command "(Get-Content provisioning-template.json) -replace 'aquachain-sensor-dev', 'aquachain-sensor-%ENVIRONMENT%' -replace 'aquachain-device-policy-dev', 'aquachain-device-policy-%ENVIRONMENT%' | Set-Content provisioning-template-%ENVIRONMENT%.json"
    
    REM Create provisioning template
    aws iot create-provisioning-template ^
        --template-name aquachain-device-provisioning-%ENVIRONMENT% ^
        --description "AquaChain device fleet provisioning template" ^
        --provisioning-role-arn %ROLE_ARN% ^
        --template-body file://provisioning-template-%ENVIRONMENT%.json ^
        --enabled
    
    if %ERRORLEVEL% EQU 0 (
        echo Provisioning template created successfully
    ) else (
        echo WARNING: Failed to create provisioning template
        echo You can create it manually using: create-provisioning-template.bat %ENVIRONMENT%
    )
    
    REM Cleanup
    if exist provisioning-template-%ENVIRONMENT%.json (
        del provisioning-template-%ENVIRONMENT%.json
    )
) else (
    echo WARNING: Could not find provisioning role ARN
    echo You can create the template manually using: create-provisioning-template.bat %ENVIRONMENT%
)
echo.

REM Step 6: Verify Deployment
echo [6/6] Verifying deployment...
aws iot describe-thing-type --thing-type-name aquachain-sensor-%ENVIRONMENT% >nul 2>nul
if %ERRORLEVEL% EQU 0 (
    echo Thing Type: OK
) else (
    echo Thing Type: FAILED
)

aws iot describe-thing-group --thing-group-name aquachain-active-%ENVIRONMENT% >nul 2>nul
if %ERRORLEVEL% EQU 0 (
    echo Thing Group: OK
) else (
    echo Thing Group: FAILED
)

aws lambda get-function --function-name aquachain-device-provisioning-%ENVIRONMENT% >nul 2>nul
if %ERRORLEVEL% EQU 0 (
    echo Lambda Function: OK
) else (
    echo Lambda Function: FAILED
)
echo.

echo ========================================
echo Deployment Complete!
echo ========================================
echo.
echo Next Steps:
echo 1. Test device provisioning with simulator
echo 2. Deploy frontend device pairing UI
echo 3. Configure device certificates
echo.
echo Documentation: DOCS/iot/IOT-CORE-SETUP-GUIDE.md
echo.

pause
