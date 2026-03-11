@echo off
REM Deploy SageMaker Infrastructure for AquaChain
REM This script sets up the complete SageMaker ML infrastructure

echo ========================================
echo AquaChain SageMaker Infrastructure Setup
echo ========================================

REM Check if Python is available
python --version >nul 2>&1
if errorlevel 1 (
    echo ERROR: Python is not installed or not in PATH
    echo Please install Python 3.8+ and try again
    pause
    exit /b 1
)

REM Check if AWS CLI is configured
aws sts get-caller-identity >nul 2>&1
if errorlevel 1 (
    echo ERROR: AWS CLI is not configured
    echo Please run 'aws configure' and try again
    pause
    exit /b 1
)

REM Check if CDK is installed
cdk --version >nul 2>&1
if errorlevel 1 (
    echo ERROR: AWS CDK is not installed
    echo Please install CDK: npm install -g aws-cdk
    pause
    exit /b 1
)

echo.
echo Checking prerequisites...
echo ✓ Python is available
echo ✓ AWS CLI is configured
echo ✓ AWS CDK is available

echo.
echo Starting SageMaker infrastructure deployment...
echo.

REM Run the Python deployment script
python "%~dp0deploy-sagemaker-infrastructure.py"

if errorlevel 1 (
    echo.
    echo ❌ Deployment failed. Check the error messages above.
    pause
    exit /b 1
)

echo.
echo ✅ SageMaker infrastructure deployment completed!
echo.
echo Next steps:
echo 1. Test the IoT data pipeline with real sensor data
echo 2. Monitor SageMaker endpoint performance in CloudWatch
echo 3. Set up automated model retraining
echo.

pause