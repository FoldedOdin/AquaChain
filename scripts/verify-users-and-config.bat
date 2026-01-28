@echo off
REM Verify Users and Configuration
REM Diagnoses login issues and provides solutions

echo 🔧 AquaChain - Verify Users and Configuration
echo ==============================================================
echo This script will:
echo • Check if users were created correctly in Cognito
echo • Verify User Pool and Client configuration
echo • Check frontend configuration
echo • Test authentication
echo • Provide solutions for login issues
echo ==============================================================

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

echo Running verification script...
python scripts\verify-users-and-config.py

echo.
echo ==============================================================
echo If issues were found, follow the solutions provided above.
echo After making changes, restart your frontend server:
echo   cd frontend
echo   npm start
echo ==============================================================

pause