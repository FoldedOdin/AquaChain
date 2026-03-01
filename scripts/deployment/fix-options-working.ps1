# Fix OPTIONS Methods - Working Approach
# Step-by-step configuration matching working endpoints

$apiId = "vtqjfznspc"
$region = "ap-south-1"

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

foreach ($path in $resources.Keys) {
    $resourceId = $resources[$path]
    Write-Host "Configuring OPTIONS for $path..."
    
    # Step 1: Ensure method response exists
    Write-Host "  Creating method response..."
    aws apigateway put-method-response `
        --rest-api-id $apiId `
        --region $region `
        --resource-id $resourceId `
        --http-method OPTIONS `
        --status-code 200 `
        2>$null | Out-Null
    
    # Step 2: Add response parameters to method response
    Write-Host "  Adding response parameters..."
    aws apigateway update-method-response `
        --rest-api-id $apiId `
        --region $region `
        --resource-id $resourceId `
        --http-method OPTIONS `
        --status-code 200 `
        --patch-operations `
            "op=add,path=/responseParameters/method.response.header.Access-Control-Allow-Headers,value=false" `
            "op=add,path=/responseParameters/method.response.header.Access-Control-Allow-Methods,value=false" `
            "op=add,path=/responseParameters/method.response.header.Access-Control-Allow-Origin,value=false" `
        2>$null | Out-Null
    
    # Step 3: Add integration response with CORS header values
    Write-Host "  Setting integration response with CORS headers..."
    aws apigateway put-integration-response `
        --rest-api-id $apiId `
        --region $region `
        --resource-id $resourceId `
        --http-method OPTIONS `
        --status-code 200 `
        --response-parameters `
            "method.response.header.Access-Control-Allow-Headers='Content-Type,Authorization,X-Amz-Date,X-Api-Key,X-Amz-Security-Token'" `
            "method.response.header.Access-Control-Allow-Methods='GET,POST,PUT,DELETE,OPTIONS'" `
            "method.response.header.Access-Control-Allow-Origin='*'" `
        2>$null | Out-Null
    
    if ($LASTEXITCODE -eq 0) {
        Write-Host "  ✓ Configured successfully"
    } else {
        Write-Host "  ✗ Failed"
    }
    
    Write-Host ""
}

# Deploy API
Write-Host "Deploying API Gateway..."
$deploymentId = aws apigateway create-deployment `
    --rest-api-id $apiId `
    --region $region `
    --stage-name dev `
    --description "Fixed OPTIONS CORS - working approach" `
    --query "id" `
    --output text

if ($LASTEXITCODE -eq 0) {
    Write-Host "✓ Deployment successful: $deploymentId"
} else {
    Write-Host "✗ Deployment failed"
    exit 1
}

Write-Host ""
Write-Host "Waiting 5 seconds for deployment..."
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
        Write-Host "  ✗ Returns $response"
        $allPassed = $false
    }
}

Write-Host ""
if ($allPassed) {
    Write-Host "========================================"
    Write-Host "✓✓✓ SUCCESS! All OPTIONS Working! ✓✓✓"
    Write-Host "========================================"
    Write-Host ""
    Write-Host "Refresh your dashboard now!"
    Write-Host "CORS errors should be gone."
} else {
    Write-Host "Still having issues. Check AWS Console."
}
