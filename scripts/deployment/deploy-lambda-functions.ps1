# Deploy Lambda Functions with Fixed Imports
# Packages and deploys Lambda functions with shared utilities

param(
    [string]$Region = "ap-south-1",
    [string[]]$Functions = @("data_processing", "alert_detection", "notification_service")
)

Write-Host "=== Deploying Lambda Functions ===" -ForegroundColor Cyan
Write-Host "Region: $Region" -ForegroundColor White
Write-Host ""

$successCount = 0
$errorCount = 0

foreach ($functionName in $Functions) {
    Write-Host "Deploying: $functionName" -ForegroundColor Yellow
    
    $functionDir = "lambda/$functionName"
    
    # Map directory names to actual Lambda function names
    $lambdaNameMap = @{
        "data_processing" = "aquachain-function-data-processing-dev"
        "alert_detection" = "aquachain-function-alert-detection-dev"
        "notification_service" = "aquachain-function-notification-dev"
        "user_management" = "aquachain-function-user-management-dev"
    }
    
    $lambdaName = $lambdaNameMap[$functionName]
    if (-not $lambdaName) {
        Write-Host "  ✗ Unknown function name: $functionName" -ForegroundColor Red
        $errorCount++
        continue
    }
    
    if (-not (Test-Path $functionDir)) {
        Write-Host "  ✗ Directory not found: $functionDir" -ForegroundColor Red
        $errorCount++
        continue
    }
    
    try {
        # Create deployment package
        Write-Host "  Creating deployment package..." -ForegroundColor Gray
        
        Push-Location $functionDir
        
        # Remove old zip if exists
        if (Test-Path "function.zip") {
            Remove-Item "function.zip" -Force
        }
        
        # Create zip with all Python files
        if (Get-Command "7z" -ErrorAction SilentlyContinue) {
            # Use 7-Zip if available
            7z a -tzip function.zip *.py 2>&1 | Out-Null
        } elseif (Get-Command "Compress-Archive" -ErrorAction SilentlyContinue) {
            # Use PowerShell built-in
            Get-ChildItem -Filter "*.py" | Compress-Archive -DestinationPath "function.zip" -Force
        } else {
            Write-Host "  ✗ No zip utility found (need 7z or Compress-Archive)" -ForegroundColor Red
            Pop-Location
            $errorCount++
            continue
        }
        
        if (-not (Test-Path "function.zip")) {
            Write-Host "  ✗ Failed to create deployment package" -ForegroundColor Red
            Pop-Location
            $errorCount++
            continue
        }
        
        Write-Host "  ✓ Package created: function.zip" -ForegroundColor Green
        
        # Deploy to AWS Lambda
        Write-Host "  Deploying to AWS Lambda..." -ForegroundColor Gray
        
        $result = aws lambda update-function-code `
            --function-name $lambdaName `
            --zip-file "fileb://function.zip" `
            --region $Region `
            2>&1
        
        if ($LASTEXITCODE -eq 0) {
            Write-Host "  ✓ Deployed successfully" -ForegroundColor Green
            $successCount++
        } else {
            Write-Host "  ✗ Deployment failed: $result" -ForegroundColor Red
            $errorCount++
        }
        
        Pop-Location
        
    } catch {
        Write-Host "  ✗ Error: $_" -ForegroundColor Red
        $errorCount++
        if (Get-Location | Select-Object -ExpandProperty Path | Select-String "lambda") {
            Pop-Location
        }
    }
    
    Write-Host ""
}

Write-Host "=== Deployment Summary ===" -ForegroundColor Cyan
Write-Host "Successful: $successCount" -ForegroundColor Green
Write-Host "Failed: $errorCount" -ForegroundColor $(if ($errorCount -gt 0) { "Red" } else { "Green" })
Write-Host ""

if ($successCount -gt 0) {
    Write-Host "✓ Lambda functions deployed!" -ForegroundColor Green
    Write-Host ""
    Write-Host "Test your endpoints:" -ForegroundColor Yellow
    Write-Host "  .\scripts\testing\test-api-endpoints.ps1" -ForegroundColor Gray
    Write-Host ""
    Write-Host "Or refresh your dashboard:" -ForegroundColor Yellow
    Write-Host "  http://localhost:3000" -ForegroundColor Gray
}

if ($errorCount -gt 0) {
    Write-Host "⚠ Some deployments failed. Check errors above." -ForegroundColor Yellow
}

Write-Host ""
