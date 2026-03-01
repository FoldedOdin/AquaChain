@echo off
echo ========================================
echo Cleaning and Restarting Dev Server
echo ========================================

echo.
echo [1/5] Stopping any running dev servers...
taskkill /F /IM node.exe 2>nul
timeout /t 2 /nobreak >nul

echo.
echo [2/5] Clearing npm cache...
cd /d "%~dp0"
call npm cache clean --force

echo.
echo [3/5] Removing node_modules/.cache...
if exist "node_modules\.cache" (
    rmdir /s /q "node_modules\.cache"
    echo Cache directory removed
) else (
    echo No cache directory found
)

echo.
echo [4/5] Clearing browser storage (instructions)...
echo IMPORTANT: After the server starts, do the following in your browser:
echo   1. Open DevTools (F12)
echo   2. Go to Application tab
echo   3. Click "Clear storage" on the left
echo   4. Click "Clear site data" button
echo   5. Refresh the page (Ctrl+Shift+R for hard refresh)
echo.

echo.
echo [5/5] Starting dev server...
echo.
call npm start

pause
