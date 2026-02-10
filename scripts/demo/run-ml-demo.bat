@echo off
REM AquaChain ML Model Demo Runner
REM Runs the ML model demo script with proper environment

echo ========================================
echo AquaChain ML Model Demo
echo ========================================
echo.

REM Check if Python is available
python --version >nul 2>&1
if errorlevel 1 (
    echo ERROR: Python is not installed or not in PATH
    echo Please install Python 3.8+ and try again
    pause
    exit /b 1
)

REM Check if required packages are installed
echo Checking dependencies...
python -c "import xgboost" >nul 2>&1
if errorlevel 1 (
    echo.
    echo WARNING: XGBoost is not installed
    echo Installing required packages...
    pip install xgboost numpy scikit-learn
    if errorlevel 1 (
        echo ERROR: Failed to install dependencies
        pause
        exit /b 1
    )
)

echo.
echo Starting demo...
echo.

REM Run the interactive demo (requires user input)
python scripts\demo\ml_model_demo.py

echo.
echo Demo completed!
pause
