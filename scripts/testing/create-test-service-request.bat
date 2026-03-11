@echo off
REM Create test service request for Technician Dashboard testing
REM Usage: create-test-service-request.bat <TECHNICIAN_COGNITO_SUB> [environment] [count]

setlocal

if "%1"=="" (
    echo Usage: create-test-service-request.bat ^<TECHNICIAN_COGNITO_SUB^> [environment] [count]
    echo.
    echo Example: create-test-service-request.bat abc123-def456-ghi789 dev 1
    echo.
    echo Arguments:
    echo   TECHNICIAN_COGNITO_SUB  - Cognito sub ID of the technician (required)
    echo   environment             - dev, staging, or prod (default: dev)
    echo   count                   - Number of test requests to create (default: 1)
    exit /b 1
)

set TECHNICIAN_ID=%1
set ENVIRONMENT=%2
set COUNT=%3

if "%ENVIRONMENT%"=="" set ENVIRONMENT=dev
if "%COUNT%"=="" set COUNT=1

echo ========================================
echo Creating Test Service Request
echo ========================================
echo Technician ID: %TECHNICIAN_ID%
echo Environment: %ENVIRONMENT%
echo Count: %COUNT%
echo ========================================
echo.

python scripts\testing\create-test-service-request.py --technician-id %TECHNICIAN_ID% --environment %ENVIRONMENT% --count %COUNT%

if %ERRORLEVEL% EQU 0 (
    echo.
    echo ========================================
    echo Test service request created successfully!
    echo ========================================
) else (
    echo.
    echo ========================================
    echo Failed to create test service request
    echo ========================================
    exit /b 1
)

endlocal
