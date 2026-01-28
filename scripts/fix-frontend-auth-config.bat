@echo off
REM Fix Frontend Authentication Configuration
REM Updates frontend to use real Cognito instead of mock auth

echo 🔧 Fix Frontend Authentication Configuration
echo ==================================================
echo This will update your frontend to use real Cognito authentication
echo instead of mock authentication.
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

echo Updating frontend configuration...
python scripts\fix-frontend-auth-config.py

echo.
echo ==================================================
echo If successful, restart your frontend server:
echo   cd frontend
echo   npm start
echo.
echo Then try logging in with your supply chain users!
echo ==================================================

pause