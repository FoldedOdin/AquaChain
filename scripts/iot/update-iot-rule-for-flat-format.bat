@echo off
REM Update IoT Rule to handle flat ESP32 data format

echo ============================================================
echo Update IoT Rule for Flat ESP32 Data Format
echo ============================================================
echo.

python scripts\iot\update-iot-rule-for-flat-format.py

if %ERRORLEVEL% EQU 0 (
    echo.
    echo ============================================================
    echo SUCCESS: IoT Rule Updated
    echo ============================================================
) else (
    echo.
    echo ============================================================
    echo FAILED: IoT Rule Update Failed
    echo ============================================================
    exit /b 1
)
