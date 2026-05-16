@echo off
REM ============================================================================
REM AquaChain Complete AWS Resource Destruction Script
REM WARNING: This will permanently delete ALL AquaChain resources across ALL regions
REM ============================================================================

echo.
echo ========================================================================
echo  CRITICAL WARNING: COMPLETE AWS RESOURCE DESTRUCTION
echo ========================================================================
echo.
echo This script will PERMANENTLY DELETE:
echo   - All CDK stacks in current region
echo   - All S3 buckets (including versioned objects)
echo   - All DynamoDB tables
echo   - All Lambda functions
echo   - All IoT devices and certificates
echo   - All CloudWatch logs
echo   - All Cognito user pools
echo   - Resources in ALL AWS regions
echo.
echo THIS ACTION CANNOT BE UNDONE!
echo.
echo Press Ctrl+C to cancel, or
pause

echo.
echo ========================================================================
echo  STEP 1: Destroying CDK Stacks in Current Region
echo ========================================================================
echo.

cd /d "%~dp0..\..\infrastructure\cdk"

REM Destroy stacks in reverse dependency order
echo Destroying Contact Service Stack...
call cdk destroy AquaChain-ContactService-dev --force 2>nul

echo Destroying Ledger Security Stack...
call cdk destroy AquaChain-LedgerSecurity-dev --force 2>nul

echo Destroying SageMaker Stack...
call cdk destroy AquaChain-SageMaker-dev --force 2>nul

echo Destroying Auto Technician Assignment Stack...
call cdk destroy AquaChain-AutoTechnicianAssignment-dev --force 2>nul

echo Destroying Security Audit Stack...
call cdk destroy AquaChain-SecurityAudit-dev --force 2>nul

echo Destroying WebSocket Stack...
call cdk destroy AquaChain-WebSocket-dev --force 2>nul

echo Destroying Enhanced Ordering Stack...
call cdk destroy AquaChain-EnhancedOrdering-dev --force 2>nul

echo Destroying Production Monitoring Stack...
call cdk destroy AquaChain-ProductionMonitoring-dev --force 2>nul

echo Destroying Dashboard Overhaul Stack...
call cdk destroy AquaChain-DashboardOverhaul-dev --force 2>nul

echo Destroying Lambda Performance Stack...
call cdk destroy AquaChain-LambdaPerformance-dev --force 2>nul

echo Destroying Lambda Layers Stack...
call cdk destroy AquaChain-LambdaLayers-dev --force 2>nul

echo Destroying GDPR Compliance Stack...
call cdk destroy AquaChain-GDPRCompliance-dev --force 2>nul

echo Destroying Audit Logging Stack...
call cdk destroy AquaChain-AuditLogging-dev --force 2>nul

echo Destroying Data Classification Stack...
call cdk destroy AquaChain-DataClassification-dev --force 2>nul

echo Destroying Performance Dashboard Stack...
call cdk destroy AquaChain-PerformanceDashboard-dev --force 2>nul

echo Destroying Phase 3 Stack...
call cdk destroy AquaChain-Phase3-dev --force 2>nul

echo Destroying IoT Security Stack...
call cdk destroy AquaChain-IoTSecurity-dev --force 2>nul

echo Destroying IoT Core Stack...
call cdk destroy AquaChain-IoTCore-dev --force 2>nul

echo Destroying CloudFront Stack...
call cdk destroy AquaChain-CloudFront-dev --force 2>nul

echo Destroying API Throttling Stack...
call cdk destroy AquaChain-APIThrottling-dev --force 2>nul

echo Destroying Backup Stack...
call cdk destroy AquaChain-Backup-dev --force 2>nul

echo Destroying VPC Stack...
call cdk destroy AquaChain-VPC-dev --force 2>nul

echo Destroying Landing Page Stack...
call cdk destroy AquaChain-LandingPage-dev --force 2>nul

echo Destroying Disaster Recovery Stack...
call cdk destroy AquaChain-DR-dev --force 2>nul

echo Destroying Monitoring Stack...
call cdk destroy AquaChain-Monitoring-dev --force 2>nul

echo Destroying API Stack...
call cdk destroy AquaChain-API-dev --force 2>nul

echo Destroying Compute Stack...
call cdk destroy AquaChain-Compute-dev --force 2>nul

echo Destroying Data Stack...
call cdk destroy AquaChain-Data-dev --force 2>nul

echo Destroying Core Stack...
call cdk destroy AquaChain-Core-dev --force 2>nul

echo Destroying Security Stack...
call cdk destroy AquaChain-Security-dev --force 2>nul

echo.
echo ========================================================================
echo  STEP 2: Cleaning Up S3 Buckets (Force Delete with Versioning)
echo ========================================================================
echo.

REM List and delete all AquaChain S3 buckets
for /f "tokens=*" %%b in ('aws s3 ls ^| findstr "aquachain"') do (
    set bucket=%%b
    set bucket=!bucket:~20!
    echo Deleting bucket: !bucket!
    aws s3 rb s3://!bucket! --force 2>nul
)

