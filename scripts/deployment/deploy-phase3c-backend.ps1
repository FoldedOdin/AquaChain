# Phase 3c Backend Deployment Script
# Deploys System Health Monitoring backend components

param(
    [string]$Environment = "dev",
    [string]$Region = "ap-south-1",
    [switch]$SkipTests,
    [switch]$DryRun
)

$ErrorActionPreference = "Stop"

Write-Host "========================================" -ForegroundColor Cyan
Write-Host "Phase 3c Backend Deployment" -ForegroundColor Cyan
Write-Host "Environment: $Environment" -ForegroundColor Cyan
Write-Host "Region: $Region" -ForegroundColor Cyan
Write-Host "========================================" -ForegroundColor Cyan
Write-Host ""

# Configuration
$LambdaFunctionName = "aquachain-function-admin-service-$Environment"
$LambdaPath = "lambda/admin_service"
$DeploymentPackage = "admin_service.zip"

# Step 1: Pre-deployment checks
Write-Host "[1/7] Running pre-deployment checks..." -ForegroundColor Yellow

# Check if Lambda directory exists
if (-not (Test-Path $LambdaPath)) {
    Write-Host "ERROR: Lambda directory not found: $LambdaPath" -ForegroundColor Red
    exit 1
}

# Check if health_monitor.py exists
if (-not (Test-Path "$LambdaPath/health_monitor.py")) {
    Write-Host "ERROR: health_monitor.py not found in $LambdaPath" -ForegroundColor Red
    exit 1
}

Write-Host "✓ Pre-deployment checks passed" -ForegroundColor Green
Write-Host ""

# Step 2: Run tests
if (-not $SkipTests) {
    Write-Host "[2/7] Running backend tests..." -ForegroundColor Yellow
    
    Push-Location $LambdaPath
    
    # Run unit tests
    Write-Host "Running unit tests..." -ForegroundColor Gray
    python -m pytest tests/test_health_monitor.py -v
    
    if ($LASTEXITCODE -ne 0) {
        Write-Host "ERROR: Unit tests failed" -ForegroundColor Red
        Pop-Location
        exit 1
    }
    
    # Run integration tests
    Write-Host "Running integration tests..." -ForegroundColor Gray
    Push-Location ../..
    python tests/integration/test_phase3c_health.py
    
    if ($LASTEXITCODE -ne 0) {
        Write-Host "ERROR: Integration tests failed" -ForegroundColor Red
        Pop-Location
        Pop-Location
        exit 1
    }
    
    Pop-Location
    Pop-Location
    
    Write-Host "✓ All tests passed" -ForegroundColor Green
} else {
    Write-Host "[2/7] Skipping tests (--SkipTests flag)" -ForegroundColor Yellow
}
Write-Host ""

# Step 3: Create backup
Write-Host "[3/7] Creating backup..." -ForegroundColor Yellow

# Create Git tag
$timestamp = Get-Date -Format "yyyyMMdd-HHmmss"
$tagName = "phase3c-backup-$timestamp"

git tag -a $tagName -m "Phase 3c pre-deployment backup - $timestamp"

if ($LASTEXITCODE -eq 0) {
    Write-Host "✓ Git tag created: $tagName" -ForegroundColor Green
} else {
    Write-Host "WARNING: Failed to create Git tag" -ForegroundColor Yellow
}

