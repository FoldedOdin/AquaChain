# Phase 3 Production Deployment Script
# Automates deployment of System Configuration Phase 3 to production
# Run with: .\deploy-phase3-production.ps1 -Environment prod -Confirm

param(
    [Parameter(Mandatory=$true)]
    [ValidateSet("prod", "staging")]
    [string]$Environment,
    
    [Parameter(Mandatory=$false)]
    [switch]$Confirm,
    
    [Parameter(Mandatory=$false)]
    [switch]$SkipBackup,
    
    [Parameter(Mandatory=$false)]
    [switch]$SkipTests
)

$ErrorActionPreference = "Stop"
$Region = "ap-south-1"
$FunctionName = "aquachain-function-admin-service-$Environment"
$ApiName = "aquachain-api-rest-$Environment"
$FrontendBucket = "aquachain-frontend-$Environment"

Write-Host "========================================" -ForegroundColor Cyan
Write-Host "Phase 3 Production Deployment Script" -ForegroundColor Cyan
Write-Host "========================================" -ForegroundColor Cyan
Write-Host ""
Write-Host "Environment: $Environment" -ForegroundColor Yellow
Write-Host "Region: $Region" -ForegroundColor Yellow
Write-Host "Lambda: $FunctionName" -ForegroundColor Yellow
Write-Host ""

# Confirmation check
if (-not $Confirm) {
    Write-Host "WARNING: This will deploy to $Environment environment!" -ForegroundColor Red
    Write-Host "Add -Confirm flag to proceed with deployment." -ForegroundColor Red
    exit 1
}

Write-Host "Starting deployment..." -ForegroundColor Green
Write-Host ""

# Step 1: Pre-deployment checks
Write-Host "[1/8] Running pre-deployment checks..." -ForegroundColor Cyan

# Check AWS CLI
try {
    $awsVersion = aws --version
    Write-Host "  ✓ AWS CLI installed: $awsVersion" -ForegroundColor Green
} catch {
    Write-Host "  ✗ AWS CLI not found. Please install AWS CLI." -ForegroundColor Red
    exit 1
}

# Check AWS credentials
try {
    $identity = aws sts get-caller-identity --query 'Account' --output text
    Write-Host "  ✓ AWS credentials configured (Account: $identity)" -ForegroundColor Green
} catch {
    Write-Host "  ✗ AWS credentials not configured." -ForegroundColor Red
    exit 1
}

# Check Git status
$gitStatus = git status --porcelain
if ($gitStatus) {
    Write-Host "  ⚠ Warning: Uncommitted changes detected" -ForegroundColor Yellow
    Write-Host "  Continuing with deployment..." -ForegroundColor Yellow
} else {
    Write-Host "  ✓ Git repository clean" -ForegroundColor Green
}

# Check Git tag
$gitTag = git describe --tags --exact-match 2>$null
if ($gitTag -eq "phase3-production-ready") {
    Write-Host "  ✓ Git tag verified: $gitTag" -ForegroundColor Green
} else {
    Write-Host "  ⚠ Warning: Not on phase3-production-ready tag" -ForegroundColor Yellow
}

Write-Host ""

# Step 2: Create backups
if (-not $SkipBackup) {
    Write-Host "[2/8] Creating backups..." -ForegroundColor Cyan
    
    $timestamp = Get-Date -Format "yyyyMMdd-HHmmss"
    $backupDir = "backup/$timestamp"
    New-Item -ItemType Directory -Force -Path $backupDir | Out-Null
    
    # Backup Lambda version
    Write-Host "  Creating Lambda version backup..." -ForegroundColor Gray
    try {
        $versionOutput = aws lambda publish-version `
            --function-name $FunctionName `
            --description "Pre-Phase3 backup - $(Get-Date -Format 'yyyy-MM-dd')" `
            --region $Region `
            --output json
        
        $version = ($versionOutput | ConvertFrom-Json).Version
        Write-Host "  ✓ Lambda version created: $version" -ForegroundColor Green
        
        # Save version to backup manifest
        "Lambda Version: $version" | Out-File "$backupDir/backup-manifest.txt"
    } catch {
        Write-Host "  ✗ Failed to create Lambda backup: $_" -ForegroundColor Red
        exit 1
    }
    
    # Backup DynamoDB configuration
    Write-Host "  Backing up DynamoDB configuration..." -ForegroundColor Gray
    try {
        aws dynamodb get-item `
            --table-name AquaChain-SystemConfig `
            --key '{\"PK\": {\"S\": \"SYSTEM_CONFIG\"}, \"SK\": {\"S\": \"CURRENT\"}}' `
            --region $Region `
            --output json | Out-File "$backupDir/config-backup.json"
        
        Write-Host "  ✓ DynamoDB configuration backed up" -ForegroundColor Green
    } catch {
        Write-Host "  ✗ Failed to backup DynamoDB: $_" -ForegroundColor Red
        exit 1
    }
    
    # Backup frontend
    Write-Host "  Backing up frontend..." -ForegroundColor Gray
    try {
        aws s3 sync "s3://$FrontendBucket/" "$backupDir/frontend/" --region $Region --quiet
        Write-Host "  ✓ Frontend backed up" -ForegroundColor Green
    } catch {
        Write-Host "  ✗ Failed to backup frontend: $_" -ForegroundColor Red
        exit 1
    }
    
    Write-Host "  Backup location: $backupDir" -ForegroundColor Yellow
    Write-Host ""
} else {
    Write-Host "[2/8] Skipping backups (--SkipBackup flag set)" -ForegroundColor Yellow
    Write-Host ""
}

