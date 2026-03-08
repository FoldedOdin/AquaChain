@echo off
REM Prepare and upload trained models to S3 for SageMaker

echo ========================================
echo Preparing Models for SageMaker
echo ========================================

REM Save current directory
set SCRIPT_DIR=%~dp0
set PROJECT_ROOT=%SCRIPT_DIR%..\..

echo Current directory: %CD%
echo Script directory: %SCRIPT_DIR%
echo Project root: %PROJECT_ROOT%

echo.
echo Step 1: Installing Python dependencies...
pip install boto3 numpy scikit-learn xgboost

echo.
echo Step 2: Packaging models for SageMaker...
cd /d "%PROJECT_ROOT%\lambda\ml_inference"
echo Working directory: %CD%

python prepare_sagemaker_model.py

if %ERRORLEVEL% EQU 0 (
    echo.
    echo ========================================
    echo Model Preparation Complete!
    echo ========================================
    echo.
    echo Models uploaded to S3
    echo Check sagemaker_models/model_s3_uri.txt for S3 location
) else (
    echo.
    echo ========================================
    echo Model Preparation Failed!
    echo ========================================
    cd /d "%SCRIPT_DIR%"
    exit /b 1
)

cd /d "%SCRIPT_DIR%"
