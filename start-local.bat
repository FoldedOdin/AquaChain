@echo off
REM Start AquaChain Local Development
REM This starts both frontend and mock backend

echo ========================================
echo   AquaChain - Local Development
echo ========================================
echo.

REM Check if node_modules exists
if not exist "frontend\node_modules" (
    echo ERROR: Dependencies not installed!
    echo.
    echo Please run setup-local.bat first:
    echo   setup-local.bat
    echo.
    pause
    exit /b 1
)

echo Starting local development environment...
echo.
echo Frontend: http://localhost:3000
echo Mock API: http://localhost:3002
echo.
echo Use OTP: 123456 for email verification
echo.
echo Press Ctrl+C to stop all servers
echo.
echo ========================================
echo.

cd frontend

REM Start both dev server and React app
call npm run start:full
