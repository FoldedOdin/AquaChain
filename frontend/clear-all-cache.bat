@echo off
echo ========================================
echo AGGRESSIVE CACHE CLEARING
echo ========================================

echo.
echo [1/6] Killing all Node processes...
taskkill /F /IM node.exe 2>nul
timeout /t 2 /nobreak >nul

echo.
echo [2/6] Clearing npm cache...
cd /d "%~dp0"
call npm cache clean --force

echo.
echo [3/6] Removing build artifacts...
if exist "build" (
    rmdir /s /q "build"
    echo Build directory removed
)

echo.
echo [4/6] Removing node_modules cache...
if exist "node_modules\.cache" (
    rmdir /s /q "node_modules\.cache"
    echo Cache directory removed
)

echo.
echo [5/6] Removing .env.local if exists...
if exist ".env.local" (
    del /f ".env.local"
    echo .env.local removed
)

echo.
echo [6/6] IMPORTANT: Manual browser steps required!
echo.
echo ========================================
echo CRITICAL: You MUST do this in your browser:
echo ========================================
echo.
echo 1. Close ALL browser tabs for localhost:3000
echo 2. Open a NEW browser window
echo 3. Press Ctrl+Shift+Delete (Clear browsing data)
echo 4. Select:
echo    - Cookies and site data
echo    - Cached images and files
echo    - Time range: All time
echo 5. Click "Clear data"
echo 6. Close browser completely
echo 7. Reopen browser
echo.
echo OR use Incognito/Private mode for testing
echo.
echo ========================================
echo.

pause

echo.
echo Starting dev server...
call npm start
