@echo off
REM Check Prerequisites for SageMaker Deployment

echo ========================================
echo AquaChain SageMaker Prerequisites Check
echo ========================================

REM Run the prerequisites check
python "%~dp0check-prerequisites.py"

if errorlevel 1 (
    echo.
    echo ❌ Prerequisites check failed.
    echo Please fix the issues above before running the deployment.
    pause
    exit /b 1
)

echo.
echo ✅ Prerequisites check completed!
echo.

pause