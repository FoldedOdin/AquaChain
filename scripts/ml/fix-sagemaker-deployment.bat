@echo off
REM Fix SageMaker Deployment - Delete failed stack and redeploy with correct ECR account
REM This script fixes the ECR repository permissions issue

echo ========================================
echo SageMaker Deployment Fix
echo ========================================
echo.

echo Step 1: Deleting failed CloudFormation stack...
cd ..\..\infrastructure\cdk
cdk destroy AquaChain-SageMaker-dev --force
if %ERRORLEVEL% NEQ 0 (
    echo Warning: Stack deletion had issues, continuing anyway...
)
echo.

echo Step 2: Waiting for stack deletion to complete...
timeout /t 10 /nobreak
echo.

echo Step 3: Redeploying SageMaker stack with correct configuration...
cdk deploy AquaChain-SageMaker-dev --require-approval never
if %ERRORLEVEL% NEQ 0 (
    echo ========================================
    echo Deployment Failed!
    echo ========================================
    echo Check the error messages above for details.
    exit /b 1
)

echo.
echo ========================================
echo Deployment Successful!
echo ========================================
echo SageMaker stack deployed successfully with correct ECR configuration.
echo.
echo Next steps:
echo 1. Upload trained model to S3: aquachain-ml-models-dev-{account}/ml-models/current/model.tar.gz
echo 2. Test endpoint with Lambda inference function
echo 3. Monitor CloudWatch logs for any issues
echo.

cd ..\..
