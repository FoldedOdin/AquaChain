# Deploy Secure OTP System with Enhanced Security Features
# This script deploys the enhanced OTP system with:
# - Hashed OTP storage
# - IP-based rate limiting
# - Global attempt lockout
# - Audit logging
# - CloudWatch metrics

Write-Host "========================================" -ForegroundColor Cyan
Write-Host "Deploying Secure OTP System" -ForegroundColor Cyan
Write-Host "========================================" -ForegroundColor Cyan
Write-Host ""

$ErrorActionPreference = "Stop"

# Configuration
$REGION = "ap-south-1"
$API_ID = aws apigateway get-rest-apis --region $REGION --query "items[?name=='AquaChain-API'].id" --output text

if ([string]::IsNullOrEmpty($API_ID)) {
    Write-Host "Error: Could not find AquaChain-API" -ForegroundColor Red
    exit 1
}

Write-Host "API Gateway ID: $API_ID" -ForegroundColor Green
Write-Host ""

# Step 1: Create AquaChain-AuthEvents table for audit logging
Write-Host "Step 1: Creating AquaChain-AuthEvents table..." -ForegroundColor Yellow

$tableExists = aws dynamodb describe-table --table-name "AquaChain-AuthEvents" --region $REGION 2>$null

if ($LASTEXITCODE -ne 0) {
    Write-Host "Creating AquaChain-AuthEvents table..." -ForegroundColor Cyan
    
    aws dynamodb create-table `
        --table-name "AquaChain-AuthEvents" `
        --attribute-definitions `
            AttributeName=email,AttributeType=S `
            AttributeName=timestamp,AttributeType=S `
        --key-schema `
            AttributeName=email,KeyType=HASH `
            AttributeName=timestamp,KeyType=RANGE `
        --billing-mode PAY_PER_REQUEST `
        --region $REGION `
        --tags Key=Project,Value=AquaChain Key=Environment,Value=dev
    
    if ($LASTEXITCODE -eq 0) {
        Write-Host "✓ AquaChain-AuthEvents table created" -ForegroundColor Green
        
        # Wait for table to be active
        Write-Host "Waiting for table to be active..." -ForegroundColor Cyan
        aws dynamodb wait table-exists --table-name "AquaChain-AuthEvents" --region $REGION
        
        # Enable TTL for automatic cleanup (90 days retention)
        Write-Host "Enabling TTL for automatic cleanup..." -ForegroundColor Cyan
        aws dynamodb update-time-to-live `
            --table-name "AquaChain-AuthEvents" `
            --time-to-live-specification "Enabled=true,AttributeName=ttl" `
            --region $REGION
        
        Write-Host "✓ TTL enabled" -ForegroundColor Green
    } else {
        Write-Host "✗ Failed to create table" -ForegroundColor Red
        exit 1
    }
} else {
    Write-Host "✓ AquaChain-AuthEvents table already exists" -ForegroundColor Green
}

Write-Host ""

# Step 2: Update OTP table with TTL if not already enabled
Write-Host "Step 2: Configuring OTP table TTL..." -ForegroundColor Yellow

$ttlStatus = aws dynamodb describe-time-to-live --table-name "AquaChain-OTP" --region $REGION --query "TimeToLiveDescription.TimeToLiveStatus" --output text

if ($ttlStatus -ne "ENABLED") {
    Write-Host "Enabling TTL on AquaChain-OTP table..." -ForegroundColor Cyan
    aws dynamodb update-time-to-live `
        --table-name "AquaChain-OTP" `
        --time-to-live-specification "Enabled=true,AttributeName=ttl" `
        --region $REGION
    
    Write-Host "✓ TTL enabled on OTP table" -ForegroundColor Green
} else {
    Write-Host "✓ TTL already enabled on OTP table" -ForegroundColor Green
}

Write-Host ""

# Step 3: Create Lambda Layer for shared utilities
Write-Host "Step 3: Creating Lambda Layer for shared utilities..." -ForegroundColor Yellow

# Create layer directory structure
$layerDir = "lambda-layer-otp-security"
$pythonDir = "$layerDir/python"

if (Test-Path $layerDir) {
    Remove-Item -Recurse -Force $layerDir
}

New-Item -ItemType Directory -Path $pythonDir -Force | Out-Null

# Copy shared utilities to layer
Copy-Item "lambda/shared/otp_security.py" "$pythonDir/"
Copy-Item "lambda/shared/audit_logger.py" "$pythonDir/"
Copy-Item "lambda/shared/otp_metrics.py" "$pythonDir/"

Write-Host "✓ Layer files prepared" -ForegroundColor Green

# Create ZIP file
Write-Host "Creating layer ZIP..." -ForegroundColor Cyan
Compress-Archive -Path "$layerDir/*" -DestinationPath "otp-security-layer.zip" -Force

Write-Host "✓ Layer ZIP created" -ForegroundColor Green

# Publish layer
Write-Host "Publishing Lambda Layer..." -ForegroundColor Cyan
$layerArn = aws lambda publish-layer-version `
    --layer-name "aquachain-otp-security" `
    --description "OTP security utilities with hashing, rate limiting, and audit logging" `
    --zip-file "fileb://otp-security-layer.zip" `
    --compatible-runtimes python3.11 python3.10 python3.9 `
    --region $REGION `
    --query "LayerVersionArn" `
    --output text

if ($LASTEXITCODE -eq 0) {
    Write-Host "✓ Lambda Layer published: $layerArn" -ForegroundColor Green
} else {
    Write-Host "✗ Failed to publish layer" -ForegroundColor Red
    exit 1
}

# Cleanup
Remove-Item -Recurse -Force $layerDir
Remove-Item "otp-security-layer.zip"

Write-Host ""

# Step 4: Package and deploy Lambda functions
Write-Host "Step 4: Deploying Lambda functions..." -ForegroundColor Yellow

$functions = @(
    @{Name="register-secure"; File="lambda/auth_service/register_secure.py"; Handler="register_secure.lambda_handler"},
    @{Name="request-otp-secure"; File="lambda/auth_service/request_otp_secure.py"; Handler="request_otp_secure.lambda_handler"},
    @{Name="verify-otp-secure"; File="lambda/auth_service/verify_otp_secure.py"; Handler="verify_otp_secure.lambda_handler"}
)

foreach ($func in $functions) {
    $functionName = "AquaChain-Auth-$($func.Name)"
    Write-Host "Deploying $functionName..." -ForegroundColor Cyan
    
    # Create deployment package
    $deployDir = "deploy-$($func.Name)"
    if (Test-Path $deployDir) {
        Remove-Item -Recurse -Force $deployDir
    }
    New-Item -ItemType Directory -Path $deployDir -Force | Out-Null
    
    # Copy function code
    Copy-Item $func.File "$deployDir/"
    
    # Copy shared utilities (as fallback if layer fails)
    Copy-Item "lambda/shared/otp_security.py" "$deployDir/"
    Copy-Item "lambda/shared/audit_logger.py" "$deployDir/"
    Copy-Item "lambda/shared/otp_metrics.py" "$deployDir/"
    Copy-Item "lambda/shared/cors_utils.py" "$deployDir/"
    
    # Create ZIP
    $zipFile = "$($func.Name).zip"
    Compress-Archive -Path "$deployDir/*" -DestinationPath $zipFile -Force
    
    # Check if function exists
    $functionExists = aws lambda get-function --function-name $functionName --region $REGION 2>$null
    
    if ($LASTEXITCODE -eq 0) {
        # Update existing function
        Write-Host "Updating existing function..." -ForegroundColor Cyan
        aws lambda update-function-code `
            --function-name $functionName `
            --zip-file "fileb://$zipFile" `
            --region $REGION | Out-Null
        
        # Update configuration to add layer
        aws lambda update-function-configuration `
            --function-name $functionName `
            --layers $layerArn `
            --region $REGION | Out-Null
        
        Write-Host "✓ Function updated" -ForegroundColor Green
    } else {
        Write-Host "Function does not exist. Please create it first or use CDK deployment." -ForegroundColor Yellow
    }
    
    # Cleanup
    Remove-Item -Recurse -Force $deployDir
    Remove-Item $zipFile
}

Write-Host ""

# Step 5: Create CloudWatch Dashboard
Write-Host "Step 5: Creating CloudWatch Dashboard..." -ForegroundColor Yellow

$dashboardBody = @"
{
    "widgets": [
        {
            "type": "metric",
            "properties": {
                "metrics": [
                    ["AquaChain/Auth", "OTPGenerated", {"stat": "Sum"}],
                    [".", "OTPVerification", {"stat": "Sum"}],
                    [".", "OTPRateLimited", {"stat": "Sum"}],
                    [".", "AccountLocked", {"stat": "Sum"}]
                ],
                "period": 300,
                "stat": "Sum",
                "region": "$REGION",
                "title": "OTP System Metrics",
                "yAxis": {
                    "left": {
                        "min": 0
                    }
                }
            }
        },
        {
            "type": "metric",
            "properties": {
                "metrics": [
                    ["AquaChain/Auth", "OTPVerification", {"stat": "Sum", "label": "Total"}],
                    ["...", {"stat": "Sum", "label": "Success"}]
                ],
                "period": 300,
                "stat": "Sum",
                "region": "$REGION",
                "title": "OTP Verification Success Rate"
            }
        },
        {
            "type": "metric",
            "properties": {
                "metrics": [
                    ["AquaChain/Auth", "UserRegistration", {"stat": "Sum"}],
                    [".", "EmailDelivery", {"stat": "Sum"}]
                ],
                "period": 300,
                "stat": "Sum",
                "region": "$REGION",
                "title": "Registration & Email Delivery"
            }
        }
    ]
}
"@

aws cloudwatch put-dashboard `
    --dashboard-name "AquaChain-OTP-Security" `
    --dashboard-body $dashboardBody `
    --region $REGION

if ($LASTEXITCODE -eq 0) {
    Write-Host "✓ CloudWatch Dashboard created" -ForegroundColor Green
} else {
    Write-Host "✗ Failed to create dashboard" -ForegroundColor Yellow
}

Write-Host ""

# Step 6: Create CloudWatch Alarms
Write-Host "Step 6: Creating CloudWatch Alarms..." -ForegroundColor Yellow

# Alarm for high rate limiting
aws cloudwatch put-metric-alarm `
    --alarm-name "AquaChain-OTP-HighRateLimiting" `
    --alarm-description "Alert when OTP rate limiting is high" `
    --metric-name "OTPRateLimited" `
    --namespace "AquaChain/Auth" `
    --statistic Sum `
    --period 300 `
    --evaluation-periods 2 `
    --threshold 10 `
    --comparison-operator GreaterThanThreshold `
    --region $REGION

# Alarm for account lockouts
aws cloudwatch put-metric-alarm `
    --alarm-name "AquaChain-OTP-AccountLockouts" `
    --alarm-description "Alert when accounts are being locked out" `
    --metric-name "AccountLocked" `
    --namespace "AquaChain/Auth" `
    --statistic Sum `
    --period 300 `
    --evaluation-periods 1 `
    --threshold 5 `
    --comparison-operator GreaterThanThreshold `
    --region $REGION

Write-Host "✓ CloudWatch Alarms created" -ForegroundColor Green

Write-Host ""
Write-Host "========================================" -ForegroundColor Cyan
Write-Host "Deployment Summary" -ForegroundColor Cyan
Write-Host "========================================" -ForegroundColor Cyan
Write-Host ""
Write-Host "✓ AquaChain-AuthEvents table created" -ForegroundColor Green
Write-Host "✓ OTP table TTL configured" -ForegroundColor Green
Write-Host "✓ Lambda Layer published" -ForegroundColor Green
Write-Host "✓ Lambda functions deployed" -ForegroundColor Green
Write-Host "✓ CloudWatch Dashboard created" -ForegroundColor Green
Write-Host "✓ CloudWatch Alarms configured" -ForegroundColor Green
Write-Host ""
Write-Host "Security Improvements Implemented:" -ForegroundColor Yellow
Write-Host "  • OTP hashing with SHA-256 + salt" -ForegroundColor White
Write-Host "  • Constant-time OTP comparison" -ForegroundColor White
Write-Host "  • IP-based rate limiting (5 req/5min)" -ForegroundColor White
Write-Host "  • Global attempt lockout (5 failures = 15min lock)" -ForegroundColor White
Write-Host "  • Comprehensive audit logging" -ForegroundColor White
Write-Host "  • CloudWatch metrics for monitoring" -ForegroundColor White
Write-Host "  • Idempotency key support" -ForegroundColor White
Write-Host "  • DynamoDB TTL for automatic cleanup" -ForegroundColor White
Write-Host ""
Write-Host "Next Steps:" -ForegroundColor Yellow
Write-Host "  1. Update API Gateway endpoints to use new Lambda functions" -ForegroundColor White
Write-Host "  2. Test the enhanced OTP flow" -ForegroundColor White
Write-Host "  3. Monitor CloudWatch Dashboard for metrics" -ForegroundColor White
Write-Host "  4. Configure SNS notifications for alarms" -ForegroundColor White
Write-Host ""
Write-Host "Dashboard URL:" -ForegroundColor Yellow
Write-Host "https://console.aws.amazon.com/cloudwatch/home?region=$REGION#dashboards:name=AquaChain-OTP-Security" -ForegroundColor Cyan
Write-Host ""
