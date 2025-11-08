@echo off
REM Test AquaChain Infrastructure
REM Verifies all components are working after optimization

echo ========================================
echo  AQUACHAIN INFRASTRUCTURE TEST
echo ========================================
echo.

echo [1/8] Testing AWS Connection...
aws sts get-caller-identity --query "Account" --output text >nul 2>&1
if %ERRORLEVEL% EQU 0 (
    echo ✓ AWS connection successful
    aws sts get-caller-identity --query "{Account:Account, User:Arn}" --output table
) else (
    echo ✗ AWS connection failed
    echo Please run: aws configure
    pause
    exit /b 1
)
echo.

echo [2/8] Checking CloudFormation Stacks...
echo.
aws cloudformation describe-stacks --region ap-south-1 --query "Stacks[?contains(StackName, 'AquaChain') && StackStatus != 'DELETE_COMPLETE'].{Name:StackName, Status:StackStatus}" --output table
echo.

echo [3/8] Checking DynamoDB Tables...
echo.
aws dynamodb list-tables --region ap-south-1 --query "TableNames[?contains(@, 'AquaChain')]" --output table
echo.

echo Checking if tables are active...
for /f "tokens=*" %%i in ('aws dynamodb list-tables --region ap-south-1 --query "TableNames[?contains(@, 'AquaChain')]" --output text') do (
    aws dynamodb describe-table --region ap-south-1 --table-name %%i --query "Table.{Name:TableName, Status:TableStatus, Items:ItemCount, Size:TableSizeBytes}" --output table 2>nul
)
echo.

echo [4/8] Checking Lambda Functions...
echo.
aws lambda list-functions --region ap-south-1 --query "Functions[?contains(FunctionName, 'AquaChain')].{Name:FunctionName, Runtime:Runtime, Memory:MemorySize}" --output table
echo.

echo [5/8] Checking S3 Buckets...
echo.
aws s3 ls | findstr aquachain
echo.

echo [6/8] Checking API Gateway...
echo.
aws apigateway get-rest-apis --region ap-south-1 --query "items[?contains(name, 'AquaChain')].{Name:name, ID:id, Created:createdDate}" --output table
echo.

echo [7/8] Checking Cognito User Pool...
echo.
aws cognito-idp list-user-pools --region ap-south-1 --max-results 10 --query "UserPools[?contains(Name, 'AquaChain')].{Name:Name, ID:Id, Status:Status}" --output table
echo.

echo [8/8] Checking IoT Things...
echo.
aws iot list-things --region ap-south-1 --query "things[?contains(thingName, 'AquaChain')].{Name:thingName, Type:thingTypeName}" --output table 2>nul
if %ERRORLEVEL% NEQ 0 (
    echo No IoT devices registered yet (this is normal)
)
echo.

echo ========================================
echo  DETAILED HEALTH CHECK
echo ========================================
echo.

echo Checking DynamoDB Provisioned Capacity...
for /f "tokens=*" %%i in ('aws dynamodb list-tables --region ap-south-1 --query "TableNames[?contains(@, 'AquaChain')]" --output text') do (
    echo.
    echo Table: %%i
    aws dynamodb describe-table --region ap-south-1 --table-name %%i --query "Table.{BillingMode:BillingModeSummary.BillingMode, ReadCapacity:ProvisionedThroughput.ReadCapacityUnits, WriteCapacity:ProvisionedThroughput.WriteCapacityUnits}" --output table 2>nul
)
echo.

echo ========================================
echo  COST CHECK
echo ========================================
echo.

echo Current month costs (may take a moment)...
aws ce get-cost-and-usage --time-period Start=2025-11-01,End=2025-11-02 --granularity DAILY --metrics BlendedCost --region us-east-1 2>nul
echo.

echo ========================================
echo  TEST SUMMARY
echo ========================================
echo.

echo ✓ AWS Connection: Working
echo ✓ CloudFormation Stacks: Listed above
echo ✓ DynamoDB Tables: Listed above
echo ✓ Lambda Functions: Listed above
echo ✓ S3 Buckets: Listed above
echo ✓ API Gateway: Listed above
echo ✓ Cognito: Listed above
echo.

echo ========================================
echo  NEXT STEPS
echo ========================================
echo.

echo 1. Check if all stacks show "CREATE_COMPLETE" or "UPDATE_COMPLETE"
echo 2. Verify DynamoDB tables show "BillingMode: PROVISIONED"
echo 3. Confirm Lambda functions are listed
echo 4. Check S3 buckets exist
echo.

echo To test API endpoints:
echo   1. Get API Gateway URL from AWS Console
echo   2. Test with: curl https://your-api-url/health
echo.

echo To check costs:
echo   1. Open AWS Console
echo   2. Go to Cost Explorer
echo   3. Compare today vs yesterday
echo.

echo To check free tier usage:
echo   Run: check-free-tier-usage.bat
echo.

pause
