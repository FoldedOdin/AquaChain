@echo off
echo.
echo AquaChain Quick Start (Windows)
echo ================================
echo.
echo Checking prerequisites...
echo.

REM Check Node.js
where node >nul 2>nul
if %ERRORLEVEL% EQU 0 (
    echo [32m✓ Node.js installed[0m
) else (
    echo [31m✗ Node.js not found[0m
    echo   Install from: https://nodejs.org
    exit /b 1
)

REM Check Python
where python >nul 2>nul
if %ERRORLEVEL% EQU 0 (
    echo [32m✓ Python installed[0m
) else (
    echo [31m✗ Python not found[0m
    echo   Install Python 3.11+
    exit /b 1
)

REM Check AWS CLI
where aws >nul 2>nul
if %ERRORLEVEL% EQU 0 (
    echo [32m✓ AWS CLI installed[0m
) else (
    echo [31m✗ AWS CLI not found[0m
    echo   Install from: https://aws.amazon.com/cli/
    exit /b 1
)

echo.
echo What would you like to do?
echo.
echo 1) Full setup (Infrastructure + Frontend)
echo 2) Frontend only (Development mode)
echo 3) Infrastructure only
echo 4) Just install dependencies
echo 5) Exit
echo.
set /p choice="Enter your choice (1-5): "

if "%choice%"=="1" goto full_setup
if "%choice%"=="2" goto frontend_only
if "%choice%"=="3" goto infrastructure_only
if "%choice%"=="4" goto dependencies_only
if "%choice%"=="5" goto exit_script
goto invalid_choice

:full_setup
echo.
echo Full Setup Selected
echo ===================
echo.
echo Installing root dependencies...
call npm install
echo.
echo Installing frontend dependencies...
cd frontend
call npm install
cd ..
echo.
echo Installing Python dependencies...
pip install -r requirements-dev.txt
echo.
echo [32m✓ Setup complete![0m
echo.
echo Run './deploy-all.sh' to deploy infrastructure
goto end

:frontend_only
echo.
echo Frontend Development Setup
echo ===========================
echo.
echo Installing frontend dependencies...
cd frontend
call npm install
if not exist ".env.development" (
    if exist ".env.example" (
        copy .env.example .env.development
        echo [33m! Please edit frontend/.env.development with your AWS settings[0m
    )
)
echo.
echo [32m✓ Frontend setup complete![0m
echo.
echo To start development server:
echo   cd frontend
echo   npm start
cd ..
goto end

:infrastructure_only
echo.
echo Infrastructure Setup
echo ====================
echo.
echo Installing CDK dependencies...
cd infrastructure\cdk
pip install -r requirements.txt
echo.
echo [32m✓ Infrastructure setup complete![0m
echo.
echo To deploy:
echo   cd infrastructure\cdk
echo   cdk bootstrap
echo   cdk deploy --all
cd ..\..
goto end

:dependencies_only
echo.
echo Installing Dependencies Only
echo ============================
echo.
echo Installing root dependencies...
call npm install
echo.
echo Installing frontend dependencies...
cd frontend
call npm install
cd ..
echo.
echo Installing Python dependencies...
pip install -r requirements-dev.txt
echo.
echo [32m✓ All dependencies installed![0m
goto end

:invalid_choice
echo [31m✗ Invalid choice[0m
exit /b 1

:exit_script
echo Goodbye!
exit /b 0

:end
echo.
echo Next steps:
echo   1. Read SETUP_GUIDE.md for detailed instructions
echo   2. Read PROJECT_REPORT.md for comprehensive documentation
echo   3. Read README_START_HERE.md for navigation
echo.
