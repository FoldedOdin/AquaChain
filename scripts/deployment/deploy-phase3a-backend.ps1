# Deploy Phase 3a Backend to AWS Lambda
# This script deploys the admin_service Lambda function with Phase 3a severity threshold features

param(
    [string]$FunctionName = "AquaChain-AdminService-dev",
    [string]$Region = "ap-south-1",
    [switch]$CreateBackup = $true,
    [switch]$SkipTests = $false
)

Write-Host "========================================" -ForegroundColor Cyan
Write-Host "  Phase 3a Backend Deployment" -ForegroundColor Cyan
Write-Host "========================================" -ForegroundColor Cyan
Write-Host ""
Write-Host "Function: $FunctionName" -ForegroundColor White
Write-Host "Region: $Region" -ForegroundColor White
Write-Host ""

# Step 1: Pre-deployment checks
Write-Host "[1/7] Pre-deployment checks..." -ForegroundColor Yellow

# Check AWS CLI
$awsAccount = aws sts get-caller-identity --query Account --output text 2>$null
if ($LASTEXITCODE -ne 0) {
    Write-Host "✗ AWS CLI not configured" -ForegroundColor Red
    exit 1
}
Write-Host "✓ AWS Account: $awsAccount" -ForegroundColor Green

# Check Lambda function exists
$functionExists = aws lambda get-function --function-name $FunctionName --region $Region 2>$null
if ($LASTEXITCODE -ne 0) {
    Write-Host "✗ Lambda function not found: $FunctionName" -ForegroundColor Red
    Write-Host "  Please create the function first or check the function name" -ForegroundColor Yellow
    exit 1
}
Write-Host "✓ Lambda function exists: $FunctionName" -ForegroundColor Green

# Step 2: Run tests (optional)
if (-not $SkipTests) {
    Write-Host ""
    Write-Host "[2/7] Running unit tests..." -ForegroundColor Yellow
    
    Push-Location lambda/admin_service
    
    # Check if pytest is available
    $pytestAvailable = Get-Command pytest -ErrorAction SilentlyContinue
    if ($pytestAvailable) {
        pytest tests/test_severity_validation.py -v
        if ($LASTEXITCODE -ne 0) {
            Write-Host "✗ Unit tests failed" -ForegroundColor Red
            Pop-Location
            exit 1
        }
        Write-Host "✓ Unit tests passed" -ForegroundColor Green
    } else {
        Write-Host "⚠ pytest not found, skipping tests" -ForegroundColor Yellow
        Write-Host "  Install with: pip install pytest" -ForegroundColor Gray
    }
    
    Pop-Location
} else {
    Write-Host ""
    Write-Host "[2/7] Skipping tests (--SkipTests flag)" -ForegroundColor Yellow
}

# Step 3: Create backup version
if ($CreateBackup) {
    Write-Host ""
    Write-Host "[3/7] Creating backup version..." -ForegroundColor Yellow
    
    $backupResult = aws lambda publish-version `
        --function-name $FunctionName `
        --description "Pre-Phase3a deployment backup" `
        --region $Region `
        2>&1
    
    if ($LASTEXITCODE -eq 0) {
        $versionNumber = ($backupResult | ConvertFrom-Json).Version
        Write-Host "✓ Backup version created: $versionNumber" -ForegroundColor Green
        Write-Host "  Rollback command: aws lambda update-alias --function-name $FunctionName --name live --function-version $versionNumber" -ForegroundColor Gray
    } else {
        Write-Host "⚠ Failed to create backup version (continuing anyway)" -ForegroundColor Yellow
    }
} else {
    Write-Host ""
    Write-Host "[3/7] Skipping backup (--CreateBackup=false)" -ForegroundColor Yellow
}

# Step 4: Create deployment package
Write-Host ""
Write-Host "[4/7] Creating deployment package..." -ForegroundColor Yellow

Push-Location lambda/admin_service

# Remove old packages
if (Test-Path "function.zip") {
    Remove-Item "function.zip" -Force
}
if (Test-Path "admin_service.zip") {
    Remove-Item "admin_service.zip" -Force
}

# Create zip with all Python files
try {
    if (Get-Command "7z" -ErrorAction SilentlyContinue) {
        # Use 7-Zip if available (better compression)
        7z a -tzip function.zip *.py 2>&1 | Out-Null
    } else {
        # Use PowerShell built-in
        $pythonFiles = Get-ChildItem -Filter "*.py"
        Compress-Archive -Path $pythonFiles -DestinationPath "function.zip" -Force
    }
    
    if (Test-Path "function.zip") {
        $zipSize = (Get-Item "function.zip").Length / 1KB
        Write-Host "✓ Package created: function.zip ($([math]::Round($zipSize, 2)) KB)" -ForegroundColor Green
    } else {
        Write-Host "✗ Failed to create deployment package" -ForegroundColor Red
        Pop-Location
        exit 1
    }
} catch {
    Write-Host "✗ Error creating package: $_" -ForegroundColor Red
    Pop-Location
    exit 1
}

# Step 5: Verify package contents
Write-Host ""
Write-Host "[5/7] Verifying package contents..." -ForegroundColor Yellow

$expectedFiles = @("handler.py", "config_validation.py")
$tempDir = "temp_verify_$(Get-Random)"

