@echo off
REM Deploy Device Status Monitor Stack Only
REM Windows batch script for deploying device status monitoring

echo.
echo ========================================
echo   AquaChain Device Status Monitor
echo ========================================
echo.

REM Check if CDK is installed
cdk --version >nul 2>&1
if %errorlevel% neq 0 (
    echo ERROR: AWS CDK is not installed or not in PATH
    echo Please install CDK: npm install -g aws-cdk
    pause
    exit /b 1
)

REM Check if AWS credentials are configured
aws sts get-caller-identity >nul 2>&1
if %errorlevel% neq 0 (
    echo ERROR: AWS credentials not configured
    echo Please run: aws configure
    pause
    exit /b 1
)

REM Set environment
set ENVIRONMENT=dev
if not "%1"=="" set ENVIRONMENT=%1

echo Environment: %ENVIRONMENT%
echo.

REM Change to CDK directory
cd /d "%~dp0..\..\infrastructure\cdk"

echo Deploying Device Status Monitor Stack...
echo.

REM Deploy the stack
cdk deploy AquaChain-DeviceStatusMonitor-%ENVIRONMENT% --require-approval never

if %errorlevel% equ 0 (
    echo.
    echo ========================================
    echo   Deployment Successful!
    echo ========================================
    echo.
    echo Device Status Monitor is now active:
    echo   - Monitoring device connectivity every 2 minutes
    echo   - CloudWatch metrics and alarms configured
    echo   - Dashboard available in AWS Console
    echo.
    echo Next steps:
    echo   1. Test the deployment: python ..\..\scripts\testing\test-device-status-monitor.py
    echo   2. View dashboard: https://console.aws.amazon.com/cloudwatch/home#dashboards:name=AquaChain-DeviceStatus
    echo   3. Check device status in frontend
    echo.
) else (
    echo.
    echo ========================================
    echo   Deployment Failed!
    echo ========================================
    echo.
    echo Please check the error messages above.
    echo Common issues:
    echo   - Missing DynamoDB tables (deploy data stack first)
    echo   - Insufficient IAM permissions
    echo   - Region mismatch
    echo.
)

pause