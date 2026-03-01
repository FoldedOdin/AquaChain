# Deploy Service Request Lambda with Fixed Imports
# Fixes the "attempted relative import with no known parent package" error

Write-Host "=== Deploying Service Request Lambda ===" -ForegroundColor Cyan
Write-Host ""

$serviceDir = "lambda/technician_service"
$sharedDir = "lambda/shared"
$packageDir = "$serviceDir/package"
$deploymentPackage = "$serviceDir/service-request-deployment.zip"

# Clean up previous package
Write-Host "Step 1: Cleaning up previous deployment package..." -ForegroundColor Cyan
if (Test-Path $packageDir) {
    Remove-Item -Recurse -Force $packageDir
}
if (Test-Path $deploymentPackage) {
    Remove-Item -Force $deploymentPackage
}

# Create package directory
New-Item -ItemType Directory -Path $packageDir | Out-Null

# Install dependencies
Write-Host "Step 2: Installing Python dependencies..." -ForegroundColor Cyan
if (Test-Path "$serviceDir/requirements.txt") {
    pip install -r $serviceDir/requirements.txt -t $packageDir --quiet
    
    if ($LASTEXITCODE -ne 0) {
        Write-Host "✗ Failed to install dependencies" -ForegroundColor Red
        exit 1
    }
    Write-Host "  ✓ Dependencies installed" -ForegroundColor Green
} else {
    Write-Host "  ⚠ No requirements.txt found, skipping dependencies" -ForegroundColor Yellow
}

# Copy service files (all Python files in the service directory)
Write-Host "Step 3: Copying service files..." -ForegroundColor Cyan
$serviceFiles = @(
    "handler.py",
    "location_service.py",
    "availability_manager.py",
    "assignment_algorithm.py",
    "service_request_manager.py",
    "__init__.py"
)

foreach ($file in $serviceFiles) {
    $sourcePath = "$serviceDir/$file"
    if (Test-Path $sourcePath) {
        Copy-Item $sourcePath $packageDir/
        Write-Host "  ✓ Copied $file" -ForegroundColor Gray
    } else {
        Write-Host "  ⚠ $file not found, skipping" -ForegroundColor Yellow
    }
}

# Copy shared utilities
Write-Host "Step 4: Copying shared utilities..." -ForegroundColor Cyan
if (Test-Path $sharedDir) {
    $sharedFiles = Get-ChildItem -Path $sharedDir -Filter "*.py"
    foreach ($file in $sharedFiles) {
        Copy-Item $file.FullName $packageDir/
        Write-Host "  ✓ Copied $($file.Name)" -ForegroundColor Gray
    }
} else {
    Write-Host "  ⚠ Shared directory not found" -ForegroundColor Yellow
}

# Create deployment package
Write-Host "Step 5: Creating deployment package..." -ForegroundColor Cyan
Push-Location $packageDir
Compress-Archive -Path * -DestinationPath ../$([System.IO.Path]::GetFileName($deploymentPackage)) -Force
Pop-Location

$packageSize = (Get-Item $deploymentPackage).Length / 1MB
Write-Host "  ✓ Package created: $([math]::Round($packageSize, 2)) MB" -ForegroundColor Green

# Deploy to Lambda
Write-Host "Step 6: Deploying to AWS Lambda..." -ForegroundColor Cyan
$result = aws lambda update-function-code `
    --function-name aquachain-function-service-request-dev `
    --zip-file fileb://$deploymentPackage `
    --region ap-south-1 `
    --query '{FunctionName:FunctionName,LastModified:LastModified,CodeSize:CodeSize}' `
    --output json | ConvertFrom-Json

if ($LASTEXITCODE -eq 0) {
    Write-Host "  ✓ Lambda deployed successfully" -ForegroundColor Green
    Write-Host "    Function: $($result.FunctionName)" -ForegroundColor Gray
    Write-Host "    Modified: $($result.LastModified)" -ForegroundColor Gray
    Write-Host "    Size: $([math]::Round($result.CodeSize / 1MB, 2)) MB" -ForegroundColor Gray
} else {
    Write-Host "  ✗ Lambda deployment failed" -ForegroundColor Red
    exit 1
}

