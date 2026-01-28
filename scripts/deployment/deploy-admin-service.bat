@echo off
REM Deploy Admin Service Infrastructure
REM Deploys the admin Lambda service and updates API Gateway routes

echo 🚀 Deploying AquaChain Admin Service
echo ==================================================

REM Check if Python is installed
python --version >nul 2>&1
if %errorlevel% neq 0 (
    echo ✗ Python not found. Please install Python.
    exit /b 1
)
echo ✓ Python installed

REM Check if AWS CLI is installed
aws --version >nul 2>&1
if %errorlevel% neq 0 (
    echo ✗ AWS CLI not found. Please install AWS CLI.
    exit /b 1
)
echo ✓ AWS CLI installed

REM Check if CDK is installed
cdk --version >nul 2>&1
if %errorlevel% neq 0 (
    echo ✗ AWS CDK not found. Please install AWS CDK.
    exit /b 1
)
echo ✓ AWS CDK installed

echo.
echo Installing admin service dependencies...
cd lambda\admin_service
if exist requirements.txt (
    pip install -r requirements.txt
    echo ✓ Admin service dependencies installed
) else (
    echo ✗ requirements.txt not found in admin service
    exit /b 1
)

echo.
echo Deploying infrastructure...
cd ..\..\infrastructure\cdk

REM Install CDK dependencies
echo Installing CDK dependencies...
pip install -r requirements.txt

REM Bootstrap CDK if needed
echo Checking CDK bootstrap...
cdk bootstrap

REM Deploy stacks in order
echo Deploying Security stack...
cdk deploy AquaChain-Security-dev --require-approval never
if %errorlevel% neq 0 (
    echo ✗ Failed to deploy Security stack
    exit /b 1
)
echo ✓ Security stack deployed

echo Deploying Data stack...
cdk deploy AquaChain-Data-dev --require-approval never
if %errorlevel% neq 0 (
    echo ✗ Failed to deploy Data stack
    exit /b 1
)
echo ✓ Data stack deployed

echo Deploying Compute stack...
cdk deploy AquaChain-Compute-dev --require-approval never
if %errorlevel% neq 0 (
    echo ✗ Failed to deploy Compute stack
    exit /b 1
)
echo ✓ Compute stack deployed

echo Deploying API stack...
cdk deploy AquaChain-API-dev --require-approval never
if %errorlevel% neq 0 (
    echo ✗ Failed to deploy API stack
    exit /b 1
)
echo ✓ API stack deployed

echo.
echo ==================================================
echo ✅ Admin Service Deployment Complete!
echo.
echo Next steps:
echo 1. Restart your frontend development server
echo 2. Test admin dashboard functionality
echo 3. Verify admin endpoints are working
echo.
echo Admin endpoints available:
echo - GET /api/admin/users
echo - GET/PUT /api/admin/system/configuration
echo - GET /api/admin/system/health
echo - GET /api/admin/incidents/stats
echo - GET /api/admin/audit/trail
echo - GET /api/admin/devices
echo.
echo Run 'npm start' in the frontend directory to test the changes.

cd ..\..
pause