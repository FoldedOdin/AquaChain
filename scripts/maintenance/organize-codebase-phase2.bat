@echo off
REM AquaChain Codebase Organization - Phase 2: Directory Consolidation
REM Generated: May 11, 2026
REM Purpose: Merge duplicate directories and relocate misplaced files

echo ========================================
echo AquaChain Codebase Organization
echo Phase 2: Directory Consolidation
echo ========================================
echo.

REM Safety check
echo WARNING: This script will move and consolidate directories.
echo Ensure Phase 1 completed successfully before proceeding.
echo Press Ctrl+C to cancel, or
pause

cd /d "%~dp0..\.."

echo.
echo Creating backup commit...
git add -A
git commit -m "Pre-Phase 2 backup"
if errorlevel 1 (
    echo WARNING: Git commit failed. Continue anyway? Press Ctrl+C to cancel.
    pause
)

echo.
echo ========================================
echo Step 1: Moving test files to tests/
echo ========================================

if not exist "tests\ml" mkdir "tests\ml"
if not exist "tests\integration" mkdir "tests\integration"
if not exist "tests\iot" mkdir "tests\iot"

if exist "test_multiple_predictions.py" (
    echo Moving test_multiple_predictions.py to tests\ml\
    move "test_multiple_predictions.py" "tests\ml\"
)

if exist "test_xgboost_endpoint.py" (
    echo Moving test_xgboost_endpoint.py to tests\ml\
    move "test_xgboost_endpoint.py" "tests\ml\"
)

if exist "test-backend-deduplication.py" (
    echo Moving test-backend-deduplication.py to tests\integration\
    move "test-backend-deduplication.py" "tests\integration\"
)

if exist "test-broadcast.py" (
    echo Moving test-broadcast.py to tests\integration\
    move "test-broadcast.py" "tests\integration\"
)

if exist "test-demo-device.py" (
    echo Moving test-demo-device.py to tests\iot\
    move "test-demo-device.py" "tests\iot\"
)

echo.
echo ========================================
echo Step 2: Moving IoT scripts
echo ========================================

if not exist "scripts\iot" mkdir "scripts\iot"

if exist "send_sensor_data.py" (
    echo Moving send_sensor_data.py to scripts\iot\
    move "send_sensor_data.py" "scripts\iot\"
)

echo.
echo ========================================
echo Step 3: Moving reports to DOCS/
echo ========================================

if not exist "DOCS\reports" mkdir "DOCS\reports"
if not exist "DOCS\fixes" mkdir "DOCS\fixes"

if exist "FINAL_VERIFICATION_REPORT.md" (
    echo Moving FINAL_VERIFICATION_REPORT.md to DOCS\reports\
    move "FINAL_VERIFICATION_REPORT.md" "DOCS\reports\"
)

if exist "RAZORPAY_FIX_COMPLETE.md" (
    echo Moving RAZORPAY_FIX_COMPLETE.md to DOCS\fixes\
    move "RAZORPAY_FIX_COMPLETE.md" "DOCS\fixes\"
)

if exist "READING_HISTORY_DIAGNOSIS.md" (
    echo Moving READING_HISTORY_DIAGNOSIS.md to DOCS\reports\
    move "READING_HISTORY_DIAGNOSIS.md" "DOCS\reports\"
)

if exist "us-east-1-backup-20260314-081655.json" (
    echo Moving us-east-1-backup-20260314-081655.json to backups\
    if not exist "backups" mkdir "backups"
    move "us-east-1-backup-20260314-081655.json" "backups\"
)

echo.
echo ========================================
echo Step 4: Consolidating reports/ directory
echo ========================================

if exist "reports" (
    if not exist "DOCS\reports\test-reports" mkdir "DOCS\reports\test-reports"
    echo Copying reports/ to DOCS\reports\test-reports\
    xcopy /E /I /Y "reports" "DOCS\reports\test-reports"
    echo Deleting reports/ directory...
    rmdir /s /q "reports"
    echo Consolidated reports/
) else (
    echo reports/ not found, skipping...
)

echo.
echo ========================================
echo Step 5: Consolidating project_report/ directory
echo ========================================

if exist "project_report" (
    if not exist "DOCS\project_report" mkdir "DOCS\project_report"
    echo Copying project_report/ to DOCS\project_report\
    xcopy /E /I /Y "project_report" "DOCS\project_report"
    echo Deleting project_report/ directory...
    rmdir /s /q "project_report"
    echo Consolidated project_report/
) else (
    echo project_report/ not found, skipping...
)

echo.
echo ========================================
echo Step 6: Moving Sensors/ to iot-firmware/
echo ========================================

if exist "Sensors" (
    if not exist "iot-firmware\sensors" mkdir "iot-firmware\sensors"
    echo Copying Sensors/ to iot-firmware\sensors\
    xcopy /E /I /Y "Sensors" "iot-firmware\sensors"
    echo Deleting Sensors/ directory...
    rmdir /s /q "Sensors"
    echo Moved Sensors/ to iot-firmware\sensors\
) else (
    echo Sensors/ not found, skipping...
)

echo.
echo ========================================
echo Step 7: Deleting empty/obsolete directories
echo ========================================

if exist "package" (
    echo Deleting empty package/ directory...
    rmdir /s /q "package"
)

if exist "src\ordering-system" (
    echo WARNING: Checking if src\ordering-system is duplicate...
    echo If this contains unique code, manual review needed.
    echo Skipping automatic deletion. Review manually.
)

if exist "node_modules" (
    echo WARNING: Found root-level node_modules/
    echo This should only exist in frontend/
    echo Deleting root-level node_modules/...
    rmdir /s /q "node_modules"
)

echo.
echo ========================================
echo Step 8: Committing changes
echo ========================================

git add -A
git commit -m "Phase 2: Directory consolidation - moved test files, reports, and IoT scripts"

if errorlevel 1 (
    echo WARNING: Git commit failed. Check git status manually.
) else (
    echo Successfully committed Phase 2 changes.
)

echo.
echo ========================================
echo Phase 2 Complete!
echo ========================================
echo.
echo Summary:
echo - Moved test files to tests/ subdirectories
echo - Moved IoT scripts to scripts\iot\
echo - Consolidated reports/ into DOCS\reports\
echo - Consolidated project_report/ into DOCS\project_report\
echo - Moved Sensors/ to iot-firmware\sensors\
echo - Deleted empty directories
echo.
echo Next steps:
echo 1. Review changes: git diff main
echo 2. Test builds: npm run build (frontend), cdk synth (infrastructure)
echo 3. If everything works, run Phase 3: organize-codebase-phase3.bat
echo 4. If issues occur, rollback: git checkout main
echo.
echo Press any key to exit...
pause >nul
