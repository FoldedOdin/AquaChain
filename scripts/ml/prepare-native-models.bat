@echo off
REM Prepare XGBoost models in native format for SageMaker deployment
REM Solves scipy/numpy version incompatibility issue

echo ========================================
echo Preparing Native Format Models
echo ========================================
echo.

REM Step 1: Convert pickled models to native format
echo Step 1: Converting pickled models to XGBoost native format...
echo.
python convert-models-to-native.py
if %ERRORLEVEL% NEQ 0 (
    echo.
    echo ========================================
    echo ERROR: Model conversion failed
    echo ========================================
    exit /b 1
)

echo.
echo ========================================
echo Step 1 Complete: Models Converted
echo ========================================
echo.
pause

REM Step 2: Package models for SageMaker
echo Step 2: Packaging models for SageMaker...
echo.
python package-native-models.py
if %ERRORLEVEL% NEQ 0 (
    echo.
    echo ========================================
    echo ERROR: Model packaging failed
    echo ========================================
    exit /b 1
)

echo.
echo ========================================
echo SUCCESS! Models Ready for Deployment
echo ========================================
echo.
echo Next steps:
echo 1. Deploy SageMaker stack:
echo    cd ..\..\infrastructure\cdk
echo    cdk deploy AquaChain-SageMaker-dev
echo.
echo 2. Monitor endpoint:
echo    cd ..\..\scripts\ml
echo    .\monitor-endpoint.bat
echo.
pause
