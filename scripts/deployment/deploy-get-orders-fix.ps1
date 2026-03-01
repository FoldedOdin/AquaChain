# Deploy get_orders Lambda with address fix
# This fixes the missing address and phone fields in order details

$ErrorActionPreference = "Stop"

Write-Host "========================================" -ForegroundColor Cyan
Write-Host "Deploy Get Orders Lambda Fix" -ForegroundColor Cyan
Write-Host "========================================" -ForegroundColor Cyan
Write-Host ""

$FUNCTION_NAME = "aquachain-get-orders-dev"
$REGION = "ap-south-1"

Write-Host "Step 1: Packaging Lambda function..." -ForegroundColor Yellow

$originalLocation = Get-Location

try {
    # Create temporary directory for packaging
    $tempDir = "lambda/orders/temp_package"
    if (Test-Path $tempDir) {
        Remove-Item $tempDir -Recurse -Force
    }
    New-Item -ItemType Directory -Path $tempDir -Force | Out-Null
    
    Write-Host "  Copying Lambda file..." -ForegroundColor White
    
    # Copy get_orders.py to temp directory (keep original name)
    Copy-Item "lambda/orders/get_orders.py" -Destination $tempDir -Force
    
    Write-Host "  ✓ File copied" -ForegroundColor Green
    
    # Create zip from temp directory
    Set-Location $tempDir
    
    Write-Host "  Creating deployment package..." -ForegroundColor White
    Compress-Archive -Path get_orders.py -DestinationPath ../get-orders-deployment.zip -Force
    
    Set-Location $originalLocation
    
    Write-Host "✓ Package created" -ForegroundColor Green
    
    # Verify handler.py exists in the zip
    Write-Host "  Verifying package contents..." -ForegroundColor White
    $zipPath = "lambda/orders/get-orders-deployment.zip"
    
    if (Test-Path $zipPath) {
        Add-Type -AssemblyName System.IO.Compression.FileSystem
        $zip = [System.IO.Compression.ZipFile]::OpenRead((Resolve-Path $zipPath))
        $hasHandler = $zip.Entries | Where-Object { $_.Name -eq "get_orders.py" }
        $zip.Dispose()
        
        if ($hasHandler) {
            Write-Host "  ✓ get_orders.py found in package" -ForegroundColor Green
        } else {
            throw "get_orders.py not found in deployment package!"
        }
    }
    
    # Upload to Lambda
    Write-Host ""
    Write-Host "Step 2: Uploading to Lambda..." -ForegroundColor Yellow
    
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
    if (Test-Path "lambda/orders/get-orders-deployment.zip") {
        Remove-Item "lambda/orders/get-orders-deployment.zip" -Force
    }
    if (Test-Path "lambda/orders/temp_package") {
        Remove-Item "lambda/orders/temp_package" -Recurse -Force
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

Write-Host "What was fixed:" -ForegroundColor Cyan
Write-Host "• Added 'address' field (flattened from deliveryAddress)" -ForegroundColor White
Write-Host "• Added 'phone' field (extracted from contactInfo)" -ForegroundColor White
Write-Host "• Address formatted as: street, city, state, pincode" -ForegroundColor White
Write-Host ""
Write-Host "Next Steps:" -ForegroundColor Cyan
Write-Host "1. Refresh your browser to see the updated order details" -ForegroundColor White
Write-Host "2. Check that address and phone now display correctly" -ForegroundColor White
Write-Host ""