echo.
echo ========================================================================
echo  STEP 3: Deleting CloudWatch Log Groups
echo ========================================================================
echo.

for /f "tokens=*" %%l in ('aws logs describe-log-groups --query "logGroups[?contains(logGroupName, 'aquachain')].logGroupName" --output text') do (
    echo Deleting log group: %%l
    aws logs delete-log-group --log-group-name %%l 2>nul
)

echo.
echo ========================================================================
echo  STEP 4: Multi-Region Cleanup
echo ========================================================================
echo.

REM List of all AWS regions
set regions=us-east-1 us-east-2 us-west-1 us-west-2 eu-west-1 eu-west-2 eu-central-1 ap-south-1 ap-southeast-1 ap-southeast-2 ap-northeast-1 ap-northeast-2 sa-east-1 ca-central-1

for %%r in (%regions%) do (
    echo.
    echo Cleaning region: %%r
    echo ----------------------------------------
    
    REM Delete Lambda functions
    for /f "tokens=*" %%f in ('aws lambda list-functions --region %%r --query "Functions[?contains(FunctionName, 'AquaChain')].FunctionName" --output text 2^>nul') do (
        echo   Deleting Lambda: %%f
        aws lambda delete-function --region %%r --function-name %%f 2>nul
    )
    
    REM Delete DynamoDB tables
    for /f "tokens=*" %%t in ('aws dynamodb list-tables --region %%r --query "TableNames[?contains(@, 'AquaChain')]" --output text 2^>nul') do (
        echo   Deleting DynamoDB table: %%t
        aws dynamodb delete-table --region %%r --table-name %%t 2>nul
    )
    
    REM Delete IoT things
    for /f "tokens=*" %%i in ('aws iot list-things --region %%r --query "things[?contains(thingName, 'AquaChain')].thingName" --output text 2^>nul') do (
        echo   Deleting IoT thing: %%i
        aws iot delete-thing --region %%r --thing-name %%i 2>nul
    )
    
    REM Delete API Gateways
    for /f "tokens=*" %%a in ('aws apigateway get-rest-apis --region %%r --query "items[?contains(name, 'AquaChain')].id" --output text 2^>nul') do (
        echo   Deleting API Gateway: %%a
        aws apigateway delete-rest-api --region %%r --rest-api-id %%a 2>nul
    )
    
    REM Delete CloudFormation stacks
    for /f "tokens=*" %%s in ('aws cloudformation list-stacks --region %%r --stack-status-filter CREATE_COMPLETE UPDATE_COMPLETE --query "StackSummaries[?contains(StackName, 'AquaChain')].StackName" --output text 2^>nul') do (
        echo   Deleting CloudFormation stack: %%s
        aws cloudformation delete-stack --region %%r --stack-name %%s 2>nul
    )
)

echo.
echo ========================================================================
echo  STEP 5: Deleting Cognito User Pools
echo ========================================================================
echo.

for /f "tokens=*" %%p in ('aws cognito-idp list-user-pools --max-results 60 --query "UserPools[?contains(Name, 'AquaChain')].Id" --output text 2^>nul') do (
    echo Deleting Cognito User Pool: %%p
    aws cognito-idp delete-user-pool --user-pool-id %%p 2>nul
)

echo.
echo ========================================================================
echo  STEP 6: Deleting IAM Roles and Policies
echo ========================================================================
echo.

for /f "tokens=*" %%r in ('aws iam list-roles --query "Roles[?contains(RoleName, 'AquaChain')].RoleName" --output text 2^>nul') do (
    echo Detaching policies from role: %%r
    for /f "tokens=*" %%p in ('aws iam list-attached-role-policies --role-name %%r --query "AttachedPolicies[].PolicyArn" --output text 2^>nul') do (
        aws iam detach-role-policy --role-name %%r --policy-arn %%p 2>nul
    )
    echo Deleting role: %%r
    aws iam delete-role --role-name %%r 2>nul
)

echo.
echo ========================================================================
echo  STEP 7: Deleting KMS Keys
echo ========================================================================
echo.

for /f "tokens=*" %%k in ('aws kms list-keys --query "Keys[].KeyId" --output text 2^>nul') do (
    for /f "tokens=*" %%a in ('aws kms describe-key --key-id %%k --query "KeyMetadata.Description" --output text 2^>nul ^| findstr "AquaChain"') do (
        echo Scheduling KMS key deletion: %%k
        aws kms schedule-key-deletion --key-id %%k --pending-window-in-days 7 2>nul
    )
)

echo.
echo ========================================================================
echo  CLEANUP COMPLETE
echo ========================================================================
echo.
echo All AquaChain AWS resources have been deleted or scheduled for deletion.
echo.
echo Note: Some resources may take time to fully delete:
echo   - KMS keys: 7-day waiting period
echo   - S3 buckets with versioning: May require manual cleanup
echo   - CloudFormation stacks: May take 5-10 minutes
echo.
echo Verify deletion by checking AWS Console in all regions.
echo.
pause
