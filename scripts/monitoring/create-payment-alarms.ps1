# Create CloudWatch Alarms for Payment Endpoints
# These alarms are cost-free (first 10 alarms free, using existing metrics)

$ErrorActionPreference = "Stop"

$REGION = "ap-south-1"
$LAMBDA_FUNCTION = "aquachain-function-payment-service-dev"
$SNS_TOPIC_ARN = "arn:aws:sns:ap-south-1:637423326645:aquachain-alerts-dev"

Write-Host "Creating CloudWatch Alarms for Payment Service..." -ForegroundColor Cyan
Write-Host ""

# Check if SNS topic exists, create if not
Write-Host "Checking SNS topic..." -ForegroundColor Yellow
try {
    aws sns get-topic-attributes --topic-arn $SNS_TOPIC_ARN --region $REGION 2>$null | Out-Null
    Write-Host "✓ SNS topic exists: $SNS_TOPIC_ARN" -ForegroundColor Green
} catch {
    Write-Host "Creating SNS topic for alerts..." -ForegroundColor Yellow
    $topicArn = aws sns create-topic --name "aquachain-alerts-dev" --region $REGION --query 'TopicArn' --output text
    $SNS_TOPIC_ARN = $topicArn
    Write-Host "✓ Created SNS topic: $SNS_TOPIC_ARN" -ForegroundColor Green
    
    # Subscribe email (optional - user can add later)
    Write-Host ""
    Write-Host "To receive email alerts, subscribe to the SNS topic:" -ForegroundColor Yellow
    Write-Host "  aws sns subscribe --topic-arn $SNS_TOPIC_ARN --protocol email --notification-endpoint your-email@example.com --region $REGION" -ForegroundColor Gray
}

Write-Host ""

# Alarm 1: Lambda Errors
Write-Host "Creating Alarm 1: Payment Lambda Errors" -ForegroundColor Cyan
try {
    aws cloudwatch put-metric-alarm `
        --alarm-name "AquaChain-Payment-Lambda-Errors-dev" `
        --alarm-description "Alert when payment Lambda has errors" `
        --metric-name "Errors" `
        --namespace "AWS/Lambda" `
        --statistic "Sum" `
        --period 300 `
        --evaluation-periods 1 `
        --threshold 5 `
        --comparison-operator "GreaterThanThreshold" `
        --dimensions "Name=FunctionName,Value=$LAMBDA_FUNCTION" `
        --alarm-actions $SNS_TOPIC_ARN `
        --treat-missing-data "notBreaching" `
        --region $REGION
    
    Write-Host "✓ Created alarm: Payment Lambda Errors" -ForegroundColor Green
    Write-Host "  Triggers when: >5 errors in 5 minutes" -ForegroundColor Gray
} catch {
    Write-Host "✗ Failed to create alarm" -ForegroundColor Red
    Write-Host "  Error: $($_.Exception.Message)" -ForegroundColor Red
}

Write-Host ""

# Alarm 2: Lambda Throttles
Write-Host "Creating Alarm 2: Payment Lambda Throttles" -ForegroundColor Cyan
try {
    aws cloudwatch put-metric-alarm `
        --alarm-name "AquaChain-Payment-Lambda-Throttles-dev" `
        --alarm-description "Alert when payment Lambda is throttled" `
        --metric-name "Throttles" `
        --namespace "AWS/Lambda" `
        --statistic "Sum" `
        --period 300 `
        --evaluation-periods 1 `
        --threshold 1 `
        --comparison-operator "GreaterThanThreshold" `
        --dimensions "Name=FunctionName,Value=$LAMBDA_FUNCTION" `
        --alarm-actions $SNS_TOPIC_ARN `
        --treat-missing-data "notBreaching" `
        --region $REGION
    
    Write-Host "✓ Created alarm: Payment Lambda Throttles" -ForegroundColor Green
    Write-Host "  Triggers when: >1 throttle in 5 minutes" -ForegroundColor Gray
} catch {
    Write-Host "✗ Failed to create alarm" -ForegroundColor Red
    Write-Host "  Error: $($_.Exception.Message)" -ForegroundColor Red
}

Write-Host ""

