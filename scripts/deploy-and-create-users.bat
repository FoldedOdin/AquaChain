@echo off
REM Deploy Infrastructure and Create Real Users
REM Complete workflow for production-like testing

echo 🚀 Deploy Infrastructure and Create Real Users
echo ==============================================================
echo This will:
echo 1. Deploy AWS infrastructure (Cognito, Lambda, API Gateway)
echo 2. Create real supply chain users in Cognito
echo 3. Configure frontend for real authentication
echo 4. Provide login credentials
echo.
echo ⚠️  WARNING: This will create real AWS resources and may incur costs
echo ==============================================================

set /p confirm="Continue with AWS deployment? (y/n): "
if /i not "%confirm%"=="y" (
    echo Deployment cancelled.
    exit /b 0
)

echo.
echo Step 1: Deploying AWS infrastructure...
call scripts\deployment\deploy-admin-service.bat
if %errorlevel% neq 0 (
    echo ❌ Infrastructure deployment failed
    exit /b 1
)

echo.
echo Step 2: Finding User Pool ID...
python scripts\get-user-pool-id.py

echo.
echo Step 3: Creating supply chain users...
python scripts\create-supply-chain-users-with-passwords.py

echo.
echo Step 4: Configuring frontend for real authentication...
python scripts\fix-frontend-auth-config.py

echo.
echo ==============================================================
echo ✅ DEPLOYMENT AND USER CREATION COMPLETE!
echo.
echo Your supply chain users are ready for login.
echo Check the generated credential files for login details.
echo.
echo Restart your frontend server:
echo   cd frontend
echo   npm start
echo ==============================================================

pause