# Publish Lambda version
Write-Host "Publishing Lambda version..." -ForegroundColor Gray
$versionOutput = aws lambda publish-version `
    --function-name $LambdaFunctionName `
    --description "Pre-Phase 3c backup - $timestamp" `
    --region $Region `
    --query 'Version' `
    --output text

if ($LASTEXITCODE -eq 0) {
    Write-Host "✓ Lambda version published: $versionOutput" -ForegroundColor Green
    Write-Host "  Rollback command: aws lambda update-alias --function-name $LambdaFunctionName --name PROD --function-version $versionOutput" -ForegroundColor Gray
} else {
    Write-Host "WARNING: Failed to publish Lambda version" -ForegroundColor Yellow
}
Write-Host ""

# Step 4: Package Lambda function
Write-Host "[4/7] Packaging Lambda function..." -ForegroundColor Yellow

Push-Location $LambdaPath

# Remove old package if exists
if (Test-Path $DeploymentPackage) {
    Remove-Item $DeploymentPackage -Force
}

# Create deployment package
Write-Host "Creating deployment package..." -ForegroundColor Gray
$excludePatterns = @(
    "*.pyc",
    "__pycache__/*",
    "tests/*",
    "*.md",
    ".pytest_cache/*",
    "*.log",
    ".coverage",
    "htmlcov/*"
)

$excludeArgs = $excludePatterns | ForEach-Object { "-x", $_ }

# Use 7-Zip if available, otherwise use PowerShell Compress-Archive
if (Get-Command 7z -ErrorAction SilentlyContinue) {
    7z a -tzip $DeploymentPackage * -xr!*.pyc -xr!__pycache__ -xr!tests -xr!*.md -xr!.pytest_cache
} else {
    # PowerShell Compress-Archive (slower but works)
    $files = Get-ChildItem -Recurse -File | Where-Object {
        $_.FullName -notmatch "(__pycache__|tests|\.pytest_cache|\.pyc|\.md)" 
    }
    Compress-Archive -Path $files -DestinationPath $DeploymentPackage -Force
}

if (-not (Test-Path $DeploymentPackage)) {
    Write-Host "ERROR: Failed to create deployment package" -ForegroundColor Red
    Pop-Location
    exit 1
}

# Verify health_monitor.py is included
Write-Host "Verifying package contents..." -ForegroundColor Gray
$zipContents = 7z l $DeploymentPackage 2>$null
if ($zipContents -match "health_monitor.py") {
    Write-Host "✓ health_monitor.py included in package" -ForegroundColor Green
} else {
    Write-Host "ERROR: health_monitor.py not found in package" -ForegroundColor Red
    Pop-Location
    exit 1
}

$packageSize = (Get-Item $DeploymentPackage).Length / 1MB
Write-Host "✓ Deployment package created: $DeploymentPackage ($([math]::Round($packageSize, 2)) MB)" -ForegroundColor Green

Pop-Location
Write-Host ""

# Step 5: Deploy to Lambda
if ($DryRun) {
    Write-Host "[5/7] DRY RUN: Skipping Lambda deployment" -ForegroundColor Yellow
} else {
    Write-Host "[5/7] Deploying to Lambda..." -ForegroundColor Yellow
    
    $packagePath = Join-Path $LambdaPath $DeploymentPackage
    
    aws lambda update-function-code `
        --function-name $LambdaFunctionName `
        --zip-file "fileb://$packagePath" `
        --region $Region
    
    if ($LASTEXITCODE -ne 0) {
        Write-Host "ERROR: Lambda deployment failed" -ForegroundColor Red
        exit 1
    }
    
    Write-Host "✓ Lambda function deployed successfully" -ForegroundColor Green
    
    # Wait for Lambda to be ready
    Write-Host "Waiting for Lambda to be ready..." -ForegroundColor Gray
    Start-Sleep -Seconds 5
}
Write-Host ""

# Step 6: Verify deployment
Write-Host "[6/7] Verifying deployment..." -ForegroundColor Yellow

