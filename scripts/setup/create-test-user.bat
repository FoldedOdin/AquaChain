@echo off
REM Create Test User in Cognito
REM This script creates a test user for development and testing

echo ========================================
echo Create AquaChain Test User
echo ========================================
echo.

set USER_POOL_ID=ap-south-1_QUDl7hG8u
set REGION=ap-south-1

echo Enter test user email:
set /p USER_EMAIL=

echo Enter temporary password (min 8 chars, must include uppercase, lowercase, number, special char):
set /p TEMP_PASSWORD=

echo.
echo Creating user: %USER_EMAIL%
echo.

aws cognito-idp admin-create-user ^
  --user-pool-id %USER_POOL_ID% ^
  --username %USER_EMAIL% ^
  --user-attributes Name=email,Value=%USER_EMAIL% Name=email_verified,Value=true ^
  --temporary-password %TEMP_PASSWORD% ^
  --region %REGION%

if %ERRORLEVEL% EQU 0 (
    echo.
    echo ========================================
    echo User Created Successfully!
    echo ========================================
    echo.
    echo Email: %USER_EMAIL%
    echo Temporary Password: %TEMP_PASSWORD%
    echo.
    echo IMPORTANT: User will be prompted to change password on first login
    echo.
    echo Next steps:
    echo 1. Start frontend: cd frontend ^&^& npm start
    echo 2. Go to http://localhost:3000
    echo 3. Sign in with the credentials above
    echo 4. Change the temporary password when prompted
    echo.
) else (
    echo.
    echo ========================================
    echo Error Creating User
    echo ========================================
    echo.
    echo Please check:
    echo 1. AWS CLI is configured correctly
    echo 2. You have permissions to create Cognito users
    echo 3. Password meets requirements (min 8 chars, uppercase, lowercase, number, special char)
    echo.
)

pause