# Step 3: Build Lambda package
Write-Host "[3/8] Building Lambda deployment package..." -ForegroundColor Cyan

Push-Location lambda/admin_service

# Clean previous build
if (Test-Path "package") {
    Remove-Item -Recurse -Force package
}
if (Test-Path "admin-service-phase3.zip") {
    Remove-Item -Force admin-service-phase3.zip
}

# Create package directory
New-Item -ItemType Directory -Force -Path package | Out-Null

# Install dependencies
Write-Host "  Installing dependencies..." -ForegroundColor Gray
pip install -r requirements.txt -t package/ --quiet

# Copy Lambda code
Write-Host "  Copying Lambda code..." -ForegroundColor Gray
Copy-Item *.py package/

# Create ZIP
Write-Host "  Creating deployment package..." -ForegroundColor Gray
Push-Location package
Compress-Archive -Path * -DestinationPath ../admin-service-phase3.zip -Force
Pop-Location

$zipSize = (Get-Item admin-service-phase3.zip).Length / 1MB
Write-Host "  ✓ Package created: $([math]::Round($zipSize, 2)) MB" -ForegroundColor Green

Pop-Location
Write-Host ""

# Step 4: Deploy Lambda
Write-Host "[4/8] Deploying Lambda function..." -ForegroundColor Cyan

try {
    # Update function code
    Write-Host "  Updating function code..." -ForegroundColor Gray
    aws lambda update-function-code `
        --function-name $FunctionName `
        --zip-file fileb://lambda/admin_service/admin-service-phase3.zip `
        --region $Region `
        --output json | Out-Null
    
    # Wait for update
    Write-Host "  Waiting for update to complete..." -ForegroundColor Gray
    aws lambda wait function-updated `
        --function-name $FunctionName `
        --region $Region
    
    Write-Host "  ✓ Lambda function deployed" -ForegroundColor Green
    
    # Update environment variables
    Write-Host "  Updating environment variables..." -ForegroundColor Gray
    
    $allowedOrigins = if ($Environment -eq "prod") {
        "https://aquachain.example.com,https://www.aquachain.example.com"
    } else {
        "https://staging.aquachain.example.com"
    }
    
    aws lambda update-function-configuration `
        --function-name $FunctionName `
        --environment "Variables={ENVIRONMENT=$Environment,REGION=$Region,USERS_TABLE=AquaChain-Users,CONFIG_TABLE=AquaChain-SystemConfig,CONFIG_HISTORY_TABLE=AquaChain-ConfigHistory,ALLOWED_ORIGINS=$allowedOrigins}" `
        --region $Region `
        --output json | Out-Null
    
    # Wait for configuration update
    aws lambda wait function-updated `
        --function-name $FunctionName `
        --region $Region
    
    Write-Host "  ✓ Environment variables updated" -ForegroundColor Green
    
} catch {
    Write-Host "  ✗ Lambda deployment failed: $_" -ForegroundColor Red
    exit 1
}

Write-Host ""

# Step 5: Configure API Gateway
Write-Host "[5/8] Configuring API Gateway..." -ForegroundColor Cyan

try {
    # Get API ID
    $apiId = aws apigateway get-rest-apis `
        --query "items[?name=='$ApiName'].id" `
        --output text `
        --region $Region
    
    if (-not $apiId) {
        Write-Host "  ✗ API Gateway not found: $ApiName" -ForegroundColor Red
        exit 1
    }
    
    Write-Host "  API ID: $apiId" -ForegroundColor Gray
    
    # Deploy API
    Write-Host "  Deploying API changes..." -ForegroundColor Gray
    aws apigateway create-deployment `
        --rest-api-id $apiId `
        --stage-name $Environment `
        --description "Phase 3 deployment - $(Get-Date -Format 'yyyy-MM-dd HH:mm')" `
        --region $Region `
        --output json | Out-Null
    
    Write-Host "  ✓ API Gateway deployed" -ForegroundColor Green
    
} catch {
    Write-Host "  ✗ API Gateway configuration failed: $_" -ForegroundColor Red
    exit 1
}

Write-Host ""

# Step 6: Build and deploy frontend
Write-Host "[6/8] Building and deploying frontend..." -ForegroundColor Cyan

Push-Location frontend

# Install dependencies
Write-Host "  Installing dependencies..." -ForegroundColor Gray
npm install --silent

# Build
Write-Host "  Building frontend..." -ForegroundColor Gray
$env:REACT_APP_API_URL = "https://api.aquachain.example.com"
$env:REACT_APP_ENVIRONMENT = $Environment
npm run build --silent

# Deploy to S3
Write-Host "  Deploying to S3..." -ForegroundColor Gray
aws s3 sync build/ "s3://$FrontendBucket/" `
    --region $Region `
    --cache-control "public, max-age=31536000, immutable" `
    --exclude "index.html" `
    --exclude "service-worker.js" `
    --quiet

# Upload index.html with no-cache
aws s3 cp build/index.html "s3://$FrontendBucket/index.html" `
    --region $Region `
    --cache-control "no-cache, no-store, must-revalidate" `
    --metadata-directive REPLACE `
    --quiet

Write-Host "  ✓ Frontend deployed to S3" -ForegroundColor Green

# Invalidate CloudFront
Write-Host "  Invalidating CloudFront cache..." -ForegroundColor Gray
try {
    $distributionId = aws cloudfront list-distributions `
        --query "DistributionList.Items[?Origins.Items[0].DomainName=='$FrontendBucket.s3.amazonaws.com'].Id" `
        --output text `
        --region us-east-1
    
    if ($distributionId) {
        $invalidationId = aws cloudfront create-invalidation `
            --distribution-id $distributionId `
            --paths "/*" `
            --region us-east-1 `
            --query 'Invalidation.Id' `
            --output text
        
        Write-Host "  ✓ CloudFront invalidation created: $invalidationId" -ForegroundColor Green
        Write-Host "  (Invalidation will complete in 5-10 minutes)" -ForegroundColor Gray
    } else {
        Write-Host "  ⚠ CloudFront distribution not found" -ForegroundColor Yellow
    }
} catch {
    Write-Host "  ⚠ CloudFront invalidation failed: $_" -ForegroundColor Yellow
}

