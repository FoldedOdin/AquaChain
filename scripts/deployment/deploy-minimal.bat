@echo off
REM AquaChain Ultra Cost-Optimized Deployment Script
REM Deploys only essential stacks for minimal cost (~$20-30/month)
REM Usage: deploy-minimal.bat [environment] [region]

setlocal enabledelayedexpansion

set ENVIRONMENT=%1
if "%ENVIRONMENT%"=="" set ENVIRONMENT=dev

set AWS_REGION=%2
if "%AWS_REGION%"=="" set AWS_REGION=ap-south-1

echo ================================================================
echo     AquaChain Ultra Cost-Optimized Deployment
echo              Minimal Essential Stacks
echo.
echo   Environment: %ENVIRONMENT%
echo   Region: %AWS_REGION%
echo   Target Cost: $20-30/month
echo ================================================================
echo.

REM Pre-flight Checks
echo [Pre-flight Checks]
echo.

REM Check AWS CLI
aws --version >nul 2>&1
if errorlevel 1 (
    echo [ERROR] AWS CLI not found. Please install it first.
    echo Download from: https://aws.amazon.com/cli/
    exit /b 1
)
echo [OK] AWS CLI found

REM Check AWS credentials
aws sts get-caller-identity >nul 2>&1
if errorlevel 1 (
    echo [ERROR] AWS credentials not configured
    echo Run: aws configure
    exit /b 1
)
echo [OK] AWS credentials configured

REM Check Node.js
node --version >nul 2>&1
if errorlevel 1 (
    echo [ERROR] Node.js not found
    exit /b 1
)
echo [OK] Node.js found

REM Check Python
python --version >nul 2>&1
if errorlevel 1 (
    echo [ERROR] Python not found
    exit /b 1
)
echo [OK] Python found

REM Check CDK
cdk --version >nul 2>&1
if errorlevel 1 (
    echo [WARNING] CDK not found. Installing...
    npm install -g aws-cdk
)
echo [OK] CDK found

echo.
echo ================================================================
echo [Installing Dependencies]
echo ================================================================
echo.

REM Infrastructure dependencies
echo Installing infrastructure dependencies...
cd infrastructure\cdk
pip install -r requirements.txt
if errorlevel 1 (
    echo [ERROR] Infrastructure dependency installation failed
    exit /b 1
)
cd ..\..
echo [OK] Infrastructure dependencies installed

echo.
echo ================================================================
echo [Cost Optimization Configuration]
echo ================================================================
echo.

echo This deployment will create ONLY essential stacks:
echo.
echo   1. Security Stack      - KMS keys, IAM roles
echo   2. Core Stack          - Foundation resources
echo   3. Data Stack          - DynamoDB, S3, IoT Core
echo   4. LambdaLayers Stack  - Shared Lambda code
echo   5. Compute Stack       - Lambda functions (256MB)
echo   6. API Stack           - API Gateway, Cognito
echo   7. IoTSecurity Stack   - IoT device policies
echo.
echo Excluded (to save costs):
echo   X Monitoring Stack     - Save ~$20-30/month
echo   X Backup Stack         - Save ~$5-10/month
echo   X DR Stack             - Save ~$2-5/month
echo   X CloudFront Stack     - Save ~$10-20/month
echo   X VPC Stack            - Save ~$0-1/month (no NAT)
echo   X Cache Stack          - Save ~$15-25/month
echo   X Performance Stack    - Save ~$5-10/month
echo.
echo Estimated monthly cost: $20-30 USD
echo.

set /p CONFIRM="Continue with minimal deployment? (yes/no): "
if /i not "%CONFIRM%"=="yes" (
    echo.
    echo Deployment cancelled.
    exit /b 0
)

echo.
echo ================================================================
echo [Deploying Infrastructure]
echo ================================================================
echo.

cd infrastructure\cdk

