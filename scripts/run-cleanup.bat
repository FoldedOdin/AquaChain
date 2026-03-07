@echo off
REM AquaChain Scripts Cleanup Runner
REM Executes the PowerShell cleanup script

echo ========================================
echo AquaChain Scripts Cleanup
echo ========================================
echo.
echo This will:
echo   1. Create a backup of current scripts
echo   2. Remove 150+ redundant/outdated scripts
echo   3. Reorganize remaining scripts
echo   4. Create comprehensive documentation
echo.
echo A backup will be created before any changes.
echo.

set /p CONFIRM="Do you want to proceed? (yes/no): "
if /i not "%CONFIRM%"=="yes" (
    echo Cleanup cancelled.
    pause
    exit /b 0
)

echo.
echo Running cleanup script...
echo.

powershell -ExecutionPolicy Bypass -File "%~dp0cleanup-scripts.ps1"

if %ERRORLEVEL% EQU 0 (
    echo.
    echo ========================================
    echo Cleanup completed successfully!
    echo ========================================
    echo.
    echo Please review the changes and test essential scripts.
    echo Backup folder created in scripts/backup-*
    echo.
) else (
    echo.
    echo ========================================
    echo Cleanup failed!
    echo ========================================
    echo.
    echo Please check the error messages above.
    echo.
)

pause
