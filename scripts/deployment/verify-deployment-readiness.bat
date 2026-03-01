@echo off
REM AquaChain Deployment Readiness Verification Script
REM Checks if all prerequisites are met before deployment

setlocal enabledelayedexpansion

echo ================================================================
echo     AquaChain Deployment Readiness Verification
echo ================================================================
echo.

set ERRORS=0
set WARNINGS=0

REM Check AWS CLI
echo [1/10] Checking AWS CLI...
aws --version >nul 2>&1
if errorlevel 1 (
    echo [ERROR] AWS CLI not found
    set /a ERRORS+=1
) else (
    for /f "tokens=*" %%a in ('aws --version 2^>^&1') do echo [OK] %%a
)

REM Check AWS Credentials
echo [2/10] Checking AWS credentials...
aws sts get-caller-identity >nul 2>&1
if errorlevel 1 (
    echo [ERROR] AWS credentials not configured
    set /a ERRORS+=1
) else (
    for /f "tokens=*" %%a in ('aws sts get-caller-identity --query Account --output text 2^>nul') do (
        echo [OK] AWS Account: %%a
    )
)

REM Check Node.js
echo [3/10] Checking Node.js...
node --version >nul 2>&1
if errorlevel 1 (
    echo [ERROR] Node.js not found
    set /a ERRORS+=1
) else (
    for /f "tokens=*" %%a in ('node --version') do echo [OK] Node.js %%a
)

REM Check Python
echo [4/10] Checking Python...
python --version >nul 2>&1
if errorlevel 1 (
    echo [ERROR] Python not found
    set /a ERRORS+=1
) else (
    for /f "tokens=*" %%a in ('python --version') do echo [OK] %%a
)

REM Check CDK
echo [5/10] Checking AWS CDK...
cdk --version >nul 2>&1
if errorlevel 1 (
    echo [WARNING] AWS CDK not found - will be installed during deployment
    set /a WARNINGS+=1
) else (
    for /f "tokens=*" %%a in ('cdk --version') do echo [OK] %%a
)

REM Check CDK Bootstrap
echo [6/10] Checking CDK bootstrap status...
aws cloudformation describe-stacks --stack-name CDKToolkit --region ap-south-1 >nul 2>&1
if errorlevel 1 (
    echo [WARNING] CDK not bootstrapped - run: cdk bootstrap aws://ACCOUNT/ap-south-1
    set /a WARNINGS+=1
) else (
    echo [OK] CDK bootstrapped
)

REM Check Razorpay Secret
echo [7/10] Checking Razorpay credentials in Secrets Manager...
aws secretsmanager describe-secret --secret-id aquachain-secret-razorpay-credentials-dev --region ap-south-1 >nul 2>&1
if errorlevel 1 (
    echo [WARNING] Razorpay secret not found in Secrets Manager
    echo          Run: scripts\setup\setup-razorpay-complete.bat
    set /a WARNINGS+=1
) else (
    echo [OK] Razorpay credentials configured
)

REM Check Google OAuth Secret
echo [8/10] Checking Google OAuth credentials in Secrets Manager...
aws secretsmanager describe-secret --secret-id aquachain-secret-google-oauth-dev --region ap-south-1 >nul 2>&1
if errorlevel 1 (
    echo [WARNING] Google OAuth secret not found in Secrets Manager
    echo          Create manually or deployment will use default values
    set /a WARNINGS+=1
) else (
    echo [OK] Google OAuth credentials configured
)

REM Check Infrastructure Dependencies
echo [9/10] Checking infrastructure dependencies...
if exist "infrastructure\cdk\requirements.txt" (
    echo [OK] CDK requirements.txt found
) else (
    echo [ERROR] CDK requirements.txt not found
    set /a ERRORS+=1
)

REM Check Frontend Dependencies
echo [10/10] Checking frontend dependencies...
if exist "frontend\package.json" (
    echo [OK] Frontend package.json found
    if exist "frontend\node_modules" (
        echo [OK] Frontend dependencies installed
    ) else (
        echo [WARNING] Frontend dependencies not installed - run: cd frontend ^&^& npm install
        set /a WARNINGS+=1
    )
) else (
    echo [ERROR] Frontend package.json not found
    set /a ERRORS+=1
)

echo.
echo ================================================================
echo                    Verification Summary
echo ================================================================
echo.

if %ERRORS% EQU 0 (
    if %WARNINGS% EQU 0 (
        echo [SUCCESS] All checks passed! Ready for deployment.
        echo.
        echo Next steps:
        echo   1. Run: scripts\deployment\deploy-all.bat dev ap-south-1 minimal
        echo   2. Or: scripts\deployment\deploy-all.bat dev ap-south-1 full
        echo.
    ) else (
        echo [READY] System is ready with %WARNINGS% warning(s)
        echo.
        echo You can proceed with deployment, but consider addressing warnings.
        echo.
    )
) else (
    echo [FAILED] Found %ERRORS% error(s) and %WARNINGS% warning(s)
    echo.
    echo Please fix errors before deploying.
    echo.
)

echo Errors: %ERRORS%
echo Warnings: %WARNINGS%
echo.

if %ERRORS% GTR 0 (
    exit /b 1
) else (
    exit /b 0
)

endlocal
