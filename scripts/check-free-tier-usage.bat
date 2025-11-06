@echo off
REM Check AWS Free Tier Usage
REM Helps identify which services are exceeding free tier limits

echo ========================================
echo  AWS FREE TIER USAGE CHECK
echo ========================================
echo.

echo Checking your AWS Free Tier usage...
echo.

echo ========================================
echo  1. LAMBDA USAGE
echo ========================================
echo Free Tier: 1M requests/month, 400,000 GB-seconds
echo.

REM Get Lambda invocations for last 30 days
aws cloudwatch get-metric-statistics ^
    --region ap-south-1 ^
    --namespace AWS/Lambda ^
    --metric-name Invocations ^
    --dimensions Name=FunctionName,Value=* ^
    --start-time %date:~-4%-%date:~4,2%-%date:~7,2%T00:00:00Z ^
    --end-time %date:~-4%-%date:~4,2%-%date:~7,2%T23:59:59Z ^
    --period 2592000 ^
    --statistics Sum ^
    --query "Datapoints[0].Sum" ^
    --output text

echo.

echo ========================================
echo  2. DYNAMODB USAGE
echo ========================================
echo Free Tier: 25 GB storage, 25 RCU, 25 WCU
echo.

REM List all DynamoDB tables
echo Tables:
aws dynamodb list-tables --region ap-south-1 --query "TableNames" --output table

echo.

echo ========================================
echo  3. S3 USAGE
echo ========================================
echo Free Tier: 5 GB storage, 20K GET, 2K PUT
echo.

REM List all S3 buckets
echo Buckets:
aws s3 ls

echo.

echo ========================================
echo  4. CLOUDWATCH USAGE
echo ========================================
echo Free Tier: 10 custom metrics, 10 alarms, 5 GB logs
echo.

REM Count CloudWatch alarms
echo Alarms:
aws cloudwatch describe-alarms --region ap-south-1 --query "length(MetricAlarms)" --output text
echo (Free tier limit: 10)

echo.

REM Count custom metrics
echo Custom Metrics:
aws cloudwatch list-metrics --region ap-south-1 --namespace "AquaChain" --query "length(Metrics)" --output text 2>nul
echo (Free tier limit: 10)

echo.

echo ========================================
echo  5. API GATEWAY USAGE
echo ========================================
echo Free Tier: 1M requests/month (first 12 months)
echo.

REM Get API Gateway requests
aws cloudwatch get-metric-statistics ^
    --region ap-south-1 ^
    --namespace AWS/ApiGateway ^
    --metric-name Count ^
    --start-time %date:~-4%-%date:~4,2%-%date:~7,2%T00:00:00Z ^
    --end-time %date:~-4%-%date:~4,2%-%date:~7,2%T23:59:59Z ^
    --period 2592000 ^
    --statistics Sum ^
    --query "Datapoints[0].Sum" ^
    --output text 2>nul

echo.

echo ========================================
echo  6. IOT CORE USAGE
echo ========================================
echo Free Tier: 250K messages/month (first 12 months)
echo.

REM Count IoT devices
echo Registered Devices:
aws iot list-things --region ap-south-1 --query "length(things)" --output text

echo.

echo ========================================
echo  RECOMMENDATIONS
echo ========================================
echo.

echo To view detailed free tier usage:
echo 1. Open AWS Console: https://console.aws.amazon.com/billing/home#/freetier
echo 2. Check "AWS Free Tier" page
echo 3. Review services exceeding limits
echo.

echo To reduce costs:
echo 1. Run: ultra-cost-optimize.bat
echo 2. Remove expensive stacks (Monitoring, Backup, DR)
echo 3. Optimize Lambda memory (1024MB -^> 256MB)
echo 4. Reduce CloudWatch log retention (30d -^> 1d)
echo.

echo ========================================
echo  COST ESTIMATION
echo ========================================
echo.

echo Current estimated cost: Rs 5,810-7,470/month
echo After optimization: Rs 249-1,000/month
echo Potential savings: Rs 4,810-6,470/month (80-90%%)
echo.

pause
