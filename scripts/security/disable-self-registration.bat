@echo off
REM Disable Self-Registration in Cognito User Pool
REM Restore admin-only user creation (recommended for production)

echo ========================================
echo Disable Self-Registration
echo ========================================
echo.
echo This will restore admin-only user creation
echo Users will need to be created by administrators
echo.

set /p CONFIRM="Type 'yes' to continue: "

if /i not "%CONFIRM%"=="yes" (
    echo.
    echo Operation cancelled.
    pause
    exit /b 1
)

echo.
echo Disabling self-registration...
echo.

aws cognito-idp update-user-pool ^
  --user-pool-id ap-south-1_QUDl7hG8u ^
  --admin-create-user-config AllowAdminCreateUserOnly=true ^
  --region ap-south-1

if %ERRORLEVEL% EQU 0 (
    echo.
    echo ========================================
    echo Self-Registration Disabled
    echo ========================================
    echo.
    echo Only administrators can create users now
    echo.
    echo To create users:
    echo   scripts\setup\create-test-user.bat
    echo.
    echo Or via AWS CLI:
    echo   aws cognito-idp admin-create-user --user-pool-id ap-south-1_QUDl7hG8u ...
    echo.
) else (
    echo.
    echo Error disabling self-registration
    echo.
)

pause
