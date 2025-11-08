@echo off
REM Setup Local Development Environment

echo ========================================
echo   AquaChain - Setup Local Development
echo ========================================
echo.
echo Installing dependencies...
echo.

cd frontend

REM Install all dependencies
call npm install

echo.
echo ========================================
echo Setup Complete!
echo ========================================
echo.
echo Next step: Run start-local.bat
echo.
pause
