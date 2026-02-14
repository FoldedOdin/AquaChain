@echo off
REM Enable Self-Registration in Cognito User Pool
REM WARNING: This allows anyone to create an account

echo ========================================
echo Enable Self-Registration
echo ========================================
echo.
echo WARNING: This will allow public self-registration
echo Anyone on the internet can create an account
echo.
echo This is NOT recommended for production IoT systems
echo.

set /p CONFIRM="Type 'yes' to continue: "

if /i not "%CONFIRM%"=="yes" (
    echo.
    echo Operation cancelled.
    pause
    exit /b 1
)

echo.
echo Enabling self-registration...
echo.

aws cognito-idp update-user-pool ^
  --user-pool-id ap-south-1_QUDl7hG8u ^
  --admin-create-user-config AllowAdminCreateUserOnly=false ^
  --region ap-south-1

if %ERRORLEVEL% EQU 0 (
    echo.
    echo ========================================
    echo Self-Registration Enabled
    echo ========================================
    echo.
    echo Users can now register via the frontend
    echo.
    echo SECURITY REMINDER:
    echo - Monitor new user registrations
    echo - Consider adding email verification
    echo - Implement rate limiting
    echo - Review user accounts regularly
    echo.
    echo To disable self-registration:
    echo   scripts\security\disable-self-registration.bat
    echo.
) else (
    echo.
    echo Error enabling self-registration
    echo.
)

pause
