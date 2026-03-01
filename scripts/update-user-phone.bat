@echo off
REM Script to update user phone number in DynamoDB
REM Make sure AWS credentials are configured

echo ========================================
echo AquaChain User Phone Update
echo ========================================
echo.

REM Check if Python is installed
python --version >nul 2>&1
if errorlevel 1 (
    echo ERROR: Python is not installed or not in PATH
    echo Please install Python 3.x and try again
    pause
    exit /b 1
)

REM Check if boto3 is installed
python -c "import boto3" >nul 2>&1
if errorlevel 1 (
    echo Installing boto3...
    pip install boto3
    echo.
)

REM Run the update script
python scripts\update_user_phone.py

echo.
pause
