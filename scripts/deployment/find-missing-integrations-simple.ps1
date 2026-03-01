$API_ID = "vtqjfznspc"
$REGION = "ap-south-1"

# Get all resources
$resources = aws apigateway get-resources --rest-api-id $API_ID --region $REGION | ConvertFrom-Json

$missing = @()

foreach ($resource in $resources.items) {
    if ($resource.resourceMethods) {
        foreach ($method in $resource.resourceMethods.PSObject.Properties.Name) {
            try {
                $null = aws apigateway get-integration --rest-api-id $API_ID --resource-id $resource.id --http-method $method --region $REGION 2>&1
                if ($LASTEXITCODE -ne 0) {
                    $missing += "$method $($resource.path) ($($resource.id))"
                    Write-Host "✗ $method $($resource.path)" -ForegroundColor Red
                }
            } catch {
                $missing += "$method $($resource.path) ($($resource.id))"
                Write-Host "✗ $method $($resource.path)" -ForegroundColor Red
            }
        }
    }
}

Write-Host ""
Write-Host "Total missing: $($missing.Count)" -ForegroundColor Yellow
$missing
