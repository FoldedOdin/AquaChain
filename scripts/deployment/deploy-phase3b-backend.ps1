# Phase 3b Backend Deployment Script
# Deploys ML Configuration Controls to AWS Lambda

param(
    [Parameter(Mandatory=$false)]
    [string]$Environment = "dev",
    
    [Parameter(Mandatory=$false)]
    [switch]$SkipTests = $false,
    
    [Parameter(Mandatory=$false)]
    [switch]$CreateBackup = $true
)

$ErrorActionPreference = "Stop"

Write-Host "========================================" -ForegroundColor Cyan
Write-Host "Phase 3b Backend Deployment" -ForegroundColor Cyan
Write-Host "Environment: $Environment" -ForegroundColor Cyan
Write-Host "========================================" -ForegroundColor Cyan
Write-Host ""

# Configuration
$LambdaFunctionName = "AquaChain-AdminService-$Environment"
$LambdaDir = "lambda/admin_service"
$PackageDir = "lambda/admin_service/package"
$ZipFile = "admin_service_phase3b.zip"

# Step 1: Pre-deployment checks
Write-Host "[1/8] Running pre-deployment checks..." -ForegroundColor Yellow

# Check if Lambda directory exists
if (-not (Test-Path $LambdaDir)) {
    Write-Host "ERROR: Lambda directory not found: $LambdaDir" -ForegroundColor Red
    exit 1
}

# Check if required files exist
$RequiredFiles = @(
    "$LambdaDir/handler.py",
    "$LambdaDir/config_validation.py",
    "$LambdaDir/requirements.txt"
)

foreach ($file in $RequiredFiles) {
    if (-not (Test-Path $file)) {
        Write-Host "ERROR: Required file not found: $file" -ForegroundColor Red
        exit 1
    }
}

Write-Host "✓ All required files present" -ForegroundColor Green

# Step 2: Run tests
if (-not $SkipTests) {
    Write-Host "[2/8] Running backend tests..." -ForegroundColor Yellow
    
    Push-Location $LambdaDir
    
    # Run ML validation tests
    Write-Host "Running ML validation tests..." -ForegroundColor Gray
    $testResult = pytest tests/test_ml_validation.py -v
    
    if ($LASTEXITCODE -ne 0) {
        Write-Host "ERROR: Tests failed. Aborting deployment." -ForegroundColor Red
        Pop-Location
        exit 1
    }
    
    Write-Host "✓ All tests passed" -ForegroundColor Green
    Pop-Location
} else {
    Write-Host "[2/8] Skipping tests (--SkipTests flag set)" -ForegroundColor Yellow
}

