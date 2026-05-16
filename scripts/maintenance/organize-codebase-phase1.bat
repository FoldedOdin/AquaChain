@echo off
REM AquaChain Codebase Organization - Phase 1: Critical Cleanup
REM Generated: May 11, 2026
REM Purpose: Remove temporary files and build artifacts

echo ========================================
echo AquaChain Codebase Organization
echo Phase 1: Critical Cleanup
echo ========================================
echo.

REM Safety check
echo WARNING: This script will delete temporary files and build artifacts.
echo Press Ctrl+C to cancel, or
pause

echo.
echo Creating backup commit...
git add -A
git commit -m "Pre-organization backup - Phase 1"
if errorlevel 1 (
    echo WARNING: Git commit failed. Continue anyway? Press Ctrl+C to cancel.
    pause
)

echo.
echo Creating organization branch...
git checkout -b codebase-organization-phase1
if errorlevel 1 (
    echo Branch already exists, switching to it...
    git checkout codebase-organization-phase1
)

echo.
echo ========================================
echo Step 1: Deleting temporary files from root
echo ========================================

cd /d "%~dp0..\.."

if exist "api-test.html" (
    echo Deleting api-test.html...
    del /f "api-test.html"
)

if exist "check_readings.py" (
    echo Deleting check_readings.py...
    del /f "check_readings.py"
)

if exist "COMPLETE_DELETION_CONFIRMED.md" (
    echo Deleting COMPLETE_DELETION_CONFIRMED.md...
    del /f "COMPLETE_DELETION_CONFIRMED.md"
)

if exist "DELETION_REPORT.md" (
    echo Deleting DELETION_REPORT.md...
    del /f "DELETION_REPORT.md"
)

if exist "frontend-auth-test.js" (
    echo Deleting frontend-auth-test.js...
    del /f "frontend-auth-test.js"
)

if exist "notif-key.json" (
    echo WARNING: Deleting notif-key.json (secrets should be in AWS Secrets Manager)
    del /f "notif-key.json"
)

if exist "notification_api.zip" (
    echo Deleting notification_api.zip...
    del /f "notification_api.zip"
)

if exist "otp-key.json" (
    echo WARNING: Deleting otp-key.json (secrets should be in AWS Secrets Manager)
    del /f "otp-key.json"
)

if exist "response4.json" (
    echo Deleting response4.json...
    del /f "response4.json"
)

if exist "temp-security-template.json" (
    echo Deleting temp-security-template.json...
    del /f "temp-security-template.json"
)

if exist "temp-user.json" (
    echo Deleting temp-user.json...
    del /f "temp-user.json"
)

if exist "test-admin-route.html" (
    echo Deleting test-admin-route.html...
    del /f "test-admin-route.html"
)

if exist "test-websocket.html" (
    echo Deleting test-websocket.html...
    del /f "test-websocket.html"
)

if exist "test-websocket.js" (
    echo Deleting test-websocket.js...
    del /f "test-websocket.js"
)

if exist "user_management.zip" (
    echo Deleting user_management.zip...
    del /f "user_management.zip"
)

echo.
echo ========================================
echo Step 2: Deleting build artifacts from lambda/
echo ========================================

cd lambda

if exist "auth-service-deploy.zip" (
    echo Deleting auth-service-deploy.zip...
    del /f "auth-service-deploy.zip"
)

if exist "auth-test-payload.json" (
    echo Deleting auth-test-payload.json...
    del /f "auth-test-payload.json"
)

if exist "auth-test-response.json" (
    echo Deleting auth-test-response.json...
    del /f "auth-test-response.json"
)

if exist "notification-service-deployment.zip" (
    echo Deleting notification-service-deployment.zip...
    del /f "notification-service-deployment.zip"
)

if exist "order-management-fixed.zip" (
    echo Deleting order-management-fixed.zip...
    del /f "order-management-fixed.zip"
)

if exist "order-management-update.zip" (
    echo Deleting order-management-update.zip...
    del /f "order-management-update.zip"
)

cd ..

echo.
echo ========================================
echo Step 3: Deleting lambda_fixes/ directory
echo ========================================

if exist "lambda_fixes" (
    echo WARNING: Deleting lambda_fixes/ (ensure fixes are already applied)
    rmdir /s /q "lambda_fixes"
    echo Deleted lambda_fixes/
) else (
    echo lambda_fixes/ not found, skipping...
)

echo.
echo ========================================
echo Step 4: Updating .gitignore
echo ========================================

echo.>> .gitignore
echo # Build artifacts (added by organization script)>> .gitignore
echo *.zip>> .gitignore
echo *.pyc>> .gitignore
echo __pycache__/>> .gitignore
echo.>> .gitignore
echo # Environment files (keep .env.example only)>> .gitignore
echo .env>> .gitignore
echo .env.local>> .gitignore
echo.>> .gitignore
echo # Dependencies>> .gitignore
echo node_modules/>> .gitignore
echo.>> .gitignore
echo # Cache directories>> .gitignore
echo .mypy_cache/>> .gitignore
echo .pytest_cache/>> .gitignore
echo __pycache__/>> .gitignore
echo.>> .gitignore
echo # Build directories>> .gitignore
echo build/>> .gitignore
echo dist/>> .gitignore
echo coverage/>> .gitignore
echo.>> .gitignore
echo # Temporary files>> .gitignore
echo temp-*>> .gitignore
echo *.tmp>> .gitignore
echo.>> .gitignore
echo # Backup files>> .gitignore
echo backups/>> .gitignore
echo *-backup-*/>> .gitignore

echo Updated .gitignore

echo.
echo ========================================
echo Step 5: Committing changes
echo ========================================

git add -A
git commit -m "Phase 1: Critical cleanup - removed temporary files and build artifacts"

if errorlevel 1 (
    echo WARNING: Git commit failed. Check git status manually.
) else (
    echo Successfully committed Phase 1 changes.
)

echo.
echo ========================================
echo Phase 1 Complete!
echo ========================================
echo.
echo Summary:
echo - Deleted temporary files from root directory
echo - Deleted build artifacts from lambda/
echo - Deleted lambda_fixes/ directory
echo - Updated .gitignore to prevent future pollution
echo.
echo Next steps:
echo 1. Review changes: git diff main
echo 2. Test builds: npm run build (frontend), cdk synth (infrastructure)
echo 3. If everything works, run Phase 2: organize-codebase-phase2.bat
echo 4. If issues occur, rollback: git checkout main
echo.
echo Press any key to exit...
pause >nul
