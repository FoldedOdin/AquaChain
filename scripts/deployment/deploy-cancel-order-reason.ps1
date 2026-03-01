# Deploy cancel_order Lambda with cancellation reason support

$ErrorActionPreference = "Stop"

Write-Host "========================================" -ForegroundColor Cyan
Write-Host "Deploy Cancel Order Lambda" -ForegroundColor Cyan
Write-Host "========================================" -ForegroundColor Cyan
Write-Host ""

$FUNCTION_NAME = "aquachain-cancel-order-dev"
$REGION = "ap-south-1"

Write-Host "Step 1: Packaging Lambda function..." -ForegroundColor Yellow

$originalLocation = Get-Location

try {
    # Create temporary directory for packaging
    $tempDir = "lambda/orders/temp_cancel_package"
    if (Test-Path $tempDir) {
        Remove-Item $tempDir -Recurse -Force
    }
    New-Item -ItemType Directory -Path $tempDir -Force | Out-Null
    
    Write-Host "  Copying Lambda file..." -ForegroundColor White
    
    # Copy cancel_order.py to temp directory
    Copy-Item "lambda/orders/cancel_order.py" -Destination $tempDir -Force
    
    Write-Host "  ✓ File copied" -ForegroundColor Green
    
    # Create zip from temp directory
    Set-Location $tempDir
    
    Write-Host "  Creating deployment package..." -ForegroundColor White
    Compress-Archive -Path cancel_order.py -DestinationPath ../cancel-order-deployment.zip -Force
    
    Set-Location $originalLocation
    
    Write-Host "✓ Package created" -ForegroundColor Green
    
    # Upload to Lambda
    Write-Host ""
    Write-Host "Step 2: Uploading to Lambda..." -ForegroundColor Yellow
    
    $zipPath = "lambda/orders/cancel-order-deployment.zip"
    aws lambda update-function-code `
        --function-name $FUNCTION_NAME `
        --zip-file fileb://$zipPath `
        --region $REGION | Out-Null
    
    Write-Host "✓ Lambda code updated" -ForegroundColor Green
    
    # Wait for update to complete
    Write-Host "  Waiting for update to complete..." -ForegroundColor White
    Start-Sleep -Seconds 10
    
    # Verify the update worked
    Write-Host "  Verifying Lambda update..." -ForegroundColor White
    $updateStatus = aws lambda get-function `
        --function-name $FUNCTION_NAME `
        --region $REGION | ConvertFrom-Json
    
    if ($updateStatus.Configuration.LastUpdateStatus -eq "Successful") {
        Write-Host "  ✓ Lambda update verified" -ForegroundColor Green
    } else {
        Write-Host "  ⚠️  Lambda update status: $($updateStatus.Configuration.LastUpdateStatus)" -ForegroundColor Yellow
    }
    
    # Cleanup
    Remove-Item $zipPath -Force
    Remove-Item $tempDir -Recurse -Force
    
} catch {
    Write-Host "❌ Deployment failed" -ForegroundColor Red
    Write-Host $_.Exception.Message -ForegroundColor Red
    
    # Cleanup on error
    if (Test-Path "lambda/orders/cancel-order-deployment.zip") {
        Remove-Item "lambda/orders/cancel-order-deployment.zip" -Force
    }
    if (Test-Path "lambda/orders/temp_cancel_package") {
        Remove-Item "lambda/orders/temp_cancel_package" -Recurse -Force
    }
    
    Set-Location $originalLocation
    exit 1
} finally {
    Set-Location $originalLocation
}

Write-Host ""
Write-Host "========================================" -ForegroundColor Green
Write-Host "✓ Deployment Complete!" -ForegroundColor Green
Write-Host "========================================" -ForegroundColor Green
Write-Host ""

Write-Host "What was added:" -ForegroundColor Cyan
Write-Host "• Cancellation reason now captured from request body" -ForegroundColor White
Write-Host "• Reason stored in order record as 'cancellationReason'" -ForegroundColor White
Write-Host "• Reason included in status history message" -ForegroundColor White
Write-Host ""
Write-Host "Next Steps:" -ForegroundColor Cyan
Write-Host "1. Test order cancellation in the frontend" -ForegroundColor White
Write-Host "2. Verify cancellation reason modal appears" -ForegroundColor White
Write-Host "3. Check that reason is saved in DynamoDB" -ForegroundColor White
Write-Host ""
