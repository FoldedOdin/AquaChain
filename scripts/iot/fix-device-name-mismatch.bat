@echo off
REM Fix Device Name Mismatch Between Config and AWS IoT Thing

echo ========================================
echo Fix Device Name Mismatch
echo ========================================
echo.

echo Step 1: Check current IoT Things...
python scripts\iot\check-iot-thing.py

echo.
echo ========================================
echo Choose Your Solution:
echo ========================================
echo.
echo Option 1: Rename AWS IoT Thing (ESP32-001 to DEV-0001)
echo   - Keeps your config.h as DEV-0001
echo   - Requires AWS changes
echo.
echo Option 2: Revert config.h (DEV-0001 to ESP32-001)
echo   - Keeps AWS IoT Thing as ESP32-001
echo   - Only requires reflashing ESP32
echo.
set /p choice="Enter 1 or 2: "

if "%choice%"=="1" (
    echo.
    echo Renaming AWS IoT Thing...
    python scripts\iot\rename-iot-thing.py ESP32-001 DEV-0001
    echo.
    echo ✅ AWS Thing renamed to DEV-0001
    echo.
    echo Next: Reflash ESP32 with current config.h
) else if "%choice%"=="2" (
    echo.
    echo Reverting config.h to ESP32-001...
    echo.
    echo Manual step required:
    echo 1. Open: iot-firmware\aquachain-esp32\config.h
    echo 2. Change: #define DEVICE_ID "ESP32-001"
    echo 3. Save and reflash ESP32
    echo.
    echo Then update Lambda to accept ESP32-XXX format:
    echo   python scripts\deployment\deploy_lambda_fix.py
) else (
    echo Invalid choice
)

echo.
pause
