@echo off
REM Trigger Auto-Progress for Demo Orders (Windows)
REM This script manually triggers the auto-progression for demo orders

echo.
echo ========================================
echo  Auto-Progress Demo Orders
echo ========================================
echo.

cd /d "%~dp0..\.."

python scripts\testing\trigger-auto-progress.py

echo.
pause
