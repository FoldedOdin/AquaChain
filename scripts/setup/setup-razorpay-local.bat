@echo off
REM Setup Razorpay for Local Development (No AWS Required)
REM This configures frontend only for local testing

echo ========================================
echo   Razorpay Local Setup
echo ========================================
echo.
echo This setup is for LOCAL DEVELOPMENT ONLY.
echo It configures the frontend without AWS Secrets Manager.
echo.
echo For production deployment, you'll need AWS permissions.
echo.

REM Get Razorpay Key ID
:get_key_id
set /p KEY_ID="Enter Razorpay Key ID (rzp_test_*): "
if "%KEY_ID%"=="" goto get_key_id

echo.
echo Configuring frontend...

REM Check if .env.local exists
if exist "frontend\.env.local" (
    echo Found existing frontend\.env.local
    
    REM Check if key already exists
    findstr /C:"REACT_APP_RAZORPAY_KEY_ID" frontend\.env.local >nul
    if errorlevel 1 (
        echo Adding REACT_APP_RAZORPAY_KEY_ID
        echo REACT_APP_RAZORPAY_KEY_ID=%KEY_ID% >> frontend\.env.local
    ) else (
        echo Updating REACT_APP_RAZORPAY_KEY_ID
        powershell -Command "(Get-Content frontend\.env.local) -replace 'REACT_APP_RAZORPAY_KEY_ID=.*', 'REACT_APP_RAZORPAY_KEY_ID=%KEY_ID%' | Set-Content frontend\.env.local"
    )
) else (
    echo Creating frontend\.env.local
    copy frontend\.env.example frontend\.env.local >nul
    echo. >> frontend\.env.local
    echo # Razorpay Configuration >> frontend\.env.local
    echo REACT_APP_RAZORPAY_KEY_ID=%KEY_ID% >> frontend\.env.local
)

echo.
echo ========================================
echo   Local Setup Complete!
echo ========================================
echo.
echo ✓ Frontend configured with Razorpay Key ID
echo.
echo IMPORTANT NOTES:
echo.
echo 1. This is for LOCAL TESTING ONLY
echo    - Frontend will work
echo    - Backend payment verification will fail without AWS setup
echo.
echo 2. To test payments locally:
echo    cd frontend
echo    npm start
echo.
echo 3. Use test card: 4111 1111 1111 1111
echo.
echo 4. For full production setup, you need:
echo    - AWS Secrets Manager access
echo    - IAM permissions
echo    - Run: scripts\setup\add-razorpay-permissions.bat
echo.

pause
