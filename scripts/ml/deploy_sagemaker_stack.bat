@echo off
REM Deploy SageMaker Stack for AquaChain ML Infrastructure

echo ========================================
echo Deploying AquaChain SageMaker Stack
echo ========================================

REM Save current directory and set paths
set SCRIPT_DIR=%~dp0
set PROJECT_ROOT=%SCRIPT_DIR%..\..

cd /d "%PROJECT_ROOT%\infrastructure\cdk"

echo.
echo Step 1: Installing CDK dependencies...
call npm install

echo.
echo Step 2: Synthesizing CDK stack...
call cdk synth AquaChain-SageMaker-dev

echo.
echo Step 3: Deploying SageMaker stack...
call cdk deploy AquaChain-SageMaker-dev --require-approval never

if %ERRORLEVEL% EQU 0 (
    echo.
    echo ========================================
    echo SageMaker Stack Deployed Successfully!
    echo ========================================
    echo.
    echo Next steps:
    echo 1. Run prepare_and_upload_model.bat to upload trained models
    echo 2. Wait for SageMaker endpoint to be InService
    echo 3. Update ML inference Lambda to use SageMaker endpoint
) else (
    echo.
    echo ========================================
    echo Deployment Failed!
    echo ========================================
    cd /d "%SCRIPT_DIR%"
    exit /b 1
)

cd /d "%SCRIPT_DIR%"