REM Bootstrap CDK
echo Bootstrapping CDK...
for /f "tokens=*" %%a in ('aws sts get-caller-identity --query Account --output text') do set ACCOUNT_ID=%%a
cdk bootstrap aws://%ACCOUNT_ID%/%AWS_REGION%

REM Synthesize stacks
echo Synthesizing CDK stacks...
cdk synth --all

REM Deploy only essential stacks in order
echo.
echo Deploying essential stacks only...
echo.

REM Stack 1: Security (KMS, IAM)
echo ================================================================
echo [1/7] Deploying Security Stack...
echo ================================================================
cdk deploy AquaChain-Security-%ENVIRONMENT% --require-approval never
if errorlevel 1 (
    echo [ERROR] Failed to deploy Security Stack
    cd ..\..
    exit /b 1
)
echo [OK] Security Stack deployed
echo.

REM Stack 2: Core (Foundation)
echo ================================================================
echo [2/7] Deploying Core Stack...
echo ================================================================
cdk deploy AquaChain-Core-%ENVIRONMENT% --require-approval never
if errorlevel 1 (
    echo [ERROR] Failed to deploy Core Stack
    cd ..\..
    exit /b 1
)
echo [OK] Core Stack deployed
echo.

REM Stack 3: Data (DynamoDB, S3, IoT)
echo ================================================================
echo [3/7] Deploying Data Stack...
echo ================================================================
cdk deploy AquaChain-Data-%ENVIRONMENT% --require-approval never
if errorlevel 1 (
    echo [ERROR] Failed to deploy Data Stack
    cd ..\..
    exit /b 1
)
echo [OK] Data Stack deployed
echo.

REM Stack 4: Lambda Layers (Shared code)
echo ================================================================
echo [4/7] Deploying Lambda Layers Stack...
echo ================================================================
cdk deploy AquaChain-LambdaLayers-%ENVIRONMENT% --require-approval never
if errorlevel 1 (
    echo [ERROR] Failed to deploy Lambda Layers Stack
    cd ..\..
    exit /b 1
)
echo [OK] Lambda Layers Stack deployed
echo.

REM Stack 5: Compute (Lambda functions)
echo ================================================================
echo [5/7] Deploying Compute Stack...
echo ================================================================
cdk deploy AquaChain-Compute-%ENVIRONMENT% --require-approval never
if errorlevel 1 (
    echo [ERROR] Failed to deploy Compute Stack
    cd ..\..
    exit /b 1
)
echo [OK] Compute Stack deployed
echo.

REM Stack 6: API (API Gateway, Cognito)
echo ================================================================
echo [6/7] Deploying API Stack...
echo ================================================================
cdk deploy AquaChain-API-%ENVIRONMENT% --require-approval never
if errorlevel 1 (
    echo [ERROR] Failed to deploy API Stack
    cd ..\..
    exit /b 1
)
echo [OK] API Stack deployed
echo.

REM Stack 7: IoT Security (Device policies)
echo ================================================================
echo [7/7] Deploying IoT Security Stack...
echo ================================================================
cdk deploy AquaChain-IoTSecurity-%ENVIRONMENT% --require-approval never
if errorlevel 1 (
    echo [ERROR] Failed to deploy IoT Security Stack
    cd ..\..
    exit /b 1
)
echo [OK] IoT Security Stack deployed
echo.

cd ..\..

echo [OK] All essential stacks deployed successfully
echo.

echo.
echo ================================================================
echo [Post-Deployment Verification]
echo ================================================================
echo.

REM Check API Gateway
for /f "tokens=*" %%a in ('aws apigateway get-rest-apis --query "items[?name=='aquachain-api-%ENVIRONMENT%'].id" --output text 2^>nul') do set API_ID=%%a

if not "%API_ID%"=="" (
    set API_URL=https://%API_ID%.execute-api.%AWS_REGION%.amazonaws.com/%ENVIRONMENT%
    echo [OK] API Gateway: !API_URL!
) else (
    echo [WARNING] API Gateway not found
)

