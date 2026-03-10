@echo off
REM Clean up test orders from DynamoDB

echo ========================================
echo Clean Up Test Orders
echo ========================================
echo.

REM Check if Python is installed
where python >nul 2>nul
if %ERRORLEVEL% NEQ 0 (
    echo ERROR: Python not found. Please install Python first.
    exit /b 1
)

REM Check AWS credentials
aws sts get-caller-identity >nul 2>nul
if %ERRORLEVEL% NEQ 0 (
    echo ERROR: AWS credentials not configured. Run 'aws configure' first.
    exit /b 1
)

echo Options:
echo   1. Dry run (show what would be deleted)
echo   2. Delete CANCELLED and old orders
echo   3. Delete ALL orders (⚠️  WARNING!)
echo   4. Cancel
echo.

set /p choice="Enter your choice (1-4): "

if "%choice%"=="1" (
    echo.
    echo Running dry run...
    python cleanup-test-orders.py
) else if "%choice%"=="2" (
    echo.
    echo Deleting CANCELLED and old orders...
    python cleanup-test-orders.py --execute
) else if "%choice%"=="3" (
    echo.
    echo ⚠️  WARNING: This will delete ALL orders!
    python cleanup-test-orders.py --all --execute
) else if "%choice%"=="4" (
    echo Cancelled
    exit /b 0
) else (
    echo Invalid choice
    exit /b 1
)

echo.
pause