# Alarm 3: Lambda Duration (High Latency)
Write-Host "Creating Alarm 3: Payment Lambda High Latency" -ForegroundColor Cyan
try {
    aws cloudwatch put-metric-alarm `
        --alarm-name "AquaChain-Payment-Lambda-HighLatency-dev" `
        --alarm-description "Alert when payment Lambda has high latency" `
        --metric-name "Duration" `
        --namespace "AWS/Lambda" `
        --statistic "Average" `
        --period 300 `
        --evaluation-periods 2 `
        --threshold 3000 `
        --comparison-operator "GreaterThanThreshold" `
        --dimensions "Name=FunctionName,Value=$LAMBDA_FUNCTION" `
        --alarm-actions $SNS_TOPIC_ARN `
        --treat-missing-data "notBreaching" `
        --region $REGION
    
    Write-Host "✓ Created alarm: Payment Lambda High Latency" -ForegroundColor Green
    Write-Host "  Triggers when: Average duration >3000ms for 10 minutes" -ForegroundColor Gray
} catch {
    Write-Host "✗ Failed to create alarm" -ForegroundColor Red
    Write-Host "  Error: $($_.Exception.Message)" -ForegroundColor Red
}

Write-Host ""

# Alarm 4: API Gateway 5XX Errors
Write-Host "Creating Alarm 4: Payment API 5XX Errors" -ForegroundColor Cyan
try {
    aws cloudwatch put-metric-alarm `
        --alarm-name "AquaChain-Payment-API-5XXErrors-dev" `
        --alarm-description "Alert when payment API has 5XX errors" `
        --metric-name "5XXError" `
        --namespace "AWS/ApiGateway" `
        --statistic "Sum" `
        --period 300 `
        --evaluation-periods 1 `
        --threshold 5 `
        --comparison-operator "GreaterThanThreshold" `
        --dimensions "Name=ApiName,Value=aquachain-api-rest-dev" `
        --alarm-actions $SNS_TOPIC_ARN `
        --treat-missing-data "notBreaching" `
        --region $REGION
    
    Write-Host "✓ Created alarm: Payment API 5XX Errors" -ForegroundColor Green
    Write-Host "  Triggers when: >5 5XX errors in 5 minutes" -ForegroundColor Gray
} catch {
    Write-Host "✗ Failed to create alarm" -ForegroundColor Red
    Write-Host "  Error: $($_.Exception.Message)" -ForegroundColor Red
}

Write-Host ""

# Alarm 5: API Gateway High Latency
Write-Host "Creating Alarm 5: Payment API High Latency" -ForegroundColor Cyan
try {
    aws cloudwatch put-metric-alarm `
        --alarm-name "AquaChain-Payment-API-HighLatency-dev" `
        --alarm-description "Alert when payment API has high latency" `
        --metric-name "Latency" `
        --namespace "AWS/ApiGateway" `
        --statistic "Average" `
        --period 300 `
        --evaluation-periods 2 `
        --threshold 2000 `
        --comparison-operator "GreaterThanThreshold" `
        --dimensions "Name=ApiName,Value=aquachain-api-rest-dev" `
        --alarm-actions $SNS_TOPIC_ARN `
        --treat-missing-data "notBreaching" `
        --region $REGION
    
    Write-Host "✓ Created alarm: Payment API High Latency" -ForegroundColor Green
    Write-Host "  Triggers when: Average latency >2000ms for 10 minutes" -ForegroundColor Gray
} catch {
    Write-Host "✗ Failed to create alarm" -ForegroundColor Red
    Write-Host "  Error: $($_.Exception.Message)" -ForegroundColor Red
}

Write-Host ""
Write-Host "=== Alarm Creation Complete ===" -ForegroundColor Cyan
Write-Host ""
Write-Host "Created Alarms:" -ForegroundColor Green
Write-Host "  1. Payment Lambda Errors (>5 errors in 5 min)" -ForegroundColor Gray
Write-Host "  2. Payment Lambda Throttles (>1 throttle in 5 min)" -ForegroundColor Gray
Write-Host "  3. Payment Lambda High Latency (>3000ms avg for 10 min)" -ForegroundColor Gray
Write-Host "  4. Payment API 5XX Errors (>5 errors in 5 min)" -ForegroundColor Gray
Write-Host "  5. Payment API High Latency (>2000ms avg for 10 min)" -ForegroundColor Gray
Write-Host ""
Write-Host "Cost Impact: $0" -ForegroundColor Green
Write-Host "  - First 10 CloudWatch alarms are free" -ForegroundColor Gray
Write-Host "  - Using existing Lambda and API Gateway metrics (no additional cost)" -ForegroundColor Gray
Write-Host ""
Write-Host "To subscribe to email alerts:" -ForegroundColor Yellow
Write-Host "  aws sns subscribe --topic-arn $SNS_TOPIC_ARN --protocol email --notification-endpoint your-email@example.com --region $REGION" -ForegroundColor Gray
Write-Host ""
Write-Host "To view alarms:" -ForegroundColor Yellow
Write-Host "  aws cloudwatch describe-alarms --alarm-name-prefix 'AquaChain-Payment' --region $REGION" -ForegroundColor Gray
Write-Host ""
Write-Host "To test alarms (trigger manually):" -ForegroundColor Yellow
Write-Host "  aws cloudwatch set-alarm-state --alarm-name 'AquaChain-Payment-Lambda-Errors-dev' --state-value ALARM --state-reason 'Testing alarm' --region $REGION" -ForegroundColor Gray
