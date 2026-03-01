# Fix OPTIONS Methods - Final Approach
# Uses file-based templates to avoid escaping issues

$apiId = "vtqjfznspc"
$region = "ap-south-1"

# Resource IDs
$resources = @{
    "/api/devices" = "tg7v66"
    "/dashboard/stats" = "24ycy9"
    "/alerts" = "9wcsnm"
    "/water-quality/latest" = "hi5fic"
}

Write-Host "========================================"
Write-Host "Fixing OPTIONS Methods"
Write-Host "========================================"
Write-Host ""

# Create request template file
$requestTemplate = @{
    "application/json" = '{"statusCode": 200}'
}
$requestTemplate | ConvertTo-Json -Depth 10 | Out-File -FilePath "temp-request-template.json" -Encoding utf8

# Create response parameters file
$responseParams = @{
    "method.response.header.Access-Control-Allow-Headers" = "'Content-Type,Authorization,X-Amz-Date,X-Api-Key,X-Amz-Security-Token'"
    "method.response.header.Access-Control-Allow-Methods" = "'GET,POST,PUT,DELETE,OPTIONS'"
    "method.response.header.Access-Control-Allow-Origin" = "'*'"
}
$responseParams | ConvertTo-Json -Depth 10 | Out-File -FilePath "temp-response-params.json" -Encoding utf8

foreach ($path in $resources.Keys) {
    $resourceId = $resources[$path]
    Write-Host "Fixing OPTIONS for $path (ID: $resourceId)..."
    
    # 1. Put integration with request template
    Write-Host "  Setting MOCK integration..."
    aws apigateway put-integration `
        --rest-api-id $apiId `
        --region $region `
        --resource-id $resourceId `
        --http-method OPTIONS `
        --type MOCK `
        --request-templates file://temp-request-template.json `
        2>$null | Out-Null
    
    if ($LASTEXITCODE -ne 0) {
        Write-Host "  ✗ Failed to set integration"
        continue
    }
    
    # 2. Put method response
    Write-Host "  Setting method response..."
    aws apigateway put-method-response `
        --rest-api-id $apiId `
        --region $region `
        --resource-id $resourceId `
        --http-method OPTIONS `
        --status-code 200 `
        --response-parameters '{\"method.response.header.Access-Control-Allow-Headers\":false,\"method.response.header.Access-Control-Allow-Methods\":false,\"method.response.header.Access-Control-Allow-Origin\":false}' `
        2>$null | Out-Null
    
    if ($LASTEXITCODE -ne 0) {
        Write-Host "  ✗ Failed to set method response"
        continue
    }
    
    # 3. Put integration response with CORS headers
    Write-Host "  Setting integration response with CORS headers..."
    aws apigateway put-integration-response `
        --rest-api-id $apiId `
        --region $region `
        --resource-id $resourceId `
        --http-method OPTIONS `
        --status-code 200 `
        --response-parameters file://temp-response-params.json `
        2>$null | Out-Null
    
    if ($LASTEXITCODE -eq 0) {
        Write-Host "  ✓ OPTIONS configured successfully"
    } else {
        Write-Host "  ✗ Failed to set integration response"
    }
    
    Write-Host ""
}

# Clean up temp files
Remove-Item "temp-request-template.json" -ErrorAction SilentlyContinue
Remove-Item "temp-response-params.json" -ErrorAction SilentlyContinue

# Deploy API
Write-Host "Deploying API Gateway..."
$deploymentId = aws apigateway create-deployment `
    --rest-api-id $apiId `
    --region $region `
    --stage-name dev `
    --description "Fixed OPTIONS CORS configuration" `
    --query "id" `
    --output text

if ($LASTEXITCODE -eq 0) {
    Write-Host "✓ Deployment successful: $deploymentId"
} else {
    Write-Host "✗ Deployment failed"
    exit 1
}

Write-Host ""
Write-Host "Waiting 5 seconds for deployment to propagate..."
Start-Sleep -Seconds 5

Write-Host ""
Write-Host "========================================"
Write-Host "Testing OPTIONS Endpoints"
Write-Host "========================================"
Write-Host ""

$allPassed = $true

foreach ($path in $resources.Keys) {
    $url = "https://vtqjfznspc.execute-api.ap-south-1.amazonaws.com/dev$path"
    Write-Host "Testing $path..."
    
    $response = curl -X OPTIONS $url -s -o /dev/null -w "%{http_code}"
    
    if ($response -eq "200") {
        Write-Host "  ✓ Returns 200 OK"
    } else {
        Write-Host "  ✗ Returns $response (expected 200)"
        $allPassed = $false
    }
}

Write-Host ""
if ($allPassed) {
    Write-Host "========================================"
    Write-Host "✓ SUCCESS! All OPTIONS Methods Working!"
    Write-Host "========================================"
    Write-Host ""
    Write-Host "Next steps:"
    Write-Host "1. Refresh your dashboard (Ctrl+Shift+R)"
    Write-Host "2. CORS errors should be gone"
    Write-Host "3. Check for any remaining errors"
} else {
    Write-Host "========================================"
    Write-Host "⚠ Some OPTIONS Methods Still Failing"
    Write-Host "========================================"
    Write-Host ""
    Write-Host "Check CloudWatch Logs for API Gateway:"
    Write-Host "aws logs tail /aws/apigateway/$apiId --follow --region $region"
}
