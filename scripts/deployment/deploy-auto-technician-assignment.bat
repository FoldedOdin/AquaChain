@echo off
REM Deploy Auto Technician Assignment Stack
REM This script deploys the Lambda function and EventBridge rule for automatic technician assignment

echo ========================================
echo Auto Technician Assignment Deployment
echo ========================================
echo.

cd infrastructure\cdk

echo [1/3] Installing dependencies...
pip install -r requirements.txt
if %ERRORLEVEL% NEQ 0 (
    echo ERROR: Failed to install dependencies
    exit /b 1
)

echo.
echo [2/3] Synthesizing CDK stack...
cdk synth AquaChain-AutoTechnicianAssignment-dev
if %ERRORLEVEL% NEQ 0 (
    echo ERROR: CDK synthesis failed
    exit /b 1
)

echo.
echo [3/3] Deploying stack...
cdk deploy AquaChain-AutoTechnicianAssignment-dev --require-approval never
if %ERRORLEVEL% NEQ 0 (
    echo ERROR: Deployment failed
    exit /b 1
)

echo.
echo ========================================
echo Deployment Complete!
echo ========================================
echo.
echo The following resources have been created:
echo - Lambda: aquachain-function-auto-technician-assignment-dev
echo - SNS Topic: aquachain-topic-technician-alerts-dev
echo - EventBridge Rule: aquachain-rule-order-placed-assignment-dev
echo.
echo Automatic technician assignment is now active!
echo When an order reaches ORDER_PLACED status, the nearest technician
echo with a complete profile will be automatically assigned.
echo.

cd ..\..
