@echo off
REM Fix Inventory Manager Login Issue
REM Resets password for the inventory manager user so they can sign in

echo 🔧 AquaChain - Fix Inventory Manager Login
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

echo Running the fix script...
python scripts\fix-inventory-manager-login.py

echo.
echo ==================================================
echo Instructions for the inventory manager:
echo 1. Go to the AquaChain login page
echo 2. Enter email: karthikpradeep897@gmail.com
echo 3. Enter the temporary password shown above
echo 4. You will be prompted to create a new permanent password
echo 5. After setting the new password, you can access the system
echo ==================================================

pause