try {
    Expand-Archive -Path "function.zip" -DestinationPath $tempDir -Force
    $actualFiles = Get-ChildItem -Path $tempDir -Filter "*.py" | Select-Object -ExpandProperty Name
    
    $allPresent = $true
    foreach ($file in $expectedFiles) {
        if ($actualFiles -contains $file) {
            Write-Host "  ✓ $file" -ForegroundColor Green
        } else {
            Write-Host "  ✗ $file (MISSING)" -ForegroundColor Red
            $allPresent = $false
        }
    }
    
    Remove-Item -Recurse -Force $tempDir
    
    if (-not $allPresent) {
        Write-Host "✗ Package verification failed" -ForegroundColor Red
        Pop-Location
        exit 1
    }
    
    Write-Host "✓ Package verified" -ForegroundColor Green
} catch {
    Write-Host "⚠ Could not verify package contents: $_" -ForegroundColor Yellow
}

# Step 6: Deploy to AWS Lambda
Write-Host ""
Write-Host "[6/7] Deploying to AWS Lambda..." -ForegroundColor Yellow

$deployResult = aws lambda update-function-code `
    --function-name $FunctionName `
    --zip-file "fileb://function.zip" `
    --region $Region `
    2>&1

if ($LASTEXITCODE -eq 0) {
    Write-Host "✓ Code uploaded successfully" -ForegroundColor Green
    
    # Wait for function to be updated
    Write-Host "  Waiting for deployment to complete..." -ForegroundColor Gray
    aws lambda wait function-updated --function-name $FunctionName --region $Region
    
    if ($LASTEXITCODE -eq 0) {
        Write-Host "✓ Deployment completed" -ForegroundColor Green
    } else {
        Write-Host "⚠ Deployment may still be in progress" -ForegroundColor Yellow
    }
} else {
    Write-Host "✗ Deployment failed: $deployResult" -ForegroundColor Red
    Pop-Location
    exit 1
}

Pop-Location

# Step 7: Verify deployment
Write-Host ""
Write-Host "[7/7] Verifying deployment..." -ForegroundColor Yellow

$functionInfo = aws lambda get-function `
    --function-name $FunctionName `
    --region $Region `
    --query 'Configuration.[FunctionName,LastModified,State,Runtime]' `
    --output json | ConvertFrom-Json

Write-Host "  Function: $($functionInfo[0])" -ForegroundColor Gray
Write-Host "  Last Modified: $($functionInfo[1])" -ForegroundColor Gray
Write-Host "  State: $($functionInfo[2])" -ForegroundColor Gray
Write-Host "  Runtime: $($functionInfo[3])" -ForegroundColor Gray

if ($functionInfo[2] -eq "Active") {
    Write-Host "✓ Function is active and ready" -ForegroundColor Green
} else {
    Write-Host "⚠ Function state: $($functionInfo[2])" -ForegroundColor Yellow
}

# Check environment variables
Write-Host ""
Write-Host "Checking environment variables..." -ForegroundColor Yellow
$envVars = aws lambda get-function-configuration `
    --function-name $FunctionName `
    --region $Region `
    --query 'Environment.Variables' `
    --output json | ConvertFrom-Json

$requiredVars = @("CONFIG_TABLE", "CONFIG_HISTORY_TABLE", "AUDIT_TABLE")
foreach ($var in $requiredVars) {
    if ($envVars.PSObject.Properties.Name -contains $var) {
        Write-Host "  ✓ $var = $($envVars.$var)" -ForegroundColor Green
    } else {
        Write-Host "  ✗ $var (MISSING)" -ForegroundColor Red
    }
}

# Summary
Write-Host ""
Write-Host "========================================" -ForegroundColor Cyan
Write-Host "  Deployment Summary" -ForegroundColor Cyan
Write-Host "========================================" -ForegroundColor Cyan
Write-Host ""
Write-Host "✓ Phase 3a backend deployed successfully!" -ForegroundColor Green
Write-Host ""
Write-Host "Next Steps:" -ForegroundColor Yellow
Write-Host "  1. Monitor CloudWatch Logs for 10 minutes" -ForegroundColor White
Write-Host "     aws logs tail /aws/lambda/$FunctionName --follow" -ForegroundColor Gray
Write-Host ""
Write-Host "  2. Test API endpoints (see PHASE3A_DEPLOYMENT_GUIDE.md)" -ForegroundColor White
Write-Host ""
Write-Host "  3. Verify DynamoDB tables updated correctly" -ForegroundColor White
Write-Host ""
Write-Host "  4. Complete verification checklist" -ForegroundColor White
Write-Host "     DOCS/PHASE3A_VERIFICATION_CHECKLIST.md" -ForegroundColor Gray
Write-Host ""
Write-Host "  5. Deploy frontend (Task 3a.11)" -ForegroundColor White
Write-Host ""

Write-Host "Documentation:" -ForegroundColor Yellow
Write-Host "  Deployment Guide: DOCS/PHASE3A_DEPLOYMENT_GUIDE.md" -ForegroundColor Gray
Write-Host "  Verification Checklist: DOCS/PHASE3A_VERIFICATION_CHECKLIST.md" -ForegroundColor Gray
Write-Host ""

# Offer to tail logs
$tailLogs = Read-Host "Would you like to tail CloudWatch Logs now? (y/n)"
if ($tailLogs -eq "y" -or $tailLogs -eq "Y") {
    Write-Host ""
    Write-Host "Tailing logs (Ctrl+C to exit)..." -ForegroundColor Yellow
    aws logs tail "/aws/lambda/$FunctionName" --follow --region $Region
}

Write-Host ""
Write-Host "Deployment complete!" -ForegroundColor Green
Write-Host ""
