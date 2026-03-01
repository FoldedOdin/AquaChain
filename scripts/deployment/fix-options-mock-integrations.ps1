# Fix MOCK Integration Request Templates for OPTIONS Methods
# This fixes the 500 Internal Server Error on OPTIONS requests

$apiId = "vtqjfznspc"
$region = "ap-south-1"

Write-Host "========================================"
Write-Host "Fixing OPTIONS MOCK Integrations"
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

# Function to fix OPTIONS integration
function Fix-OptionsIntegration {
    param(
        [string]$ResourceId,
        [string]$ResourcePath
    )
    
    Write-Host "Fixing OPTIONS for $ResourcePath..."
    
    # Update integration request template
    aws apigateway put-integration `
        --rest-api-id $apiId `
        --region $region `
        --resource-id $ResourceId `
        --http-method OPTIONS `
        --type MOCK `
        --request-templates '{\"application/json\":\"{\\\"statusCode\\\": 200}\"}' `
        2>$null | Out-Null
    
    if ($LASTEXITCODE -eq 0) {
        Write-Host "  ✓ Integration request template updated"
    } else {
        Write-Host "  ✗ Failed to update integration request template"
    }
    
    # Ensure method response exists
    aws apigateway put-method-response `
        --rest-api-id $apiId `
        --region $region `
        --resource-id $ResourceId `
        --http-method OPTIONS `
        --status-code 200 `
        --response-parameters '{\"method.response.header.Access-Control-Allow-Headers\":false,\"method.response.header.Access-Control-Allow-Methods\":false,\"method.response.header.Access-Control-Allow-Origin\":false}' `
        2>$null | Out-Null
    
    # Update integration response with proper CORS headers
    aws apigateway put-integration-response `
        --rest-api-id $apiId `
        --region $region `
        --resource-id $ResourceId `
        --http-method OPTIONS `
        --status-code 200 `
        --response-parameters '{\"method.response.header.Access-Control-Allow-Headers\":\"'"'"'Content-Type,Authorization,X-Amz-Date,X-Api-Key,X-Amz-Security-Token'"'"'\",\"method.response.header.Access-Control-Allow-Methods\":\"'"'"'GET,POST,PUT,DELETE,OPTIONS'"'"'\",\"method.response.header.Access-Control-Allow-Origin\":\"'"'"'*'"'"'\"}' `
        2>$null | Out-Null
    
    if ($LASTEXITCODE -eq 0) {
        Write-Host "  ✓ Integration response updated with CORS headers"
    } else {
        Write-Host "  ✗ Failed to update integration response"
    }
    
    Write-Host ""
}

# Fix all OPTIONS integrations
Fix-OptionsIntegration -ResourceId $devicesId -ResourcePath "/api/devices"
Fix-OptionsIntegration -ResourceId $statsId -ResourcePath "/dashboard/stats"
Fix-OptionsIntegration -ResourceId $alertsId -ResourcePath "/alerts"
Fix-OptionsIntegration -ResourceId $latestId -ResourcePath "/water-quality/latest"

# Deploy API
Write-Host "Deploying API Gateway..."
$deploymentId = aws apigateway create-deployment `
    --rest-api-id $apiId `
    --region $region `
    --stage-name dev `
    --description "Fixed OPTIONS MOCK integration templates" `
    --query "id" `
    --output text

if ($LASTEXITCODE -eq 0) {
    Write-Host "  ✓ Deployment successful: $deploymentId"
} else {
    Write-Host "  ✗ Deployment failed"
    exit 1
}

Write-Host ""
Write-Host "========================================"
Write-Host "Testing OPTIONS Endpoints"
Write-Host "========================================"
Write-Host ""

# Test each endpoint
Write-Host "Testing /api/devices..."
$response = curl -X OPTIONS https://vtqjfznspc.execute-api.ap-south-1.amazonaws.com/dev/api/devices -s -o /dev/null -w "%{http_code}"
if ($response -eq "200") {
    Write-Host "  ✓ Returns 200 OK"
} else {
    Write-Host "  ✗ Returns $response (expected 200)"
}

Write-Host "Testing /dashboard/stats..."
$response = curl -X OPTIONS https://vtqjfznspc.execute-api.ap-south-1.amazonaws.com/dev/dashboard/stats -s -o /dev/null -w "%{http_code}"
if ($response -eq "200") {
    Write-Host "  ✓ Returns 200 OK"
} else {
    Write-Host "  ✗ Returns $response (expected 200)"
}

Write-Host "Testing /alerts..."
$response = curl -X OPTIONS https://vtqjfznspc.execute-api.ap-south-1.amazonaws.com/dev/alerts -s -o /dev/null -w "%{http_code}"
if ($response -eq "200") {
    Write-Host "  ✓ Returns 200 OK"
} else {
    Write-Host "  ✗ Returns $response (expected 200)"
}

Write-Host "Testing /water-quality/latest..."
$response = curl -X OPTIONS https://vtqjfznspc.execute-api.ap-south-1.amazonaws.com/dev/water-quality/latest -s -o /dev/null -w "%{http_code}"
if ($response -eq "200") {
    Write-Host "  ✓ Returns 200 OK"
} else {
    Write-Host "  ✗ Returns $response (expected 200)"
}

Write-Host ""
Write-Host "========================================"
Write-Host "OPTIONS Fix Complete!"
Write-Host "========================================"
Write-Host ""
Write-Host "Next steps:"
Write-Host "1. Refresh your dashboard"
Write-Host "2. Check if CORS errors are gone"
Write-Host "3. If you see 404 or other errors, Lambda functions may need path routing updates"
