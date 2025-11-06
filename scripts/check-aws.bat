@echo off
echo Checking AWS Configuration...
echo.

echo [1] AWS Account:
aws sts get-caller-identity

echo.
echo [2] AWS Region:
aws configure get region

echo.
echo [3] Checking if CDK is already bootstrapped:
aws cloudformation describe-stacks --stack-name CDKToolkit --region ap-south-1 2>nul
if %errorlevel% equ 0 (
    echo CDK Bootstrap stack EXISTS
) else (
    echo CDK Bootstrap stack NOT FOUND - needs bootstrapping
)

echo.
echo [4] Testing AWS connectivity:
aws s3 ls --region ap-south-1 2>nul
if %errorlevel% equ 0 (
    echo AWS connectivity OK
) else (
    echo AWS connectivity FAILED
)
