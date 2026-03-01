# Deploy Security Fixes to AquaChain Infrastructure
# This script deploys the critical security fixes to the specified environment

param(
    [Parameter(Mandatory=$true)]
    [ValidateSet('dev', 'staging', 'prod')]
    [string]$Environment,
    
    [Parameter(Mandatory=$false)]
    [switch]$SkipVerification,
    
    [Parameter(Mandatory=$false)]
    [switch]$DryRun
)

$ErrorActionPreference = "Stop"

Write-Host "🔒 AquaChain Security Fixes Deployment" -ForegroundColor Cyan
Write-Host "Environment: $Environment" -ForegroundColor Yellow
Write-Host "Dry Run: $DryRun" -ForegroundColor Yellow
Write-Host "=" * 60

# Check prerequisites
Write-Host "`n📋 Checking Prerequisites..." -ForegroundColor Cyan

# Check AWS CLI
try {
    $awsVersion = aws --version 2>&1
    Write-Host "✓ AWS CLI: $awsVersion" -ForegroundColor Green
} catch {
    Write-Host "✗ AWS CLI not found. Please install AWS CLI." -ForegroundColor Red
    exit 1
}

# Check CDK
try {
    $cdkVersion = cdk --version 2>&1
    Write-Host "✓ CDK: $cdkVersion" -ForegroundColor Green
} catch {
    Write-Host "✗ CDK not found. Please install AWS CDK." -ForegroundColor Red
    exit 1
}

# Check Python
try {
    $pythonVersion = python --version 2>&1
    Write-Host "✓ Python: $pythonVersion" -ForegroundColor Green
} catch {
    Write-Host "✗ Python not found. Please install Python 3.11+." -ForegroundColor Red
    exit 1
}

# Navigate to CDK directory
$cdkPath = "infrastructure/cdk"
if (-not (Test-Path $cdkPath)) {
    Write-Host "✗ CDK directory not found: $cdkPath" -ForegroundColor Red
    exit 1
}

Set-Location $cdkPath
Write-Host "✓ Changed directory to: $cdkPath" -ForegroundColor Green

# Install dependencies
Write-Host "`n📦 Installing Dependencies..." -ForegroundColor Cyan
pip install -r requirements.txt --quiet
if ($LASTEXITCODE -ne 0) {
    Write-Host "✗ Failed to install dependencies" -ForegroundColor Red
    exit 1
}
Write-Host "✓ Dependencies installed" -ForegroundColor Green

# Synthesize CloudFormation templates
Write-Host "`n🔨 Synthesizing CloudFormation Templates..." -ForegroundColor Cyan
cdk synth --all --quiet
if ($LASTEXITCODE -ne 0) {
    Write-Host "✗ CDK synthesis failed" -ForegroundColor Red
    exit 1
}
Write-Host "✓ Templates synthesized successfully" -ForegroundColor Green

# Show diff
Write-Host "`n📊 Reviewing Changes..." -ForegroundColor Cyan
$stackName = "AquaChain-Data-$Environment"
Write-Host "Stack: $stackName" -ForegroundColor Yellow

cdk diff $stackName

if ($DryRun) {
    Write-Host "`n⚠️  DRY RUN MODE - No changes will be deployed" -ForegroundColor Yellow
    Write-Host "Review the diff above to see what would change." -ForegroundColor Yellow
    Set-Location ../..
    exit 0
}

# Confirm deployment
if ($Environment -eq 'prod') {
    Write-Host "`n⚠️  WARNING: You are about to deploy to PRODUCTION" -ForegroundColor Red
    $confirmation = Read-Host "Type 'DEPLOY' to confirm"
    if ($confirmation -ne 'DEPLOY') {
        Write-Host "Deployment cancelled" -ForegroundColor Yellow
        Set-Location ../..
        exit 0
    }
}

# Deploy
Write-Host "`n🚀 Deploying Security Fixes..." -ForegroundColor Cyan
Write-Host "This may take 10-15 minutes..." -ForegroundColor Yellow

cdk deploy $stackName --require-approval never

if ($LASTEXITCODE -ne 0) {
    Write-Host "`n✗ Deployment failed" -ForegroundColor Red
    Write-Host "Check CloudFormation console for details" -ForegroundColor Yellow
    Set-Location ../..
    exit 1
}

Write-Host "`n✅ Deployment completed successfully!" -ForegroundColor Green

