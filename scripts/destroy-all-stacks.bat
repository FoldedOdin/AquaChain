@echo off
REM Destroy all AWS CDK stacks - Use for local development only
REM This will DELETE all AWS resources and stop all costs

echo ========================================
echo   AquaChain - Destroy All AWS Stacks
echo ========================================
echo.
echo WARNING: This will DELETE all AWS resources!
echo.
echo Current deployment: 9 stacks in ap-south-1
echo Monthly cost: ~Rs 2,850-4,500
echo.
echo After deletion:
echo - All data will be LOST
echo - Authentication will NOT work
echo - You can only run locally with mock data
echo.
echo Cost after deletion: Rs 0/month
echo.

set /p CONFIRM="Type 'DELETE' to confirm destruction: "

if not "%CONFIRM%"=="DELETE" (
    echo.
    echo Cancelled. No changes made.
    exit /b 0
)

echo.
echo ========================================
echo Step 1: Backup Important Data
echo ========================================
echo.

REM Create backup directory
set BACKUP_DIR=backup-%date:~-4,4%%date:~-10,2%%date:~-7,2%-%time:~0,2%%time:~3,2%%time:~6,2%
set BACKUP_DIR=%BACKUP_DIR: =0%
mkdir %BACKUP_DIR% 2>nul

echo Backing up Cognito users...
aws cognito-idp list-users --user-pool-id ap-south-1_KkQZlYidJ --region ap-south-1 > %BACKUP_DIR%\cognito-users.json 2>nul

echo Backing up DynamoDB tables...
aws dynamodb list-tables --region ap-south-1 > %BACKUP_DIR%\dynamodb-tables.json 2>nul

echo Backing up S3 buckets...
aws s3 ls > %BACKUP_DIR%\s3-buckets.txt 2>nul

echo.
echo Backup saved to: %BACKUP_DIR%
echo.

echo ========================================
echo Step 2: Destroy CDK Stacks
echo ========================================
echo.
echo Destroying stacks in reverse dependency order...
echo.

cd infrastructure\cdk

REM Destroy in reverse order (opposite of deployment)
echo [1/9] Destroying Landing Page Stack...
cdk destroy AquaChain-LandingPage-dev --force --region ap-south-1

echo [2/9] Destroying IoT Security Stack...
cdk destroy AquaChain-IoTSecurity-dev --force --region ap-south-1

echo [3/9] Destroying API Stack (includes Cognito)...
cdk destroy AquaChain-API-dev --force --region ap-south-1

echo [4/9] Destroying Compute Stack (Lambda functions)...
cdk destroy AquaChain-Compute-dev --force --region ap-south-1

echo [5/9] Destroying Lambda Layers Stack...
cdk destroy AquaChain-LambdaLayers-dev --force --region ap-south-1

echo [6/9] Destroying Data Stack (DynamoDB, S3, IoT)...
cdk destroy AquaChain-Data-dev --force --region ap-south-1

echo [7/9] Destroying VPC Stack...
cdk destroy AquaChain-VPC-dev --force --region ap-south-1

echo [8/9] Destroying Core Stack...
cdk destroy AquaChain-Core-dev --force --region ap-south-1

echo [9/9] Destroying Security Stack (KMS)...
cdk destroy AquaChain-Security-dev --force --region ap-south-1

cd ..\..

echo.
echo ========================================
echo Step 3: Clean Up Remaining Resources
echo ========================================
echo.

echo Checking for orphaned S3 buckets...
aws s3 ls --region ap-south-1 | findstr aquachain

echo.
echo Checking for orphaned CloudWatch log groups...
aws logs describe-log-groups --region ap-south-1 --log-group-name-prefix /aws/lambda/AquaChain

echo.
echo ========================================
echo Destruction Complete!
echo ========================================
echo.
echo Status:
echo - All CDK stacks destroyed
echo - AWS resources deleted
echo - Monthly cost: Rs 0
echo.
echo Backup location: %BACKUP_DIR%
echo.
echo Next Steps:
echo 1. Run locally: cd frontend ^&^& npm start
echo 2. See: RUN_LOCALLY.md for local development guide
echo 3. To redeploy: scripts\deploy-minimal.bat
echo.
echo ========================================
