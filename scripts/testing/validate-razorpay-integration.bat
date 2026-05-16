@echo off
REM Razorpay Integration Validation Script
REM This script validates the Razorpay payment integration setup

echo ========================================
echo Razorpay Integration Validation
echo ========================================
echo.

REM Check if we're in the correct directory
if not exist "frontend\.env" (
    echo ERROR: frontend\.env not found
    echo Please run this script from the project root directory
    exit /b 1
)

echo [1/5] Checking environment variables...
echo.

REM Check frontend .env file
findstr /C:"REACT_APP_RAZORPAY_KEY_ID" frontend\.env >nul
if %errorlevel% equ 0 (
    echo [OK] REACT_APP_RAZORPAY_KEY_ID found in .env
) else (
    echo [ERROR] REACT_APP_RAZORPAY_KEY_ID not found in .env
    echo Please add: REACT_APP_RAZORPAY_KEY_ID=rzp_test_YOUR_KEY
    exit /b 1
)

REM Check if key is not the placeholder
findstr /C:"REACT_APP_RAZORPAY_KEY_ID=rzp_test_YOUR_KEY_ID_HERE" frontend\.env >nul
if %errorlevel% equ 0 (
    echo [WARNING] Using placeholder Razorpay key
    echo Please replace with actual test key from https://dashboard.razorpay.com/app/keys
)

echo.
echo [2/5] Checking frontend component...
echo.

REM Check if RazorpayCheckout component exists
if exist "frontend\src\components\Dashboard\RazorpayCheckout.tsx" (
    echo [OK] RazorpayCheckout.tsx found
) else (
    echo [ERROR] RazorpayCheckout.tsx not found
    exit /b 1
)

REM Check for key fixes in component
findstr /C:"razorpayKey" frontend\src\components\Dashboard\RazorpayCheckout.tsx >nul
if %errorlevel% equ 0 (
    echo [OK] razorpayKey state variable found
) else (
    echo [ERROR] razorpayKey state variable not found
    echo Component may not have the latest fixes
    exit /b 1
)

findstr /C:"ALWAYS create fresh order" frontend\src\components\Dashboard\RazorpayCheckout.tsx >nul
if %errorlevel% equ 0 (
    echo [OK] Fresh order creation logic found
) else (
    echo [WARNING] Fresh order creation comment not found
)

echo.
echo [3/5] Checking backend Lambda function...
echo.

REM Check if payment service exists
if exist "lambda\payment_service\payment_service.py" (
    echo [OK] payment_service.py found
) else (
    echo [ERROR] payment_service.py not found
    exit /b 1
)

REM Check if backend returns key
findstr /C:"'key': credentials['key_id']" lambda\payment_service\payment_service.py >nul
if %errorlevel% equ 0 (
    echo [OK] Backend returns Razorpay key in response
) else (
    echo [ERROR] Backend does not return key in response
    exit /b 1
)

echo.
echo [4/5] Checking documentation...
echo.

if exist "DOCS\guides\features\payments\RAZORPAY_DEBUGGING_GUIDE.md" (
    echo [OK] Debugging guide found
) else (
    echo [WARNING] Debugging guide not found
)

if exist "DOCS\guides\features\payments\QUICK_REFERENCE.md" (
    echo [OK] Quick reference found
) else (
    echo [WARNING] Quick reference not found
)

if exist "RAZORPAY_FIX_COMPLETE.md" (
    echo [OK] Fix summary found
) else (
    echo [WARNING] Fix summary not found
)

echo.
echo [5/5] Checking Node modules...
echo.

if exist "frontend\node_modules\razorpay" (
    echo [OK] Razorpay SDK installed
) else (
    echo [WARNING] Razorpay SDK not found in node_modules
    echo Run: cd frontend ^&^& npm install
)

echo.
echo ========================================
echo Validation Complete
echo ========================================
echo.

echo Next Steps:
echo 1. Start development server: cd frontend ^&^& npm start
echo 2. Open browser console
echo 3. Navigate to payment page
echo 4. Test payment flow with test card: 4111 1111 1111 1111
echo.
echo Documentation:
echo - Quick Reference: DOCS\guides\features\payments\QUICK_REFERENCE.md
echo - Debugging Guide: DOCS\guides\features\payments\RAZORPAY_DEBUGGING_GUIDE.md
echo - Fix Summary: RAZORPAY_FIX_COMPLETE.md
echo.

pause