# Wait for Lambda to be ready
Write-Host ""
Write-Host "Step 7: Waiting for Lambda to be ready..." -ForegroundColor Cyan
Start-Sleep -Seconds 5

# Test the deployment
Write-Host "Step 8: Testing Lambda function..." -ForegroundColor Cyan

$testPayload = @{
    httpMethod = "GET"
    path = "/api/v1/service-requests"
    queryStringParameters = @{
        status = "assigned"
    }
    requestContext = @{
        authorizer = @{
            claims = @{
                sub = "test-user-123"
                "cognito:groups" = "technician"
            }
        }
    }
} | ConvertTo-Json -Depth 5 -Compress

$testResult = aws lambda invoke `
    --function-name aquachain-function-service-request-dev `
    --region ap-south-1 `
    --payload $testPayload `
    --cli-binary-format raw-in-base64-out `
    response.json

if ($LASTEXITCODE -eq 0) {
    $response = Get-Content response.json | ConvertFrom-Json
    Remove-Item response.json
    
    if ($response.statusCode -eq 200 -or $response.statusCode -eq 404) {
        Write-Host "  ✓ Lambda responding correctly" -ForegroundColor Green
        Write-Host "    Status Code: $($response.statusCode)" -ForegroundColor Gray
    } elseif ($response.statusCode -eq 502) {
        Write-Host "  ✗ Still getting 502 error" -ForegroundColor Red
        Write-Host "    Check CloudWatch logs for details" -ForegroundColor Yellow
    } else {
        Write-Host "  ⚠ Unexpected status code: $($response.statusCode)" -ForegroundColor Yellow
    }
} else {
    Write-Host "  ✗ Test invocation failed" -ForegroundColor Red
}

# Check CloudWatch logs
Write-Host ""
Write-Host "Step 9: Checking CloudWatch logs..." -ForegroundColor Cyan
Start-Sleep -Seconds 2

$logs = aws logs tail /aws/lambda/aquachain-function-service-request-dev `
    --since 1m `
    --format short `
    --region ap-south-1 2>&1 | Select-String -Pattern "ERROR|ImportError|ModuleNotFoundError|SUCCESS|Processing"

if ($logs) {
    Write-Host "  Recent log entries:" -ForegroundColor Gray
    $logs | ForEach-Object { 
        if ($_ -like "*ERROR*" -or $_ -like "*ImportError*" -or $_ -like "*ModuleNotFoundError*") {
            Write-Host "    $_" -ForegroundColor Red
        } else {
            Write-Host "    $_" -ForegroundColor Gray
        }
    }
} else {
    Write-Host "  No relevant log entries found" -ForegroundColor Gray
}

# Cleanup
Write-Host ""
Write-Host "Step 10: Cleaning up temporary files..." -ForegroundColor Cyan
Remove-Item -Recurse -Force $packageDir

Write-Host ""
Write-Host "=== Deployment Complete ===" -ForegroundColor Green
Write-Host ""
Write-Host "Summary:" -ForegroundColor White
Write-Host "  ✓ Service request Lambda updated" -ForegroundColor Green
Write-Host "  ✓ Fixed relative import issues" -ForegroundColor Green
Write-Host "  ✓ All dependencies packaged" -ForegroundColor Green
Write-Host ""
Write-Host "Next Steps:" -ForegroundColor Yellow
Write-Host "  1. Test the endpoint: GET /api/v1/service-requests" -ForegroundColor Gray
Write-Host "  2. Check technician dashboard for real data" -ForegroundColor Gray
Write-Host "  3. Monitor CloudWatch logs for any errors" -ForegroundColor Gray
Write-Host ""
Write-Host "If still getting 502 errors:" -ForegroundColor Yellow
Write-Host "  - Check CloudWatch logs: /aws/lambda/aquachain-function-service-request-dev" -ForegroundColor Gray
Write-Host "  - Verify environment variables are set correctly" -ForegroundColor Gray
Write-Host "  - Check IAM permissions for DynamoDB access" -ForegroundColor Gray
Write-Host ""