REM Check Cognito User Pool
for /f "tokens=*" %%a in ('aws cognito-idp list-user-pools --max-results 10 --query "UserPools[?Name=='aquachain-pool-users-%ENVIRONMENT%'].Id" --output text 2^>nul') do set USER_POOL_ID=%%a
if not "%USER_POOL_ID%"=="" (
    echo [OK] Cognito User Pool: %USER_POOL_ID%
) else (
    echo [WARNING] Cognito User Pool not found
)

REM Check DynamoDB tables
for /f "tokens=*" %%a in ('aws dynamodb list-tables --query "length(TableNames[?starts_with(@, 'aquachain-')])" --output text 2^>nul') do set TABLE_COUNT=%%a
echo [OK] Found %TABLE_COUNT% DynamoDB tables

REM Check Lambda functions
for /f "tokens=*" %%a in ('aws lambda list-functions --query "length(Functions[?starts_with(FunctionName, 'aquachain-')])" --output text 2^>nul') do set FUNCTION_COUNT=%%a
echo [OK] Found %FUNCTION_COUNT% Lambda functions

REM Check KMS keys
for /f "tokens=*" %%a in ('aws kms list-aliases --query "length(Aliases[?starts_with(AliasName, 'alias/aquachain-')])" --output text 2^>nul') do set KEY_COUNT=%%a
echo [OK] Found %KEY_COUNT% KMS keys

echo.
echo ================================================================
echo [Cost Optimization Summary]
echo ================================================================
echo.

echo Deployed Stacks: 7 (essential only)
echo.
echo Monthly Cost Estimate:
echo   - Lambda (256MB):        $2-5
echo   - DynamoDB (on-demand):  $10-15
echo   - S3 Storage:            $1-3
echo   - API Gateway:           $0-5
echo   - Cognito:               $0 (free tier)
echo   - KMS:                   $3-5
echo   - IoT Core:              $0-3
echo   - Other:                 $1-2
echo   --------------------------------
echo   TOTAL:                   $20-35/month
echo.
echo Savings vs Full Deployment:
echo   - Full deployment:       $150-200/month
echo   - Your deployment:       $20-35/month
echo   - Monthly savings:       $130-180 (85%% reduction!)
echo.

echo ================================================================
echo        ULTRA COST-OPTIMIZED DEPLOYMENT COMPLETED!
echo ================================================================
echo.
echo Environment: %ENVIRONMENT%
echo Region: %AWS_REGION%
echo Stacks Deployed: 7 essential stacks
echo Estimated Cost: $20-35/month
echo.
echo API URL: %API_URL%
echo User Pool ID: %USER_POOL_ID%
echo DynamoDB Tables: %TABLE_COUNT%
echo Lambda Functions: %FUNCTION_COUNT%
echo KMS Keys: %KEY_COUNT%
echo.
echo ================================================================
echo Next Steps:
echo ================================================================
echo.
echo 1. Create test user in Cognito:
echo    aws cognito-idp admin-create-user \
echo      --user-pool-id %USER_POOL_ID% \
echo      --username test@example.com \
echo      --region %AWS_REGION%
echo.
echo 2. Configure frontend:
echo    cd frontend
echo    npm run get-aws-config
echo.
echo 3. Test locally:
echo    cd frontend
echo    npm install
echo    npm start
echo.
echo 4. Monitor costs:
echo    - Set up AWS Budget alert at $30/month
echo    - Check AWS Cost Explorer daily
echo    - Run: scripts\check-free-tier-usage.bat
echo.
echo 5. Optional optimizations:
echo    - Keep DynamoDB on-demand (already optimal)
echo    - Review CloudWatch log retention (1 day)
echo    - Delete unused S3 objects
echo.
echo ================================================================
echo.
echo Happy deploying with minimal costs! 💰
echo.

endlocal
