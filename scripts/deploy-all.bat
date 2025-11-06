@echo off
REM AquaChain Complete Deployment Script for Windows CMD
REM Usage: deploy-all.bat [environment] [region] [mode]
REM Modes: full (default), minimal (cost-optimized)

setlocal enabledelayedexpansion

set ENVIRONMENT=%1
if "%ENVIRONMENT%"=="" set ENVIRONMENT=dev

set AWS_REGION=%2
if "%AWS_REGION%"=="" set AWS_REGION=ap-south-1

set MODE=%3
if "%MODE%"=="" set MODE=full

echo ================================================================
echo          AquaChain Deployment Script
echo                Windows CMD
echo.
echo   Environment: %ENVIRONMENT%
echo   Region: %AWS_REGION%
echo   Mode: %MODE%
echo ================================================================
echo.

REM Check if minimal mode requested
if /i "%MODE%"=="minimal" (
    echo.
    echo [INFO] Minimal mode selected - deploying cost-optimized stacks only
    echo [INFO] Redirecting to deploy-minimal.bat...
    echo.
    call "%~dp0deploy-minimal.bat" %ENVIRONMENT% %AWS_REGION%
    exit /b %ERRORLEVEL%
)

echo [INFO] Full deployment mode - deploying all stacks
echo.

REM Pre-flight Checks
echo [Pre-flight Checks]
echo.

REM Check AWS CLI
aws --version >nul 2>&1
if errorlevel 1 (
    echo [ERROR] AWS CLI not found. Please install it first.
    echo Download from: https://aws.amazon.com/cli/
    exit /b 1
)
echo [OK] AWS CLI found

REM Check AWS credentials
aws sts get-caller-identity >nul 2>&1
if errorlevel 1 (
    echo [ERROR] AWS credentials not configured
    echo Run: aws configure
    exit /b 1
)
echo [OK] AWS credentials configured

REM Check Node.js
node --version >nul 2>&1
if errorlevel 1 (
    echo [ERROR] Node.js not found
    exit /b 1
)
echo [OK] Node.js found

REM Check Python
python --version >nul 2>&1
if errorlevel 1 (
    echo [ERROR] Python not found
    exit /b 1
)
echo [OK] Python found

REM Check CDK
cdk --version >nul 2>&1
if errorlevel 1 (
    echo [WARNING] CDK not found. Installing...
    npm install -g aws-cdk
)
echo [OK] CDK found

echo.
echo ================================================================
echo [Installing Dependencies]
echo ================================================================
echo.

REM Frontend dependencies
echo Installing frontend dependencies...
cd frontend
call npm install
if errorlevel 1 (
    echo [ERROR] Frontend dependency installation failed
    exit /b 1
)
cd ..
echo [OK] Frontend dependencies installed

REM Infrastructure dependencies
echo Installing infrastructure dependencies...
cd infrastructure\cdk
pip install -r requirements.txt
if errorlevel 1 (
    echo [ERROR] Infrastructure dependency installation failed
    exit /b 1
)
cd ..\..
echo [OK] Infrastructure dependencies installed

echo.
echo ================================================================
echo [Deploying Infrastructure]
echo ================================================================
echo.

cd infrastructure\cdk

REM Bootstrap CDK
echo Bootstrapping CDK...
for /f "tokens=*" %%a in ('aws sts get-caller-identity --query Account --output text') do set ACCOUNT_ID=%%a
cdk bootstrap aws://%ACCOUNT_ID%/%AWS_REGION%

REM Synthesize stacks
echo Synthesizing CDK stacks...
cdk synth --all

REM Deploy stacks
echo.
echo Deploying stacks...
echo.

set STACKS=AquaChain-Security-%ENVIRONMENT% AquaChain-Core-%ENVIRONMENT% AquaChain-Data-%ENVIRONMENT% AquaChain-Compute-%ENVIRONMENT% AquaChain-API-%ENVIRONMENT%

for %%s in (%STACKS%) do (
    echo Deploying %%s...
    cdk deploy %%s --require-approval never
    if errorlevel 1 (
        echo [ERROR] Failed to deploy %%s
        echo Check CloudFormation console for details
        cd ..\..
        exit /b 1
    )
    echo [OK] %%s deployed
    echo.
)

cd ..\..

echo [OK] Infrastructure deployed successfully
echo.

REM Build Frontend
echo ================================================================
echo [Building Frontend]
echo ================================================================
echo.

cd frontend
call npm run build
if errorlevel 1 (
    echo [ERROR] Frontend build failed
    cd ..
    exit /b 1
)
echo [OK] Frontend built successfully
cd ..

echo.
echo ================================================================
echo [Post-Deployment Verification]
echo ================================================================
echo.

REM Check API Gateway
for /f "tokens=*" %%a in ('aws apigateway get-rest-apis --query "items[?name=='aquachain-api-%ENVIRONMENT%'].id" --output text 2^>nul') do set API_ID=%%a

if not "%API_ID%"=="" (
    set API_URL=https://%API_ID%.execute-api.%AWS_REGION%.amazonaws.com/%ENVIRONMENT%
    echo [OK] API Gateway: !API_URL!
) else (
    echo [WARNING] API Gateway not found
)

REM Check DynamoDB tables
for /f "tokens=*" %%a in ('aws dynamodb list-tables --query "length(TableNames[?starts_with(@, 'aquachain-')])" --output text 2^>nul') do set TABLE_COUNT=%%a
echo [OK] Found %TABLE_COUNT% DynamoDB tables

REM Check Lambda functions
for /f "tokens=*" %%a in ('aws lambda list-functions --query "length(Functions[?starts_with(FunctionName, 'aquachain-')])" --output text 2^>nul') do set FUNCTION_COUNT=%%a
echo [OK] Found %FUNCTION_COUNT% Lambda functions

echo.
echo ================================================================
echo           DEPLOYMENT COMPLETED SUCCESSFULLY!
echo ================================================================
echo.
echo Environment: %ENVIRONMENT%
echo Region: %AWS_REGION%
echo API URL: %API_URL%
echo DynamoDB Tables: %TABLE_COUNT%
echo Lambda Functions: %FUNCTION_COUNT%
echo.
echo Next Steps:
echo 1. Verify all services are running
echo 2. Create test user in Cognito
echo 3. Test frontend at http://localhost:3000
echo 4. Check CloudWatch logs for errors
echo.
echo Happy deploying!
echo.

endlocal
