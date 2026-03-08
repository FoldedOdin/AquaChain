@echo off
REM Create IoT Provisioning Template
REM This script creates the fleet provisioning template manually via AWS CLI
REM Run this AFTER deploying the IoT Core stack

echo ========================================
echo Create IoT Provisioning Template
echo ========================================
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

REM Get provisioning role ARN from CloudFormation stack
echo [1/3] Getting provisioning role ARN from stack...
for /f "tokens=*" %%i in ('aws cloudformation describe-stacks --stack-name AquaChain-IoTCore-%ENVIRONMENT% --query "Stacks[0].Outputs[?OutputKey=='ProvisioningRoleArn'].OutputValue" --output text') do set ROLE_ARN=%%i

if "%ROLE_ARN%"=="" (
    echo ERROR: Could not find provisioning role ARN in stack outputs
    echo Make sure the IoT Core stack is deployed first
    exit /b 1
)

echo Provisioning Role ARN: %ROLE_ARN%
echo.

REM Update template with correct environment
echo [2/3] Updating provisioning template with environment...
powershell -Command "(Get-Content provisioning-template.json) -replace 'aquachain-sensor-dev', 'aquachain-sensor-%ENVIRONMENT%' -replace 'aquachain-device-policy-dev', 'aquachain-device-policy-%ENVIRONMENT%' | Set-Content provisioning-template-%ENVIRONMENT%.json"

REM Create provisioning template
echo [3/3] Creating provisioning template...
aws iot create-provisioning-template ^
    --template-name aquachain-device-provisioning-%ENVIRONMENT% ^
    --description "AquaChain device fleet provisioning template" ^
    --provisioning-role-arn %ROLE_ARN% ^
    --template-body file://provisioning-template-%ENVIRONMENT%.json ^
    --enabled ^
    --pre-provisioning-hook targetArn=arn:aws:lambda:%AWS_DEFAULT_REGION%:%AWS_ACCOUNT_ID%:function:aquachain-device-provisioning-%ENVIRONMENT%

if %ERRORLEVEL% EQU 0 (
    echo.
    echo ========================================
    echo Provisioning Template Created!
    echo ========================================
    echo.
    echo Template Name: aquachain-device-provisioning-%ENVIRONMENT%
    echo.
    echo Next Steps:
    echo 1. Test device provisioning with simulator
    echo 2. Verify pre-provisioning hook is working
    echo 3. Check CloudWatch logs for provisioning events
    echo.
) else (
    echo.
    echo ERROR: Failed to create provisioning template
    echo.
    echo Troubleshooting:
    echo 1. Check if the Lambda function exists
    echo 2. Verify the role ARN is correct
    echo 3. Check AWS CLI credentials
    echo.
)

REM Cleanup temporary file
if exist provisioning-template-%ENVIRONMENT%.json (
    del provisioning-template-%ENVIRONMENT%.json
)

pause