if (-not $DryRun) {
    # Check Lambda configuration
    $lambdaConfig = aws lambda get-function-configuration `
        --function-name $LambdaFunctionName `
        --region $Region `
        --output json | ConvertFrom-Json
    
    Write-Host "Lambda Configuration:" -ForegroundColor Gray
    Write-Host "  Runtime: $($lambdaConfig.Runtime)" -ForegroundColor Gray
    Write-Host "  Timeout: $($lambdaConfig.Timeout) seconds" -ForegroundColor Gray
    Write-Host "  Memory: $($lambdaConfig.MemorySize) MB" -ForegroundColor Gray
    Write-Host "  Last Modified: $($lambdaConfig.LastModified)" -ForegroundColor Gray
    
    # Test Lambda invocation
    Write-Host "Testing Lambda invocation..." -ForegroundColor Gray
    
    $testPayload = @{
        httpMethod = "GET"
        path = "/api/admin/system/health"
        queryStringParameters = $null
        headers = @{
            Authorization = "Bearer test-token"
        }
    } | ConvertTo-Json -Compress
    
    $testPayload | Out-File -FilePath "test-payload.json" -Encoding utf8
    
    aws lambda invoke `
        --function-name $LambdaFunctionName `
        --payload file://test-payload.json `
        --region $Region `
        response.json
    
    if ($LASTEXITCODE -eq 0) {
        $response = Get-Content response.json | ConvertFrom-Json
        if ($response.statusCode -eq 200 -or $response.statusCode -eq 403) {
            Write-Host "✓ Lambda invocation successful (status: $($response.statusCode))" -ForegroundColor Green
        } else {
            Write-Host "WARNING: Unexpected status code: $($response.statusCode)" -ForegroundColor Yellow
        }
    } else {
        Write-Host "WARNING: Lambda invocation test failed" -ForegroundColor Yellow
    }
    
    # Cleanup test files
    Remove-Item test-payload.json -ErrorAction SilentlyContinue
    Remove-Item response.json -ErrorAction SilentlyContinue
}
Write-Host ""

# Step 7: Next steps
Write-Host "[7/7] Deployment complete!" -ForegroundColor Green
Write-Host ""
Write-Host "========================================" -ForegroundColor Cyan
Write-Host "Next Steps:" -ForegroundColor Cyan
Write-Host "========================================" -ForegroundColor Cyan
Write-Host "1. Configure API Gateway endpoint:" -ForegroundColor White
Write-Host "   See: DOCS/PHASE3C_API_GATEWAY_SETUP.md" -ForegroundColor Gray
Write-Host ""
Write-Host "2. Test the health endpoint:" -ForegroundColor White
Write-Host "   curl -X GET 'https://YOUR_API_URL/api/admin/system-health' \" -ForegroundColor Gray
Write-Host "     -H 'Authorization: Bearer YOUR_ADMIN_TOKEN'" -ForegroundColor Gray
Write-Host ""
Write-Host "3. Deploy frontend:" -ForegroundColor White
Write-Host "   cd frontend && npm run build" -ForegroundColor Gray
Write-Host ""
Write-Host "4. Monitor CloudWatch logs:" -ForegroundColor White
Write-Host "   aws logs tail /aws/lambda/$LambdaFunctionName --follow" -ForegroundColor Gray
Write-Host ""
Write-Host "5. Complete verification checklist:" -ForegroundColor White
Write-Host "   See: DOCS/PHASE3C_VERIFICATION_CHECKLIST.md" -ForegroundColor Gray
Write-Host ""

if ($DryRun) {
    Write-Host "NOTE: This was a DRY RUN. No actual deployment occurred." -ForegroundColor Yellow
    Write-Host "Run without --DryRun flag to perform actual deployment." -ForegroundColor Yellow
}

Write-Host "========================================" -ForegroundColor Cyan
Write-Host "Deployment Summary" -ForegroundColor Cyan
Write-Host "========================================" -ForegroundColor Cyan
Write-Host "Environment: $Environment" -ForegroundColor White
Write-Host "Lambda Function: $LambdaFunctionName" -ForegroundColor White
Write-Host "Region: $Region" -ForegroundColor White
Write-Host "Backup Tag: $tagName" -ForegroundColor White
Write-Host "Status: SUCCESS" -ForegroundColor Green
Write-Host "========================================" -ForegroundColor Cyan
