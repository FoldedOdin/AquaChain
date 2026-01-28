@echo off
REM Get User Pool ID using AWS CLI commands

echo 🔍 Getting User Pool ID using AWS CLI
echo ==================================================

REM Check if AWS CLI is installed
aws --version >nul 2>&1
if %errorlevel% neq 0 (
    echo ✗ AWS CLI not found. Please install and configure AWS CLI.
    exit /b 1
)

echo Method 1: Checking CloudFormation stacks...
echo.

REM Try to get from CloudFormation
aws cloudformation describe-stacks --stack-name AquaChain-API-dev --query "Stacks[0].Outputs[?OutputKey=='UserPoolId'].OutputValue" --output text 2>nul
if %errorlevel% equ 0 (
    echo ✓ Found User Pool ID from CloudFormation
    goto :end
)

echo Method 2: Listing Cognito User Pools...
echo.

REM List all user pools and filter for AquaChain
aws cognito-idp list-user-pools --max-results 50 --query "UserPools[?contains(Name, 'AquaChain') || contains(Name, 'aquachain')].{Name:Name,Id:Id}" --output table

echo.
echo ==================================================
echo Copy the User Pool ID from above and use it when prompted
echo ==================================================

:end
pause