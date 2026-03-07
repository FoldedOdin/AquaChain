@echo off
REM AquaChain Comprehensive System Test Runner (Batch)
REM Simple wrapper for running the comprehensive test suite

echo ========================================
echo AquaChain Comprehensive System Test
echo ========================================
echo.

REM Check if environment argument is provided
set ENVIRONMENT=%1
if "%ENVIRONMENT%"=="" set ENVIRONMENT=dev

echo Environment: %ENVIRONMENT%
echo.

REM Run PowerShell script
powershell -ExecutionPolicy Bypass -File "%~dp0run-comprehensive-test.ps1" -Environment %ENVIRONMENT%

pause
