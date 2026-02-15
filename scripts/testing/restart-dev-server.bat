@echo off
REM Restart Development Server with Fresh Environment
REM This ensures .env.local is loaded correctly

echo ========================================
echo Restarting Development Server
echo ========================================
echo.

echo Step 1: Stopping any running dev servers...
echo Please press Ctrl+C in the terminal running npm start
echo.
pause

echo.
echo Step 2: Clearing node cache...
cd frontend
if exist "node_modules\.cache" (
    rmdir /s /q "node_modules\.cache"
    echo Cache cleared!
) else (
    echo No cache to clear
)

echo.
echo Step 3: Verifying .env.local exists...
if exist ".env.local" (
    echo ✓ .env.local found
    echo.
    echo Contents:
    type .env.local | findstr "REACT_APP_AWS_REGION REACT_APP_USER_POOL_ID REACT_APP_IDENTITY_POOL_ID"
) else (
    echo ✗ .env.local NOT FOUND!
    echo Please create it first
    pause
    exit /b 1
)

echo.
echo Step 4: Starting dev server...
echo The server will load .env.local settings
echo.
echo After server starts:
echo 1. Open http://localhost:3000
echo 2. Press F12 to open DevTools
echo 3. Go to Application ^> Storage ^> Clear site data
echo 4. Refresh the page
echo 5. Try logging in
echo.

start cmd /k "npm start"

echo.
echo ========================================
echo Dev server starting in new window...
echo ========================================
echo.
echo IMPORTANT: Clear browser storage before testing!
echo.
pause
