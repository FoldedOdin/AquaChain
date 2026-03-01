# Recreate OPTIONS Methods with Proper CORS Configuration
# This deletes and recreates OPTIONS methods to fix the 500 error

$apiId = "vtqjfznspc"
$region = "ap-south-1"

Write-Host "========================================"
Write-Host "Recreating OPTIONS Methods"
Write-Host "========================================"
Write-Host ""

# Get resource IDs
Write-Host "Getting resource IDs..."
$devicesId = aws apigateway get-resources --rest-api-id $apiId --region $region --query "items[?path=='/api/devices'].id" --output text
$statsId = aws apigateway get-resources --rest-api-id $apiId --region $region --query "items[?path=='/dashboard/stats'].id" --output text
$alertsId = aws apigateway get-resources --rest-api-id $apiId --region $region --query "items[?path=='/alerts'].id" --output text
$latestId = aws apigateway get-resources --rest-api-id $apiId --region $region --query "items[?path=='/water-quality/latest'].id" --output text

Write-Host "  /api/devices: $devicesId"
Write-Host "  /dashboard/stats: $statsId"
Write-Host "  /alerts: $alertsId"
Write-Host "  /water-quality/latest: $latestId"
Write-Host ""

# Function to recreate OPTIONS method
function Recreate-OptionsMethod {
    param(
        [string]$ResourceId,
        [string]$ResourcePath
    )
    
    Write-Host "Processing $ResourcePath..."
    
    # Delete existing OPTIONS method
    Write-Host "  Deleting existing OPTIONS method..."
    aws apigateway delete-method `
        --rest-api-id $apiId `
        --region $region `
        --resource-id $ResourceId `
        --http-method OPTIONS `
        2>$null | Out-Null
    
    Start-Sleep -Seconds 1
    
    # Create OPTIONS method
    Write-Host "  Creating OPTIONS method..."
    aws apigateway put-method `
        --rest-api-id $apiId `
        --region $region `
        --resource-id $ResourceId `
        --http-method OPTIONS `
        --authorization-type NONE `
        --no-api-key-required `
        2>$null | Out-Null
    
    if ($LASTEXITCODE -ne 0) {
        Write-Host "  ✗ Failed to create method"
        return $false
    }
    
    # Create MOCK integration
    Write-Host "  Creating MOCK integration..."
    aws apigateway put-integration `
        --rest-api-id $apiId `
        --region $region `
        --resource-id $ResourceId `
        --http-method OPTIONS `
        --type MOCK `
        --request-templates '{\"application/json\":\"{\\\"statusCode\\\": 200}\"}' `
        2>$null | Out-Null
    
    if ($LASTEXITCODE -ne 0) {
        Write-Host "  ✗ Failed to create integration"
        return $false
    }
    
    # Create method response
    Write-Host "  Creating method response..."
    aws apigateway put-method-response `
        --rest-api-id $apiId `
        --region $region `
        --resource-id $ResourceId `
        --http-method OPTIONS `
        --status-code 200 `
        --response-parameters '{\"method.response.header.Access-Control-Allow-Headers\":false,\"method.response.header.Access-Control-Allow-Methods\":false,\"method.response.header.Access-Control-Allow-Origin\":false}' `
        2>$null | Out-Null
    
    if ($LASTEXITCODE -ne 0) {
        Write-Host "  ✗ Failed to create method response"
        return $false
    }
    
    # Create integration response with CORS headers
    Write-Host "  Creating integration response with CORS headers..."
    aws apigateway put-integration-response `
        --rest-api-id $apiId `
        --region $region `
        --resource-id $ResourceId `
        --http-method OPTIONS `
        --status-code 200 `
        --response-parameters '{\"method.response.header.Access-Control-Allow-Headers\":\"'"'"'Content-Type,Authorization,X-Amz-Date,X-Api-Key,X-Amz-Security-Token'"'"'\",\"method.response.header.Access-Control-Allow-Methods\":\"'"'"'GET,POST,PUT,DELETE,OPTIONS'"'"'\",\"method.response.header.Access-Control-Allow-Origin\":\"'"'"'*'"'"'\"}' `
        2>$null | Out-Null
    
    if ($LASTEXITCODE -eq 0) {
        Write-Host "  ✓ OPTIONS method recreated successfully"
        return $true
    } else {
        Write-Host "  ✗ Failed to create integration response"
        return $false
    }
}

# Recreate all OPTIONS methods
$success = $true
$success = $success -and (Recreate-OptionsMethod -ResourceId $devicesId -ResourcePath "/api/devices")
Write-Host ""
$success = $success -and (Recreate-OptionsMethod -ResourceId $statsId -ResourcePath "/dashboard/stats")
Write-Host ""
$success = $success -and (Recreate-OptionsMethod -ResourceId $alertsId -ResourcePath "/alerts")
Write-Host ""
$success = $success -and (Recreate-OptionsMethod -ResourceId $latestId -ResourcePath "/water-quality/latest")
Write-Host ""

if (-not $success) {
    Write-Host "⚠ Some OPTIONS methods failed to recreate"
    Write-Host "You may need to fix them manually in AWS Console"
    Write-Host ""
}

# Deploy API
Write-Host "Deploying API Gateway..."
$deploymentId = aws apigateway create-deployment `
    --rest-api-id $apiId `
    --region $region `
    --stage-name dev `
    --description "Recreated OPTIONS methods with proper CORS" `
    --query "id" `
    --output text

if ($LASTEXITCODE -eq 0) {
    Write-Host "✓ Deployment successful: $deploymentId"
} else {
    Write-Host "✗ Deployment failed"
    exit 1
}

Write-Host ""
Write-Host "========================================"
Write-Host "Testing OPTIONS Endpoints"
Write-Host "========================================"
Write-Host ""

# Wait for deployment to propagate
Write-Host "Waiting 5 seconds for deployment to propagate..."
Start-Sleep -Seconds 5

# Test each endpoint
function Test-OptionsEndpoint {
    param([string]$Path)
    
    $url = "https://vtqjfznspc.execute-api.ap-south-1.amazonaws.com/dev$Path"
    Write-Host "Testing $Path..."
    
    $response = curl -X OPTIONS $url -s -o /dev/null -w "%{http_code}"
    
    if ($response -eq "200") {
        Write-Host "  ✓ Returns 200 OK"
        return $true
    } else {
        Write-Host "  ✗ Returns $response (expected 200)"
        return $false
    }
}

$allPassed = $true
$allPassed = $allPassed -and (Test-OptionsEndpoint -Path "/api/devices")
$allPassed = $allPassed -and (Test-OptionsEndpoint -Path "/dashboard/stats")
$allPassed = $allPassed -and (Test-OptionsEndpoint -Path "/alerts")
$allPassed = $allPassed -and (Test-OptionsEndpoint -Path "/water-quality/latest")

Write-Host ""
if ($allPassed) {
    Write-Host "========================================"
    Write-Host "✓ All OPTIONS Methods Working!"
    Write-Host "========================================"
    Write-Host ""
    Write-Host "Next steps:"
    Write-Host "1. Refresh your dashboard"
    Write-Host "2. CORS errors should be gone"
    Write-Host "3. Check for any remaining errors (404, 500, etc.)"
} else {
    Write-Host "========================================"
    Write-Host "⚠ Some OPTIONS Methods Still Failing"
    Write-Host "========================================"
    Write-Host ""
    Write-Host "Please check AWS Console for errors"
}
