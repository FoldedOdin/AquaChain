@echo off
REM Quick script to verify region configuration

echo ================================================================
echo          Region Configuration Verification
echo ================================================================
echo.

echo [Checking AWS CLI Configuration]
aws configure get region
echo.

echo [Checking CDK Configuration]
findstr /C:"region" infrastructure\cdk\config\environment_config.py
echo.

echo [Checking Deployment Scripts]
findstr /C:"AWS_REGION" deploy-all.bat
echo.

echo ================================================================
echo.
echo Expected region: ap-south-1 (Mumbai, India)
echo.
echo To deploy:
echo   deploy-all.bat
echo.
echo ================================================================
