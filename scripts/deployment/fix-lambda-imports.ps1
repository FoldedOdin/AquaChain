# Fix Lambda Import Errors - Copy Shared Utilities
# Copies shared utilities into Lambda function directories

Write-Host "=== Fixing Lambda Import Errors ===" -ForegroundColor Cyan
Write-Host ""

$lambdaFunctions = @(
    "data_processing",
    "alert_detection",
    "notification_service",
    "user_management"
)

$sharedFiles = @(
    "cors_utils.py",
    "errors.py",
    "error_handler.py",
    "structured_logger.py"
)

$successCount = 0
$errorCount = 0

foreach ($function in $lambdaFunctions) {
    Write-Host "Processing: lambda/$function" -ForegroundColor Yellow
    
    $targetDir = "lambda/$function"
    
    if (-not (Test-Path $targetDir)) {
        Write-Host "  ✗ Directory not found: $targetDir" -ForegroundColor Red
        $errorCount++
        continue
    }
    
    # Copy each shared file
    foreach ($file in $sharedFiles) {
        $sourcePath = "lambda/shared/$file"
        $targetPath = "$targetDir/$file"
        
        if (Test-Path $sourcePath) {
            try {
                Copy-Item -Path $sourcePath -Destination $targetPath -Force
                Write-Host "  ✓ Copied $file" -ForegroundColor Green
            } catch {
                Write-Host "  ✗ Failed to copy $file : $_" -ForegroundColor Red
                $errorCount++
            }
        } else {
            Write-Host "  ⚠ Source file not found: $sourcePath" -ForegroundColor Yellow
        }
    }
    
    $successCount++
    Write-Host ""
}

Write-Host "=== Summary ===" -ForegroundColor Cyan
Write-Host "Functions processed: $successCount" -ForegroundColor Green
if ($errorCount -gt 0) {
    Write-Host "Errors: $errorCount" -ForegroundColor Red
}

Write-Host ""
Write-Host "Next steps:" -ForegroundColor Yellow
Write-Host "1. Deploy the updated Lambda functions:" -ForegroundColor White
Write-Host "   .\scripts\deployment\deploy-lambda-functions.ps1" -ForegroundColor Gray
Write-Host ""
Write-Host "2. Or deploy individually:" -ForegroundColor White
Write-Host "   cd lambda/data_processing && zip -r function.zip . && aws lambda update-function-code ..." -ForegroundColor Gray
Write-Host ""
