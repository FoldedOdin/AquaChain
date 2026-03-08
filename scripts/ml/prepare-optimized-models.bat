@echo off
REM Prepare optimized custom models for SageMaker deployment
REM Uses smaller custom models (14 MB) instead of large v1.0 models (1.2 GB)

echo ============================================================
echo AquaChain - Prepare Optimized Models for SageMaker
echo ============================================================
echo.

REM Step 1: Convert custom models
echo Step 1: Converting custom models...
echo.
python convert-custom-models.py
if %ERRORLEVEL% NEQ 0 (
    echo.
    echo ERROR: Model conversion failed!
    exit /b 1
)

echo.
echo ============================================================
echo.

REM Step 2: Package models for SageMaker
echo Step 2: Packaging models for SageMaker...
echo.
python package-optimized-models.py
if %ERRORLEVEL% NEQ 0 (
    echo.
    echo ERROR: Model packaging failed!
    exit /b 1
)

echo.
echo ============================================================
echo SUCCESS! Models ready for deployment
echo ============================================================
echo.
echo Next step: Deploy SageMaker stack
echo   cd infrastructure\cdk
echo   cdk deploy AquaChain-SageMaker-dev
echo.

pause
