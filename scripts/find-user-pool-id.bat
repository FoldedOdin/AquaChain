@echo off
REM Find Cognito User Pool ID from deployed infrastructure

echo 🔍 Finding AquaChain Cognito User Pool ID
echo ==================================================

REM Check if Python is installed
python --version >nul 2>&1
if %errorlevel% neq 0 (
    echo ✗ Python not found. Please install Python.
    exit /b 1
)

REM Check if AWS CLI is installed and configured
aws --version >nul 2>&1
if %errorlevel% neq 0 (
    echo ✗ AWS CLI not found. Please install and configure AWS CLI.
    exit /b 1
)

echo Searching for User Pool ID...
python scripts\get-user-pool-id.py

echo.
echo ==================================================
echo If User Pool ID was found, you can now run:
echo scripts\create-supply-chain-users-with-passwords.bat
echo ==================================================

pause