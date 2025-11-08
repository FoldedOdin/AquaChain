@echo off
REM Delete All AquaChain Infrastructure
REM This will make your cost ₹0/month

echo ========================================
echo  DELETE ALL AQUACHAIN INFRASTRUCTURE
echo ========================================
echo.

echo WARNING: This will delete ALL your stacks!
echo You can redeploy anytime with: cdk deploy --all
echo.

set /p CONFIRM="Are you sure you want to delete everything? (yes/no): "
if /i not "%CONFIRM%"=="yes" (
    echo Operation cancelled.
    exit /b 0
)

echo.
echo Starting deletion...
echo This will take 10-15 minutes.
echo.

cd infrastructure\cdk

echo Deleting all stacks...
cdk destroy --all --force

if %ERRORLEVEL% EQU 0 (
    echo.
    echo ========================================
    echo  ✓ ALL STACKS DELETED!
    echo ========================================
    echo.
    echo Your AWS cost is now: ₹0/month
    echo.
    echo To redeploy when needed:
    echo   cd infrastructure\cdk
    echo   cdk deploy --all
    echo.
    echo Deployment takes ~30 minutes
    echo.
) else (
    echo.
    echo ⚠ Some stacks may have failed to delete
    echo Check AWS Console for details
    echo.
)

pause
