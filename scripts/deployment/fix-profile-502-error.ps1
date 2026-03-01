# Fix Profile Update 502 Error
# This script deploys the updated Lambda code with better error handling
# and checks CloudWatch logs for the root cause

$ErrorActionPreference = "Stop"

Write-Host "========================================" -ForegroundColor Cyan
Write-Host "Fix Profile Update 502 Error" -ForegroundColor Cyan
Write-Host "========================================" -ForegroundColor Cyan
Write-Host ""

$FUNCTION_NAME = "aquachain-function-user-management-dev"
$REGION = "ap-south-1"

# Step 1: Check current Lambda configuration
Write-Host "Step 1: Checking Lambda configuration..." -ForegroundColor Yellow
try {
    $config = aws lambda get-function-configuration `
        --function-name $FUNCTION_NAME `
        --region $REGION | ConvertFrom-Json
    
    Write-Host "✓ Lambda found" -ForegroundColor Green
    Write-Host "  Runtime: $($config.Runtime)" -ForegroundColor White
    Write-Host "  Timeout: $($config.Timeout) seconds" -ForegroundColor White
    Write-Host "  Memory: $($config.MemorySize) MB" -ForegroundColor White
    Write-Host "  Last Modified: $($config.LastModified)" -ForegroundColor White
    
    # Check if timeout is too low
    if ($config.Timeout -lt 30) {
        Write-Host "⚠️  Warning: Timeout is low ($($config.Timeout)s). Increasing to 30s..." -ForegroundColor Yellow
        aws lambda update-function-configuration `
            --function-name $FUNCTION_NAME `
            --timeout 30 `
            --region $REGION | Out-Null
        Write-Host "✓ Timeout increased to 30 seconds" -ForegroundColor Green
        Start-Sleep -Seconds 3
    }
    
} catch {
    Write-Host "❌ Failed to get Lambda configuration" -ForegroundColor Red
    Write-Host $_.Exception.Message -ForegroundColor Red
    exit 1
}

# Step 2: Check recent CloudWatch logs for errors
Write-Host ""
Write-Host "Step 2: Checking recent CloudWatch logs..." -ForegroundColor Yellow
try {
    $logGroup = "/aws/lambda/$FUNCTION_NAME"
    
    # Get the most recent log stream
    $streams = aws logs describe-log-streams `
        --log-group-name $logGroup `
        --order-by LastEventTime `
        --descending `
        --max-items 1 `
        --region $REGION | ConvertFrom-Json
    
    if ($streams.logStreams.Count -gt 0) {
        $latestStream = $streams.logStreams[0].logStreamName
        Write-Host "✓ Found recent log stream: $latestStream" -ForegroundColor Green
        
        # Get recent log events
        Write-Host ""
        Write-Host "Recent errors from CloudWatch:" -ForegroundColor Cyan
        Write-Host "----------------------------------------" -ForegroundColor Gray
        
        $logs = aws logs get-log-events `
            --log-group-name $logGroup `
            --log-stream-name $latestStream `
            --limit 50 `
            --region $REGION | ConvertFrom-Json
        
        $errorFound = $false
        foreach ($event in $logs.events) {
            $message = $event.message
            if ($message -match "ERROR|Error|error|Exception|Traceback|502|500") {
                Write-Host $message -ForegroundColor Red
                $errorFound = $true
            }
        }
        
        if (-not $errorFound) {
            Write-Host "No recent errors found in logs" -ForegroundColor Green
        }
        Write-Host "----------------------------------------" -ForegroundColor Gray
    }
    
} catch {
    Write-Host "⚠️  Could not retrieve CloudWatch logs" -ForegroundColor Yellow
    Write-Host $_.Exception.Message -ForegroundColor Yellow
}

# Step 3: Package and deploy updated Lambda
Write-Host ""
Write-Host "Step 3: Deploying updated Lambda code..." -ForegroundColor Yellow

$originalLocation = Get-Location

try {
    # Create temporary directory for packaging
    $tempDir = "lambda/user_management/temp_package"
    if (Test-Path $tempDir) {
        Remove-Item $tempDir -Recurse -Force
    }
    New-Item -ItemType Directory -Path $tempDir -Force | Out-Null
    
    Write-Host "  Copying Lambda files..." -ForegroundColor White
    
    # Copy all Python files to temp directory (flat structure)
    Copy-Item "lambda/user_management/*.py" -Destination $tempDir -Force
    
    # Count files
    $files = Get-ChildItem -Path $tempDir -Filter "*.py" -File
    
    if ($files.Count -eq 0) {
        throw "No Python files found in lambda/user_management"
    }
    
    Write-Host "  Found $($files.Count) Python files" -ForegroundColor White
    
    # Create zip from temp directory
    Set-Location $tempDir
    
    Write-Host "  Creating deployment package..." -ForegroundColor White
    
    # Use 7-Zip if available for better compatibility, otherwise use Compress-Archive
    if (Get-Command "7z" -ErrorAction SilentlyContinue) {
        7z a -tzip ../deployment.zip * | Out-Null
    } else {
        Compress-Archive -Path * -DestinationPath ../deployment.zip -Force
    }
    
    Set-Location $originalLocation
    
    Write-Host "✓ Package created" -ForegroundColor Green
    
    # Verify handler.py exists in the zip
    Write-Host "  Verifying package contents..." -ForegroundColor White
    $zipPath = "lambda/user_management/deployment.zip"
    
    if (Test-Path $zipPath) {
        # Check if handler.py is in the zip
        Add-Type -AssemblyName System.IO.Compression.FileSystem
        $zip = [System.IO.Compression.ZipFile]::OpenRead((Resolve-Path $zipPath))
        $hasHandler = $zip.Entries | Where-Object { $_.Name -eq "handler.py" }
        $zip.Dispose()
        
        if ($hasHandler) {
            Write-Host "  ✓ handler.py found in package" -ForegroundColor Green
        } else {
            throw "handler.py not found in deployment package!"
        }
    }
    
    # Upload to Lambda
    Write-Host "  Uploading to Lambda..." -ForegroundColor White
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
    if (Test-Path "lambda/user_management/deployment.zip") {
        Remove-Item "lambda/user_management/deployment.zip" -Force
    }
    if (Test-Path "lambda/user_management/temp_package") {
        Remove-Item "lambda/user_management/temp_package" -Recurse -Force
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

# Step 4: Provide next steps
Write-Host "Next Steps:" -ForegroundColor Cyan
Write-Host "1. Test the profile update endpoint in your browser" -ForegroundColor White
Write-Host "2. If still getting 502, run this command to see live logs:" -ForegroundColor White
Write-Host "   aws logs tail /aws/lambda/$FUNCTION_NAME --follow --region $REGION" -ForegroundColor Yellow
Write-Host ""
Write-Host "3. Or use the debug script:" -ForegroundColor White
Write-Host "   .\scripts\testing\debug-profile-502.ps1" -ForegroundColor Yellow
Write-Host ""

# Step 5: Check if the issue is with the data structure
Write-Host "Common Issues to Check:" -ForegroundColor Cyan
Write-Host "• Phone number stored as 'profile.phone' in DynamoDB" -ForegroundColor White
Write-Host "• Frontend expects 'profile.phone' in response" -ForegroundColor White
Write-Host "• Lambda timeout (now set to 30s)" -ForegroundColor White
Write-Host "• DynamoDB table permissions" -ForegroundColor White
Write-Host "• Cache service connectivity (Redis)" -ForegroundColor White
Write-Host ""