# Verification
if (-not $SkipVerification) {
    Write-Host "`n🔍 Verifying Security Fixes..." -ForegroundColor Cyan
    
    # Get account ID
    $accountId = aws sts get-caller-identity --query Account --output text
    
    # Verify PITR on DynamoDB tables
    Write-Host "`nChecking DynamoDB Point-in-Time Recovery..." -ForegroundColor Yellow
    
    $tables = @(
        "aquachain-table-readings-$Environment",
        "aquachain-table-ledger-$Environment",
        "aquachain-table-sequence-$Environment",
        "aquachain-table-users-$Environment",
        "aquachain-table-service-requests-$Environment",
        "aquachain-table-devices-$Environment",
        "aquachain-table-audit-logs-$Environment",
        "aquachain-table-system-config-$Environment"
    )
    
    $pitrFailed = $false
    foreach ($table in $tables) {
        try {
            $pitrStatus = aws dynamodb describe-continuous-backups `
                --table-name $table `
                --query 'ContinuousBackupsDescription.PointInTimeRecoveryDescription.PointInTimeRecoveryStatus' `
                --output text 2>&1
            
            if ($pitrStatus -eq "ENABLED") {
                Write-Host "  ✓ $table : PITR Enabled" -ForegroundColor Green
            } else {
                Write-Host "  ✗ $table : PITR NOT Enabled ($pitrStatus)" -ForegroundColor Red
                $pitrFailed = $true
            }
        } catch {
            Write-Host "  ⚠ $table : Could not verify (table may not exist yet)" -ForegroundColor Yellow
        }
    }
    
    # Verify S3 Public Access Block
    Write-Host "`nChecking S3 Public Access Block..." -ForegroundColor Yellow
    
    $buckets = @(
        "aquachain-bucket-access-logs-$accountId-$Environment",
        "aquachain-bucket-data-lake-$accountId-$Environment",
        "aquachain-bucket-audit-trail-$accountId-$Environment",
        "aquachain-bucket-ml-models-$accountId-$Environment"
    )
    
    $s3Failed = $false
    foreach ($bucket in $buckets) {
        try {
            $blockStatus = aws s3api get-public-access-block `
                --bucket $bucket `
                --query 'PublicAccessBlockConfiguration.BlockPublicAcls' `
                --output text 2>&1
            
            if ($blockStatus -eq "True") {
                Write-Host "  ✓ $bucket : Public Access Blocked" -ForegroundColor Green
            } else {
                Write-Host "  ✗ $bucket : Public Access NOT Blocked" -ForegroundColor Red
                $s3Failed = $true
            }
        } catch {
            Write-Host "  ⚠ $bucket : Could not verify (bucket may not exist yet)" -ForegroundColor Yellow
        }
    }
    
    # Verify S3 Access Logging
    Write-Host "`nChecking S3 Access Logging..." -ForegroundColor Yellow
    
    $dataBuckets = @(
        "aquachain-bucket-data-lake-$accountId-$Environment",
        "aquachain-bucket-audit-trail-$accountId-$Environment",
        "aquachain-bucket-ml-models-$accountId-$Environment"
    )
    
    $loggingFailed = $false
    foreach ($bucket in $dataBuckets) {
        try {
            $loggingConfig = aws s3api get-bucket-logging `
                --bucket $bucket `
                --query 'LoggingEnabled.TargetBucket' `
                --output text 2>&1
            
            if ($loggingConfig -and $loggingConfig -ne "None") {
                Write-Host "  ✓ $bucket : Logging Enabled → $loggingConfig" -ForegroundColor Green
            } else {
                Write-Host "  ✗ $bucket : Logging NOT Enabled" -ForegroundColor Red
                $loggingFailed = $true
            }
        } catch {
            Write-Host "  ⚠ $bucket : Could not verify logging" -ForegroundColor Yellow
        }
    }
    
    # Summary
    Write-Host "`n" + ("=" * 60) -ForegroundColor Cyan
    Write-Host "Verification Summary:" -ForegroundColor Cyan
    
    if (-not $pitrFailed) {
        Write-Host "  ✓ DynamoDB PITR: All tables enabled" -ForegroundColor Green
    } else {
        Write-Host "  ✗ DynamoDB PITR: Some tables not enabled" -ForegroundColor Red
    }
    
    if (-not $s3Failed) {
        Write-Host "  ✓ S3 Public Access Block: All buckets protected" -ForegroundColor Green
    } else {
        Write-Host "  ✗ S3 Public Access Block: Some buckets not protected" -ForegroundColor Red
    }
    
    if (-not $loggingFailed) {
        Write-Host "  ✓ S3 Access Logging: All buckets logging" -ForegroundColor Green
    } else {
        Write-Host "  ✗ S3 Access Logging: Some buckets not logging" -ForegroundColor Red
    }
    
    if ($pitrFailed -or $s3Failed -or $loggingFailed) {
        Write-Host "`n⚠️  Some verifications failed. Please review manually." -ForegroundColor Yellow
    } else {
        Write-Host "`n✅ All security fixes verified successfully!" -ForegroundColor Green
    }
}

# Return to original directory
Set-Location ../..

Write-Host "`n📚 Next Steps:" -ForegroundColor Cyan
Write-Host "  1. Review the verification results above" -ForegroundColor White
Write-Host "  2. Test PITR recovery: aws dynamodb restore-table-to-point-in-time" -ForegroundColor White
Write-Host "  3. Check S3 access logs in access-logs bucket" -ForegroundColor White
Write-Host "  4. Review IAM permissions in compute_stack.py" -ForegroundColor White
Write-Host "  5. See DOCS/deployment/SECURITY_FIXES_APPLIED.md for details" -ForegroundColor White

Write-Host "`n✅ Deployment Complete!" -ForegroundColor Green
