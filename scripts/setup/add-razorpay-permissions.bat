@echo off
REM Add Razorpay Secrets Manager Permissions to IAM User

echo ========================================
echo   Add Razorpay IAM Permissions
echo ========================================
echo.

set IAM_USER=Karthik
set POLICY_NAME=AquaChainRazorpaySecretsAccess

echo This script will add Secrets Manager permissions to IAM user: %IAM_USER%
echo.
echo Policy: %POLICY_NAME%
echo Permissions: Create/Read/Update Razorpay secrets
echo.

set /p CONFIRM="Continue? (y/n): "
if /i not "%CONFIRM%"=="y" (
    echo Cancelled.
    pause
    exit /b 0
)

echo.
echo Creating IAM policy...

REM Create the policy
aws iam create-policy ^
    --policy-name %POLICY_NAME% ^
    --policy-document file://scripts/setup/razorpay-iam-policy.json ^
    --description "Allows access to Razorpay credentials in Secrets Manager" 2>error.log

if errorlevel 1 (
    findstr /C:"EntityAlreadyExists" error.log >nul
    if not errorlevel 1 (
        echo Policy already exists. Attaching to user...
        del error.log
    ) else (
        echo ERROR: Failed to create policy
        type error.log
        del error.log
        pause
        exit /b 1
    )
) else (
    echo ✓ Policy created
    del error.log 2>nul
)

echo.
echo Attaching policy to user %IAM_USER%...

REM Get account ID
for /f "delims=" %%i in ('aws sts get-caller-identity --query Account --output text') do set ACCOUNT_ID=%%i

REM Attach policy to user
aws iam attach-user-policy ^
    --user-name %IAM_USER% ^
    --policy-arn arn:aws:iam::%ACCOUNT_ID%:policy/%POLICY_NAME% 2>error.log

if errorlevel 1 (
    echo ERROR: Failed to attach policy
    type error.log
    del error.log
    pause
    exit /b 1
)

del error.log 2>nul

echo.
echo ========================================
echo   Success!
echo ========================================
echo.
echo ✓ IAM policy created: %POLICY_NAME%
echo ✓ Policy attached to user: %IAM_USER%
echo.
echo Permissions granted:
echo   - secretsmanager:CreateSecret
echo   - secretsmanager:GetSecretValue
echo   - secretsmanager:PutSecretValue
echo   - secretsmanager:UpdateSecret
echo   - secretsmanager:DescribeSecret
echo.
echo You can now run:
echo   scripts\setup\setup-razorpay-complete.bat
echo.

pause