# Step 3: Create backup
if ($CreateBackup) {
    Write-Host "[3/8] Creating backup..." -ForegroundColor Yellow
    
    # Create Lambda version
    Write-Host "Creating Lambda version..." -ForegroundColor Gray
    $timestamp = Get-Date -Format "yyyyMMdd-HHmmss"
    
    try {
        aws lambda publish-version `
            --function-name $LambdaFunctionName `
            --description "Pre-Phase3b deployment backup - $timestamp"
        
        Write-Host "✓ Lambda version created" -ForegroundColor Green
    } catch {
        Write-Host "WARNING: Failed to create Lambda version: $_" -ForegroundColor Yellow
        Write-Host "Continuing with deployment..." -ForegroundColor Yellow
    }
    
    # Backup DynamoDB configuration
    Write-Host "Backing up DynamoDB configuration..." -ForegroundColor Gray
    $backupFile = "backup-config-phase3b-$timestamp.json"
    
    try {
        aws dynamodb get-item `
            --table-name "AquaChain-SystemConfig" `
            --key '{\"PK\": {\"S\": \"SYSTEM_CONFIG\"}, \"SK\": {\"S\": \"CURRENT\"}}' `
            > $backupFile
        
        Write-Host "✓ Configuration backed up to: $backupFile" -ForegroundColor Green
    } catch {
        Write-Host "WARNING: Failed to backup configuration: $_" -ForegroundColor Yellow
        Write-Host "Continuing with deployment..." -ForegroundColor Yellow
    }
    
    # Create Git tag
    Write-Host "Creating Git tag..." -ForegroundColor Gray
    try {
        git tag -a "phase3b-pre-deployment-$timestamp" -m "Pre-Phase 3b deployment state"
        Write-Host "✓ Git tag created: phase3b-pre-deployment-$timestamp" -ForegroundColor Green
    } catch {
        Write-Host "WARNING: Failed to create Git tag: $_" -ForegroundColor Yellow
    }
} else {
    Write-Host "[3/8] Skipping backup (--CreateBackup=false)" -ForegroundColor Yellow
}

# Step 4: Clean and prepare package directory
Write-Host "[4/8] Preparing deployment package..." -ForegroundColor Yellow

if (Test-Path $PackageDir) {
    Write-Host "Cleaning existing package directory..." -ForegroundColor Gray
    Remove-Item -Recurse -Force $PackageDir
}

New-Item -ItemType Directory -Path $PackageDir | Out-Null
Write-Host "✓ Package directory created" -ForegroundColor Green

# Step 5: Install dependencies
Write-Host "[5/8] Installing dependencies..." -ForegroundColor Yellow

Push-Location $LambdaDir

Write-Host "Installing Python packages..." -ForegroundColor Gray
pip install -r requirements.txt -t package/ --quiet

if ($LASTEXITCODE -ne 0) {
    Write-Host "ERROR: Failed to install dependencies" -ForegroundColor Red
    Pop-Location
    exit 1
}

Write-Host "✓ Dependencies installed" -ForegroundColor Green

# Step 6: Copy source files
Write-Host "[6/8] Copying source files..." -ForegroundColor Yellow

$SourceFiles = @(
    "handler.py",
    "config_validation.py",
    "audit_logger.py",
    "version_manager.py"
)

foreach ($file in $SourceFiles) {
    if (Test-Path $file) {
        Copy-Item $file -Destination package/ -Force
        Write-Host "  Copied: $file" -ForegroundColor Gray
    }
}

Write-Host "✓ Source files copied" -ForegroundColor Green

# Step 7: Create deployment package
Write-Host "[7/8] Creating deployment package..." -ForegroundColor Yellow

Push-Location package

# Create zip file
if (Test-Path "../$ZipFile") {
    Remove-Item "../$ZipFile" -Force
}

Write-Host "Compressing files..." -ForegroundColor Gray
Compress-Archive -Path * -DestinationPath "../$ZipFile" -CompressionLevel Optimal

Pop-Location

$zipSize = (Get-Item $ZipFile).Length / 1MB
Write-Host "✓ Deployment package created: $ZipFile ($([math]::Round($zipSize, 2)) MB)" -ForegroundColor Green

# Step 8: Deploy to Lambda
Write-Host "[8/8] Deploying to Lambda..." -ForegroundColor Yellow

Write-Host "Updating Lambda function: $LambdaFunctionName" -ForegroundColor Gray

try {
    aws lambda update-function-code `
        --function-name $LambdaFunctionName `
        --zip-file "fileb://$ZipFile"
    
    if ($LASTEXITCODE -ne 0) {
        throw "Lambda update failed"
    }
    
    Write-Host "Waiting for function update to complete..." -ForegroundColor Gray
    aws lambda wait function-updated --function-name $LambdaFunctionName
    
    Write-Host "✓ Lambda function updated successfully" -ForegroundColor Green
} catch {
    Write-Host "ERROR: Failed to deploy Lambda function: $_" -ForegroundColor Red
    Pop-Location
    exit 1
}

Pop-Location

# Step 9: Verify deployment
Write-Host ""
Write-Host "========================================" -ForegroundColor Cyan
Write-Host "Verifying Deployment" -ForegroundColor Cyan
Write-Host "========================================" -ForegroundColor Cyan

Write-Host "Checking Lambda function status..." -ForegroundColor Yellow

try {
    $functionInfo = aws lambda get-function --function-name $LambdaFunctionName | ConvertFrom-Json
    
    $state = $functionInfo.Configuration.State
    $lastUpdateStatus = $functionInfo.Configuration.LastUpdateStatus
    
    Write-Host "  State: $state" -ForegroundColor Gray
    Write-Host "  Last Update Status: $lastUpdateStatus" -ForegroundColor Gray
    
    if ($state -eq "Active" -and $lastUpdateStatus -eq "Successful") {
        Write-Host "✓ Lambda function is active and healthy" -ForegroundColor Green
    } else {
        Write-Host "WARNING: Lambda function state is not optimal" -ForegroundColor Yellow
        Write-Host "  Please check CloudWatch logs for details" -ForegroundColor Yellow
    }
} catch {
    Write-Host "WARNING: Failed to verify Lambda status: $_" -ForegroundColor Yellow
}

# Step 10: Cleanup
Write-Host ""
Write-Host "Cleaning up temporary files..." -ForegroundColor Yellow
Push-Location $LambdaDir
if (Test-Path "package") {
    Remove-Item -Recurse -Force "package"
}
if (Test-Path $ZipFile) {
    Remove-Item -Force $ZipFile
}
Pop-Location
Write-Host "✓ Cleanup complete" -ForegroundColor Green

# Deployment summary
Write-Host ""
Write-Host "========================================" -ForegroundColor Cyan
Write-Host "Deployment Summary" -ForegroundColor Cyan
Write-Host "========================================" -ForegroundColor Cyan
Write-Host "Environment: $Environment" -ForegroundColor White
Write-Host "Lambda Function: $LambdaFunctionName" -ForegroundColor White
Write-Host "Deployment Time: $(Get-Date -Format 'yyyy-MM-dd HH:mm:ss')" -ForegroundColor White
Write-Host ""
Write-Host "✓ Phase 3b backend deployment completed successfully!" -ForegroundColor Green
Write-Host ""

# Next steps
Write-Host "========================================" -ForegroundColor Cyan
Write-Host "Next Steps" -ForegroundColor Cyan
Write-Host "========================================" -ForegroundColor Cyan
Write-Host "1. Test ML settings API endpoints" -ForegroundColor White
Write-Host "2. Verify default ML settings are applied" -ForegroundColor White
Write-Host "3. Check CloudWatch logs for errors" -ForegroundColor White
Write-Host "4. Monitor for 15 minutes" -ForegroundColor White
Write-Host "5. Complete verification checklist" -ForegroundColor White
Write-Host ""
Write-Host "See DOCS/PHASE3B_DEPLOYMENT_GUIDE.md for detailed instructions" -ForegroundColor Cyan
Write-Host ""

# Monitoring reminder
Write-Host "========================================" -ForegroundColor Yellow
Write-Host "IMPORTANT: Monitor CloudWatch Logs" -ForegroundColor Yellow
Write-Host "========================================" -ForegroundColor Yellow
Write-Host "Run this command to tail logs:" -ForegroundColor White
Write-Host "  aws logs tail /aws/lambda/$LambdaFunctionName --follow" -ForegroundColor Cyan
Write-Host ""
