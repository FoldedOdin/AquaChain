# Check for methods without integrations
$API_ID = "vtqjfznspc"
$REGION = "ap-south-1"

Write-Host "Checking for methods without integrations..." -ForegroundColor Yellow
Write-Host ""

$resources = aws apigateway get-resources --rest-api-id $API_ID --region $REGION --output json | ConvertFrom-Json

$missingIntegrations = @()

foreach ($resource in $resources.items) {
    if ($resource.resourceMethods) {
        foreach ($method in $resource.resourceMethods.PSObject.Properties.Name) {
            try {
                $integration = aws apigateway get-integration `
                    --rest-api-id $API_ID `
                    --resource-id $resource.id `
                    --http-method $method `
                    --region $REGION `
                    --output json 2>&1
                
                if ($LASTEXITCODE -ne 0) {
                    $missingIntegrations += [PSCustomObject]@{
                        Path = $resource.path
                        Method = $method
                        ResourceId = $resource.id
                    }
                    Write-Host "✗ Missing integration: $method $($resource.path)" -ForegroundColor Red
                }
            } catch {
                $missingIntegrations += [PSCustomObject]@{
                    Path = $resource.path
                    Method = $method
                    ResourceId = $resource.id
                }
                Write-Host "✗ Missing integration: $method $($resource.path)" -ForegroundColor Red
            }
        }
    }
}

Write-Host ""
if ($missingIntegrations.Count -eq 0) {
    Write-Host "✓ All methods have integrations!" -ForegroundColor Green
} else {
    Write-Host "Found $($missingIntegrations.Count) methods without integrations:" -ForegroundColor Yellow
    $missingIntegrations | Format-Table -AutoSize
}
