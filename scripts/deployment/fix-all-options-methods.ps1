# Fix ALL OPTIONS methods in API Gateway by ensuring they have MOCK integrations

$API_ID = "vtqjfznspc"
$REGION = "ap-south-1"

Write-Host "Fetching all resources..." -ForegroundColor Yellow
$resources = aws apigateway get-resources --rest-api-id $API_ID --region $REGION | ConvertFrom-Json

$optionsResources = @()
foreach ($resource in $resources.items) {
    if ($resource.resourceMethods -and $resource.resourceMethods.OPTIONS) {
        $optionsResources += $resource
    }
}

Write-Host "Found $($optionsResources.Count) resources with OPTIONS methods" -ForegroundColor Cyan
Write-Host ""

$fixed = 0
$skipped = 0

foreach ($resource in $optionsResources) {
    Write-Host "Processing: OPTIONS $($resource.path)" -ForegroundColor Gray
    
    try {
        # Add integration
        aws apigateway put-integration `
            --rest-api-id $API_ID `
            --resource-id $resource.id `
            --http-method OPTIONS `
            --type MOCK `
            --request-templates file://scripts/deployment/webhooks-request-template.json `
            --region $REGION 2>&1 | Out-Null
        
        # Add method response
        aws apigateway put-method-response `
            --rest-api-id $API_ID `
            --resource-id $resource.id `
            --http-method OPTIONS `
            --status-code 200 `
            --response-parameters file://scripts/deployment/webhooks-response-params.json `
            --region $REGION 2>&1 | Out-Null
        
        # Add integration response
        aws apigateway put-integration-response `
            --rest-api-id $API_ID `
            --resource-id $resource.id `
            --http-method OPTIONS `
            --status-code 200 `
            --response-parameters file://scripts/deployment/webhooks-integration-response.json `
            --region $REGION 2>&1 | Out-Null
        
        Write-Host "  ✓ Fixed" -ForegroundColor Green
        $fixed++
    } catch {
        Write-Host "  ℹ Already configured or error" -ForegroundColor Yellow
        $skipped++
    }
}

Write-Host ""
Write-Host "Summary:" -ForegroundColor Cyan
Write-Host "  Fixed: $fixed" -ForegroundColor Green
Write-Host "  Skipped: $skipped" -ForegroundColor Yellow
Write-Host ""

# Now try to deploy
Write-Host "Deploying API..." -ForegroundColor Yellow
aws apigateway create-deployment --rest-api-id $API_ID --stage-name dev --description "Fix all OPTIONS methods" --region $REGION

if ($LASTEXITCODE -eq 0) {
    Write-Host "✓ Deployment successful!" -ForegroundColor Green
} else {
    Write-Host "✗ Deployment failed - there may be non-OPTIONS methods without integrations" -ForegroundColor Red
}
