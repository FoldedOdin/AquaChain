@echo off
REM Deploy Notifications Service to AWS
REM Requires: Python 3.x, boto3, AWS credentials configured

echo ========================================
echo AquaChain Notifications Service Deploy
echo ========================================
echo.

REM Check Python
python --version >nul 2>&1
if errorlevel 1 (
    echo ERROR: Python not found
    pause
    exit /b 1
)

REM Check boto3
python -c "import boto3" >nul 2>&1
if errorlevel 1 (
    echo Installing boto3...
    pip install boto3
)

REM Check AWS credentials
aws sts get-caller-identity >nul 2>&1
if errorlevel 1 (
    echo ERROR: AWS credentials not configured
    echo Run: aws configure
    pause
    exit /b 1
)

REM Run deployment
python scripts\deploy-notifications-service.py

pause