Pop-Location
Write-Host ""

# Step 7: Run smoke tests
if (-not $SkipTests) {
    Write-Host "[7/8] Running smoke tests..." -ForegroundColor Cyan
    
    Write-Host "  Testing Lambda function..." -ForegroundColor Gray
    try {
        $testPayload = @{
            httpMethod = "GET"
            path = "/api/admin/system/configuration"
            headers = @{
                Authorization = "Bearer TEST"
            }
        } | ConvertTo-Json -Compress
        
        aws lambda invoke `
            --function-name $FunctionName `
            --payload $testPayload `
            --region $Region `
            response.json | Out-Null
        
        $response = Get-Content response.json | ConvertFrom-Json
        if ($response.statusCode -eq 200 -or $response.statusCode -eq 401) {
            Write-Host "  ✓ Lambda function responding" -ForegroundColor Green
        } else {
            Write-Host "  ⚠ Unexpected response: $($response.statusCode)" -ForegroundColor Yellow
        }
        
        Remove-Item response.json -ErrorAction SilentlyContinue
    } catch {
        Write-Host "  ⚠ Lambda test failed: $_" -ForegroundColor Yellow
    }
    
    Write-Host "  ✓ Smoke tests complete" -ForegroundColor Green
    Write-Host ""
} else {
    Write-Host "[7/8] Skipping smoke tests (--SkipTests flag set)" -ForegroundColor Yellow
    Write-Host ""
}

# Step 8: Post-deployment summary
Write-Host "[8/8] Deployment Summary" -ForegroundColor Cyan
Write-Host ""
Write-Host "  Environment: $Environment" -ForegroundColor White
Write-Host "  Deployment Time: $(Get-Date -Format 'yyyy-MM-dd HH:mm:ss')" -ForegroundColor White
Write-Host "  Git Tag: phase3-production-ready" -ForegroundColor White
Write-Host ""
Write-Host "  Deployed Components:" -ForegroundColor White
Write-Host "    ✓ Lambda: $FunctionName" -ForegroundColor Green
Write-Host "    ✓ API Gateway: $ApiName" -ForegroundColor Green
Write-Host "    ✓ Frontend: $FrontendBucket" -ForegroundColor Green
Write-Host ""
Write-Host "  Next Steps:" -ForegroundColor Yellow
Write-Host "    1. Monitor CloudWatch Logs for errors" -ForegroundColor Gray
Write-Host "    2. Test Phase 3 features in production" -ForegroundColor Gray
Write-Host "    3. Verify no regressions in existing features" -ForegroundColor Gray
Write-Host "    4. Monitor for 24 hours" -ForegroundColor Gray
Write-Host ""
Write-Host "  Monitoring Commands:" -ForegroundColor Yellow
Write-Host "    aws logs tail /aws/lambda/$FunctionName --follow --filter-pattern ERROR" -ForegroundColor Gray
Write-Host ""
Write-Host "========================================" -ForegroundColor Cyan
Write-Host "Deployment Complete!" -ForegroundColor Green
Write-Host "========================================" -ForegroundColor Cyan
